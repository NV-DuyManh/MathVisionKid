# Runtime publisher cell for the isolated T4 budget branch. This file is code only;
# importing/defining it does not authenticate or contact Drive. The entry cell starts
# one bounded daemon thread; credentials/API are constructed inside that thread only.
import hashlib, json, os, pathlib, sys, threading, time, traceback, zipfile, gzip, shutil
from datetime import datetime, timezone

assert 'budget_root' in globals() and pathlib.Path(budget_root).name == 'mathvisionkid_t4_budget_3h_20261023'
assert 'budget_status' in globals() and budget_status.get('schema') == 'MathVisionKid.T4_budget3h.v1'
if globals().get('budget_publisher_thread') and budget_publisher_thread.is_alive():
    print(json.dumps({'publisher_started':False,'reason':'publisher thread already alive'}))
else:
    def _pub_sha(path):
        h=hashlib.sha256()
        with pathlib.Path(path).open('rb') as f:
            for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
        return h.hexdigest()
    def _pub_atomic_json(path,obj):
        path=pathlib.Path(path); tmp=path.with_suffix(path.suffix+'.pending')
        tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        os.replace(tmp,path)
    def _budget_publish_loop():
        root=pathlib.Path(budget_root); pub=root/'drive_publication'; pub.mkdir(parents=True,exist_ok=True)
        status_path=pub/'publication_status.json'
        try: state=json.loads(status_path.read_text(encoding='utf-8'))
        except Exception: state={'schema':'MathVisionKid.T4_budget3h_drive_publication.v1','artifacts':{},'checkpoint_generations':[],'errors':[]}
        state.setdefault('artifacts',{}); state.setdefault('checkpoint_generations',[]); state.setdefault('errors',[])
        state.update({'publisher_thread_started_utc':datetime.now(timezone.utc).isoformat(),'budget_deadline_unix':float(budget_status['deadline_unix']),'folder_name':'MathVisionKid_T4_BUDGET3H_RUN_20261023_141552','training_started_by_publisher':False})
        _pub_atomic_json(status_path,state)
        try:
            # Independent OAuth and Drive client are created only in this publisher thread.
            import google.auth
            from googleapiclient.discovery import build
            credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
            api=build('drive','v3',credentials=credentials,cache_discovery=False)
            module=sys.modules.get('full_text_training_run')
            if module is None or not hasattr(module,'RunStore'):
                raise RuntimeError('full_text_training_run.RunStore is not already loaded; refusing to import a training module in publisher thread')
            BaseStore=module.RunStore; parent=module.PARENT
            class BudgetRunStore(BaseStore):
                def __init__(self,api,work):
                    self.api=api; self.work=pathlib.Path(work); self.work.mkdir(parents=True,exist_ok=True)
                    self.name='MathVisionKid_T4_BUDGET3H_RUN_20261023_141552'
                    found=self._find(parent,self.name)
                    if len(found)>1: raise ValueError('Multiple matching budget run folders')
                    if found:
                        if found[0].get('mimeType')!='application/vnd.google-apps.folder': raise ValueError('Stable budget run name exists and is not a folder')
                        self.folder=found[0]['id']
                    else:
                        self.folder=api.files().create(body={'name':self.name,'mimeType':'application/vnd.google-apps.folder','parents':[parent]},fields='id').execute()['id']
            store=BudgetRunStore(api,pub/'runstore_work')
            state['folder_id']=store.folder; state['folder_parent_id']=parent; state['publisher_state']='RUNNING'; _pub_atomic_json(status_path,state)
            last_sig=None; last_status_write=0; done=False
            def publish_file(name,path,immutable=False):
                p=pathlib.Path(path)
                if not p.is_file(): return None
                snapshot=store.work/('upload_snapshot_'+name)
                shutil.copyfile(p,snapshot)
                p=snapshot
                digest=_pub_sha(p); prior=state['artifacts'].get(name)
                if prior and prior.get('sha256')==digest and prior.get('fresh_raw_readback_verified') is True:
                    return prior
                proof=store.put(name,p)
                if proof.get('sha256')!=digest or proof.get('bytes')!=p.stat().st_size or proof.get('fresh_raw_readback_verified') is not True:
                    raise ValueError('RunStore returned no matching fresh raw readback proof for '+name)
                state['artifacts'][name]=dict(proof,local_sha256=digest,published_utc=datetime.now(timezone.utc).isoformat())
                _pub_atomic_json(status_path,state); return state['artifacts'][name]
            def publish_json(name,obj):
                raw=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'); digest=hashlib.sha256(raw).hexdigest()
                prior=state['artifacts'].get(name)
                if prior and prior.get('sha256')==digest and prior.get('fresh_raw_readback_verified') is True: return prior
                local=pub/('_json_'+name); local.write_bytes(raw)
                proof=store.put(name,local)
                if proof.get('sha256')!=digest or proof.get('bytes')!=len(raw) or proof.get('fresh_raw_readback_verified') is not True: raise ValueError('JSON raw readback proof mismatch: '+name)
                state['artifacts'][name]=dict(proof,local_sha256=digest,published_utc=datetime.now(timezone.utc).isoformat()); _pub_atomic_json(status_path,state); return state['artifacts'][name]
            def stable_file(p):
                p=pathlib.Path(p)
                if not p.is_file(): return False
                a=(p.stat().st_size,p.stat().st_mtime_ns); time.sleep(2); b=(p.stat().st_size,p.stat().st_mtime_ns)
                return a==b and p.is_file()
            def package_checkpoint(gen):
                mp=gen/'generation_manifest.json'
                if not mp.is_file() or not stable_file(mp): return None
                manifest=json.loads(mp.read_text(encoding='utf-8'))
                if manifest.get('complete') is not True or not isinstance(manifest.get('files'),dict): return None
                files=manifest['files']
                already=next((x for x in state['checkpoint_generations'] if x.get('manifest_sha256')==_pub_sha(mp)),None)
                if already and already.get('fresh_raw_readback_verified'):return already
                for nm,dig in files.items():
                    f=gen/nm
                    if not f.is_file() or not stable_file(f) or _pub_sha(f)!=dig: return None
                step=int(manifest['step']); rows=int(manifest['rows_done'])
                if step<0 or rows<0: return None
                raw=mp.read_bytes(); zipname=f'checkpoint_step_{step:06d}_rows_{rows:08d}_{hashlib.sha256(raw).hexdigest()[:16]}.zip'
                dest=pub/zipname
                if not dest.exists():
                    tmp=dest.with_suffix('.zip.pending')
                    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
                        for nm in sorted(files): z.write(gen/nm,arcname=nm)
                        z.write(mp,arcname='generation_manifest.json')
                    os.replace(tmp,dest)
                proof=publish_file(zipname,dest,immutable=True)
                if proof and not any(x.get('name')==zipname for x in state['checkpoint_generations']):
                    state['checkpoint_generations'].append(dict(proof,step=step,rows_done=rows,manifest_sha256=_pub_sha(mp)))
                    _pub_atomic_json(status_path,state)
                # The mutable pointer is written strictly after the generation's raw SHA proof.
                if proof and proof.get('fresh_raw_readback_verified'):
                    publish_json('latest_checkpoint.json',dict(name=zipname,id=proof['id'],bytes=proof['bytes'],sha256=proof['sha256'],step=step,rows_done=rows,manifest_sha256=_pub_sha(mp),fresh_raw_readback_verified=True))
                    state['last_checkpoint']=dict(name=zipname,id=proof['id'],bytes=proof['bytes'],sha256=proof['sha256'],step=step,rows_done=rows,fresh_raw_readback_verified=True); _pub_atomic_json(status_path,state)
                return proof
            code_items=[
              ('publisher_code.py',next((q for q in [root/'drive_publication/start_budget_publisher_runtime.py',root/'start_budget_publisher_runtime.py',pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023/start_budget_publisher_runtime.py')] if q.is_file()),None)),
              ('training_worker.py',root/'unsloth_t4_worker.py'),
              ('sampler_worker.py',pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023/sampling/colab_train_view_worker.py')),
              ('sampling_plan.json',pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023/sampling/sampling_plan.json')),
              ('eval_fixtures.jsonl',root/'sampling/new_eval_candidates.jsonl'),
              ('eval_oracleQA_receipt.json',pathlib.Path('/content/mathvisionkid_t4_budget_3h_20261023/evaluation/oracleQA_receipt.json'))]
            # Publish code/fixtures/plan once per digest; this is a small auditable set, no corpus/model.
            for name,p in code_items:
                if p and p.is_file(): publish_file(name,p)
            run=root/'training'
            last_error=None
            while True:
                now=time.time(); deadline=float(budget_status['deadline_unix'])
                progress_path=run/'progress.json'; progress=json.loads(progress_path.read_text()) if progress_path.is_file() else None
                if progress:
                    step=progress.get('step'); rows=progress.get('rows_done')
                    sig=(step,rows)
                else: sig=None
                # Publish small mutable summaries only when their content changes.
                for nm,p in [('run_config.json',run/'run_config.json'),('progress.json',progress_path),('base_generations.jsonl',run/'base_generations.jsonl'),('adapter_generations.jsonl',run/'adapter_generations.jsonl')]:
                    if p.is_file() and stable_file(p): publish_file(nm,p)
                view=root/'sampling/run/training_view.jsonl'
                view_manifest=root/'sampling/run/training_view_manifest.json'
                if view.is_file() and view_manifest.is_file() and stable_file(view) and stable_file(view_manifest):
                    vm=json.loads(view_manifest.read_text(encoding='utf-8'))
                    if vm.get('members_complete')==32 and vm.get('training_view_rows')==vm.get('selected_chat_rows') and vm.get('training_view_sha256')==_pub_sha(view):
                        publish_file('sampling_manifest.json',view_manifest)
                        digest=_pub_sha(view); gz=pub/f'selected_training_view_{digest}.jsonl.gz'
                        if not gz.exists():
                            tmp=gz.with_suffix('.gz.pending')
                            with view.open('rb') as inp,gzip.open(tmp,'wb',compresslevel=1) as outgz: shutil.copyfileobj(inp,outgz,1024*1024)
                            if _pub_sha(view)!=digest: tmp.unlink(missing_ok=True); raise ValueError('selected view changed during gzip packaging')
                            os.replace(tmp,gz)
                        publish_file(gz.name,gz)
                # Publish verified immutable generations; manifest/file hashes must all match.
                for gen in sorted(run.glob('generation_step_*')):
                    if gen.is_dir(): package_checkpoint(gen)
                # Publish run config/sampler manifest/code that may have appeared after publisher start.
                for name,p in [('budget_control.json',root/'budget_control.json'),('run_config.json',run/'run_config.json'),('sampling_manifest.json',view_manifest),('training_worker.py',root/'unsloth_t4_worker.py')]:
                    if p.is_file() and stable_file(p): publish_file(name,p)
                complete_path=run/'run_complete.json'
                complete=json.loads(complete_path.read_text()) if complete_path.is_file() and stable_file(complete_path) else None
                adapter=run/'adapter_export.zip'
                if complete and complete.get('complete') is True and adapter.is_file() and stable_file(adapter):
                    ah=_pub_sha(adapter)
                    if complete.get('adapter_zip_sha256')!=ah: raise ValueError('adapter export SHA does not match run_complete.json')
                    publish_file(f'adapter_export_{ah}.zip',adapter,immutable=True)
                    publish_file('run_complete.json',complete_path)
                    for extra in ('successful_ids.jsonl','checkpoint_timing.jsonl','base_generation_provenance.json'):
                        if (run/extra).is_file():publish_file(extra,run/extra)
                # Final report is only archived as a source artifact; publication does not approve production.
                for extra in ('base_semantic_review.json','oracleQA_receipt.json','torch_baseline_benchmark.json','gpu_total_memory_observations.json'):
                    if (root/extra).is_file() and stable_file(root/extra):publish_file(extra,root/extra)
                report=run/'final_quality_report.json'
                if report.is_file() and stable_file(report):
                    rp=publish_file('final_quality_report.json',report)
                    if rp and rp.get('fresh_raw_readback_verified'): state['final_quality_report_published']=True; done=True
                status_doc={'schema':'MathVisionKid.T4_budget3h_publication_status.v1','observed_utc':datetime.now(timezone.utc).isoformat(),'folder_id':store.folder,'folder_name':store.name,'last_progress':progress,'last_checkpoint':state.get('last_checkpoint'),'checkpoint_generations':state['checkpoint_generations'],'artifacts':state['artifacts'],'final_quality_report_published':state.get('final_quality_report_published',False),'publisher_state':'RUNNING','training_started_by_publisher':False,'production_approval':False,'last_error':last_error}
                _pub_atomic_json(status_path,status_doc)
                if done or now>=deadline+120:
                    status_doc['publisher_state']='STOPPED_AFTER_FINAL_QUALITY_REPORT' if done else 'STOPPED_AFTER_DEADLINE_GRACE'
                    status_doc['stopped_utc']=datetime.now(timezone.utc).isoformat(); _pub_atomic_json(status_path,status_doc); break
                if sig!=last_sig:
                    last_sig=sig
                time.sleep(60)
        except BaseException as e:
            try:
                state.update(publisher_state='ERROR',last_error={'at_utc':datetime.now(timezone.utc).isoformat(),'type':type(e).__name__,'message':str(e),'traceback_tail':traceback.format_exc()[-4000:]})
                _pub_atomic_json(status_path,state)
            except Exception: pass
            # Bounded retry: one-minute wait, then retry until deadline+120s.
            if time.time()<float(budget_status.get('deadline_unix',time.time()))+120:
                time.sleep(60)
                try:
                    # Re-enter loop in this same publisher thread; no GPU, training, or stop action.
                    _budget_publish_loop()
                except BaseException: pass
    budget_publisher_thread=threading.Thread(target=_budget_publish_loop,name='MathVisionKidBudgetDrivePublisher',daemon=True)
    budget_publisher_thread.start()
    print(json.dumps({'publisher_started':True,'folder_name':'MathVisionKid_T4_BUDGET3H_RUN_20261023_141552','deadline_utc':budget_status['deadline_utc'],'drive_calls_in_current_cell':False,'thread':'MathVisionKidBudgetDrivePublisher'},ensure_ascii=False))
