from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
P=Path(__file__).parent
peer=json.loads((P/'independent_candidate_prefix6_review.json').read_bytes())
pairs=json.loads((P/'completed_prefix6_review.json').read_bytes())['pairs']
judgments=[(True,False,False),(True,False,False),(False,False,False),(True,False,False),(False,False,True),(False,False,False)]
for r,p,(passed,leak,critical) in zip(peer['decisions'],pairs,judgments):
 assert r['fixture_id']==p['fixture']['id'] and r['adapter_pass']==passed and r['adapter_hint_leak']==leak and r['critical_new_error']==critical
 assert r['adapter_output_sha256']==hashlib.sha256(p['adapter']['output'].encode()).hexdigest()
peer.update({'schema':'MathVisionKid.root_prefix_semantic_review.v1','root_has_read_all_actual_prefix_pairs':True,'reviewed_utc':datetime.now(timezone.utc).isoformat(),
 'review_nature':'Root read all actual first6problem/rubric/base and candidate full outputs, agrees with independent per-fixture judgments; no human verification.',
 'independent_review_sha256':hashlib.sha256((P/'independent_candidate_prefix6_review.json').read_bytes()).hexdigest()})
out=P/'root_candidate_prefix6_review.json';assert not out.exists();out.write_text(json.dumps(peer,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print({'prefix_reviewed':6,'candidate_pass':3,'known_regressions':1,'known_new_critical':1,'full_gate_created':False})
