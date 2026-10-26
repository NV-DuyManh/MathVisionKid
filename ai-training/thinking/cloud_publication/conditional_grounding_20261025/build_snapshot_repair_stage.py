from pathlib import Path
import base64,hashlib
P=Path(__file__).parent
names=['native_backend_v2.py','recovery_worker_v4.py','code_repair_snapshot_binding.json']
files={n:base64.b64encode((P/n).read_bytes()).decode() for n in names}
pins={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in names}
code='''import pathlib,json,base64,hashlib,subprocess,sys,os,time,importlib.util
r=pathlib.Path('/content/mathvisionkid_conditional_grounding_20261025')
assert conditional_training_process.poll()==1 and not (r/'training/run_config.json').exists()
previous=json.loads((r/'training/error.json').read_bytes())
assert previous['error']=="ValueError('model/tokenizer revision mismatch')"
payload=FILES;pins=PINS
for name,value in payload.items():
 data=base64.b64decode(value);assert hashlib.sha256(data).hexdigest()==pins[name]
 path=r/name
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
history=r/'error_history/attempt_0001_revision_metadata';history.mkdir(parents=True,exist_ok=False)
for name in ['error.json','progress.json']:
 source=r/'training'/name
 if source.exists():(history/name).write_bytes(source.read_bytes())
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 lib=sys.modules['qrec_integrity_store']
 store=conditional_publisher.parent_verified_store_class(lib)(api,parent=conditional_publisher.PARENT,folder_name=conditional_publisher.FOLDER)
 folders=store.find(conditional_publisher.PARENT,conditional_publisher.FOLDER)
 assert len(folders)==1 and folders[0]['id']=='1iP691P_pYTf-Pt_RdGpTZMnDtwjKR4ya'
 store.folder=folders[0]['id']
 proofs={n:store.put(n,r/n,immutable=True) for n in payload}
 (r/'active_code_raw_verified.json').write_text(json.dumps(proofs,indent=2)+'\\n')
 activeproof=store.put('active_code_raw_verified.json',r/'active_code_raw_verified.json',immutable=True)
finally:api.close()
(r/'training/error.json').unlink()  # original bytes retained in error_history; zero optimizer updates
conditional_training_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker_v4.py'),'--root',str(r)],
 stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,
 env={**os.environ,'TOKENIZERS_PARALLELISM':'false','PYTHONPATH':str(r)})
print(json.dumps({'worker_relaunched_after_preoptimizer_metadata_repair':True,'pid':conditional_training_process.pid,
 'optimizer_updates_before_repair':0,'code_raw_proofs':proofs,'active_code_proof':activeproof,'runtime_restarted':False}))
'''.replace('FILES',repr(files)).replace('PINS',repr(pins))
compile(code,'snapshot_repair_stage','exec')
(P/'snapshot_repair_runtime.py').write_bytes(code.encode())
print('Prepared versioned snapshot-binding repair and pre-optimizer relaunch.')
