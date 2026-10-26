from pathlib import Path
import base64,json
p=Path(__file__).parent
names=['probe_step1_worker.py','test_probe_step1_worker.py']
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
code='''import pathlib,json,base64,subprocess
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert recovery_process.poll()==0,'Existing train must exit safely first'
assert not (r/'training/eval_step_000001').exists(),'Probe once only'
assert not (r/'final_eval').exists(),'Locked test stays unused until selection'
payload=PAYLOAD
for n,v in payload.items():
 b=base64.b64decode(v);f=r/n
 if f.exists():assert f.read_bytes()==b
 else:f.write_bytes(b)
log=(r/'probe_step1.log').open('ab',buffering=0)
recovery_probe_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(r/'probe_step1_worker.py'),'--root',str(r)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps({'probe_started':True,'pid':recovery_probe_process.pid,'training_performed':False,'checkpoint_step':1,'locked_test_access':False,'run_complete':json.loads((r/'training/run_complete.json').read_bytes())}))
'''.replace('PAYLOAD',repr(payload))
(p/'start_probe_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'bytes':len(code.encode())}))
