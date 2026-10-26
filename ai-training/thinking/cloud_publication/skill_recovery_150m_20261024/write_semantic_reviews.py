from pathlib import Path
import json,hashlib,sys
from base_review_notes import B
from candidate_review_notes import C
step=int(sys.argv[1]);p=Path(__file__).parent/f'review_step_{step:06d}'
dev=[json.loads(x) for x in (p/'new_validation_candidates.jsonl').read_text(encoding='utf8').splitlines()]
base=[json.loads(x) for x in (p/'training__eval_step_000000__base_generations.jsonl').read_text(encoding='utf8').splitlines()]
cand=[json.loads(x) for x in (p/f'training__eval_step_{step:06d}__adapter_generations.jsonl').read_text(encoding='utf8').splitlines()]
for label,indices in [('g1_g2',range(12)),('g3_g4',range(12,24)),('g5',range(24,30))]:
 if not all(i in B and i in C[step] and i<len(cand) for i in indices):continue
 rows=[]
 for i in indices:
  bp,bl,br=B[i];ap,al,critical,ar=C[step][i];f=dev[i];b,a=base[i],cand[i]
  assert f['id']==b['fixture_id']==a['fixture_id']
  for x,passed in [(b,bp),(a,ap)]:
   if passed:assert x['ended_eos'] and not x['possibly_truncated'] and not x['timed_out']
  rows.append({'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],'base_pass':bp,'adapter_pass':ap,'base_hint_leak':bl,'adapter_hint_leak':al,'critical_new_error':critical,'base_reason':br,'adapter_reason':ar})
 pair=p/f'paired_{label}.json';assert pair.exists()
 report={'all_actual_fields_read':True,'human_review_claimed':False,'root_review':True,'input_pair_sha256':hashlib.sha256(pair.read_bytes()).hexdigest(),'decisions':rows}
 target=p/f'semantic_{label}.json';raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
 if target.exists():assert target.read_bytes()==raw,'Do not overwrite frozen decisions'
 else:target.write_bytes(raw)
 print(json.dumps({'step':step,'label':label,'base':sum(x['base_pass'] for x in rows),'candidate':sum(x['adapter_pass'] for x in rows)}))
