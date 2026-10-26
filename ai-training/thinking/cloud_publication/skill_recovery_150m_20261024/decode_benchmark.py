from pathlib import Path
import json,base64,gzip,hashlib
p=Path(__file__).parent;r=json.loads((p/'benchmark_capture_receipt.json').read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
b=json.loads(gzip.decompress(base64.b64decode(t.split('CALIBRATION_BUNDLE_GZIP_BASE64:',1)[1].split()[0])))
d=p/'benchmark_review';d.mkdir(exist_ok=True)
for n,v in b['files'].items():
 raw=base64.b64decode(v);assert hashlib.sha256(raw).hexdigest()==b['hashes'][n];(d/n).write_bytes(raw)
for row in (d/'final_generations.jsonl').read_text(encoding='utf8').splitlines():print(row)
