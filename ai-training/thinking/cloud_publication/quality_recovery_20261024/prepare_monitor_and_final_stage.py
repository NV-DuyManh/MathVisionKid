from pathlib import Path
import json,base64,hashlib
p=Path(__file__).parent
(p/'status_update_args.json').write_text(json.dumps({'cellId':'poueQGu4aDUb','content':(p/'status_runtime.py').read_text(encoding='utf8')},ensure_ascii=False),encoding='utf8')
names=['final_evaluation_worker.py','test_final_evaluation_worker.py']
assert all((p/n).exists() for n in names)
payload={n:base64.b64encode((p/n).read_bytes()).decode() for n in names}
code='''import pathlib,json,base64,hashlib
r=pathlib.Path('/content/mathvisionkid_quality_recovery_20261024')
payload=PAYLOAD
for n,v in payload.items():
 b=base64.b64decode(v);f=r/n
 if f.exists():assert f.read_bytes()==b,'Do not overwrite staged evaluation code'
 else:f.write_bytes(b)
print(json.dumps({'evaluation_code_staged':True,'evaluation_executed':False,'hashes':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in payload}}))
'''.replace('PAYLOAD',repr(payload))
(p/'stage_final_eval_runtime.py').write_text(code,encoding='utf8')
print(json.dumps({'files':names,'code_bytes':len(code.encode())}))
