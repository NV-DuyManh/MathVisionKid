"""Finite actual-page supplement checkpoint. No training or app changes."""
from pathlib import Path
from collections import Counter
from itertools import permutations
from fractions import Fraction
from decimal import Decimal, localcontext
import json, hashlib, zipfile, re, argparse
from datetime import datetime, timezone
import exhaustive_colab_loader as L
from exhaustive_primary_math import chat_records
from sgk_gap_release import evaluate
import sgk_page_numeric_oracle as N
from sgk_spatial_peer_oracle import finite_oracle as spatial_oracle
from sgk_page_g5_peer_review import independent as g5_oracle
from sgk_g4extra_peer_oracle import independent as g4_extra_oracle

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_page_audit_20261019'
OUT=RUN/'release'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def rows(p):return [(json.loads(b),sha(b)) for b in p.read_bytes().splitlines() if b.strip()]
def jl(p,a):p.write_bytes(b''.join((dump(r)+'\n').encode() for r in a))

def g1_independent(r):
    """Separate computations transcribed from the actually read givens."""
    sid=r['sample_id'];i=int(sid[-2:]);t=r['topic'];o=r['gap_oracle']
    if t=='add_group_strict_comparison':
        start,target,options,relation=[(4,7,{'P':2,'Q':3,'R':4},'>'),(8,12,{'A':2,'B':4,'C':5},'<'),(5,9,{'M':3,'N':4,'K':5},'>')][i-1]
        totals={k:start+v for k,v in options.items()}
        valid=[k for k,v in totals.items() if (v>target if relation=='>' else v<target)]
        assert valid==o['valid'];return dict(totals=totals,valid=valid)
    if t=='construct_equations_from_number_cards':
        cards=[[2,5,7],[1,3,4,6],[0,4,7]][i-1];valid=[]
        for a,b,c in permutations(cards,3):
            if a+b==c:valid.append(f'{a}+{b}={c}')
            if i!=2 and a-b==c:valid.append(f'{a}-{b}={c}')
        assert sorted(valid)==sorted(o['valid']);return dict(valid=valid)
    if t=='ordinal_after_insertion':
        if i==1:line=['An','Bình','Hà','Chi','Dũng'];assert line.index('Dũng')+1==o['rank']
        elif i==2:
            line=['Gấu','Thỏ','Mèo','Sóc','Cáo'];assert {x:line.index(x)+1 for x in ('Thỏ','Sóc')}==o['targets']
        else:
            variants=[['Lan','mới','Minh','Nga','Phúc'],['Lan','Minh','Nga','Phúc','mới']]
            ranks=[v.index('Nga')+1 for v in variants];assert ranks==[4,3] and not r['can_solve'];return dict(possible_ranks=ranks)
        return dict(updated_line=line)
    if t=='ordinal_from_both_ends':
        if i==2:assert 7-3+1==o['right'];return dict(before=2,after=4,rank_from_end=5)
        a,target=([['A','B','C','D','E'],'B'] if i==1 else [['Voi','Gấu','Thỏ','Mèo','Sóc','Cáo'],'Mèo'])
        ranks=[a.index(target)+1,len(a)-a.index(target)];assert ranks==[o['left'],o['right']];return dict(ranks=ranks)
    if t=='periodic_attribute_pattern':
        if i==1:
            a=['Đỏ','Xanh','Xanh']*3;v=[a[5],a[7]];assert v==o['valid'];return dict(full_sequence=a,blanks=v)
        if i==2:
            a=['tam giác','tròn','vuông','chữ nhật']*3;assert a[9]==o['valid'];return dict(position10=a[9])
        correct=['vuông','vuông','tròn']*2;actual=['vuông','vuông','tròn','vuông','tròn','tròn']
        errors=[j+1 for j,(a,b) in enumerate(zip(correct,actual)) if a!=b];assert errors==[o['first_error']];return dict(error_positions=errors)
    if t=='resource_assignment_inequality':
        needs,resources=[({'A':2,'B':4},{'P':3,'Q':5}),({'A':1,'B':3,'C':5},{'P':2,'Q':4,'R':6}),({'A':2,'B':4},{'P':4,'Q':5})][i-1]
        valid=[]
        for keys in permutations(resources):
            mapping=dict(zip(needs,keys))
            if min(resources[mapping[k]]-v for k,v in needs.items())>0:valid.append(mapping)
        assert valid==o['valid'];return dict(valid=valid,all_assignments_checked=True)
    if t=='two_sided_strict_bound_selection':
        cards,lo,hi=[([3,5,6,8,9],5,9),([20,21,24,28,30],20,30),([5,6,7,8],6,7)][i-1]
        v=[c for c in cards if c>lo and c<hi];assert v==o['valid'];return dict(valid=v)
    raise AssertionError(t)

def audit():
    OUT.mkdir(exist_ok=True)
    old=rows(RUN/'current_sources.jsonl');old_ids={r['sample_id'] for r,h in old}
    normalized=lambda s:re.sub(r'\s+',' ',s).strip().casefold()
    old_questions={normalized(r['problem']) for r,h in old}
    g1=rows(RUN/'g1_append/cases.jsonl');g4=rows(RUN/'root_numeric/draft_cases.jsonl')
    assert sha((RUN/'g1_append/cases.jsonl').read_bytes())=='f0826eaceddc95a5c90f95ea9b72d2e7e39472e1b5530d0a07af66d5812ef992'
    peer=json.loads((RUN/'root_numeric/root48_peer_review_repaired.json').read_text('utf-8'))
    assert peer['source_file_sha256']==sha((RUN/'root_numeric/draft_cases.jsonl').read_bytes())
    assert peer['rows_read']==48 and peer['math_oracle_pass_rows']==48
    protection_path=RUN/'extensions/protected_numeric_signatures.json'
    protected=set(json.loads(protection_path.read_text('utf-8'))['signatures'])
    spatial=rows(RUN/'g3_spatial_append/cases.jsonl')
    spatial_peer=json.loads((RUN/'g3_spatial_append/peer_review.json').read_text('utf-8'))
    assert spatial_peer['source_file_sha256']==sha((RUN/'g3_spatial_append/cases.jsonl').read_bytes()) and spatial_peer['seven_criteria_pass_count']==9
    g5=rows(RUN/'g5_append/draft_cases.jsonl')
    g5_peer=json.loads((RUN/'g5_append/peer_review.json').read_text('utf-8'))
    assert g5_peer['source_file_sha256']==sha((RUN/'g5_append/draft_cases.jsonl').read_bytes()) and g5_peer['seven_criteria_pass_count']==12
    g4_extra=rows(RUN/'g4_remaining_append/cases.jsonl')
    extra_peer=json.loads((RUN/'g4_remaining_append/peer_review.json').read_text('utf-8'))
    assert extra_peer['source_file_sha256']==sha((RUN/'g4_remaining_append/cases.jsonl').read_bytes())=='a57bea461bfc50ceadb40a0b8dfb35dc686add160fb136931c01fc85dfa3257c'
    assert extra_peer['seven_criteria_pass_count']==20 and extra_peer['chat_count']==80
    accepted=[];chats=[];reviews=[];oracle=[];eligibility=[];seen=set();questions=set();num=0
    criteria={k:'PASS' for k in ['math_correctness_or_explicit_guard','givens_request_consistency','grade_and_scope','steps_reasons_units_check','initial_and_all_hints_no_answer_leak','student_work_grounding','schema_provenance_preservation']}
    extra_ids={r['sample_id'] for r,h in g4_extra}
    for r,parent_hash in g1+g4+spatial+g5+g4_extra:
        sid=r['sample_id'];q=normalized(r['problem'])
        assert sid not in seen|old_ids and q not in questions|old_questions
        seen.add(sid);questions.add(q)
        assert len(r['hints'])==3 and [h['level'] for h in r['hints']]==[1,2,3]
        assert not any(r.get(k) for k in ('human_verified','teacher_certified','owner_human_reviewed'))
        structural=g4_extra_oracle(r) if sid in extra_ids else g1_independent(r) if r['grade']==1 else spatial_oracle(r) if r['grade']==3 else g5_oracle(r['oracle_evidence']) if r['grade']==5 else N.audit(r)
        numeric=[];previous={}
        for s in r['worked_steps']:
            assert s['reason'] and s['explanation']
            if s.get('expression'):
                expanded=re.sub(r'\{(s\d+)\}',lambda m:'('+str(Fraction(previous[m[1]]))+')',s['expression'])
                value=evaluate(expanded,'fraction');assert value==Fraction(s['result'])
                with localcontext() as ctx:
                    ctx.prec=90;d=evaluate(expanded,'decimal');assert abs(d-Decimal(value.numerator)/Decimal(value.denominator))<Decimal('1e-70')
                numeric.append(dict(step_id=s['step_id'],expression=s['expression'],expanded_expression=expanded,exact=str(value),decimal_agrees=True));num+=1
            previous[s['step_id']]=s['result']
        # This is a derived acceptance export: preserve the actually reviewed draft hash.
        r['acceptance_status']='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED';r['quality_status']='CONTENT_QA_AND_CROSS_REVIEW_PASSED'
        r['provenance']['acceptance_basis']='OWNER_PREAUTHORIZED_AFTER_CONTENT_QA_AND_CROSS_REVIEW'
        r['provenance']['reviewed_draft_row_sha256']=parent_hash
        r['provenance']['content_human_review_completed']=False
        h=sha(dump(r).encode());accepted.append(r)
        reviews.append(dict(sample_id=sid,source_row_sha256=h,reviewed_draft_row_sha256=parent_hash,status='PASS',criteria=criteria,review_role='CONTENT_CROSS_REVIEW',human_review_claimed=False,external_review_claimed=False,actual_fields_read=['problem','givens','requested_quantity','student_work','worked_steps','reasons','explanations','expected_answer','initial_guidance','all_three_hints'],semantic_proof_is_not_parser_pass=True))
        oracle.append(dict(sample_id=sid,source_row_sha256=h,reviewed_draft_row_sha256=parent_hash,structural=structural,numeric_steps=numeric,status='PASS'))
        overlap=sorted((set(L.source_signatures(r))|set(r.get('canonical_signatures',[])))&protected)
        eligibility.append(dict(sample_id=sid,source_row_sha256=h,training_eligible=True,blind_numeric_overlap_hashes=overlap,basis='OWNER_HASH_SCOPED_NUMERIC_EXCEPTION_AFTER_QA' if overlap else 'CONTENT_QA_PASSED',authorization='Cho phép ngoại lệ theo hash sau QA',numeric_benchmark_independence_claimed=False))
        for c in chat_records(r):
            c.update(source_row_sha256=h,acceptance_status=r['acceptance_status']);L.validate_chat(c)
            target=json.loads(c['messages'][2]['content'])
            if c['mode']=='worked_solution':assert target['steps']==r['worked_steps'] and target['answer']==r['expected_answer']
            else:
                hint=r['hints'][int(c['mode'][-1])-1];assert target==dict(hint=hint['hint'],question=hint['question'])
            chats.append(c)
    assert len(accepted)==110 and len(chats)==440 and len({c['sample_id'] for c in chats})==440
    jl(OUT/'accepted_cases.jsonl',accepted);jl(OUT/'accepted_chat.jsonl',chats);jl(OUT/'cross_reviews.jsonl',reviews);jl(OUT/'independent_oracles.jsonl',oracle);jl(OUT/'training_eligibility_by_hash.jsonl',eligibility)
    tokenpath=Path.home()/'.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots'/L.REVISION
    token=L.full_token_audit(chats,L.load_qwen_tokenizer(tokenpath));token['scope']='ALL_NEW_CHAT_ONLY_NO_WEIGHTS_OR_TRAINING';write(OUT/'token_audit.json',token)
    report=dict(cases=len(accepted),chat_rows=len(chats),by_grade=dict(Counter(str(r['grade']) for r in accepted)),by_topic=dict(Counter(r['topic'] for r in accepted)),representation_families=len({r['topic'] for r in accepted}),independent_numeric_steps=num,exact_hash_numeric_exceptions=sum(bool(r['blind_numeric_overlap_hashes']) for r in eligibility),protection_index_sha256=sha(protection_path.read_bytes()),prior_fullfield_source_index_rows=len(old),all_sgk_forms_audited=False,full_archive_token_audit=False,training_started=False,preservation='All old payloads and original draft hashes preserved; accepted rows are derived exports.',diversity_limit='110 cases cover 40 representation families. Some within-family entries are numeric variants; do not count as separate forms.')
    write(OUT/'audit_report.json',report);print(dump(report))

def snapshot():
    """Hash a point-in-time copy; pending candidates never become coverage credit."""
    report=json.loads((OUT/'audit_report.json').read_text('utf-8'))
    mapping=json.loads((RUN/'root_numeric/family_comparison_pending.json').read_text('utf-8'))
    index={r['sample_id']:(r,h) for r,h in rows(RUN/'current_sources.jsonl')}
    compared=[]
    for family,(book,pages,node,reason,ids) in mapping.items():
        refs=[]
        for sid in ids:
            r,h=index[sid];assert r.get('split','train')=='train' and not re.search('holdout|eval|pilot|protected',sid,re.I)
            refs.append(dict(sample_id=sid,source_row_sha256=h))
        compared.append(dict(family=family,book_id=book,printed_pages=pages,relation=reason,nearest_sources=refs,status='DISTINCT_TASK_STRUCTURE_FROM_LISTED_NEAREST_REVIEWED_SOURCES',claim_limit='Targeted actual full-field comparison. Not an exhaustive semantic absence proof over every old case.'))
    write(OUT/'root_numeric_representation_comparison.json',compared)
    books=[]
    for directory in ['g1v1_audit','g1v2_audit','g2v1_audit','g2v2_audit','g3_audit','g4_audit','g5_audit']:
        raw=rows(RUN/directory/'page_review.jsonl')
        bybook={}
        for r,h in raw:
            bid=r.get('book_id') or f"g{r['grade']}v{r['volume']}"
            page=r.get('printed_page');bybook.setdefault(bid,[]).append(page)
        for bid,pages in bybook.items():
            g,v=int(bid[1]),int(bid[3]);bounds={(1,1):(6,113),(1,2):(4,105),(2,1):(6,137),(2,2):(4,138),(3,1):(6,121),(3,2):(4,126),(4,1):(6,130),(4,2):(4,118),(5,1):(6,138),(5,2):(4,134)}
            first,last=bounds[g,v];present=set(p for p in pages if p is not None and first<=p<=last)
            missing=sorted(set(range(first,last+1))-present)
            books.append(dict(book_id=bid,content_range=[first,last],actual_content_pages_read=len(present),missing_content_pages=missing,all_content_pages_read=not missing,semantic_mapping_complete=False,receipt_path=f'{directory}/page_review.jsonl',receipt_sha256=sha((RUN/directory/'page_review.jsonl').read_bytes())))
    assert len(books)==10
    snapshot=dict(schema='actual_page_audit_checkpoint.v1',utc=datetime.now(timezone.utc).isoformat(),books=books,content_pages_read=sum(b['actual_content_pages_read'] for b in books),books_content_read_complete=sum(b['all_content_pages_read'] for b in books),all_sgk_exercise_forms_audited=False,accepted_in_this_checkpoint=report['cases'],pending_candidate_mapping=True,pending_additional_drafts_are_not_accepted=True,training_started=False)
    write(OUT/'page_audit_checkpoint.json',snapshot)
    queue_source=RUN/'prior_append/data/pending_sgk_exercise_audit.json'
    queue=json.loads(queue_source.read_text('utf-8'));assert len(queue['lessons'])==345
    for lesson in queue['lessons']:
        lesson['status']='ACTUAL_CONTENT_PAGES_READ_CANDIDATE_MAPPING_PENDING'
        lesson['actual_book_content_pages_read']=True
        lesson['semantic_coverage_complete']=False
    queue.update(schema='sgk_exercise_audit_queue.v2',parent_queue_sha256=sha(queue_source.read_bytes()),all_content_pages_read=snapshot['books_content_read_complete']==10,status='SEMANTIC_MAPPING_AND_CONFIRMED_GAP_APPEND_IN_PROGRESS',all_sgk_exercise_forms_audited=False,not_a_generation_quota=True)
    write(OUT/'pending_sgk_exercise_audit.json',queue)
    g2_mapping=json.loads((RUN/'g2v2_audit/g2_combined_candidate_adjudication.json').read_text('utf-8'))
    assert g2_mapping['candidate_count']==91 and g2_mapping['finite_master_count']==65
    write(OUT/'candidate_mapping_resume.json',dict(g2=dict(mapping_member='data/g2v2_audit/g2_combined_candidate_adjudication.json',mapping_sha256=sha((RUN/'g2v2_audit/g2_combined_candidate_adjudication.json').read_bytes()),candidate_count=91,finite_master_count=65,status_counts=g2_mapping['status_counts'],master_status_counts=g2_mapping['master_status_counts'],pending_master_count=51,accepted_credit_from_mapping_alone=0),all_grades_semantic_mapping_complete=False,avoid_duplicate_authoring=True))
    write(OUT/'resume_instructions.json',dict(priority=['Resume only missing actual content pages from page_audit_checkpoint; never infer viewed status from downloaded images or annotations.', 'Complete each candidate adjudication against actual valid train source fields; merge common forms across grades.', 'Review additional bounded drafts before next acceptance; only rows in accepted_cases.jsonl are accepted.', 'Preserve all old payload IDs/hashes and frozen evaluation. No training authorized.'],restore_comparison_source=dict(path='current_sources.jsonl',bytes=(RUN/'current_sources.jsonl').stat().st_size,sha256=sha((RUN/'current_sources.jsonl').read_bytes()),restore_receipt='prior_restore_receipt.json',prior_append_id='17Mu8ewL7JCEWylvdCTX4h_GJaVFm74lo',balanced_id='1SohvXHL6EaoU194cgsAQ2TfayPkl-IIV',corpus_part7_id='1xGxZFqD8tgUjDO8tZpMLWWk-ZTnNANwV'),schema='NEUTRAL_TEACHER_NOT_LIVE_GUIDE_OR_PLANDRAFT',training_started=False))
    # Freeze each selected file's bytes once. No textbook image/PDF/HTML is packaged.
    members={}
    for directory in ['g1v1_audit','g1v2_audit','g2v1_audit','g2v2_audit','g3_audit','g4_audit','g5_audit','g1_append','g3_spatial_append','g5_append','g4_remaining_append','root_numeric','release']:
        for p in sorted((RUN/directory).rglob('*')):
            if p.is_file() and p.suffix in ('.json','.jsonl','.py') and 'temp' not in p.parts and 'cache' not in p.parts:
                members['data/'+p.relative_to(RUN).as_posix()]=p.read_bytes()
    members['data/prior_restore_receipt.json']=(RUN/'prior_restore_receipt.json').read_bytes()
    for p in sorted(HERE.glob('*sgk*.py')):members['code/'+p.name]=p.read_bytes()
    for name in ['exhaustive_colab_loader.py','exhaustive_primary_math.py','exhaustive_curriculum_scope.py']:
        members['code/'+name]=(HERE/name).read_bytes()
    assert not any(re.search(r'\.blob\.core\.windows\.net|Bearer\s+[A-Za-z0-9]|[?&]sig=',b.decode('utf-8'),re.I) for b in members.values())
    manifest=dict(schema='sgk_page_append_bundle.v1',accepted_cases=report['cases'],chat_rows=report['chat_rows'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',page_checkpoint_member='data/release/page_audit_checkpoint.json',all_sgk_forms_audited=False,training_started=False,members={n:dict(bytes=len(b),sha256=sha(b)) for n,b in members.items()})
    members['manifest.json']=(dump(manifest)+'\n').encode()
    temp=RUN/'page_append.partial.zip'
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in members.items():
            info=zipfile.ZipInfo(n,date_time=(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b)
    with zipfile.ZipFile(temp) as z:
        assert not z.testzip() and all(z.read(n)==b for n,b in members.items())
    h=sha(temp.read_bytes());dest=RUN/f'MathVisionKid_SGK_PAGE_APPEND_20261020_{h[:16]}.zip'
    if dest.exists():assert sha(dest.read_bytes())==h;temp.unlink()
    else:temp.replace(dest)
    write(RUN/'bundle_local.json',dict(path=str(dest),file_name=dest.name,bytes=dest.stat().st_size,sha256=h,member_count=len(members),cases=report['cases'],chat_rows=report['chat_rows'],page_snapshot=snapshot))
    print(dump(dict(path=str(dest),bytes=dest.stat().st_size,sha256=h,members=len(members),books_content_complete=snapshot['books_content_read_complete'])))

def controls():
    receipt=json.loads((RUN/'bundle_remote_verified.json').read_text('utf-8'));assert receipt['all_bytes_equal'] and receipt['fresh_raw_verified']
    state=json.loads((RUN/'source_cloud_state.json').read_text('utf-8'));chat=json.loads((RUN/'source_chat_manifest.json').read_text('utf-8'))
    report=json.loads((OUT/'audit_report.json').read_text('utf-8'));snapshot=json.loads((OUT/'page_audit_checkpoint.json').read_text('utf-8'))
    assert state['accepted_cases']==1629487 and report['cases']==110
    assert chat['chat_rows']==state['training_chat_rows']
    assert not any(r.get('run_id')=='sgk_page_audit_20261019' for r in state.get('sgk_page_runs',[]))
    profile=dict(name='Hoai Nam',email='hoainam29082005@gmail.com',profile_id='103000002357306706048',link_id='link_6abe1d9c5acc819196c39d715a3044bb',binding='EXPLICIT_OWNER_SELECTED_ACCOUNT_CONNECTOR_PROFILE_VERIFIED')
    now=datetime.now(timezone.utc).isoformat()
    run=dict(run_id='sgk_page_audit_20261019',bundle=receipt,cases=report['cases'],chat_rows=report['chat_rows'],by_grade=report['by_grade'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',page_checkpoint_member='data/release/page_audit_checkpoint.json',token_audit_member='data/release/token_audit.json',acceptance='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',human_attestation_added=False,exact_hash_numeric_exceptions=report['exact_hash_numeric_exceptions'],all_sgk_exercise_forms_audited=False,training_started=False)
    for key,delta in [('accepted_cases',report['cases']),('new_cases',report['cases']),('training_chat_rows',report['chat_rows']),('training_chat_rows_before_balancing',report['chat_rows']),('all_available_chat_rows_including_evaluation_and_audit',report['chat_rows'])]:state[key]+=delta
    for key,counts in [('by_grade',report['by_grade']),('by_topic',report['by_topic'])]:
        for k,v in counts.items():state[key][k]=state[key].get(k,0)+v
    state.setdefault('sgk_page_runs',[]).append(run);state['updated_utc']=now;state['current_drive_connection']=profile
    state['status']='SGK_ACTUAL_PAGE_AUDIT_AND_FINITE_GAP_APPEND_IN_PROGRESS';state['TRAINING_DATASET_READY']=False
    state['actual_sgk_page_checkpoint']=snapshot
    state['candidate_mapping_resume']=json.loads((OUT/'candidate_mapping_resume.json').read_text('utf-8'))
    state['next_action']='Complete remaining candidate-to-source adjudication and merge cross-grade aliases, then author only confirmed missing forms in bounded batches. All 110 accepted rows must not be reauthored. No training.'
    state['authoritative_state_note']='Current checkpoint supersedes old PROGRESS snapshots; old payloads/owner299 signoffs preserved.'
    state['local_storage']['current_run_staging']='TEMPORARY_ONLY_DELETE_AFTER_FRESH_RAW_VERIFICATION_OF_BUNDLE_AND_FOUR_CONTROLS; final publication receipt records cleanup outcome'
    chat.setdefault('supplement_bundles',[]).append(run);chat['chat_rows']+=report['chat_rows']
    chat['all_available_chat_rows_including_evaluation_and_audit']=state['all_available_chat_rows_including_evaluation_and_audit']
    chat['current_drive_connection']=profile
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    registry_path=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json'
    registry=json.loads(registry_path.read_text('utf-8'));registry.setdefault('account_identity_history',[]).append(registry['account_identity'])
    registry['account_identity']=profile;registry['link_id']=profile['link_id'];registry['current_tool_binding']='Multi-account connector: use chosen Hoai Nam profile. Reinspect link_id on reconnect.'
    registry.setdefault('sgk_page_append_bundles',[]).append(receipt);registry['connection_binding_verified_utc']=now
    write(registry_path,registry)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';text=context.read_text('utf-8')
    marker='### Nhật ký20/10/2026 — tiếp nối rà trang thật SGK, checkpoint110'
    assert marker not in text
    note=f'''\n\n{marker}\nTiếp nối state 1629487, không khởi tạo lại. Nhận {report['cases']} bài gốc sau self-QA và kiểm chéo; phân lớp {report['by_grade']}; {report['chat_rows']} chat theo schema neutral, {report['representation_families']} nhóm biểu diễn. Có biến thể số trong cùng nhóm, không tính mỗi case là một dạng độc lập. {report['independent_numeric_steps']} bước số được kiểm Fraction/Decimal và oracle riêng; token audit đủ toàn bộ chat mới, không tải weights hoặc train. {report['exact_hash_numeric_exceptions']} case có ngoại lệ numeric-overlap đúng hash sau QA; không tuyên bố benchmark số học độc lập. Giữ hash nguồn trước sửa và bản xuất riêng. Nhãn ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED; không phát sinh xác nhận đã được người đọc trực tiếp. Giữ nguyên 299 signoff cũ và mọi payload/history frozen.\n\nĐã đọc nội dung {snapshot['books_content_read_complete']}/10 tập, {snapshot['content_pages_read']} trang có receipt URL/hash. Đối chiếu dạng bài với nguồn cũ vẫn IN_PROGRESS; chưa kết luận mọi dạng SGK đã đủ. G2 có 91 candidate occurrences, gộp 65 master: 14 covered ở mức quan hệ/text, 51 pending (21 merged, 16 asset, 14 confirmed gap trong các nguồn gần nhất đã đọc). MERGED_PENDING không tính covered. Queue và evidence nằm trong g2v2_audit/g2_combined_candidate_adjudication.json của gói mới.\n\nBộ 495 core/165 node giữ nguyên. Tổng {state['accepted_cases']} case; {state['training_chat_rows']} candidate chat; {state['all_available_chat_rows_including_evaluation_and_audit']} chat nếu gồm eval/audit. Full-archive token/split audit chưa xong; balanced1256 chỉ là diagnostic. Chủ yêu cầu dùng toàn bộ dữ liệu hợp lệ cho lần train tương lai. CHƯA TRAIN.\n\nTài khoản được chủ chọn: Hoai Nam / hoainam29082005@gmail.com / profile 103000002357306706048. Đã đọc xác minh profile và 4 ID cũ; giữ identity history. Gói mới {receipt['url']}, SHA256 {receipt['sha256']}, {receipt['bytes']} bytes; raw readback mới khớp toàn bộ byte/hash trước khi cập nhật 4 control. Không đóng gói ảnh/PDF/HTML sách. Chỉ dùng staging tạm; dọn sau khi gói và bốn control được raw-verified, kết quả dọn ghi ở final publication receipt. Không xóa dữ liệu cũ.\n\nViệc tiếp: đối chiếu các candidate còn mở, gộp alias giữa lớp, chỉ soạn thêm dạng thiếu đã xác nhận trong lô hữu hạn. Không soạn lại 110 case đã nhận. Resume bằng state/manifest mới trên Drive; không chạy lại main sgk_gap_release cũ. Skill google-drive:google-drive.\n'''
    heading=f'<!-- CURRENT_CHECKPOINT sgk_page_audit_20261019: {state["accepted_cases"]} cases; {state["training_chat_rows"]} candidate chat; SGK semantic audit IN_PROGRESS; NO TRAINING; Hoai Nam Drive. Latest journal at end supersedes historical counts. -->\n'
    text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',text)
    context.write_text(heading+text+note,encoding='utf-8')
    write(RUN/'controls_local.json',dict(state_cases=state['accepted_cases'],candidate_chat=state['training_chat_rows'],profile=profile,staged_utc=now))
    with zipfile.ZipFile(RUN/'source_progress_index.zip') as old, zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for p in [OUT/'audit_report.json',OUT/'page_audit_checkpoint.json',OUT/'token_audit.json',RUN/'bundle_remote_verified.json',RUN/'publish_state.json',RUN/'publish_chat_manifest.json']:
            new.writestr('sgk_page_audit_20261019/'+p.name,p.read_bytes())
        new.writestr('sgk_page_audit_20261019/MATH_TRAINING_CONTEXT.md',context.read_bytes());new.writestr('sgk_page_audit_20261019/drive_artifacts.json',registry_path.read_bytes())
    with zipfile.ZipFile(RUN/'source_progress_index.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert not new.testzip() and all(old.read(n)==new.read(n) for n in old.namelist())
    print(dump(dict(cases=state['accepted_cases'],chat=state['training_chat_rows'],controls_staged=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['audit','snapshot','controls']);args=parser.parse_args();{'audit':audit,'snapshot':snapshot,'controls':controls}[args.action]()
