from pathlib import Path
import json,hashlib,base64
P=Path(__file__).parent
names=['native_backend_v3.py','recovery_worker_v5.py','memory_resume_migration.json','baseline_semantic_review_frozen.json']
payload={n:base64.b64encode((P/n).read_bytes()).decode() for n in names}
pins={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in names}
code='''import pathlib,json,base64,hashlib,subprocess,sys,os,time
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert conditional_training_process.poll()==1,'Old OOM worker must have exited'
error=json.loads((r/'training/error.json').read_bytes())
assert 'OutOfMemoryError' in error['error']
progress=json.loads((r/'training/progress.json').read_bytes())
assert progress['step']==6 and progress['rows_done']==96
history=r/'error_history/attempt_0002_native_OOM';history.mkdir(parents=True,exist_ok=False)
for name in ['error.json','progress.json','run_config.json','successful_ids.jsonl']:
 path=r/'training'/name
 if path.exists():(history/name).write_bytes(path.read_bytes())
payload=PAYLOAD;pins=PINS
for name,encoded in payload.items():
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==pins[name]
 path=r/name
 if path.exists():assert path.read_bytes()==raw
 else:path.write_bytes(raw)
migration=json.loads((r/'memory_resume_migration.json').read_bytes())
generation=r/'training'/migration['parent_checkpoint_generation']
manifest=json.loads((generation/'generation_manifest.json').read_bytes())
assert hashlib.sha256((generation/'generation_manifest.json').read_bytes()).hexdigest()==migration['parent_generation_manifest_sha256']
for name,h in manifest['files'].items():
 assert pathlib.Path(name).name==name and hashlib.sha256((generation/name).read_bytes()).hexdigest()==h
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 lib=sys.modules['qrec_integrity_store']
 store=conditional_publisher.parent_verified_store_class(lib)(api,parent=conditional_publisher.PARENT,folder_name=conditional_publisher.FOLDER)
 folder=store.find(conditional_publisher.PARENT,conditional_publisher.FOLDER)
 assert len(folder)==1 and folder[0]['id']=='1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya'
 store.folder=folder[0]['id']
 parent_proof=store.raw_proof(migration['parent_checkpoint_drive_id'],migration['parent_checkpoint_archive_sha256'],31150368)
 proofs={name:store.put(name,r/name,immutable=True) for name in payload}
 for path in history.iterdir():store.put('error_history__attempt2__'+path.name,path,immutable=True)
 (r/'active_memory_code_raw_verified.json').write_text(json.dumps({'files':proofs,'parent_checkpoint':parent_proof},indent=2)+'\\n')
 active=store.put('active_memory_code_raw_verified.json',r/'active_memory_code_raw_verified.json',immutable=True)
finally:api.close()
(r/'training/error.json').unlink() # verbatim copy retained locally and Drive immutable history
conditional_training_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker_v5.py'),'--root',str(r),'--resume-generation',str(generation)],
 stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,
 env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r),'PYTORCH_ALLOC_CONF':'expandable_segments:True'})
print(json.dumps({'memory_recovery_launched':True,'pid':conditional_training_process.pid,
 'parent_step':1,'parent_rows':16,'last_uncommitted_step':6,'gradient_checkpointing':True,
 'same_effective_batch':16,'learning_rate_unchanged':True,'code_proofs':proofs,'parent_checkpoint_raw_reverified':parent_proof,'active_code_proof':active,'runtime_restarted':False}))
'''.replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'memory_resume_stage','exec');(P/'memory_resume_runtime.py').write_bytes(code.encode())
print('Prepared memory resume stage; does not execute model locally.')
