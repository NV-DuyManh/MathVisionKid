import json,sys
from pathlib import Path
p=Path(__file__).parent;phase=sys.argv[1]
if phase=='dev':
 from base_review_notes import B
 from native_thinking_probe import DEV_INDICES
 allf=[json.loads(x)for x in(p/'review_step_000100/new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()];fixtures=[allf[i]for i in DEV_INDICES]
else:fixtures=[json.loads(x)for x in(p/'native_locked15.jsonl').read_text(encoding='utf8').splitlines()]
folder=p/'native_review';stem=f'native_probe__{phase}__native_thinking_final';f=folder/(stem+'.jsonl');f=f if f.exists()else folder/(stem+'.partial.jsonl')
rows=[json.loads(x)for x in f.read_text(encoding='utf8').splitlines()]
base=[]
if phase=='final':
 q=folder/'native_probe__final__baseline_nonthinking_final.jsonl';q=q if q.exists()else folder/'native_probe__final__baseline_nonthinking_final.partial.jsonl'
 base=[json.loads(x)for x in q.read_text(encoding='utf8').splitlines()]
for i in range(int(sys.argv[2]),min(len(rows),int(sys.argv[2])+int(sys.argv[3]))):
 assert fixtures[i]['id']==rows[i]['fixture_id'];v={'index':i,'fixture':fixtures[i],'candidate':rows[i]}
 if phase=='dev':v['base_review']=B[DEV_INDICES[i]]
 else:v['base']=base[i]
 print(json.dumps(v,ensure_ascii=False))
