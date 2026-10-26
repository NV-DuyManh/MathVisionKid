from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
P=Path(__file__).parent
prefix=json.loads((P/'completed_prefix_review.json').read_bytes())
frozen={x['fixture_id']:x for x in json.loads((P/'baseline_semantic_review_frozen.json').read_bytes())['records']}
# Root authored these judgments after reading all twelve actual full response pairs.
judgments=[
 (True,False,False,'7+6=13 labels, correct addition relation and unit. Imprecise relative-unit wording does not change the count or invent a problem fact.'),
 (True,False,False,'18−9=9 fruits, subtraction and explanation correct; repeated correct checks are not a retroactive failure criterion.'),
 (False,True,False,'Same complete solution and final13 as baseline. Persistent hint-answer leak; no newly wrong arithmetic.'),
 (False,True,False,'Computes14−6=8 and gives final8 leaves. Hint leaks answer; arithmetic remains correct.'),
 (True,False,False,'Identifies the missing number of cups removed and consistently refuses a definite remainder. Baseline falsely claimed complete data; this contradiction is removed.'),
 (True,False,False,'Correctly confirms only supplied8+5=13 fish line. No invented student step or false correction.'),
 (False,False,True,'5×4=20 cakes is numerically correct, but twice falsely says the problem supplied no unit while cakes and rows are explicitly given. This is a new contradictory grounding claim absent in baseline, not merely verbosity.'),
 (True,False,False,'42−10=32 and32−7=25 correctly compute42−17; relation and book unit correct.'),
 (False,True,False,'Computes3×5=15 and states final15. Persistent full-answer hint leak; malformed per-bag wording also existed in baseline.'),
 (False,True,False,'Gives36−14=22cm and final22; persistent hint leak, no new mathematical error.'),
 (False,False,True,'Still arbitrarily chooses6 instead of resolving5-versus6 contradiction, a persistent failure. Newly asserts data have no contradiction and are sufficient, unlike baseline acknowledgement; this false denial is a new grounding error.'),
 (False,False,True,'Still approves wrong relation2+7=9 for two groups of7, already wrong in baseline. Additionally newly calls2+7 a carried addition even though result9 needs no carry: a new mathematical-property error.')]
assert len(judgments)==len(prefix['pairs'])==12
records=[]
for pair,(passed,leak,critical,reason) in zip(prefix['pairs'],judgments):
 f=pair['fixture'];old=frozen[f['id']]
 records.append({'fixture_id':f['id'],'grade':f['grade'],'mode':f['mode'],
 'base_pass':old['base_pass'],'base_hint_leak':old['base_hint_leak'],
 'adapter_pass':passed,'adapter_hint_leak':leak,'critical_new_error':critical,
 'base_reason':old['reason'],'adapter_reason':reason,
 'base_output_sha256':hashlib.sha256(pair['base']['output'].encode()).hexdigest(),
 'adapter_output_sha256':hashlib.sha256(pair['adapter']['output'].encode()).hexdigest(),
 'all_actual_problem_rubric_and_output_read':True})
value={'schema':'MathVisionKid.root_partial_paired_review.v1','step':100,
 'reviewed_utc':datetime.now(timezone.utc).isoformat(),'complete_evaluation':False,'gate_may_be_created':False,
 'candidate_prefix_raw_sha256':prefix['candidate_prefix_raw_sha256'],
 'policy_sha256':hashlib.sha256((P/'paired_review_policy_pre_candidate.json').read_bytes()).hexdigest(),
 'human_review_claimed':False,'decisions':records}
dest=P/'root_prefix12_review.json';assert not dest.exists();dest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print({'reviewed_rows':len(records),'base_pass':sum(x['base_pass'] for x in records),'candidate_pass':sum(x['adapter_pass'] for x in records),'full_evaluation':False})
