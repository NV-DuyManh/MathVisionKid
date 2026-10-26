from pathlib import Path
import json,base64,gzip
P=Path(__file__).parent
r=json.loads((P/'completed_prefix_receipt.json').read_bytes())['result']
s=''.join(''.join(x.get('text',[])) for x in r['outputs'] if x.get('output_type')=='stream')
v=json.loads(gzip.decompress(base64.b64decode(s.split('COMPLETED_PREFIX:',1)[1].split()[0])))
out=P/'completed_prefix_review.json';assert not out.exists();out.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for grade in [1,2]:
 target=P/f'completed_prefix_grade{grade}.json'
 assert not target.exists();target.write_text(json.dumps([x for x in v['pairs'] if x['fixture']['grade']==grade],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print({'rows':len(v['pairs']),'complete_evaluation':False,'prefix_sha256':v['candidate_prefix_raw_sha256']})
