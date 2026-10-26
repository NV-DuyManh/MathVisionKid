"""Six reviewed finite G2 cases: local bounded release, never Drive or training.

Audit requires the root's exact-hash full-content review. Snapshot is immutable
and deterministic. Union requires a real full-raw remote verification receipt.
"""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import argparse, hashlib, json, re, zipfile
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from sgk_gap_release import evaluate
from sgk_remaining_union_recipe import verified_bundle
import math_data_candidate_stream as C

HERE=Path(__file__).resolve().parent
PUB=HERE/'cloud_publication'
RUN=PUB/'g2_finite_forms_20261021'
DRAFT=RUN/'numerals_cohort1/polished'
BASE=PUB/'sgk_final_gaps_20261021/publish_latest_union_recipe.json'
PLAN=PUB/'colab_data_audit_20261021/g2_planning/queue.json'
RESIDUAL=PUB/'sgk_final_gaps_20261021/reconciliation/next_uncovered_tasks.json'
BASE_SHA='93ec4110b9de95a84bb685ae60b1e4dc4b6df8c4fe568d88c60ca9c2e301c684'
FIELDS=['problem','givens','requested_quantity','student_work','worked_steps','expected_answer','initial_guidance','hints']
TASKS=['g2_pending_01_numerals_distinct_all','g2_pending_02_numerals_repeated_zero','g2_pending_03_numerals_bounded_three_digit']
CANIDS={'g2v1:g2_card_numeral_formation','g2v1:multiset_numeral_generation','g2v2:digit_card_permutations_zero','g2v2:digit_card_extrema'}

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def read(p):return json.loads(p.read_text('utf8'))
def rows(p):return [(json.loads(b),sha(b)) for b in p.read_bytes().splitlines() if b.strip()]
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8',newline='\n')
def jl(p,rs):p.write_text(''.join(dump(x)+'\n' for x in rs),encoding='utf8',newline='\n')

def validate_root(root,casebytes,chatbytes,source):
    if root.get('status')!='PASS' or root.get('actual_content_read') is not True:
        raise ValueError('Root actual full-content PASS review required')
    if root.get('cases_sha256')!=sha(casebytes) or root.get('chat_sha256')!=sha(chatbytes):
        raise ValueError('Root case/chat byte hash does not match reviewed draft')
    reviews=root.get('reviews',[])
    if len(reviews)!=6 or len({x['sample_id'] for x in reviews})!=6:
        raise ValueError('Six individual root reviews required')
    byid={x['sample_id']:x for x in reviews}
    for row,h in source:
        review=byid[row['sample_id']]
        if review.get('source_row_sha256')!=h:
            raise ValueError('Root per-source raw row hash mismatch')
        if review.get('actual_fields')!={k:row[k] for k in FIELDS}:
            raise ValueError('Root actual reviewed fields differ')
        if len(review.get('criteria',[]))!=7 or not all(c.get('passed') is True for c in review['criteria']):
            raise ValueError('Root individual QA7 PASS required')
    return byid

def audit():
    source=rows(DRAFT/'cases.jsonl')
    if len(source)!=6:raise ValueError('Exactly six finite reviewed cases required')
    root=read(RUN/'root_content_review.json')
    root_reviews=validate_root(root,(DRAFT/'cases.jsonl').read_bytes(),(DRAFT/'chat.jsonl').read_bytes(),source)
    peer=read(RUN/'numerals_cohort1/peer_review.json')
    if peer.get('derived_cases_sha256')!=sha((DRAFT/'cases.jsonl').read_bytes()) or peer.get('derived_chat_sha256')!=sha((DRAFT/'chat.jsonl').read_bytes()):
        raise ValueError('Independent peer receipt does not bind exact current draft')
    peerqa={x['sample_id']:x for x,h in rows(DRAFT/'peer_qa7.jsonl')}
    protected=read(PUB/'sgk_page_audit_20261019/extensions/protected_numeric_signatures.json')
    protected_set=set(protected['signatures'])
    priorpaths=[PUB/'sgk_page_audit_20261019/current_sources.jsonl',PUB/'sgk_page_audit_20261019/release/accepted_cases.jsonl']
    priorpaths += [PUB/x/'release/accepted_cases.jsonl' for x in ['sgk_finish_20261020','sgk_remaining_20261020','sgk_final_forms_20261020','sgk_completion_20261021','sgk_final_gaps_20261021']]
    priorpins={str(p.relative_to(PUB)):sha(p.read_bytes()) for p in priorpaths}
    norm=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
    prior=[r for p in priorpaths for r,h in rows(p)]
    ids={r['sample_id'] for r in prior};questions={norm(r['problem']) for r in prior}
    accepted=[];chat=[];cross=[];checks=[];eligibility=[]
    for draft,h in source:
        sid=draft['sample_id'];review=root_reviews[sid];pq=peerqa[sid]
        if pq['source_row_sha256']!=h or set(pq['criteria'].values())!={'PASS'} or len(pq['criteria'])!=7:
            raise ValueError('Independent peer QA7 does not bind current draft')
        if sid in ids or norm(draft['problem']) in questions:raise ValueError('Duplicate exact ID/question in bounded accepted reference set')
        ids.add(sid);questions.add(norm(draft['problem']))
        assert draft['grade']==2 and draft['split']=='train' and draft['can_solve'] is True
        assert not any(draft.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        assert [x['level'] for x in draft['hints']]==[1,2,3]
        assert draft['coverage']['planning_task_id'] in TASKS
        numeric=[]
        for s in draft['worked_steps']:
            assert s['reason'] and s['explanation'] and 'unit' in s
            if s.get('expression'):
                f=evaluate(s['expression'],'fraction');assert f==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=evaluate(s['expression'],'decimal');assert d==Decimal(f.numerator)/Decimal(f.denominator)
                numeric.append(dict(step_id=s['step_id'],expression=s['expression'],exact=str(f),decimal=str(d)))
        r=deepcopy(draft)
        r['acceptance_status']='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'
        r['quality_status']='CONTENT_QA_AND_CROSS_REVIEW_PASSED'
        r['provenance'].update(acceptance_basis='OWNER_PREAUTHORIZED_AFTER_FULL_CONTENT_QA_AND_CROSS_REVIEW',reviewed_draft_row_sha256=h,human_content_review_completed=False)
        exporth=sha(dump(r).encode('utf8'));accepted.append(r)
        cross.append(dict(sample_id=sid,reviewed_draft_row_sha256=h,exported_row_sha256=exporth,criteria=review['criteria'],actual_fields_read=FIELDS,semantic_decision=review['semantic_decision'],human_review_claimed=False))
        checks.append(dict(sample_id=sid,source_row_sha256=exporth,reviewed_draft_row_sha256=h,numeric=numeric,peer_oracle=pq['independent_computation'],peer_qa7_sha256=sha((DRAFT/'peer_qa7.jsonl').read_bytes())))
        overlap=sorted(set(L.source_signatures(r))&protected_set)
        eligibility.append(dict(sample_id=sid,source_row_sha256=exporth,exported_row_sha256=exporth,reviewed_draft_row_sha256=h,training_eligible=True,
            basis='OWNER_HASH_SCOPED_NUMERIC_EXCEPTION_AFTER_QA' if overlap else 'CONTENT_QA_AND_CROSS_REVIEW',
            blind_numeric_overlap_hashes=overlap,numeric_benchmark_independence_claimed=False,scope='Only exact exported row hash; does not authorize copying or editing protected benchmarks.'))
        for c in chat_records(r):
            c.update(source_row_sha256=exporth,acceptance_status=r['acceptance_status'],quality_status=r['quality_status'])
            L.validate_chat(c);chat.append(c)
    assert len(accepted)==6 and len(chat)==24 and len({x['sample_id'] for x in chat})==24
    out=RUN/'release';out.mkdir(exist_ok=True)
    for n,data in [('accepted_cases',accepted),('accepted_chat',chat),('cross_reviews',cross),('independent_oracles',checks),('training_eligibility_by_hash',eligibility)]:jl(out/(n+'.jsonl'),data)
    tokenizer=Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION
    tokens=L.full_token_audit(chat,L.load_qwen_tokenizer(tokenizer))
    tokens['scope']='ALL_24_G2_APPEND_CHAT_CPU_TOKENIZER_ONLY_NO_TRAINING';write(out/'token_audit.json',tokens)
    assert all(sha((PUB/name).read_bytes())==h for name,h in priorpins.items())
    report=dict(schema='MathVisionKid.G2FiniteAppend.ReleaseAudit.v1',cases=6,chat_rows=24,by_grade={'2':6},numeric_steps=sum(len(x['numeric']) for x in checks),
        hash_numeric_exception_cases=sum(bool(x['blind_numeric_overlap_hashes']) for x in eligibility),root_review_sha256=sha((RUN/'root_content_review.json').read_bytes()),
        peer_review_sha256=sha((RUN/'numerals_cohort1/peer_review.json').read_bytes()),
        accepted_cases_sha256=sha((out/'accepted_cases.jsonl').read_bytes()),accepted_chat_sha256=sha((out/'accepted_chat.jsonl').read_bytes()),
        actual_tokenizer_all24=True,core_unchanged=495,nodes_unchanged=165,
        human_signoff_snapshot_extended=False,old_source_file_pins_unchanged=priorpins,whole_archive_duplicate_absence_claimed=False,
        full_archive_audit_complete=False,all_sgk_forms_covered=False,training_started=False,drive_mutated=False,global_state_mutated=False)
    write(out/'audit_report.json',report);print(dump(report))

def reconcile():
    plan=read(PLAN);queue=read(RESIDUAL)
    source=rows(RUN/'release/accepted_cases.jsonl');reviews={x['sample_id']:x for x,h in rows(RUN/'release/cross_reviews.jsonl')}
    if len(source)!=6 or len(plan['tasks'])!=41 or len(queue['external_g2_remaining_separate'])!=54:raise ValueError('Parent/current finite task counts differ')
    tasks={x['task_id']:x for x in plan['tasks']}
    bound=[]
    for r,h in source:
        v=reviews[r['sample_id']];dh=r['provenance']['reviewed_draft_row_sha256']
        assert v['exported_row_sha256']==h and v['reviewed_draft_row_sha256']==dh
        assert r['acceptance_status']=='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED'
        assert not any(r.get(k) for k in ['human_verified','teacher_certified','owner_human_reviewed'])
        t=tasks[r['coverage']['planning_task_id']]
        assert r['coverage']['candidate_ids']==t['candidate_ids']
        bound.append(dict(sample_id=r['sample_id'],task_id=t['task_id'],candidate_ids=t['candidate_ids'],grade=2,branch=r['topic'],exported_row_sha256=h,reviewed_draft_row_sha256=dh,actual_math_fields={k:r[k] for k in FIELDS},publisher_image_recognition_or_physical_success_certified=False))
    assert {x['task_id'] for x in bound}==set(TASKS)
    assert {c for x in bound for c in x['candidate_ids']}==CANIDS
    decisions=[]
    for tid in TASKS:
        bs=[x for x in bound if x['task_id']==tid];assert len(bs)==2
        decisions.append(dict(task_id=tid,status='EXACT_FINITE_TEXT_BRANCH_DEMONSTRATED',accepted_examples=bs,
            candidate_ids=tasks[tid]['candidate_ids'],parent_constraints=tasks[tid]['minimal_required_specific_branches'],
            whole_curriculum_or_image_physical_master_closed=False,publisher_receipts_inherited_not_newly_viewed=True))
    pending=[deepcopy(x) for x in plan['tasks'] if x['task_id'] not in TASKS]
    residual=[deepcopy(x) for x in queue['external_g2_remaining_separate'] if x['candidate_id'] not in CANIDS]
    assert len(pending)==38 and len(residual)==50
    out=RUN/'reconciliation';out.mkdir(exist_ok=True)
    write(out/'accepted_hash_adjudication.json',dict(schema='MathVisionKid.G2FiniteAppend.AcceptedHashAdjudication.v1',
        parent_plan_sha256=sha(PLAN.read_bytes()),parent_residual_queue_sha256=sha(RESIDUAL.read_bytes()),accepted_cases=6,chat_rows=24,task_decisions=decisions,
        tasks_demonstrated=3,candidate_text_branches_demonstrated=4,core_unchanged=495,training_started=False))
    nq=deepcopy(queue);nq['schema']='MathVisionKid.G2FiniteAppend.NextUncoveredTasks.v1'
    nq['parent_residual_queue_sha256']=sha(RESIDUAL.read_bytes());nq['parent_g2_plan_sha256']=sha(PLAN.read_bytes())
    nq['external_g2_remaining_separate']=residual;nq['g2_accepted_task_decisions']=decisions;nq['g2_pending_specific_tasks']=pending
    nq['counts']['external_g2_remaining_separate']=50
    nq['counts'].update(g2_specific_tasks_pending=38,g2_new_finite_tasks_demonstrated=3,g2_new_candidate_text_branches_demonstrated=4,new_accepted_cases=6,new_accepted_chat_rows=24)
    nq['parent_authoring_priority_guidance']=queue['authoring_priority_guidance']
    nq['authoring_priority_guidance']=f'Do not reauthor the two global locator-only tasks. Address the remaining {len(pending)} specific G2 tasks covering {len(residual)} candidate constraints with actual grade2 forms, retaining explicit asset and physical limits. Shared masters, publisher-image recognition and actual measurements are not certified by accepted text models.'
    nq['scope']='Accepted exact-hash finite text branches only; original source/page receipts, all global locator tasks and10asset-only masters retained. No physical or arbitrary image coverage inferred.'
    assert nq['global_master_tasks']==queue['global_master_tasks'] and nq['unresolved_asset_only_masters']==queue['unresolved_asset_only_masters']
    write(out/'next_uncovered_tasks.json',nq)
    write(out/'validation.json',dict(status='PASS_ACCEPTED_HASH_BINDINGS_ONLY',accepted_cases=6,chat_rows=24,remaining_g2_candidates=50,remaining_specific_tasks=38,
        original41_task_plan_preserved_sha256=sha(PLAN.read_bytes()),parent54_residual_queue_preserved_sha256=sha(RESIDUAL.read_bytes()),
        source_locator_tasks_unchanged=2,asset_only_masters_unchanged=10,whole_master_closed=False,training_started=False))
    print(dump(read(out/'validation.json')))

def snapshot():
    audit=read(RUN/'release/audit_report.json');recon=read(RUN/'reconciliation/validation.json')
    validation=read(RUN/'release/helper_validation.json')
    assert validation['status']=='PASS' and validation['tests_passed']==8
    assert validation['code_sha256']==sha(Path(__file__).read_bytes())
    assert validation['test_sha256']==sha((HERE/'test_g2_finite_forms_release.py').read_bytes())
    assert audit['cases']==6 and audit['chat_rows']==24 and recon['status']=='PASS_ACCEPTED_HASH_BINDINGS_ONLY'
    assert audit['root_review_sha256']==sha((RUN/'root_content_review.json').read_bytes())
    assert audit['accepted_cases_sha256']==sha((RUN/'release/accepted_cases.jsonl').read_bytes())
    assert audit['accepted_chat_sha256']==sha((RUN/'release/accepted_chat.jsonl').read_bytes())
    members={}
    for p in sorted(RUN.rglob('*')):
        rel=p.relative_to(RUN).as_posix()
        if p.is_file() and p.suffix in ('.json','.jsonl','.py','.txt') and not p.name.startswith(('bundle_','publish_','prewrite_')) and p.name!='union_scope.json':
            members['data/'+rel]=p.read_bytes()
    code=['g2_finite_forms_release.py','g2_numerals_cohort1_author.py','review_g2_cohort1_peer.py','g2_numerals_root_review_20261022.py',
          'exhaustive_colab_loader.py','math_data_portable_resume.py','math_data_archive_audit.py','math_data_candidate_stream.py',
          'math_data_drive_bootstrap.py','exhaustive_primary_math.py','exhaustive_curriculum_scope.py','sgk_gap_release.py','sgk_remaining_union_recipe.py']
    if (HERE/'test_g2_finite_forms_release.py').exists():code.append('test_g2_finite_forms_release.py')
    for name in code:members['code/'+name]=(HERE/name).read_bytes()
    forbidden=re.compile(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9]|[?&]sig=',re.I)
    if any(forbidden.search(b.decode('utf8',errors='ignore')) for b in members.values()):raise ValueError('Potential private bearer/download URL in bounded release')
    manifest=dict(schema='MathVisionKid.G2FiniteAppend.Bundle.v1',accepted_cases=6,chat_rows=24,
        source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',
        member_roles={name:('candidate_source' if name=='data/release/accepted_cases.jsonl' else 'candidate_chat' if name=='data/release/accepted_chat.jsonl' else 'CODE_ONLY' if name.startswith('code/') else 'AUDIT_HISTORY_NOT_ADDITIONAL_CANDIDATE') for name in members},
        core_cases_unchanged=495,training_started=False,full_archive_audit_complete=False,all_sgk_forms_covered=False,
        members={n:dict(bytes=len(b),sha256=sha(b)) for n,b in members.items()})
    members['manifest.json']=(dump(manifest)+'\n').encode('utf8')
    temp=RUN/'g2_append.partial.zip'
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(members):
            info=zipfile.ZipInfo(name,(2026,10,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,members[name])
    with zipfile.ZipFile(temp) as z:
        assert not z.testzip() and all(z.read(n)==b for n,b in members.items())
        assert len(z.namelist())==len(set(z.namelist()))
    h=sha(temp.read_bytes());target=RUN/f'MathVisionKid_G2_FINITE_FORMS_APPEND_20261021_{h[:16]}.zip'
    if target.exists():
        assert target.read_bytes()==temp.read_bytes();temp.unlink()
    else:temp.replace(target)
    write(RUN/'bundle_local.json',dict(path=str(target),file_name=target.name,bytes=target.stat().st_size,sha256=h,member_count=len(members),cases=6,chat_rows=24))
    print(dump(read(RUN/'bundle_local.json')))

def compile_append_only_union(base,ref,manifest,evidence):
    if len(base.get('artifacts',{}))!=36 or len(base.get('source_members',[]))!=217 or len(base.get('chat_members',[]))!=30 or base.get('pending_discovery'):
        raise ValueError('Exact complete36/217/30 parent recipe required')
    if base.get('declared_candidate_chat_rows')!=6502064 or base.get('raw_candidate_chat_rows_including_declared_current_splits')!=6502112:
        raise ValueError('Parent row counts differ')
    new=C.build_recipe([],[ref],{ref['bundle']['sha256']:manifest})
    if new['pending_discovery'] or len(new['source_members'])!=1 or len(new['chat_members'])!=1 or len(new['artifacts'])!=1:
        raise ValueError('Exactly one verified6/24 append required')
    if ref.get('cases')!=6 or ref.get('chat_rows')!=24:raise ValueError('Finite append count differs')
    key=ref['bundle']['sha256']
    if key in base['artifacts']:raise ValueError('Append payload already present; do not duplicate')
    fid=ref['bundle']['file_id']
    if any(fid in x.get('file_ids',[]) for x in base['artifacts'].values()):raise ValueError('New payload reuses existing immutable artifact ID')
    for kind in ('source_members','chat_members'):
        oldhash={x.get('member_sha256') or x['sha256'] for x in base[kind]}
        if any((x.get('member_sha256') or x['sha256']) in oldhash for x in new[kind]):raise ValueError('Append source/chat member bytes already referenced')
    result=deepcopy(base);result['artifacts'][key]=new['artifacts'][key]
    result['source_members']+=new['source_members'];result['chat_members']+=new['chat_members']
    result['declared_candidate_chat_rows']=6502088
    result['raw_candidate_chat_rows_including_declared_current_splits']=6502136
    result['current_pedagogy_validation_test_rows_separate']=48
    result['declared_accepted_case_total']=1629858
    result['training_started']=False;result['full_archive_audit_complete']=False
    result['actual_train_only_row_total_verified']=False
    result['append_only_parent_recipe_sha256']=BASE_SHA
    result['append_only_g2_proof']=dict(descriptor=ref,evidence=evidence,old_source_chat_prefixes_exact=True,
        parent_member_counts=dict(artifacts=36,source_members=217,chat_members=30),old31_historical_pins_not_fresh_raw_verified_here=True)
    assert result['source_members'][:217]==base['source_members'] and result['chat_members'][:30]==base['chat_members']
    assert all(result['artifacts'][k]==v for k,v in base['artifacts'].items())
    assert result['excluded_members']==base['excluded_members'] and len(result['artifacts'])==37
    assert len(result['source_members'])==218 and len(result['chat_members'])==31
    return result

def union():
    if sha(BASE.read_bytes())!=BASE_SHA:raise ValueError('Pinned parent RUN7 recipe changed')
    ref,manifest,evidence=verified_bundle(RUN,6,24)
    recipe=compile_append_only_union(read(BASE),ref,manifest,evidence)
    dest=RUN/'publish_latest_union_recipe.json';write(dest,recipe)
    scope=dict(schema='MathVisionKid.G2FiniteAppend.AppendOnlyUnionScope.v1',recipe_sha256=sha(dest.read_bytes()),recipe_bytes=dest.stat().st_size,
        artifacts=37,source_members=218,chat_members=31,total_candidate_members=249,declared_candidate_chat_rows=6502088,declared_raw_chat_rows=6502136,
        current_pedagogy_eval_separate=48,declared_accepted_cases=1629858,new_accepted_cases_verified=6,new_chat_rows_verified=24,
        source_chat_prefixes_exact=True,parent_recipe_sha256=BASE_SHA,old31_historical_pins_not_fresh_raw_verified_here=True,new_append_proof=evidence,
        full_archive_audit_complete=False,actual_train_only_row_total_verified=False,training_started=False,drive_mutated=False,global_state_mutated=False)
    write(RUN/'union_scope.json',scope);print(dump(scope))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['audit','reconcile','snapshot','union'])
    globals()[parser.parse_args().action]()
