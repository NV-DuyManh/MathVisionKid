from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_bytes());v=r.get('result') or r.get('structured_content') or r.get('data')
parts=[]
for x in v['outputs']:
 t=x.get('text','');parts.append(''.join(t) if isinstance(t,list) else t)
s=json.loads(''.join(parts).strip())
out={k:s.get(k) for k in ['observed_utc','training','final_evaluation','four_controls_publication_status.json']}
out['publisher_state']=s.get('publisher',{}).get('state')
out['final_evaluation_publication_state']=s.get('final_eval_publication_status.json',{}).get('state')
for n in ['training/error.json','final_eval/error.json']:
 if n in s:out[n]=s[n]
print(json.dumps(out,ensure_ascii=False))
