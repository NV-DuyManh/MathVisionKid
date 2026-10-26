from pathlib import Path
import json,gzip,base64
p=Path(__file__).parent;r=json.loads((p/'preflight_receipt.json').read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
x=json.loads(gzip.decompress(base64.b64decode(t.split('SKILL_PREFLIGHT_GZIP_BASE64:',1)[1].split()[0])))
for name,key in [('projection_preflight.json','summary'),('locked_test_binding.json','locked_binding')]:
 q=p/name;b=(json.dumps(x[key],ensure_ascii=False,indent=2)+'\n').encode()
 if q.exists():assert q.read_bytes()==b
 else:q.write_bytes(b)
print(json.dumps({k:v for k,v in x['summary'].items() if k!='samples'},ensure_ascii=False))
for s in x['summary']['samples']:print(json.dumps(s,ensure_ascii=False))
