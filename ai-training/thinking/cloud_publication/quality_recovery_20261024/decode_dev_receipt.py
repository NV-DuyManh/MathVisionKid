from pathlib import Path
import sys,json,gzip,base64,hashlib
p=Path(__file__).parent
receipt=json.loads(Path(sys.argv[1]).read_bytes());res=receipt.get('result') or receipt.get('structured_content') or receipt.get('data')
outputs=res['outputs'];text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in outputs)
mark='EVAL_BUNDLE_GZIP_BASE64:'
bundle=json.loads(gzip.decompress(base64.b64decode(text.split(mark,1)[1].split()[0])))
dest=p/f"review_step_{bundle['step']:06d}";dest.mkdir(exist_ok=True)
for n,b64 in bundle['files'].items():
 b=base64.b64decode(b64);assert hashlib.sha256(b).hexdigest()==bundle['hashes'][n]
 f=dest/n.replace('/','__');f.write_bytes(b)
dev=[json.loads(x) for x in (dest/'new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x) for x in (dest/'training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
adapter=[json.loads(x) for x in (dest/f"training__eval_step_{bundle['step']:06d}__adapter_generations.jsonl").read_text(encoding='utf8').splitlines()]
assert [x['id'] for x in dev]==[x['fixture_id'] for x in base]
assert [x['id'] for x in dev[:len(adapter)]]==[x['fixture_id'] for x in adapter]
assert bundle.get('partial_adapter') or len(adapter)==30
for label,grades in [('g1_g2',[1,2]),('g3_g4',[3,4]),('g5',[5])]:
 paired=[{'fixture':f,'base':b,'adapter':a} for f,b,a in zip(dev,base,adapter) if f['grade'] in grades]
 if len(paired)==6*len(grades):
  path=dest/f'paired_{label}.json';data=(json.dumps(paired,ensure_ascii=False,indent=2)+'\n').encode()
  if path.exists():assert path.read_bytes()==data,'Previously reviewed output prefix changed; do not reuse judgments'
  else:path.write_bytes(data)
(dest/'captured_hashes.json').write_text(json.dumps(bundle['hashes'],indent=2)+'\n',encoding='utf8')
print(json.dumps({'step':bundle['step'],'partial_adapter':bundle.get('partial_adapter',False),'pairs':len(adapter),'completed_grade_files':[x.name for x in dest.glob('paired_*.json')],'dest':str(dest),'all_eos_base':all(x['ended_eos'] and not x['timed_out'] and not x['possibly_truncated'] for x in base),'all_eos_adapter':all(x['ended_eos'] and not x['timed_out'] and not x['possibly_truncated'] for x in adapter)}))
