from pathlib import Path
import json,hashlib,base64
p=Path(__file__).parent
names=['recovery_worker_v2.py','recovery_policy_v2.py','cpu_validation.json','test_recovery_policy.py','test_recovery_worker.py']
files={n:base64.b64encode((p/n).read_bytes()).decode() for n in names};pins={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
script="""import pathlib,json,base64,hashlib,sys,importlib.util,subprocess,os,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024');payload=PAYLOAD;pins=PINS
assert skill_benchmark_process.poll()==0
assert not globals().get('skill_training_process') or skill_training_process.poll() is not None
assert not (r/'training/run_config.json').exists(),'Never duplicate initialized training run'
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-2700
for n,value in payload.items():
 b=base64.b64decode(value);assert hashlib.sha256(b).hexdigest()==pins[n];q=r/n
 if q.exists():assert q.read_bytes()==b
 else:q.write_bytes(b)
assert json.loads((r/'cpu_validation.json').read_bytes())['exit']==0
pub=json.loads((r/'publication/publication_status.json').read_bytes());assert pub['state']=='RUNNING' and pub['folder_id']=='1dZE2gMavdnJsK_-VLmdFBdAxBwY10HmA'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
lib=load(r/'frozen_integrity_store.py','skill_integrated_archive_lib')
assert hashlib.sha256((r/'frozen_integrity_store.py').read_bytes()).hexdigest()==skill_publisher.STORE_SHA
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
api=build('drive','v3',http=AuthorizedHttp(recovery_credentials,http=httplib2.Http(timeout=60)),cache_discovery=False)
try:
 store=skill_publisher.parent_verified_store_class(lib)(api,parent=skill_publisher.PARENT,folder_name=skill_publisher.FOLDER)
 found=store.find(skill_publisher.PARENT,skill_publisher.FOLDER);assert len(found)==1 and found[0]['id']==pub['folder_id'];store.folder=found[0]['id']
 proofs={n:store.put(n,r/n,immutable=True) for n in ['recovery_worker_v2.py','recovery_policy_v2.py','inference_contract.py']}
 (r/'integrated_code_raw_verified.json').write_text(json.dumps(proofs,indent=2)+'\\n')
finally:api.close()
skill_training_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'recovery_worker_v2.py'),'--root',str(r)],stdout=(r/'training.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false'})
print(json.dumps({'training_worker_launched':True,'pid':skill_training_process.pid,'optimizer_started_confirmed':False,'requires_root_source_QA_before_optimizer':True,'code_proofs':proofs,'max_updates':300,'gate_steps':[100,300]}))
""".replace('PAYLOAD',repr(files)).replace('PINS',repr(pins))
q=p/'launch_training_runtime.py';assert not q.exists();q.write_text(script,encoding='utf8')
print(json.dumps({'stage_bytes':q.stat().st_size,'pins':pins}))
