from pathlib import Path,PurePosixPath
import json,hashlib,base64,gzip,sys
P=Path(__file__).parent
receipt=json.loads(Path(sys.argv[1]).read_bytes())
value=receipt['result']
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in value['outputs'] if x.get('output_type')=='stream')
payload=json.loads(gzip.decompress(base64.b64decode(text.split('CONDITIONAL_EVAL_BUNDLE:',1)[1].split()[0])))
step=payload['step'];folder=P/f'review_step_{step:06d}'
folder.mkdir(exist_ok=False)
for name,encoded in payload['files'].items():
 relative=PurePosixPath(name)
 if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe evidence path')
 raw=base64.b64decode(encoded)
 assert hashlib.sha256(raw).hexdigest()==payload['hashes'][name]
 path=folder/name.replace('/','__');path.write_bytes(raw)
(folder/'capture_metadata.json').write_text(json.dumps({k:v for k,v in payload.items() if k!='files'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
dev=[json.loads(x) for x in (folder/'new_validation_candidates.jsonl').read_bytes().splitlines()]
base=[json.loads(x) for x in (folder/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
candidate=[json.loads(x) for x in (folder/f'training__eval_step_{step:06d}__adapter_generations.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in dev]==[r['fixture_id'] for r in base]==[r['fixture_id'] for r in candidate]
pairs=[{'fixture':f,'base':b,'adapter':a} for f,b,a in zip(dev,base,candidate)]
for grades in ((1,2,3),(4,5)):
 subset=[r for r in pairs if r['fixture']['grade'] in grades]
 (folder/('paired_g'+''.join(map(str,grades))+'.json')).write_text(json.dumps(subset,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'step':step,'paired_rows':len(pairs),'folder':str(folder),'all_files_hash_verified':True}))
