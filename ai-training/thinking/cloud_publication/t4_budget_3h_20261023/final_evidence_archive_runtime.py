# Runtime final-evidence archiver. Define/launch only; it makes no Drive calls
# until the named bounded worker thread starts after run and reviews are ready.
import hashlib, json, os, pathlib, shutil, sys, threading, time, traceback, zipfile
from datetime import datetime, timezone

assert 'budget_root' in globals() and pathlib.Path(budget_root).name == 'mathvisionkid_t4_budget_3h_20261023'
if globals().get('final_evidence_archive_thread') and final_evidence_archive_thread.is_alive():
    print(json.dumps({'started':False,'reason':'archive worker already alive'}))
else:
    def _fea_sha(path):
        h=hashlib.sha256()
        with pathlib.Path(path).open('rb') as f:
            for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
        return h.hexdigest()
    def _fea_atomic(path,obj):
        p=pathlib.Path(path); tmp=p.with_suffix(p.suffix+'.pending')
        tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8'); os.replace(tmp,p)
    def _fea_wait_and_archive():
        root=pathlib.Path(budget_root); train=root/'training'; sampling=root/'sampling'; pub=root/'drive_publication'; pub.mkdir(parents=True,exist_ok=True)
        proof_path=pub/'final_package_proof.json'
        deadline=float(globals().get('budget_status',{}).get('deadline_unix',time.time()+3600))+120
        # Evidence required for an auditable final package. final_quality_report.json is
        # deliberately excluded so its later publication remains the publisher stop signal.
        base_review=next((p for p in (root/'base_semantic_review.json',train/'base_semantic_review.json') if p.is_file()),root/'base_semantic_review.json')
        adapter_review=next((p for p in (root/'adapter_semantic_review.json',train/'adapter_semantic_review.json') if p.is_file()),root/'adapter_semantic_review.json')
        required=[train/'run_complete.json',train/'base_generations.jsonl',train/'adapter_generations.jsonl',
          base_review,adapter_review,root/'benchmark_id_binding.json',train/'final_runtime_evidence.json',train/'publication_proof.json']
        while time.time()<deadline:
            if (train/'final_quality_report.json').exists():
                raise RuntimeError('final_quality_report.json already exists; archiver must run before publisher stop signal')
            if all(p.is_file() for p in required): break
            time.sleep(60)
        else: raise TimeoutError('required completed-run/review inputs did not appear before deadline grace')
        # Snapshot each small metadata/output file; never open weights, checkpoint payloads,
        # selected raw training view, corpus, or adapter_export.zip.
        def stable(p):
            a=(p.stat().st_size,p.stat().st_mtime_ns); time.sleep(2); return a==(p.stat().st_size,p.stat().st_mtime_ns)
        for p in required:
            if not stable(p): raise RuntimeError(f'input still changing: {p.name}')
        run=json.loads(required[0].read_text(encoding='utf-8'))
        if run.get('complete') is not True: raise ValueError('run_complete does not say complete=true')
        for review in required[3:5]:
            doc=json.loads(review.read_text(encoding='utf-8'))
            if doc.get('fixture_count')!=28 or doc.get('all_fixture_ids_matched') is not True: raise ValueError(f'{review.name} does not cover exactly 28 fixtures')
        for out in required[1:3]:
            records=[json.loads(line) for line in out.read_text(encoding='utf-8').splitlines() if line.strip()]
            if len(records)!=28: raise ValueError(f'{out.name} has {len(records)} records, expected 28')
        # Exact, bounded allowlist of evidence. Include all primary inputs and supporting
        # metadata/code; do not include generation directories, selected JSONL view, or weights.
        candidates=list(required)
        candidates += [root/'budget_control.json',sampling/'run'/'training_view_manifest.json',sampling/'training_view_manifest.json',
          root/'torch_baseline_benchmark.json',root/'benchmark_id_binding.json',root/'base_semantic_review.json',root/'adapter_semantic_review.json',
          root/'oracleQA_receipt.json',root/'gpu_total_memory_observations.json',root/'runtime_versions.json',root/'unsloth_t4_worker.py',root/'posthoc_bind_benchmarks.py',
          sampling/'new_eval_candidates.jsonl',train/'run_config.json',train/'progress.json',train/'successful_ids.jsonl',
          train/'checkpoint_timing.jsonl',train/'base_generation_provenance.json',train/'base_generations.jsonl',
          train/'adapter_generations.jsonl',train/'final_runtime_evidence.json',train/'publication_proof.json',
          train/'same16_benchmark_bundle.json',train/'torch_baseline_benchmark.json',
          train/'collect_final_evidence.py',train/'build_final_quality_report.py',train/'torch_baseline_benchmark.py',
          sampling/'sampling_plan.json']
        # Whitelist runtime logs; each still passes the same 80 MiB metadata bound.
        candidates += [root/n for n in ('training.log','torch_baseline.log','orchestrator.log')]
        candidates += [train/n for n in ('training.log','torch_baseline.log','orchestrator.log')]
        candidates += [sampling/'new_eval_candidates.jsonl',root/'oracleQA_receipt.json']
        publisher_code=next((p for p in [pub/'final_evidence_archive_runtime.py',root/'final_evidence_archive_runtime.py'] if p.is_file()),None)
        if publisher_code: candidates.append(publisher_code)
        files=[]; by_name={}; seen_paths=set()
        for p in candidates:
            p=pathlib.Path(p)
            if not p.is_file() or str(p) in seen_paths: continue
            seen_paths.add(str(p))
            # Hard guard against large assets and source/corpus duplication.
            if p.name in {'training_view.jsonl','selected_training_view.jsonl','adapter_export.zip','resume_state.pt'} or p.suffix in {'.pt','.safetensors','.bin'}:
                raise ValueError(f'forbidden large payload selected: {p.name}')
            if p.stat().st_size>80*1024*1024: raise ValueError(f'evidence file exceeds bounded metadata limit: {p.name}')
            digest=_fea_sha(p); prior=by_name.get(p.name)
            if prior:
                if prior['sha256']!=digest: raise ValueError(f'basename collision with differing content: {p.name}')
                prior['sources'].append(str(p)); continue
            rec={'path':p,'name':p.name,'sha256':digest,'sources':[str(p)]}; by_name[p.name]=rec; files.append(rec)
        if not all(any(str(r) in rec['sources'] for rec in files) for r in required): raise ValueError('required evidence missing from package set')
        work=pub/'final_archive_work'; work.mkdir(parents=True,exist_ok=True)
        prepared_path=pub/'archive_prepared.json'
        if prepared_path.is_file():
            prepared=json.loads(prepared_path.read_text(encoding='utf-8'))
            archive=pathlib.Path(prepared['local_archive'])
            if not archive.is_file() or archive.stat().st_size!=prepared['bytes'] or _fea_sha(archive)!=prepared['sha256']:
                raise ValueError('prepared archive bytes are absent or fail their frozen size/SHA pin')
            manifest=prepared['manifest']; digest=prepared['sha256']; nbytes=prepared['bytes']; artifact_name=prepared['artifact_name']
            if hashlib.sha256((json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()).hexdigest()!=prepared['manifest_sha256']:
                raise ValueError('prepared archive manifest fails its frozen SHA pin')
        else:
            manifest={'schema':'MathVisionKid.t4_final_evidence_archive.v1','created_utc':datetime.now(timezone.utc).isoformat(),
              'folder_id':'1OvUWLz4E-d2zi5eicgOYZeVpuh_7aQpo','run_complete_sha256':_fea_sha(required[0]),
              'contents':[],'excluded':['model weights/checkpoints','full corpus','selected raw training view (already separately published as gzip)','adapter_export.zip (published separately)','final_quality_report.json (must be generated only after this archive proof)'],
              'control_sync_pending':True,'main_control_sync':{'status':'PENDING','connector_unavailable':True,'reason':'Four main control updates require the separate Drive connector publisher.'}}
            pending=work/'final_evidence_archive.pending.zip'
            with zipfile.ZipFile(pending,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for rec in files:
                    p=rec['path']; raw=p.read_bytes(); actual=hashlib.sha256(raw).hexdigest()
                    if actual!=rec['sha256']: raise ValueError(f'evidence changed after snapshot: {rec["name"]}')
                    manifest['contents'].append({'name':rec['name'],'bytes':len(raw),'sha256':actual,'source_paths':rec['sources']}); z.writestr(rec['name'],raw)
                z.writestr('archive_manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
            digest=_fea_sha(pending); nbytes=pending.stat().st_size
            artifact_name=f'final_evidence_archive_{digest}.zip'; archive=work/artifact_name
            if archive.exists(): raise FileExistsError('digest-named local archive already exists without a preparation receipt')
            os.replace(pending,archive)
            manifest_sha=hashlib.sha256((json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
            prepared={'schema':'MathVisionKid.t4_final_archive_prepared.v1','local_archive':str(archive),'artifact_name':artifact_name,'bytes':nbytes,'sha256':digest,'manifest_sha256':manifest_sha,'manifest':manifest,'prepared_utc':datetime.now(timezone.utc).isoformat()}
            _fea_atomic(prepared_path,prepared)
        # Independent OAuth/Drive client is constructed only inside this archive worker.
        import google.auth
        from googleapiclient.discovery import build
        credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
        api=build('drive','v3',credentials=credentials,cache_discovery=False)
        from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
        class ExistingBudgetRunStore:
            def __init__(self,api,work): self.api=api; self.work=pathlib.Path(work); self.work.mkdir(parents=True,exist_ok=True); self.name='MathVisionKid_T4_BUDGET3H_RUN_20261023_141552'; self.folder='1OvUWLz4E-d2zi5eicgOYZeVpuh_7aQpo'
            def get(self,name):
                if "'" in name: raise ValueError('unsafe Drive artifact name')
                result=self.api.files().list(q=f"'{self.folder}' in parents and name='{name}' and trashed=false",fields='files(id,name,mimeType,size),nextPageToken',pageSize=100).execute()
                if result.get('nextPageToken'): raise ValueError('ambiguous Drive pagination')
                refs=result.get('files',[])
                if len(refs)>1: raise ValueError('duplicate immutable artifact name')
                return refs[0] if refs else None
            def download(self,ref,path):
                with pathlib.Path(path).open('wb') as output:
                    dl=MediaIoBaseDownload(output,self.api.files().get_media(fileId=ref['id']),chunksize=8*1024*1024); done=False
                    while not done: _,done=dl.next_chunk(num_retries=3)
                if pathlib.Path(path).stat().st_size!=int(ref['size']): raise ValueError('Drive readback byte count mismatch')
            def put(self,name,path):
                path=pathlib.Path(path); actual=_fea_sha(path); size=path.stat().st_size; ref=self.get(name)
                if ref:
                    existing=self.work/('existing_'+name); self.download(ref,existing)
                    if existing.stat().st_size!=size or _fea_sha(existing)!=actual: raise ValueError('immutable Drive artifact name collides with different bytes')
                    existing.unlink(); return {'id':ref['id'],'name':name,'bytes':size,'sha256':actual,'fresh_raw_readback_verified':True,'existing_immutable_match':True}
                media=MediaFileUpload(str(path),mimetype='application/octet-stream',chunksize=8*1024*1024,resumable=True)
                req=self.api.files().create(body={'name':name,'parents':[self.folder]},media_body=media,fields='id,size'); result=None
                while result is None: _,result=req.next_chunk(num_retries=3)
                ref={'id':result['id'],'size':result['size']}; readback=self.work/('readback_'+name); self.download(ref,readback)
                if _fea_sha(readback)!=actual: raise ValueError('fresh Drive raw readback SHA mismatch')
                readback.unlink(); return {'id':result['id'],'name':name,'bytes':int(result['size']),'sha256':actual,'fresh_raw_readback_verified':True,'existing_immutable_match':False}
        store=ExistingBudgetRunStore(api,work/'runstore')
        folder_meta=api.files().get(fileId=store.folder,fields='id,name,mimeType,parents').execute()
        if folder_meta.get('name')!=store.name or folder_meta.get('mimeType')!='application/vnd.google-apps.folder': raise ValueError('fixed budget run folder ID/name/type mismatch')
        prior=store.get(artifact_name)
        if prior:
            check=work/'existing_archive.zip'; store.download(prior,check)
            if check.stat().st_size!=nbytes or _fea_sha(check)!=digest: raise ValueError('immutable archive name already exists with different bytes')
            proof={'id':prior['id'],'name':artifact_name,'bytes':nbytes,'sha256':digest,'fresh_raw_readback_verified':True,'existing_immutable_match':True}
        else:
            uploaded=store.put(artifact_name,archive)
            if uploaded.get('bytes')!=nbytes or uploaded.get('sha256')!=digest or uploaded.get('fresh_raw_readback_verified') is not True: raise ValueError('RunStore did not verify exact archive readback')
            proof=dict(uploaded,existing_immutable_match=False)
        proof.update({'schema':'MathVisionKid.final_package_proof.v1','folder_id':store.folder,'archive_manifest_sha256':hashlib.sha256((json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()).hexdigest(),'uploaded_utc':datetime.now(timezone.utc).isoformat(),'control_sync_pending':True,'main_control_sync':manifest['main_control_sync'],'production_approval':False})
        _fea_atomic(proof_path,proof)
        # Also store an immutable, small proof file in the same run folder.
        proof_bytes=(json.dumps(proof,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(); proof_local=work/'final_package_proof.json'; proof_local.write_bytes(proof_bytes)
        proof_name=f'final_package_proof_{hashlib.sha256(proof_bytes).hexdigest()}.json'
        proof_upload=store.put(proof_name,proof_local)
        if proof_upload.get('sha256')!=hashlib.sha256(proof_bytes).hexdigest() or proof_upload.get('fresh_raw_readback_verified') is not True: raise ValueError('final package proof raw readback failed')
        # Keep ownership isolated: only this worker writes final_package_proof.json.
        print(json.dumps({'state':'FINAL_EVIDENCE_ARCHIVE_RAW_VERIFIED','proof':proof,'local_proof_path':str(proof_path),'proof_artifact':proof_upload},ensure_ascii=False))
    def _final_archive_guarded():
        root=pathlib.Path(budget_root); status=root/'drive_publication'/'final_package_proof.json'
        while True:
            try:
                _fea_wait_and_archive(); return
            except BaseException as e:
                d=float(globals().get('budget_status',{}).get('deadline_unix',time.time()))+120
                try:
                    _fea_atomic(root/'drive_publication'/'final_archive_error.json',{'at_utc':datetime.now(timezone.utc).isoformat(),'error_type':type(e).__name__,'message':str(e),'traceback_tail':traceback.format_exc()[-3000:]})
                except Exception: pass
                if time.time()>=d:return
                time.sleep(60)
    final_evidence_archive_thread=threading.Thread(target=_final_archive_guarded,name='MathVisionKidFinalEvidenceArchive',daemon=True)
    final_evidence_archive_thread.start()
    print(json.dumps({'started':True,'thread':'MathVisionKidFinalEvidenceArchive','folder_id':'1OvUWLz4E-d2zi5eicgOYZeVpuh_7aQpo','wait_interval_seconds':60,'control_sync_pending':True,'connector_unavailable':True},ensure_ascii=False))
