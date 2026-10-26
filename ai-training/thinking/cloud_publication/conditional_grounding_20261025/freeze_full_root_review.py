from pathlib import Path
import json,hashlib,sys
from datetime import datetime,timezone
P=Path(__file__).parent;R=P/'review_step_000100'
prefix=json.loads((P/'root_prefix12_review.json').read_bytes())['decisions']
dev=[json.loads(x) for x in (R/'new_validation_candidates.jsonl').read_bytes().splitlines()]
base=[json.loads(x) for x in (R/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
candidate=[json.loads(x) for x in (R/'training__eval_step_000100__adapter_generations.jsonl').read_bytes().splitlines()]
frozen={r['fixture_id']:r for r in json.loads((P/'baseline_semantic_review_frozen.json').read_bytes())['records']}
# Root read all actual grade3–5 transcript pairs; independent judgments retained separately.
checks=[
 (True,False,False,'123 divided5 gives24 remainder3; reconstruct120+3=123 and3<5. No invented quantities.'),
 (True,False,False,'5m=500cm and500−175=325cm correct; unused student heading removed, no new false claim.'),
 (False,True,False,'14×9=126 correct but full solution/final126 leaks in hint mode, as baseline.'),
 (False,True,False,'2000−650=1350ml correct but complete computation and final answer leak, as baseline.'),
 (False,False,False,'Claims no missing data then identifies missing width; same contradiction as baseline. Formula correct and no invented width.'),
 (True,False,False,'Accepts6×15=90 and explicitly explains6bags×15candies/bag. Broad introductory unit wording is imprecise but subsequent dimensioned relation and check are correct.'),
 (True,False,False,'Shows conversion1/6=2/12 before adding7/12+2/12=3/4m. Same-denominator wording refers to displayed converted sum; no false computation.'),
 (True,False,False,'Area12m×7m=84m² correct. Extra empty conditional correction heading alone does not fail under frozen rubric.'),
 (False,True,False,'7/8−1/4=5/8litre correct but full-answer hint leak persists.'),
 (False,True,False,'2×(16+9)=50cm correct but full-answer hint leak persists.'),
 (False,False,False,'Recognizes8-versus6 width contradiction but concludes width information absent instead of precise clarification; same false-missing-data pattern as baseline, no numeric area invented.'),
 (True,False,False,'Correctly accepts3/4−1/8=5/8m and verifies fraction/decimal arithmetic; no false student correction.'),
 (True,False,False,'24×3/8=9litres correct and matches baseline exactly.'),
 (True,False,False,'2.4×1.5=3.6m² and expanded products2+1+.4+.2=3.6 correct.'),
 (False,True,False,'150000×20/100=30000dong correct but final-answer hint leak persists.'),
 (False,True,False,'135÷5×2=54km correct but final-answer hint leak persists.'),
 (True,False,False,'Consistently identifies missingheight without claiming data complete or inventing a measured value. Improves baseline contradiction.'),
 (True,False,False,'Used24litres correct;80−24=56litres left, not66. Only provided studentclaim addressed.')]
records=list(prefix)
for f,b,a,(passed,leak,critical,reason) in zip(dev[12:],base[12:],candidate[12:],checks):
 old=frozen[f['id']]
 records.append({'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],'base_pass':old['base_pass'],'base_hint_leak':old['base_hint_leak'],
 'adapter_pass':passed,'adapter_hint_leak':leak,'critical_new_error':critical,'base_reason':old['reason'],'adapter_reason':reason,
 'base_output_sha256':hashlib.sha256(b['output'].encode()).hexdigest(),'adapter_output_sha256':hashlib.sha256(a['output'].encode()).hexdigest(),
 'all_actual_problem_rubric_and_output_read':True})
assert len(records)==30
for r,f,b,a in zip(records,dev,base,candidate):
 assert r['fixture_id']==f['id'] and r['base_output_sha256']==hashlib.sha256(b['output'].encode()).hexdigest() and r['adapter_output_sha256']==hashlib.sha256(a['output'].encode()).hexdigest()
 assert a['ended_eos'] and not a['possibly_truncated'] and not a['timed_out']
sys.path.insert(0,str(P));import recovery_policy_v2 as policy
summary=policy.summarize_decisions(records)
assert summary['base']['total']==14 and summary['candidate']['total']==15 and not summary['candidate_eligible']
out={'schema':'MathVisionKid.root_paired_decisions.v1','step':100,'decision':'STOP','reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'all_actual_outputs_reviewed':True,'human_review_claimed':False,'decisions':records,
 'review_method':'root_and_peer_agent_semantic_review_of_actual_full_responses','summary':summary,
 'all10_numeric_primary_answers_correct_both':True,'complete_full_task_answer_passes':{'base':10,'adapter':9},
 'independent_review_difference':'Agent treats g1 relative-unit wording as failure while root treats it as imprecise nonfatal wording; root additionally flags newly false carried-addition label on2+7. Both reject due g2 answer grounding regression and contradictory guard.',
 'do_not_resume_this_adapter':True,'sealed_final_test_used':False,'whole_corpus_trained':False}
dest=P/'root_paired_decisions_step_000100.json';assert not dest.exists();dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'base':summary['base']['total'],'candidate':summary['candidate']['total'],'regressions':summary['baseline_pass_regressions'],'new_critical':summary['new_critical_errors'],'decision':'STOP','candidate_eligible':False}))
