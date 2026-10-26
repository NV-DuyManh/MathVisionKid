"""Cloud-only recovery publisher. Explicit start(credentials); no I/O on import."""
import pathlib,json,hashlib,importlib.util,sys,threading,time,traceback,types,http.client
ROOT=pathlib.Path('/content/mathvisionkid_verbal_recovery_20261024')
PARENT='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
FOLDER='MathVisionKid_VERBAL_RECOVERY_20261024'
THREAD_NAME='MathVisionKidVerbalRecoveryPublisher'
STORE_SHA='5f8d69f542e63bd7cc17f9a62551710c74e931d7d2c69974b0e13aaac326fb8e'

def parent_verified_store_class(lib):
 """Adapt missing GET parents using a new, constrained LIST result only.

 Never infer parents from the intended upload/create body. The frozen store is
 unchanged. Explicit wrong/empty parents fail; publication-parent metadata does
 not need its own parent. Every fallback has one exact active ID/name/type match
 and an actual parents list including the expected parent, from a fresh query.
 """
 class ParentVerifiedDriveStore(lib.DriveStore):
  def metadata(self,file_id):
   meta=super().metadata(file_id)
   if file_id==self.parent:return meta
   run_folder=self.folder is None or file_id==self.folder
   expected_parent=self.parent if run_folder else self.folder
   if 'parents' in meta:
    if not isinstance(meta['parents'],list) or expected_parent not in meta['parents']:
     raise lib.IntegrityError('Explicit metadata parents do not include expected parent')
    return meta
   name=self.folder_name if run_folder else meta.get('name')
   expected_mime='application/vnd.google-apps.folder' if run_folder else meta.get('mimeType')
   if meta.get('id')!=file_id or not isinstance(name,str) or not name or meta.get('name')!=name or not isinstance(expected_mime,str) or not expected_mime or meta.get('mimeType')!=expected_mime or meta.get('trashed'):
    raise lib.IntegrityError('Missing-parent metadata lacks exact active ID/name/type')
   found=self.find(expected_parent,name)  # fresh expected-parent/name/active query
   if len(found)!=1:raise lib.IntegrityError('Missing-parent fallback is absent or ambiguous')
   actual=found[0]
   if actual.get('id')!=file_id or actual.get('name')!=name or actual.get('mimeType')!=expected_mime or actual.get('trashed') or not isinstance(actual.get('parents'),list) or expected_parent not in actual['parents']:
    raise lib.IntegrityError('Fresh parent-list evidence does not match exact active artifact')
   proof={'file_id':file_id,'expected_parent':expected_parent,'name':name,'mimeType':expected_mime,
          'parents_from_fresh_list':list(actual['parents']),'observed_unix':time.time(),
          'method':'fresh_expected_parent_name_active_list_exact_id_match'}
   if not hasattr(self,'parent_fallback_proofs'):self.parent_fallback_proofs=[]
   self.parent_fallback_proofs.append(proof)
   return {**meta,'parents':list(actual['parents']),'parent_verification_evidence':proof}
 return ParentVerifiedDriveStore

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(p,x):
 p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.pending')
 t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');t.replace(p)

def _registry():
 # sys.modules.setdefault shares this lock even when notebook code reloads us.
 candidate=types.ModuleType('_mathvisionkid_verbal_recovery_publisher_registry')
 candidate.lock=threading.Lock();candidate.thread=None
 return sys.modules.setdefault(candidate.__name__,candidate)

def transient_error(error,lib):
 if isinstance(error,lib.IntegrityError):return False
 if isinstance(error,lib.SnapshotBusyError):return True
 if isinstance(error,(TimeoutError,ConnectionError,OSError,http.client.HTTPException)):return True
 status=getattr(getattr(error,'resp',None),'status',None)
 message=str(error).lower()
 return status in (429,500,502,503,504) or (status==403 and any(x in message for x in ('ratelimitexceeded','userratelimitexceeded','quotaexceeded')))

class PublicationLoop:
 """One client/thread. tick/cycle support offline fake-store safety tests."""
 def __init__(self,root,lib,store):
  self.root=pathlib.Path(root);self.lib=lib;self.store=store;self.work=self.root/'publication'
  self.work.mkdir(exist_ok=True);self.state_path=self.work/'publication_status.json'
  self.state=json.loads(self.state_path.read_bytes()) if self.state_path.exists() else {'artifacts':{},'checkpoints':{},'errors':[]}
  if self.state.get('folder_id') and self.state['folder_id']!=store.folder:raise lib.IntegrityError('run folder changed')
  self.state.update(state='RUNNING',folder_id=store.folder,folder_name=FOLDER,training_started_by_publisher=False)
  self.save()
 def save(self):
  if hasattr(self.store,'parent_fallback_proofs'):
   self.state['parent_metadata_fallback_proofs']=list(self.store.parent_fallback_proofs)
  atomic(self.state_path,self.state)
 def put(self,name,path,immutable=False):
  snapshot=self.work/'snapshots'/name.replace('/','__');self.lib.snapshot_file(path,snapshot)
  h=sha(snapshot);prior=self.state['artifacts'].get(name)
  if prior and prior['sha256']==h and prior.get('fresh_raw_readback_verified'):return prior
  proof=self.store.put(name.replace('/','__'),snapshot,immutable=immutable)
  self.state['artifacts'][name]=proof;self.save();return proof
 def put_json(self,name,value):
  path=self.work/'json'/name;atomic(path,value);return self.put(name,path)
 def tick(self):
  root,work,state=self.root,self.work,self.state;out=root/'training'
  state['state']='RUNNING'
  initial=['owner_run_scope.json','recovery_policy.py','recovery_worker.py','publisher_runtime.py','frozen_code_references.json',
   'new_validation_candidates.jsonl','new_validation_candidate_notes.json','locked_test_candidates.jsonl','locked_test_notes.json',
   'source_semantic_review_g1_g3.json','source_semantic_review_g4_g5.json','input_readback.json','dev_train_screening.json','locked_train_screening.json','derived_sampling_plan.json','cpu_validation.json','verbal_training_renderer_v3.py','test_verbal_training_renderer_v3.py','verbal_projection_manifest.json','projection_preflight.json','trial_scope.json']
  initial+=sorted(p.name for p in root.glob('test_recovery*.py'))
  for name in initial:
   path=root/name
   if path.is_file():self.put(name,path,True)
  report=None
  for name in ['run_config.json','input_audit.json','evaluation_contract.json','progress.json','error.json','best.json','run_complete.json','final_semantic_assessment.json']:
   path=out/name
   if path.exists():
    proof=self.put('training/'+name,path)
    if name=='final_semantic_assessment.json':report=(path,'training/'+name,proof)
  # A root-owned final review may be staged outside training; accept that location.
  if (root/'final_semantic_assessment.json').is_file():
   path=root/'final_semantic_assessment.json';proof=self.put(path.name,path)
   if report and sha(report[0])!=sha(path):raise self.lib.IntegrityError('conflicting final semantic assessment locations')
   report=(path,path.name,proof)
  for gen in sorted(out.glob('generation_step_*')):
   if not gen.is_dir() or gen.name.endswith('.pending') or not (gen/'generation_manifest.json').exists():continue
   mh=sha(gen/'generation_manifest.json')
   if mh not in state['checkpoints']:
    archive,meta=self.lib.package_generation(gen,work/'checkpoint_packages');proof=self.put(archive.name,archive,True)
    state['checkpoints'][mh]={**proof,**meta};self.save()
  for sub in sorted(out.glob('eval_step_*')):
   for name in ['base_generations.jsonl','adapter_generations.jsonl','eval_bindings.json','gate_summary.json']:
    path=sub/name
    if path.exists():self.put(str(path.relative_to(root)),path,True)
  for path in sorted(out.glob('gate_step_*.json')):self.put(str(path.relative_to(root)),path,True)
  pointer=out/'latest.json'
  if pointer.exists():
   local=json.loads(pointer.read_bytes());cp=state['checkpoints'].get(local['manifest_sha256'])
   if cp:self.put_json('latest_checkpoint.json',{'checkpoint':cp,'local_pointer':local,'pointer_written_after_raw_checkpoint':True})
  best=out/'best.json'
  if best.exists():
   chosen=json.loads(best.read_bytes());cp=state['checkpoints'].get(chosen.get('manifest_sha256'))
   if chosen.get('kind')=='untrained_base' or cp:self.put_json('selected_best_checkpoint.json',{'selection':chosen,'checkpoint':cp,'production_approval':False})
  complete=out/'run_complete.json'
  if complete.exists():
   completion=json.loads(complete.read_bytes());artifacts={}
   for name in ['last_adapter_diagnostic.zip','selected_adapter_export.zip','adapter_export.zip']:
    path=out/name
    if path.exists():artifacts[name]=self.put(name[:-4]+'_'+sha(path)[:16]+'.zip',path,True)
   state.update(state='WAITING_FINAL_REVIEW_PUBLICATION',completion=completion,final_artifacts=artifacts)
   marker=work/'finalize_requested.json';finalize=False
   if marker.is_file():
    request=json.loads(marker.read_bytes())
    if request.get('finalize_requested') is not True:raise self.lib.IntegrityError('finalize marker must explicitly request finalization')
    if report:
     expected=request.get('final_semantic_assessment_sha256')
     if expected!=sha(report[0]):raise self.lib.IntegrityError('finalization marker does not bind current final report SHA')
     proof=report[2]
     # Never reuse an old proof to acknowledge this explicit finalization request.
     fresh=self.store.raw_proof(proof['id'],expected,proof['bytes'])
     state['artifacts'][report[1]]={**proof,**fresh};report=(report[0],report[1],state['artifacts'][report[1]])
     self.put('finalize_requested.json',marker,True);finalize=True
   self.put_json('training_complete_publication_proof.json',{'complete':True,'publication_finalized':finalize,'folder_id':self.store.folder,
    'completion':completion,'artifacts':artifacts,'checkpoint_proofs':state['checkpoints'],
    'metadata_and_evaluation_proofs':dict(state['artifacts']),'final_semantic_assessment_proof':report[2] if report else None,
    'raw_integrity_only':True,'semantic_quality_from_separate_report':bool(report),'whole_corpus_trained':False})
   if finalize:
    state.update(state='COMPLETE_RAW_VERIFIED',publication_finalized=True,final_semantic_assessment_proof=report[2]);self.save();return True
  live={'state':state['state'],'folder_id':self.store.folder,'observed_unix':time.time(),
   'progress':json.loads((out/'progress.json').read_bytes()) if (out/'progress.json').exists() else None,
   'latest_checkpoint':state['checkpoints'][next(reversed(state['checkpoints']))] if state['checkpoints'] else None,'errors':state['errors'][-3:]}
  self.put_json('LIVE_status.json',live);self.save();return False
 def cycle(self):
  try:return 'DONE' if self.tick() else 'CONTINUE'
  except BaseException as error:
   retry=transient_error(error,self.lib)
   item={'observed_unix':time.time(),'type':type(error).__name__,'error':str(error)[:1200],'retryable':retry}
   self.state.setdefault('errors',[]).append(item);self.state['errors']=self.state['errors'][-20:]
   self.state.update(state='RETRYING_TRANSIENT' if retry else 'ERROR',last_error=item)
   if not retry:self.state['traceback']=traceback.format_exc()
   self.save();return 'RETRY' if retry else 'FATAL'

def start(credentials,root=ROOT):
 global publisher_thread
 root=pathlib.Path(root);registry=_registry()
 with registry.lock:
  if (registry.thread and registry.thread.is_alive()) or any(t.name==THREAD_NAME and t.is_alive() for t in threading.enumerate()):raise RuntimeError('publisher already active in this process')
  work=root/'publication';work.mkdir(exist_ok=True)
  def run():
   api=None
   try:
    from googleapiclient.discovery import build
    from google_auth_httplib2 import AuthorizedHttp
    import httplib2
    path=root/'frozen_integrity_store.py'
    if sha(path)!=STORE_SHA:raise ValueError('integrity source changed')
    spec=importlib.util.spec_from_file_location('qrec_integrity_store',path);lib=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lib;spec.loader.exec_module(lib)
    api=build('drive','v3',http=AuthorizedHttp(credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
    store=parent_verified_store_class(lib)(api,parent=PARENT,folder_name=FOLDER);store.ensure_folder()
    loop=PublicationLoop(root,lib,store)
    while loop.cycle() in ('CONTINUE','RETRY'):time.sleep(15)
   except BaseException as error:
    path=work/'publication_status.json';state=json.loads(path.read_bytes()) if path.exists() else {'artifacts':{},'checkpoints':{},'errors':[]}
    state.update(state='ERROR',error=repr(error),traceback=traceback.format_exc());atomic(path,state)
   finally:
    if api is not None:api.close()
  publisher_thread=threading.Thread(target=run,name=THREAD_NAME,daemon=True);registry.thread=publisher_thread;publisher_thread.start()
 return {'publisher_started':True,'folder_name':FOLDER,'training_started_by_publisher':False}
