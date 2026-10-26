from pathlib import Path
import json,base64,gzip,hashlib,sys
p=Path(__file__).parent;r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result')or r.get('structured_content')or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
b=json.loads(gzip.decompress(base64.b64decode(t.split('FEWSHOT_GZIP_BASE64:',1)[1].split()[0])))
d=p/'fewshot_review';d.mkdir(exist_ok=True)
for n,x in b['files'].items():
 raw=base64.b64decode(x);assert hashlib.sha256(raw).hexdigest()==b['hashes'][n]
 f=d/n.replace('/','__')
 if f.exists() and n.endswith('generations.jsonl'):assert raw.startswith(f.read_bytes()),'Previously read output prefix changed'
 elif f.exists() and n.endswith('contract.json'):assert raw==f.read_bytes()
 f.write_bytes(raw)
rows=[json.loads(x) for x in (d/'fewshot_dev__generations.jsonl').read_text(encoding='utf8').splitlines()]
fixtures=[json.loads(x) for x in (p/'review_step_000100/new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
assert [x['fixture_id'] for x in rows]==[x['id'] for x in fixtures[:len(rows)]]
(d/'captured_hashes.json').write_text(json.dumps(b['hashes'],indent=2)+'\n',encoding='utf8')
if not b['partial']:assert len(rows)==30
print(json.dumps({'rows':len(rows),'partial':b['partial'],'all_eos':all(x['ended_eos']and not x['possibly_truncated']and not x['timed_out']for x in rows)}))
