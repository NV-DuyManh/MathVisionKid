from pathlib import Path
import sys,json,base64,hashlib,gzip
p=Path(__file__).parent;r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
text=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','') for x in v['outputs'])
bundle=json.loads(gzip.decompress(base64.b64decode(text.split('FINAL_BUNDLE_GZIP_BASE64:',1)[1].split()[0])))
d=p/'final_review';d.mkdir(exist_ok=True)
for n,b in bundle['files'].items():
 raw=base64.b64decode(b);assert hashlib.sha256(raw).hexdigest()==bundle['hashes'][n]
 (d/n.replace('/','__')).write_bytes(raw)
fixtures=[json.loads(x) for x in (d/'locked_test_candidates.jsonl').read_text(encoding='utf8').splitlines()]
assert json.loads((d/'training__best.json').read_bytes())['kind']=='untrained_base','Adapt decoder explicitly if selected adapter'
outputs=[json.loads(x) for x in (d/'final_eval__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
assert [x['fixture_id'] for x in outputs]==[x['id'] for x in fixtures[:len(outputs)]]
for grade in range(1,6):
 paired=[{'fixture':f,'base':o,'adapter':o} for f,o in zip(fixtures,outputs) if f['grade']==grade]
 if len(paired)==4:
  target=d/f'paired_g{grade}.json';raw=(json.dumps(paired,ensure_ascii=False,indent=2)+'\n').encode()
  if target.exists():assert target.read_bytes()==raw,'Previously reviewed final prefix changed'
  else:target.write_bytes(raw)
(d/'captured_hashes.json').write_text(json.dumps(bundle['hashes'],indent=2)+'\n',encoding='utf8')
print(json.dumps({'partial':bundle['partial'],'rows':len(outputs),'all_eos':all(x['ended_eos'] and not x['timed_out'] and not x['possibly_truncated'] for x in outputs),'complete_grade_files':[x.name for x in d.glob('paired_g*.json')]}))
