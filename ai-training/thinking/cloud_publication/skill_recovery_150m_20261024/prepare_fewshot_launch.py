from pathlib import Path
import hashlib,json,base64
p=Path(__file__).parent
names=['fewshot_contract.py','fewshot_dev_worker.py','source_example_bank.json','fewshot_selection_policy.json','source_example_bank_root_review.json','projection_preflight.json','source_behavior_samples.json','test_fewshot_contract.py','test_source_example_bank.py']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
pins={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
code="""import pathlib,json,hashlib,base64,subprocess,os,sys,importlib.util,time
r=pathlib.Path('/content/mathvisionkid_skill_recovery_150m_20261024')
assert skill_training_process.poll()==0,'Previous training must actually have exited'
assert not globals().get('skill_fewshot_process') or skill_fewshot_process.poll() is not None
assert not (r/'fewshot_dev').exists(),'Do not repeat a development context pass'
assert time.time()<json.loads((r/'owner_run_scope.json').read_bytes())['hard_deadline_unix']-3000
payload=PAYLOAD;pins=PINS
for n,v in payload.items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==pins[n]
 if (r/n).exists():assert (r/n).read_bytes()==b,'Existing immutable evidence differs: '+n
for n,v in payload.items():
 if not (r/n).exists():(r/n).write_bytes(base64.b64decode(v))
sys.path.insert(0,str(r))
import fewshot_contract as skill_F
bank,bank_sha=skill_F.load_and_validate_bank()
policy=json.loads((r/'fewshot_selection_policy.json').read_bytes());assert policy['source_bank_sha256']==bank_sha and policy['frozen_before_fewshot_outputs']
skill_fewshot_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'fewshot_dev_worker.py'),'--root',str(r),'--runtime-seconds','1200'],stdout=(r/'fewshot_dev.log').open('ab',buffering=0),stderr=subprocess.STDOUT,env={**os.environ,'TOKENIZERS_PARALLELISM':'false'})
(r/'fewshot_launch_pins.json').write_text(json.dumps({'files':pins,'bank_sha256':bank_sha,'pid':skill_fewshot_process.pid,'started_unix':time.time(),'training_performed':False},indent=2)+'\\n')
print(json.dumps({'fewshot_dev_launched':True,'pid':skill_fewshot_process.pid,'previous_training_exit':skill_training_process.poll(),'bank_sha256':bank_sha,'selection_policy_sha256':pins['fewshot_selection_policy.json'],'max_seconds':1200,'new_optimizer':False}))
""".replace('PAYLOAD',repr(payload)).replace('PINS',repr(pins))
compile(code,'fewshot_launch','exec')
(p/'launch_fewshot_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'code_bytes':len(code),'assets':pins}))
