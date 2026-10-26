from pathlib import Path
import json,hashlib,base64,gzip,sys
P=Path(__file__).parent;receipt=json.loads(Path(sys.argv[1]).read_bytes())
value=receipt['result']
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in value['outputs'] if x.get('output_type')=='stream')
payload=json.loads(gzip.decompress(base64.b64decode(text.split('CONDITIONAL_BASE_BUNDLE:',1)[1].split()[0])))
folder=P/'review_baseline';folder.mkdir(exist_ok=False)
for name,encoded in payload['files'].items():
 assert '..' not in name and not name.startswith('/')
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==payload['hashes'][name]
 (folder/name.replace('/','__')).write_bytes(raw)
dev=[json.loads(line) for line in (folder/'new_validation_candidates.jsonl').read_bytes().splitlines()]
base=[json.loads(line) for line in (folder/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
assert [x['id'] for x in dev]==[x['fixture_id'] for x in base]
pairs=[{'fixture':f,'base':b} for f,b in zip(dev,base)]
for grade in range(1,6):
 (folder/f'grade{grade}.json').write_text(json.dumps([x for x in pairs if x['fixture']['grade']==grade],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'baseline_outputs':len(base),'all_eos':all(x['ended_eos'] for x in base),'folder':str(folder),'hashes_verified':True}))
