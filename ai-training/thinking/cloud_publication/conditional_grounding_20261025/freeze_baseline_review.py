"""Root semantic judgments after reading all 30 actual baseline outputs."""
from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).parent;D=P/'review_baseline'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
textsha=lambda s:hashlib.sha256(s.encode()).hexdigest()
fixtures=[json.loads(line) for line in (D/'new_validation_candidates.jsonl').read_bytes().splitlines()]
outputs=[json.loads(line) for line in (D/'training__eval_step_000000__base_generations.jsonl').read_bytes().splitlines()]
reasons={
 'dev25_g1_answer_01':'7+6=13 correct; adding received labels is the right relation, label unit retained. Repeated consistency assertion is a weak check but not a false one.',
 'dev25_g1_answer_02':'18−9=9 correct with subtraction relation and fruit unit. Recomputes the same subtraction rather than an independent inverse check; no such extra requirement is imposed retrospectively.',
 'dev25_g1_hint_no_answer_01':'Gives13 and the full5+8=13 solution in hint mode; final-answer leak.',
 'dev25_g1_hint_no_answer_02':'Gives8 and14−6=8 in hint mode; final-answer leak.',
 'dev25_g1_missing_or_contradictory_info_01':'Identifies missing removed count but twice also asserts data are sufficient/full. Internal contradiction makes full response fail despite ultimately withholding a number.',
 'dev25_g1_student_error_01':'Correctly accepts supplied8+5=13 and total13fish. No invented student operation; optional style suggestion does not claim a mathematical error.',
 'dev25_g2_answer_01':'5equal rows ×4cakes=20cakes; relation and units correct, reiterates group count as check.',
 'dev25_g2_answer_02':'42−17=25books; correct remaining-quantity relation and unit. Check repeats arithmetic but contains no incorrect step.',
 'dev25_g2_hint_no_answer_01':'Gives15 and3×5=15; full solution instead of hint. Extra word buộc is poor unit wording.',
 'dev25_g2_hint_no_answer_02':'Gives22cm and36−14=22; final-answer leak.',
 'dev25_g2_missing_or_contradictory_info_01':'Notices5-versus6 conflict then arbitrarily treats6as authoritative and concludes24pens. Conditional intermediate24wouldbeallowed, unconditional final24 is not.',
 'dev25_g2_student_error_01':'False grounding: accepts2+7=9 as the total for2platesof7, claims meaning/unit appropriate. Arithmetic equality alone is true but required group multiplication is14.',
 'dev25_g3_answer_01':'Quotient24remainder3 correct;24×5=120 and123−120=3with3<5 establish valid remainder. Final detached3is contextual remainder, not false rational equality.',
 'dev25_g3_answer_02':'5m=500cm then500−175=325cm correct; relation and unit explained. Empty student-work placeholder is irrelevant wording but invents no actual student calculation.',
 'dev25_g3_hint_no_answer_01':'Gives126chairs and full14×9 calculation; final-answer leak.',
 'dev25_g3_hint_no_answer_02':'Gives1350ml and complete conversion/subtraction; final-answer leak.',
 'dev25_g3_missing_or_contradictory_info_01':'Correct missing-width conclusion and no invented width, but also asserts data sufficient/consistent. Contradictory full response fails.',
 'dev25_g3_student_error_01':'Accepts supplied6×15=90with meaning6bags15each; independently decomposes60+30=90, unit retained.',
 'dev25_g4_answer_01':'7/12+1/6=9/12=3/4m; common denominator, sum relation and unit correct.',
 'dev25_g4_answer_02':'Rectangle area12×7=84m² with formula and square-unit explanation; arithmetic check is repetitive but correct.',
 'dev25_g4_hint_no_answer_01':'Gives5/8litre through full subtraction; final-answer leak.',
 'dev25_g4_hint_no_answer_02':'Gives50cm and complete perimeter computation; final-answer leak.',
 'dev25_g4_missing_or_contradictory_info_01':'Initially identifies competing widths8and6, then incorrectly claims length or width information absent and requests either. Given15cm length is not missing; fails precise grounding/clarification.',
 'dev25_g4_student_error_01':'Correctly accepts supplied3/4−1/8=5/8m and verifies through6/8−1/8; no false correction.',
 'dev25_g5_answer_01':'24×3/8=9litres with fraction-of-quantity relation; alternate24÷8×3=9 check correct.',
 'dev25_g5_answer_02':'2.4×1.5=3.6m²; expands product3+.6=3.6 and retains area relation/square unit.',
 'dev25_g5_hint_no_answer_01':'Gives30000dong and full percentage computation; final-answer leak.',
 'dev25_g5_hint_no_answer_02':'Gives54km through both stages135÷5=27,27×2=54; final-answer leak.',
 'dev25_g5_missing_or_contradictory_info_01':'Identifies missingheight and does not invent numericheight, but explicitly asserts data full/consistent first. Contradictory full response fails; symbolic h alone would not be a hallucinated measurement.',
 'dev25_g5_student_error_01':'Checks exactly supplied24used/66left:24usedcorrect;80−24=56left, so66wrong. Does not invent hidden student reasoning.'}
passes={f['id'] for f in fixtures if f['mode']=='answer'}|{
 'dev25_g1_student_error_01','dev25_g3_student_error_01','dev25_g4_student_error_01','dev25_g5_student_error_01'}
records=[]
for f,o in zip(fixtures,outputs):
 assert f['id']==o['fixture_id'] and o['ended_eos'] and not o['timed_out'] and not o['possibly_truncated']
 records.append({'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],
  'base_pass':f['id'] in passes,'base_hint_leak':f['mode']=='hint_no_answer',
  'numeric_answer_correct_if_answer_mode':True if f['mode']=='answer' else None,
  'actual_problem_sha256':textsha(f['userproblem']),'actual_output_sha256':textsha(o['output']),
  'all_actual_problem_rubric_and_output_read':True,'reason':reasons[f['id']]})
review={'schema':'MathVisionKid.conditional_baseline_fulltask_review.v1',
 'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'fixture_raw_sha256':sha(D/'new_validation_candidates.jsonl'),
 'base_output_raw_sha256':sha(D/'training__eval_step_000000__base_generations.jsonl'),
 'contract_sha256':sha(D/'training__evaluation_contract.json'),
 'judgments_fixed_before_adapter_outputs_read':True,'root_has_read_all30':True,
 'human_review_claimed':False,'review_nature':'Root LLM semantic review of actual rendered problem, expected/rubric and final response; exact arithmetic crosscheck; no external teacher credential.',
 'grading_scope':'Requested tutor mode, correctness and grounding of the whole answer. Mathematical/contradictory claims matter. Wordiness and repeated-but-correct check alone are not retroactive fail criteria. Hint containing finalanswer fails.',
 'fulltask_pass':sum(r['base_pass'] for r in records),'fixture_count':30,
 'answer_numeric_correct':10,'answer_numeric_denominator':10,
 'hint_leaks':sum(r['base_hint_leak'] for r in records),
 'is_product_accuracy_or_fullcurriculum_certification':False,'records':records}
path=P/'baseline_semantic_review_frozen.json'
assert not path.exists(),'Do not silently change frozen baseline judgments'
path.write_bytes((json.dumps(review,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'fulltask':review['fulltask_pass'],'answer_numeric':'10/10','hint_leaks':review['hint_leaks'],'review_sha256':sha(path)}))
