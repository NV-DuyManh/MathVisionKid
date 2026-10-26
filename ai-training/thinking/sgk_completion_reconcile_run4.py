"""Rebind reviewed RUN4 projection to actual accepted18 raw row hashes."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json,hashlib
HERE=Path(__file__).resolve().parent
PUB=HERE/'cloud_publication'
RUN=PUB/'sgk_completion_20261021'
def read(p):return json.loads(p.read_text('utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    parent_path=PUB/'sgk_remaining_20261020/reconciliation/candidate_adjudication.json'
    queue_path=PUB/'sgk_remaining_20261020/reconciliation/next_uncovered_tasks.json'
    projection_path=PUB/'sgk_final_forms_20261020/reconciliation_projection.json'
    parent=read(parent_path);queue=read(queue_path);projection=read(projection_path)
    accepted_path=PUB/'sgk_final_forms_20261020/release/accepted_cases.jsonl'
    accepted={json.loads(b)['sample_id']:(json.loads(b),sha(b),i) for i,b in enumerate(accepted_path.read_bytes().splitlines(),1)}
    review_path=PUB/'sgk_final_forms_20261020/release/cross_reviews.jsonl'
    reviews={json.loads(b)['sample_id']:json.loads(b) for b in review_path.read_bytes().splitlines()}
    assert len(accepted)==len(reviews)==18
    matches=[];updates={}
    for match in projection['prospective_matches']:
        assert match['prospective_text_relation_match'] and match['status']=='PENDING_ACCEPTANCE'
        examples=[]
        for ref in match['draft_examples']:
            row,h,line=accepted[ref['sample_id']]
            assert row['provenance']['reviewed_draft_row_sha256']==ref['source_row_sha256']
            assert row['acceptance_status']=='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'
            assert reviews[row['sample_id']]['exported_row_sha256']==h
            assert reviews[row['sample_id']]['reviewed_draft_row_sha256']==ref['source_row_sha256']
            assert all(c['passed'] for c in reviews[row['sample_id']]['criteria'])
            examples.append(dict(reference=dict(sample_id=row['sample_id'],source_file='sgk_final_forms_20261020/release/accepted_cases.jsonl',line=line,sha256=h),reviewed_draft_row_sha256=ref['source_row_sha256'],grade=row['grade'],branch=row['topic'],actual_math_fields={k:row[k] for k in ['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']}))
        update=dict(candidate_id=match['candidate_id'],master_id=match['master_id'],status='ACCEPTED_TEXT_RELATION_DEMONSTRATED',semantic_basis=match['semantic_basis'],accepted_examples=examples,publisher_image_recognition_or_physical_success_certified=False,whole_curriculum_certified=False)
        matches.append(update);updates[update['candidate_id']]=update
    assert len(matches)==9 and len({m['master_id'] for m in matches})==9
    report=deepcopy(parent);report['schema']='finite_candidate_reconciliation.v2_accepted_run4'
    report['parent_adjudication_sha256']=sha(parent_path.read_bytes())
    report['run4_accepted_binding']=dict(source_sha256=sha(accepted_path.read_bytes()),projection_sha256=sha(projection_path.read_bytes()),peer_root_reviews_sha256=sha(review_path.read_bytes()),matches=matches)
    for candidate in report['candidates']:
        update=updates.get(candidate['candidate_id'])
        if not update:continue
        prior=deepcopy(candidate['reconciliation'])
        candidate.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(parent_path.read_bytes()),decision=prior))
        candidate['reconciliation'].update(status='NEW_TEXT_RELATION_DEMONSTRATED',text_relation_demonstrated=True,remaining_constraints=[],semantic_basis=update['semantic_basis'],accepted_run4_examples=update['accepted_examples'],whole_master_closed=False,publisher_image_recognition_or_physical_success_certified=False)
    bycandidate={c['candidate_id']:c for c in report['candidates']}
    closedmasters=set()
    for master in report['masters']:
        relevant=[m for m in matches if m['master_id']==master['master_id']]
        if not relevant:continue
        remaining=[r for r in master['remaining_candidate_branches'] if r['candidate_id'] not in updates]
        master['remaining_candidate_branches']=remaining
        master['accepted_run4_examples']=[e for r in relevant for e in r['accepted_examples']]
        if not remaining:
            master['prior_reconciliation_status']=master['status']
            master['status']='FINITE_TEXT_RELATION_DEMONSTRATED'
            closedmasters.add(master['master_id'])
    assert len(closedmasters)==9
    outqueue=deepcopy(queue);outqueue['schema']='finite_next_uncovered_tasks.v2_accepted_run4'
    outqueue['parent_queue_sha256']=sha(queue_path.read_bytes())
    outqueue['global_master_tasks']=[t for t in queue['global_master_tasks'] if t['master_id'] not in closedmasters]
    assert len(outqueue['global_master_tasks'])==45
    outqueue['counts'].update(global_master_tasks=45,never_appended_missing_masters=37,partial_master_tasks=8)
    report['counts'].update(new_cases_evidence=148,new_chat_links=592,run4_accepted=18,remaining_global_master_tasks=45,never_appended_missing_masters=37,master_status_counts=dict(Counter(m['status'] for m in report['masters'])),candidate_status_counts=dict(Counter(c['reconciliation']['status'] for c in report['candidates'])))
    report['all_sgk_forms_covered']=False
    report['source_selection']='Canonical prior accepted130 plus RUN4 accepted18; all original data retained. Mathematical text relation coverage only.'
    assert len(report['candidates'])==204 and len(report['occurrences'])==315 and len(report['external_g2_candidates'])==91
    assert report['occurrences']==parent['occurrences'] and report['external_g2_candidates']==parent['external_g2_candidates']
    for old,new in zip(parent['candidates'],report['candidates']):
        for k,v in old.items():
            if k not in ('reconciliation','reconciliation_history'):assert new[k]==v
    out=RUN/'reconciliation';out.mkdir(parents=True,exist_ok=True)
    write(out/'candidate_adjudication.json',report);write(out/'next_uncovered_tasks.json',outqueue);write(out/'run4_accepted_binding.json',dict(matches=matches))
    validation=dict(status='PASS',accepted_cases_bound=18,relations_bound=9,original_204_candidate_fields_unchanged=True,occurrences315_unchanged=True,external_g2_91_unchanged=True,remaining_global_master_tasks=45,asset_only_masters_separate=10,full_sgk_coverage_claimed=False,training_started=False,inputs={str(p.relative_to(PUB)):sha(p.read_bytes()) for p in [parent_path,queue_path,projection_path,accepted_path,review_path]},outputs={n:sha((out/n).read_bytes()) for n in ['candidate_adjudication.json','next_uncovered_tasks.json','run4_accepted_binding.json']})
    write(out/'validation.json',validation)
    print(json.dumps({k:v for k,v in validation.items() if k not in ('inputs','outputs')}))
if __name__=='__main__':main()

