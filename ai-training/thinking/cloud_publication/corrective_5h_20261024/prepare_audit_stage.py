from pathlib import Path
import base64
p=Path(__file__).parent
sources={'exhaustive_colab_loader.py':Path('thinking/exhaustive_colab_loader.py'),'audit_view_runtime.py':p/'audit_view_runtime.py','owner_run_scope.json':p/'owner_run_scope.json','eval_fixtures.jsonl':Path('thinking/cloud_publication/t4_budget_3h_20261023/evaluation/new_eval_candidates.jsonl')}
payload={n:base64.b64encode(s.read_bytes()).decode() for n,s in sources.items()}
code='''import pathlib,base64,json,hashlib,subprocess,os
root5=pathlib.Path('/content/mathvisionkid_corrective_5h_20261024')
payload=PAYLOAD
proofs={}
for n,v in payload.items():
 p=root5/n;b=base64.b64decode(v)
 if p.exists() and p.read_bytes()!=b:raise ValueError('differentexistingcode:'+n)
 p.write_bytes(b);proofs[n]=hashlib.sha256(b).hexdigest()
(root5/'staged_code_hashes.json').write_text(json.dumps(proofs,indent=2))
env=dict(os.environ);env['CUDA_VISIBLE_DEVICES']=''
fetch_code='from transformers import AutoTokenizer; AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B",revision="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",trust_remote_code=False); import runpy;runpy.run_path("/content/mathvisionkid_corrective_5h_20261024/audit_view_runtime.py",run_name="__main__")'
cmd=[str(root5/'venv/bin/python'),'-c',fetch_code]
assert not globals().get('corrective_audit_process') or corrective_audit_process.poll() is not None
log=(root5/'audit.log').open('ab');corrective_audit_process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
print(json.dumps({'code_hashes':proofs,'audit_pid':corrective_audit_process.pid,'cpu_only':True}))
'''.replace('PAYLOAD',repr(payload))
(p/'stage_audit_runtime.py').write_text(code,encoding='utf-8')
