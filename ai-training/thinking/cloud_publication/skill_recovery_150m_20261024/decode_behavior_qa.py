from pathlib import Path
import json,base64,gzip
p=Path(__file__).parent;r=json.loads((p/'behavior_samples_receipt.json').read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
b=gzip.decompress(base64.b64decode(t.split('BEHAVIOR_QA_GZIP_BASE64:',1)[1].split()[0]));(p/'source_behavior_samples.json').write_bytes(b)
for x in json.loads(b)['samples']:print(json.dumps(x,ensure_ascii=False))
