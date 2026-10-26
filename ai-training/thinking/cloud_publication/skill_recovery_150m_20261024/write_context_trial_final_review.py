from pathlib import Path
import json,hashlib
from final_review_notes import R
p=Path(__file__).parent;d=p/'final_review'
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert set(R)==set(range(20))
decisions=[]
for grade in range(1,6):
 pair=d/f'paired_g{grade}.json';rows=json.loads(pair.read_bytes());group=[]
 for j,row in enumerate(rows):
  i=(grade-1)*4+j;bp,sp,bl,sl,critical,reason=R[i]
  for output,passed in [(row['base'],bp),(row['selected'],sp)]:
   if passed:assert output['ended_eos'] and not output['possibly_truncated'] and not output['timed_out']
  r={'fixture_id':row['fixture']['id'],'grade':grade,'mode':row['fixture']['mode'],'base_pass':bp,'selected_pass':sp,'base_hint_leak':bl,'selected_hint_leak':sl,'critical_new_error':critical,'reason':reason};group.append(r);decisions.append(r)
 doc={'all_actual_fields_read':True,'human_review_claimed':False,'input_pair_sha256':sha(pair),'decisions':group}
 f=d/f'semantic_g{grade}.json';raw=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
 if f.exists():assert f.read_bytes()==raw
 else:f.write_bytes(raw)
def stats(key):
 return {'passed':sum(r[key] for r in decisions),'count':20,'by_mode':{m:{'passed':sum(r[key] for r in decisions if r['mode']==m),'count':sum(r['mode']==m for r in decisions)} for m in sorted({r['mode'] for r in decisions})},'by_grade':{str(g):{'passed':sum(r[key] for r in decisions if r['grade']==g),'count':4} for g in range(1,6)}}
report={'schema':'MathVisionKid.context_trial_locked20_semantic_review.v1','selected_before_test':True,'test_run_count':1,'test_used_to_reselect_original_trial':False,'full_actual_outputs_read':True,'human_review_claimed':False,'base':stats('base_pass'),'selected':stats('selected_pass'),'base_hint_leaks':sum(x['base_hint_leak'] for x in decisions),'selected_hint_leaks':sum(x['selected_hint_leak'] for x in decisions),'new_critical_errors':sum(x['critical_new_error'] for x in decisions),'baseline_pass_regressions':sum(x['base_pass'] and not x['selected_pass'] for x in decisions),'improvement_on_locked_test_demonstrated':sum(x['selected_pass'] for x in decisions)>sum(x['base_pass'] for x in decisions),'production_approved':False,'manifest_sha256':sha(d/'final_eval__complete.json'),'base_output_sha256':sha(d/'final_eval__base_generations.jsonl'),'selected_output_sha256':sha(d/'final_eval__selected_generations.jsonl'),'decisions':decisions,'limits':'20newly authored tasks, small sample; full corpus independence unproven. Same base weights; prompt-context change for5hints, not a weight-training gain.'}
f=p/'context_trial_final_review.json';raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
if f.exists():assert f.read_bytes()==raw
else:f.write_bytes(raw)
print(json.dumps({k:v for k,v in report.items() if k not in ['decisions']},ensure_ascii=False))
