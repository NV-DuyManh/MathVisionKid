import json,hashlib,base64,gzip,sys
from pathlib import Path
p=Path(__file__).parent;r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result')or r.get('structured_content')or r.get('data')
t=''.join(''.join(x.get('text',[]))if isinstance(x.get('text'),list)else x.get('text','')for x in v['outputs'])
b=json.loads(gzip.decompress(base64.b64decode(t.split('NATIVE_GZIP_BASE64:',1)[1].split()[0])))
d=p/'native_review';d.mkdir(exist_ok=True)
for n,x in b['files'].items():
 raw=base64.b64decode(x);assert hashlib.sha256(raw).hexdigest()==b['hashes'][n];dest=d/n.replace('/','__')
 if dest.exists()and n.endswith('.jsonl'):assert raw.startswith(dest.read_bytes()),'Previously read prefix changed'
 dest.write_bytes(raw)
print(json.dumps({'files':list(b['files']),'raw_thinking_downloaded':False}))
