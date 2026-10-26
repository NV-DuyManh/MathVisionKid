"""Bounded G2 handoff repair export; CPU tokenizer, never training or weights.

Original ZIPs stay audit-only. All final rows are derived from reviewed inputs.
The cloud-wide collision check remains separate from this bounded validation.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import ast, hashlib, json, sys, zipfile

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/antigravity_intake_20261022'
sys.path.insert(0,str(HERE))
import primary_math_data_pipeline as P
import exhaustive_colab_loader as L
import math_data_archive_audit as A

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(x):return hashlib.sha256(x).hexdigest()
def rowsha(x):return sha(canon(x).encode())
def load(name):return json.loads((RUN/name).read_text(encoding='utf8'))
def rows(name):return [json.loads(s) for s in (RUN/name).read_text(encoding='utf8').splitlines() if s.strip()]
def write(name,x):
    (RUN/name).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def jlines(name,rs):
    b=(''.join(canon(r)+'\n' for r in rs)).encode('utf8');(RUN/name).write_bytes(b)
    return {'bytes':len(b),'sha256':sha(b),'rows':len(rs)}
def decimal_exact(e):
    def walk(n):
        if isinstance(n,ast.Constant):return Decimal(ast.get_source_segment(e,n))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -walk(n.operand)
        a,b=walk(n.left),walk(n.right)
        if isinstance(n.op,ast.Add):return a+b
        if isinstance(n.op,ast.Sub):return a-b
        if isinstance(n.op,ast.Mult):return a*b
        if isinstance(n.op,ast.Div):return a/b
        raise ValueError('unsupported decimal operation')
    with localcontext() as c:
        c.prec=80
        return walk(ast.parse(e,mode='eval').body)

def main():
    inputs=[('repaired_b1_cases.jsonl','qa7_b1.jsonl'),
            ('repaired_b2_b4_cases.jsonl','qa7_b2_b4.jsonl'),
            ('repaired_b5_b8_cases.jsonl','repaired_b5_b8_qa7.jsonl')]
    protected,questions,protected_pins=P.protections()
    policy=HERE/'data/primary_math_teacher_20261016/numeric_overlap_exception_policy.json'
    assert json.loads(policy.read_text(encoding='utf8'))['owner_authorized'] is True
    final=[];qas=[];bindings=[];numeric=[];exceptions=[];all_inputs=[]
    root_changes=[]
    revised_claims={
      'missing_learner_date_location_guard':'Requests local date/time/location evidence; does not infer learner date from tutor system date.',
      'calendar_grid_boundary_first_weekday':'Complete weekday grid, missing cells, first weekday and prior-week month-boundary date.',
      'capacity_inclusive_bijection_all_assignments':'Common-unit finite one-to-one capacity assignment, inclusive full fits, all assignments.',
      'grid_target_copy_all_incidence':'Copies every supplied vertex and segment onto a second equal-scale grid without changing orientation.',
      'cut_origin_square_complete_cover':'Tracks specified original cut, all pieces and complete square cover without overlap.',
      'clock_continuous_hour_rollover':'Continuous minute/hour hand positions across noon after elapsed half-hour.',
      'local_max_maze_ties_dead_end':'Local maximum outgoing-edge rule, ties, lawful complete paths and dead-end paths.',
      'two_draw_all_unordered_events':'Sequential finite stock without replacement; unordered outcomes and certain/possible/impossible events.'}
    for source_name,qa_name in inputs:
        qa_by={r['sample_id']:r for r in rows(qa_name)}
        for original in rows(source_name):
            sid=original['sample_id'];h=rowsha(original);q=qa_by[sid]
            assert h==q.get('source_row_sha256',q.get('reviewed_row_sha256')),(sid,'review input hash')
            assert set(q['criteria'])==set(P.REVIEW_FIELDS)
            assert all(v is True or v=='PASS' for v in q['criteria'].values())
            r=deepcopy(original);changes=[]
            assert r['source_role']=='AI_GENERATED'
            assert all(r[k] is False for k in ['human_verified','teacher_certified','owner_human_reviewed'])
            if r.get('student_work'):
                for observation in r['student_work']['observations']:
                    assert observation['excerpt'] in r['student_work']['text']
                    if not observation.get('claim_scope'):
                        observation['claim_scope']='Only the explicitly supplied student statement; no hidden reasoning or unseen image inferred.'
                        changes.append('Added explicit observation claim_scope; excerpt/text retained.')
            if sid=='g2_bal_20261022_balance_high_pan_misconception_error':
                r['problem']=r['problem'].replace('Cân 1 ở trên','Cân 1 được mô tả trong đề')
                changes.append('Removed contextual above reference; full supplied balance description retained.')
            branch=r.get('coverage',{}).get('branch')
            if branch in revised_claims:
                r['curriculum_assignment']['coverage_claim']=revised_claims[branch]
                if branch=='local_max_maze_ties_dead_end':
                    r['coverage_tags']=['local_maximum','finite_branching_maze','ties_and_dead_ends']
                changes.append('Replaced inherited template coverage wording with exact new branch scope.')
            r['acceptance_status']='ACCEPTED_OWNER_PREAUTHORIZED'
            r['quality_status']='ROOT_FULL_FIELD_QA7_PASSED'
            r['provenance'].update(acceptance_basis='OWNER_PREAUTHORIZED_CONTENT_QA_NOT_HUMAN_ATTESTATION',
                human_content_review_completed=False,independent_external_reviewer=False,
                reviewed_repair_input_sha256=h,original_intake_drive_id='1Ji6l7rg-lpg81ddq3JG4gUeIDyOOGLYM',
                original_intake_zip_sha256='2b5f19aa2cc012865021d15c0722aac431e6e7e1b8059f91ad3d95c903f101e2',
                final_review_actor='Codex root content self-QA',final_metadata_repairs=changes)
            # Preserve all answers: no answer changes to pass any gate.
            assert r['expected_answer']==original['expected_answer']
            assert len(r['hints'])==3 and [x['level'] for x in r['hints']]==[1,2,3]
            assert r['initial_guidance'] and r['givens'] and r['requested_quantity']
            expressions=[]
            for s in r['worked_steps']:
                assert all(isinstance(s.get(k),str) and s[k].strip() for k in ['title','reason','explanation'])
                e=s.get('expression')
                if not e:expressions.append('');continue
                expanded=P.expand(e,expressions);f=P.exact(expanded);d=decimal_exact(expanded)
                assert f==Fraction(str(s['result'])),(sid,s['step_id'])
                assert abs(d-Decimal(f.numerator)/Decimal(f.denominator))<Decimal('1e-25')
                numeric.append(dict(sample_id=sid,step_id=s['step_id'],expression=expanded,
                    result=s['result'],Fraction=str(f),Decimal=str(d),passed=True))
                expressions.append(expanded)
            assert P.normalized(r['problem']) not in questions,(sid,'protected exact question')
            signatures=L.source_signatures(r);overlap=sorted(set(signatures) & protected)
            r['canonical_signatures']=signatures
            export_h=rowsha(r)
            binding=dict(sample_id=sid,reviewed_source_file=source_name,reviewed_source_row_sha256=h,
                parent_source_row_sha256=r['provenance'].get('parent_source_row_sha256'),
                exported_row_sha256=export_h,original_expected_answer_preserved=True,metadata_repairs=changes)
            bindings.append(binding)
            if overlap:exceptions.append(dict(sample_id=sid,reviewed_source_row_sha256=h,
                exported_row_sha256=export_h,overlap_signatures=overlap,
                policy_sha256=sha(policy.read_bytes()),numeric_test_independence_claimed=False,
                exact_question_overlap=False,content_QA7_passed=True,human_review_claimed=False))
            qas.append(dict(sample_id=sid,reviewed_source_row_sha256=h,exported_row_sha256=export_h,
                criteria={k:True for k in P.REVIEW_FIELDS},
                actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps',
                  'all reasons/explanations/results/units','expected_answer','initial_guidance','all three hints'],
                prior_QA_record_sha256=rowsha(q),final_review='ROOT_ACTUAL_CONTENT_READING_WITH_FINITE_ORACLES',
                semantic_proof_is_parser_or_keyword_pass=False,human_review_completed=False,
                independent_external_final_review_claimed=False,
                scope='Explicit finite text/complete annotation or missing-evidence guard; no physical result certified.'))
            final.append(r);all_inputs.append(original)
            if changes:root_changes.append(dict(sample_id=sid,changes=changes))
    assert len(final)==64 and len({r['sample_id'] for r in final})==64
    assert len({r['case_group_id'] for r in final})==64
    assert len({P.normalized(r['problem']) for r in final})==64
    chats=[]
    for r in final:
        h=rowsha(r)
        for mode in L.MODES:
            target=(dict(can_solve=r['can_solve'],initial_guidance=r['initial_guidance'],
                steps=r['worked_steps'],answer=r['expected_answer']) if mode=='worked_solution' else
                {k:r['hints'][int(mode[-1])-1][k] for k in ['hint','question']})
            prompt={k:r[k] for k in ['grade','problem','givens','requested_quantity','student_work']};prompt['mode']=mode
            chat=dict(sample_id=r['sample_id']+':'+mode,source_sample_id=r['sample_id'],
                case_group_id=r['case_group_id'],grade=r['grade'],split='train',mode=mode,
                schema='neutral_teacher_chat.v1_not_live_PlanDraft',source_row_sha256=h,
                source_role='AI_GENERATED',human_verified=False,teacher_certified=False,owner_human_reviewed=False,
                acceptance_status='ACCEPTED_OWNER_PREAUTHORIZED',canonical_signatures=r['canonical_signatures'],
                messages=[dict(role='system',content=P.SYSTEM),dict(role='user',content=canon(prompt)),
                          dict(role='assistant',content=canon(target))])
            L.validate_chat(chat);assert not A.linkage_errors(chat,A.source_projection(r))
            chats.append(chat)
    # Local cache only: tokenizer configuration and vocabulary, no model weights.
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(L.MODEL,revision=L.REVISION,local_files_only=True)
    tokens=[]
    for chat in chats:
        encoded=L.tokenize_assistant_only(chat,tokenizer,40960)
        tokens.append(dict(sample_id=chat['sample_id'],chat_row_sha256=rowsha(chat),
            sequence_tokens=len(encoded['input_ids']),completion_tokens=encoded['completion_tokens'],
            assistant_only_mask_checked=True,truncated=False))
    queue_path=HERE/'cloud_publication/data_resume_20261022/next_uncovered_tasks.json'
    queue=json.loads(queue_path.read_text(encoding='utf8'));coverage=[]
    for task in queue['g2_pending_specific_tasks']:
        matches=[r for r in final if r['coverage']['planning_task_id']==task['task_id']]
        assert matches,task['task_id']
        observed=set(c for r in matches for c in r['coverage']['candidate_ids'])
        assert set(task['candidate_ids'])<=observed,(task['task_id'],'candidate binding absent')
        physical=task['preparation_kind']=='actual_observation_required'
        coverage.append(dict(task_id=task['task_id'],candidate_ids=task['candidate_ids'],
            original_task_sha256=rowsha(task),constraints=task['minimal_required_specific_branches'],
            status='OPEN_ACTUAL_OBSERVATION_REQUIRED' if physical else 'CLOSED_EXPLICIT_FINITE_TEXT_RELATION',
            whole_publisher_image_or_physical_capability_claimed=False,
            evidence=[dict(sample_id=r['sample_id'],exported_row_sha256=rowsha(r)) for r in matches],
            semantic_basis='Exact task constraints read against all bound source fields; complete text annotation only.' if not physical else
              'Hypothetical/guard examples accepted; real measurement, assembly or learner observation remains absent.'))
    assert Counter(x['status'] for x in coverage)=={'CLOSED_EXPLICIT_FINITE_TEXT_RELATION':33,'OPEN_ACTUAL_OBSERVATION_REQUIRED':5}
    refs={}
    refs['accepted_cases.jsonl']=jlines('accepted_cases.jsonl',final)
    refs['accepted_chat.jsonl']=jlines('accepted_chat.jsonl',chats)
    refs['root_qa7.jsonl']=jlines('root_qa7.jsonl',qas)
    refs['source_export_hashes.jsonl']=jlines('source_export_hashes.jsonl',bindings)
    refs['numeric_overlap_exceptions.jsonl']=jlines('numeric_overlap_exceptions.jsonl',exceptions)
    write('root_numeric_checks.json',numeric)
    write('root_token_audit.json',dict(model=L.MODEL,revision=L.REVISION,CPU_only=True,
        no_model_weights=True,all_rows=256,max_sequence_tokens=max(t['sequence_tokens'] for t in tokens),
        truncated_rows=0,records=tokens))
    write('coverage_reconciliation.json',dict(parent_queue_sha256=sha(queue_path.read_bytes()),
        tasks=coverage,closed_finite_text_tasks=33,physical_tasks_open=5,
        asset_only_masters_still_separate=10,G3_source_locator_still_separate=1,new_core_cases=0))
    write('protected_exclusion_check.json',dict(exact_question_matches=0,
        numeric_overlap_rows=len(exceptions),numeric_overlap_policy_sha256=sha(policy.read_bytes()),
        protected_pins=protected_pins,concept_challenge_read=False,
        numeric_test_independence_claimed=False,no_answers_changed_for_gate=True))
    write('root_content_review.json',dict(status='PASS_BOUNDED_CONTENT_AND_EXPORT_PENDING_CLOUD_COLLISION_GATE',
        cases=64,derived_originals=53,new_finite_branches=11,chats=256,numeric_steps=len(numeric),
        linkage_errors=0,token_errors=0,metadata_repairs=root_changes,
        final_review_actor='Root actual full-field content review; no independent final peer approval claimed.',
        original_intake_preserved=True,full_archive_complete=False,training_started=False))
    write('cloud_collision_request.json',dict(ids=[r['sample_id'] for r in final],
        groups=[r['case_group_id'] for r in final],
        raw_problem_field_hashes=[rowsha(r['problem']) for r in final],
        question_keys=[L.question_key(c) for c in chats if c['mode']=='worked_solution'],
        signatures=sorted(set(s for r in final for s in r['canonical_signatures']))))
    names=['accepted_cases.jsonl','accepted_chat.jsonl','root_qa7.jsonl','source_export_hashes.jsonl',
        'numeric_overlap_exceptions.jsonl','root_numeric_checks.json','root_token_audit.json',
        'coverage_reconciliation.json','protected_exclusion_check.json','root_content_review.json',
        'cloud_collision_request.json','repair_validation_b1.json','peer_b1.json','review_b2_b4.json',
        'review_b5_b8.json','repair_validation_b5_b8.json']
    for name in names:
        if name not in refs:refs[name]=dict(bytes=(RUN/name).stat().st_size,sha256=sha((RUN/name).read_bytes()))
    manifest=dict(schema='MathVisionKid.DerivedG2RepairAppend.v1',entries=refs,
        cases=64,chats=256,new_core_cases=0,original_intake_drive_id='1Ji6l7rg-lpg81ddq3JG4gUeIDyOOGLYM',
        originals_audit_only=True,cloud_collision_gate_pending=True,
        original_sources=[dict(path=n,sha256=sha((RUN/n).read_bytes())) for n,_ in inputs],
        training_started=False,full_archive_ready=False,
        validator_sha256=sha(Path(__file__).read_bytes()),skills_applied=['google-drive:google-drive'])
    write('manifest.json',manifest)
    print(json.dumps(dict(cases=64,chats=256,numeric_steps=len(numeric),numeric_overlap_rows=len(exceptions),
        max_tokens=max(t['sequence_tokens'] for t in tokens),finite_text_tasks_closed=33,physical_open=5,
        cloud_collision_gate_pending=True,training_started=False)))

if __name__=='__main__':main()
