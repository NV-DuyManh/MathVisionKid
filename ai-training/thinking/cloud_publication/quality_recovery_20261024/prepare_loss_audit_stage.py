from pathlib import Path
import json,base64,hashlib
p=Path(__file__).parent;raw=(p/'target_loss_audit_worker.py').read_bytes();compile(raw,'target_loss_audit_worker.py','exec')
code='''import pathlib,json,base64,hashlib,subprocess
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
assert recovery_process.poll()==recovery_probe_process.poll()==recovery_final_process.poll()==0
assert not (r/'target_alignment_audit').exists(),'Inspect prior audit; do not duplicate'
b=base64.b64decode(DATA);f=r/'target_loss_audit_worker.py'
if f.exists():assert f.read_bytes()==b
else:f.write_bytes(b)
audit_loss_process=subprocess.Popen([str(r/'venv/bin/python'),'-u',str(f)],stdout=(r/'target_loss_audit.log').open('ab',buffering=0),stderr=subprocess.STDOUT)
print(json.dumps({'forward_audit_started':True,'pid':audit_loss_process.pid,'worker_sha256':hashlib.sha256(b).hexdigest(),'optimizer_updates':0}))
'''.replace('DATA',repr(base64.b64encode(raw).decode()))
(p/'start_loss_audit_runtime.py').write_text(code,encoding='utf8');print(json.dumps({'worker_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}))
