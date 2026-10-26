from pathlib import Path
import json,hashlib,base64,gzip,sys
p=Path(__file__).parent;r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result')or r.get('structured_content')or r.get('data')
t=''.join(''.join(x.get('text',[])) if isinstance(x.get('text'),list) else x.get('text','')for x in v['outputs'])
b=json.loads(gzip.decompress(base64.b64decode(t.split('FINAL_GZIP_BASE64:',1)[1].split()[0])))
d=p/'final_review';d.mkdir(exist_ok=False)
for n,enc in b['files'].items():
 raw=base64.b64decode(enc);assert hashlib.sha256(raw).hexdigest()==b['hashes'][n];(d/n.replace('/','__')).write_bytes(raw)
manifest=json.loads((d/'final_eval__complete.json').read_bytes());assert manifest['complete']and manifest['test_run_count']==1and not manifest['selection_changed']
fixtures=[json.loads(x)for x in(d/'locked_test_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x)for x in(d/'final_eval__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
selected=[json.loads(x)for x in(d/('final_eval__'+manifest['selected_file'])).read_text(encoding='utf8').splitlines()]
assert [f['id']for f in fixtures]==[x['fixture_id']for x in base]==[x['fixture_id']for x in selected]
for grade in range(1,6):
 pair=[{'fixture':f,'base':b,'selected':s}for f,b,s in zip(fixtures,base,selected)if f['grade']==grade]
 (d/f'paired_g{grade}.json').write_text(json.dumps(pair,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(d/'captured_hashes.json').write_text(json.dumps(b['hashes'],indent=2)+'\n',encoding='utf8')
print(json.dumps({'rows':len(fixtures),'base_all_eos':all(x['ended_eos']and not x['possibly_truncated']and not x['timed_out']for x in base),'selected_all_eos':all(x['ended_eos']and not x['possibly_truncated']and not x['timed_out']for x in selected),'selected_mode_context':manifest['mode_context_selection']['mode_selection']}))
