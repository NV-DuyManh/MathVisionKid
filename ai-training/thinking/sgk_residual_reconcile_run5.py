"""Bind immutable RUN5 draft projection to accepted source hashes. Data-only."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import json,hashlib
HERE=Path(__file__).resolve().parent;PUB=HERE/'cloud_publication'
RUN=PUB/'sgk_completion_20261021';OUT=PUB/'sgk_residual_20261021/reconciliation'
def read(p):return json.loads(p.read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def main():
    cp=RUN/'reconciliation/candidate_adjudication.json';qp=RUN/'reconciliation/next_uncovered_tasks.json'
    pp=RUN/'post_acceptance_mapping/projection.json';ap=RUN/'release/accepted_cases.jsonl';rp=RUN/'release/cross_reviews.jsonl'
    paths=[cp,qp,pp,ap,rp,RUN/'bundle_remote_verified.json']
    before={p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in paths}
    parent,queue,proj=read(cp),read(qp),read(pp)['run5_draft_projection']
    proof=read(RUN/'bundle_remote_verified.json');assert proof['fresh_raw_verified'] and proof['all_bytes_equal']
    accepted={json.loads(b)['sample_id']:(json.loads(b),sha(b),i) for i,b in enumerate(ap.read_bytes().splitlines(),1)}
    reviews={json.loads(b)['sample_id']:json.loads(b) for b in rp.read_bytes().splitlines()}
    assert len(accepted)==len(reviews)==36 and len(queue['global_master_tasks'])==45
    bound={}
    # Verify all36, including branches which do not discharge another grade.
    for sid,(row,h,line) in accepted.items():
        draft=row['provenance']['reviewed_draft_row_sha256'];qa=reviews[sid]
        assert row['acceptance_status']=='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED' and row['split']=='train'
        assert qa['exported_row_sha256']==h and qa['reviewed_draft_row_sha256']==draft
        assert len(qa['criteria'])==7 and all(x['passed'] for x in qa['criteria'])
        assert not any(row.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        bound[sid]=dict(reference=dict(sample_id=sid,source_file=ap.relative_to(PUB).as_posix(),line=line,sha256=h,bundle_id=proof['id'],bundle_member='data/release/accepted_cases.jsonl'),reviewed_draft_row_sha256=draft,grade=row['grade'],branch=row['topic'],master_id=row['coverage']['finite_master_id'],actual_math_fields={k:row[k] for k in ['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']})
    def refs(items):
        out=[]
        for ref in items:
            e=bound[ref['sample_id']];assert e['reviewed_draft_row_sha256']==ref['source_row_sha256']
            out.append(deepcopy(e))
        return out
    updates={};matches=[]
    for overlay in proj['candidate_overlay']:
        if overlay['status']=='BASELINE_UNCHANGED_NO_RUN5_DRAFT_MATCH':continue
        same=refs(overlay['same_grade_draft_examples']);related=refs(overlay['related_grade_draft_examples'])
        assert all(e['grade'] in overlay['candidate_grades'] for e in same)
        status={'FINITE_SAME_GRADE_TEXT_BRANCH_PENDING_EXPORT':'NEW_TEXT_RELATION_DEMONSTRATED',
                'PARTIAL_FINITE_TEXT_BRANCH_PENDING_EXPORT':'PARTIAL_FINITE_TEXT_BRANCH_DEMONSTRATED',
                'RELATED_RELATION_ONLY_GRADE_AND_BRANCH_PENDING':'RELATED_RELATION_GRADE_AND_BRANCH_PENDING'}[overlay['status']]
        update=dict(candidate_id=overlay['candidate_id'],master_id=overlay['master_id'],status=status,semantic_basis=overlay['semantic_basis'],same_grade_accepted_examples=same,related_grade_accepted_examples=related,remaining_constraints=deepcopy(overlay['remaining_after_hypothetical_export']),original_remaining_constraints=deepcopy(overlay['original_remaining_constraints']),whole_master_closed=False,publisher_image_recognition_or_physical_success_certified=False)
        matches.append(update);updates[overlay['candidate_id']]=update
    assert len(matches)==20
    report=deepcopy(parent);report['schema']='finite_candidate_reconciliation.v3_accepted_run5'
    report['parent_adjudication_sha256']=sha(cp.read_bytes())
    report['run5_accepted_binding']=dict(bundle_id=proof['id'],bundle_sha256=proof['sha256'],source_sha256=sha(ap.read_bytes()),projection_sha256=sha(pp.read_bytes()),root_reviews_sha256=sha(rp.read_bytes()),all36_examples=list(bound.values()),candidate_matches=matches)
    for candidate in report['candidates']:
        u=updates.get(candidate['candidate_id'])
        if not u:continue
        old=deepcopy(candidate['reconciliation'])
        candidate.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(cp.read_bytes()),decision=old))
        candidate['reconciliation'].update(status=u['status'],text_relation_demonstrated=bool(u['same_grade_accepted_examples']),remaining_constraints=u['remaining_constraints'],semantic_basis=u['semantic_basis'],accepted_run5_examples=u['same_grade_accepted_examples'],related_grade_run5_examples=u['related_grade_accepted_examples'],whole_master_closed=False,publisher_image_recognition_or_physical_success_certified=False)
    closed={m['master_id'] for m in proj['outstanding_master_overlay'] if m['status']=='FINITE_TEXT_TASK_POTENTIALLY_SATISFIED_AFTER_ACCEPTED_HASH_EXPORT'}
    assert len(closed)==15
    touched={e['master_id'] for e in bound.values()}
    for master in report['masters']:
        mid=master['master_id']
        if mid not in touched:continue
        master.setdefault('reconciliation_history',[]).append(dict(parent_sha256=sha(cp.read_bytes()),status=master['status'],remaining_candidate_branches=deepcopy(master['remaining_candidate_branches'])))
        master['accepted_run5_examples']=[e for e in bound.values() if e['master_id']==mid]
        if mid in closed:
            master['status']='FINITE_TEXT_RELATION_DEMONSTRATED';master['remaining_candidate_branches']=[]
        else:
            master['status']='PARTIAL_NEW_TEXT_RELATION_WITH_RESIDUALS'
            overlay=next(o for o in proj['outstanding_master_overlay'] if o['master_id']==mid)
            master['remaining_candidate_branches']=deepcopy(overlay['pending_candidate_branches'])
    outq=deepcopy(queue);outq['schema']='finite_next_uncovered_tasks.v3_accepted_run5';outq['parent_queue_sha256']=sha(qp.read_bytes())
    tasks=[]
    for t in queue['global_master_tasks']:
        mid=t['master_id']
        if mid in closed:continue
        new=deepcopy(t)
        if mid in touched:
            o=next(o for o in proj['outstanding_master_overlay'] if o['master_id']==mid)
            new['prior_task']=deepcopy(t)
            new['existing_relation_examples']=[e['reference'] for e in bound.values() if e['master_id']==mid]
            new['required_constraints']=[dict(candidate_id=x['candidate_id'],constraints=x['constraints'],status='PARTIAL_OR_RELATED_GRADE_BRANCH_PENDING') for x in o['pending_candidate_branches']]
            new['run5_accepted_semantic_scope']='Only exact finite text branch; retained grade, open-design, image/physical constraints remain.'
        tasks.append(new)
    assert len(tasks)==30
    outq['global_master_tasks']=tasks
    partial=sum(bool(t.get('existing_relation_examples')) for t in tasks)
    outq['counts'].update(global_master_tasks=30,never_appended_missing_masters=30-partial,partial_master_tasks=partial)
    report['counts'].update(new_cases_evidence=184,new_chat_links=736,run5_accepted=36,remaining_global_master_tasks=30,never_appended_missing_masters=30-partial,master_status_counts=dict(Counter(m['status'] for m in report['masters'])),candidate_status_counts=dict(Counter(c['reconciliation']['status'] for c in report['candidates'])))
    report['all_sgk_forms_covered']=False
    report['source_selection']='Prior accepted148 plus RUN5accepted36, immutable source/export hashes bound. Finite text relation scope only; grade aliases and91G2 retained.'
    assert report['occurrences']==parent['occurrences'] and len(report['occurrences'])==315
    assert report['external_g2_candidates']==parent['external_g2_candidates'] and len(report['external_g2_candidates'])==91
    assert len(report['candidates'])==204 and len(report['masters'])==167
    for old,new in zip(parent['candidates'],report['candidates']):
        for k,v in old.items():
            if k not in ('reconciliation','reconciliation_history'):assert new[k]==v
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/'candidate_adjudication.json',report);write(OUT/'next_uncovered_tasks.json',outq)
    write(OUT/'run5_accepted_binding.json',dict(status='ACCEPTED_HASH_BOUND',all36_examples=list(bound.values()),candidate_matches=matches,finite_text_tasks_discharged=sorted(closed),image_physical_or_other_grade_scope_unchanged=True))
    after={p.relative_to(PUB).as_posix():sha(p.read_bytes()) for p in paths};assert after==before
    result=dict(status='PASS',accepted_cases_bound=36,candidate_relations_bound=20,finite_text_tasks_discharged=15,remaining_global_master_tasks=30,partial_master_tasks=partial,never_appended_missing_masters=30-partial,asset_only_masters_separate=10,original204_candidate_fields_preserved=True,occurrences315_preserved=True,external_g2_91_preserved=True,all_sgk_forms_covered=False,training_started=False,inputs=before,outputs={n:sha((OUT/n).read_bytes()) for n in ['candidate_adjudication.json','next_uncovered_tasks.json','run5_accepted_binding.json']})
    write(OUT/'validation.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','outputs')}))
if __name__=='__main__':main()

