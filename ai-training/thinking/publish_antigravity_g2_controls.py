"""Prepare four existing-ID control updates; no remote writes from this script."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib,json,zipfile,sys
H=Path(__file__).resolve().parent
R=H/'cloud_publication/antigravity_intake_20261022'
sys.path.insert(0,str(H))
import math_data_full_audit_v3 as V
sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(name):return (R/name).read_bytes()
def load(name):return json.loads(raw(name))
def dump(name,v):
    (R/name).write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def main():
    before=load('parent_controls_raw_verified.json')
    old=load('../final_confirmation_20261022/four_controls_remote_verified.json')['controls']
    assert all(before[k]['sha256']==old[k]['sha256'] for k in old)
    s=load('parent_state.json');c=load('parent_chat.json');b=load('bundle_remote_verified.json')
    assert b['fresh_raw_readback_verified'] and b['all_bytes_equal']
    cov=load('coverage_reconciliation.json');collision=load('cloud_collision_check.json')
    assert s['accepted_cases']==1629858 and s['training_chat_rows']==6502088
    with zipfile.ZipFile(R/'parent_progress.zip') as z:
        parent_raw=z.read(s['latest_all_data_union_recipe']['member'])
        assert sha(parent_raw)==s['latest_all_data_union_recipe']['sha256']
    parent=json.loads(parent_raw);recipe=deepcopy(parent)
    assert not recipe['pending_discovery']
    ref=dict(bytes=b['bytes'],family='antigravity_g2_derived_repair_20261022',file_id=b['id'],
        file_name=b['file_name'],sha256=b['sha256'])
    m=load('manifest.json')
    for field,member,role,n in [('source_members','accepted_cases.jsonl','candidate_source',64),
                              ('chat_members','accepted_chat.jsonl','candidate_chat',256)]:
        mr=m['entries'][member]
        recipe[field].append(dict(ref,member=member,member_bytes=mr['bytes'],member_sha256=mr['sha256'],role=role,rows=n))
        assert recipe[field][:-1]==parent[field]
    assert b['sha256'] not in recipe['artifacts']
    recipe['artifacts'][b['sha256']]=dict(bytes=b['bytes'],file_ids=[b['id']],file_names=[b['file_name']],sha256=b['sha256'])
    recipe.update(append_only_parent_recipe_sha256=sha(parent_raw),declared_accepted_case_total=1629922,
        declared_candidate_chat_rows=6502344,raw_candidate_chat_rows_including_declared_current_splits=6502392,
        full_archive_audit_complete=False,training_started=False,actual_train_only_row_total_verified=False)
    recipe['append_only_g2_repair_proof']=dict(parent_identity=V.plan_identity(parent),
        source_prefix_unchanged=True,chat_prefix_unchanged=True,source_delta=64,chat_delta=256,
        original_intake_audit_only=True,checkpoint_migration_pending=True,
        live_checkpoint_recipe_must_remain_parent_until_worker_stopped=True)
    dump('publish_latest_union_recipe.json',recipe)
    recipe_ref=dict(progress_id=before['progress']['id'],member='antigravity_intake_20261022/publish_latest_union_recipe.json',
        sha256=sha(raw('publish_latest_union_recipe.json')),payload_references=38,source_members=219,chat_members=32,
        declared_candidate_chat_rows=6502344,current_pedagogy_eval_rows_separate=48,
        full_archive_audit_complete=False,actual_train_only_row_total_verified=False,
        historical_split_totals_pending_full_archive_audit=True)
    migration=dict(schema='MathVisionKid.PendingAppendOnlyAuditMigration.v1',
        checkpoint_id='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI',
        previous_identity=V.plan_identity(parent),next_identity=V.plan_identity(recipe),
        previous_recipe_sha256=sha(parent_raw),next_recipe=recipe_ref,
        original_cursors_and_issues_must_be_preserved=True,old_source_and_chat_prefixes_verified=True,
        next_action='After the current single worker stops, use FullArchiveAudit.extend_recipe on the same existing runtime database. Instantiate next recipe to index its new source before consuming new chat. Preserve all old cursor/member/source/sample/issue rows. Do not reset or create a second checkpoint.',
        transition_performed=False,training_started=False)
    dump('pending_checkpoint_append.json',migration)
    assert migration['previous_identity']=='06339a42b0a4b8d2c8ce7b1031a41a6ca1fc936dd361dd4055e17f8796f5b8e2'
    open_tasks=[x for x in cov['tasks'] if x['status'].startswith('OPEN')]
    remaining_constraints=sum(len(x['candidate_ids']) for x in open_tasks)
    current_queue=dict(parent_queue_sha256=cov['parent_queue_sha256'],
        accepted_bundle=b,accepted_cases=64,accepted_chat_rows=256,
        finite_text_tasks_closed=33,candidate_constraints_closed=50-remaining_constraints,
        physical_tasks_open=5,candidate_constraints_open=remaining_constraints,remaining_tasks=open_tasks,
        asset_only_masters_separate=10,G3_source_locator_separate=1,whole_curriculum_certified=False,
        status='BOUNDED_G2_APPEND_ACCEPTED_FULL_ARCHIVE_AND_ACTUAL_OBSERVATIONS_PENDING')
    dump('next_uncovered_tasks.json',current_queue)
    frozen=load('../hoai_live_resume_20261022/frozen_baseline_verified.json')
    for name,expected in frozen['sha256'].items():
        assert sha((H/'data/primary_math_teacher_20261016'/name).read_bytes())==expected,name
    frozen.update(verified_again_utc=datetime.now(timezone.utc).isoformat(),all_hashes_unchanged=True)
    dump('frozen_baseline_reverified.json',frozen)
    # Update counts once. Prior control bytes and all old ZIP members are retained.
    s['accepted_cases']+=64;s['new_cases']+=64;s['training_chat_rows']+=256
    s['all_available_chat_rows_including_evaluation_and_audit']+=256
    s.setdefault('all_data_union_recipe_history',[]).append(s['latest_all_data_union_recipe'])
    s['latest_all_data_union_recipe']=recipe_ref
    s['pending_checkpoint_append']=migration
    s['TRAINING_DATASET_READY']=False;s['training_started']=False
    s['status']='G2_REPAIR64_ACCEPTED_FULL_ARCHIVE_AUDIT_RUNNING_PENDING_APPEND_MIGRATION'
    s['next_action']='Continue existing CPU full audit; after worker stop apply pending_checkpoint_append on same V3 database/Drive ID without resetting any cursor. Do not train. Keep five actual-observation tasks, ten asset masters and one G3 locator open.'
    s['updated_utc']=datetime.now(timezone.utc).isoformat()
    s['latest_g2_finite_preparation_plan']=dict(progress_id=before['progress']['id'],
        member='antigravity_intake_20261022/next_uncovered_tasks.json',sha256=sha(raw('next_uncovered_tasks.json')),
        accepted_case_delta=64,finite_tasks_pending=5,candidate_constraints_pending=remaining_constraints,
        finite_text_tasks_closed=33,all_sgk_forms_covered=False)
    s['external_data_authoring_handoff'].update(external_results_received=True,
        original_intake_drive_id='1Ji6l7rg-lpg81ddq3JG4gUeIDyOOGLYM',
        original_53_rows_audit_only=True,accepted_repaired_and_new_rows=64,
        blanket_original_acceptance_claim_replaced_by_hash_bound_review=True)
    oldobs=s.get('latest_colab_runtime_observation',{})
    s.setdefault('data_only_colab_observation_history',[]).append(oldobs)
    obs=dict(oldobs,observed_utc=collision['observed_utc'],unique_chat_rows_committed=collision['committed_chat_rows'],
        worker_alive_at_observation=collision['worker_alive'],full_archive_audit_complete=False,
        current_issues=collision['current_issues'],evidence_member='antigravity_intake_20261022/cloud_collision_check.json',
        executing_recipe_identity=migration['previous_identity'],pending_next_recipe_identity=migration['next_identity'])
    s['latest_colab_runtime_observation']=obs
    s['latest_g2_derived_repair_bundle']=b
    c['chat_rows']+=256;c['all_available_chat_rows_including_evaluation_and_audit']+=256
    c.setdefault('supplement_bundles',[]).append(dict(run_id='antigravity_intake_20261022',bundle=b,
        acceptance='ACCEPTED_OWNER_PREAUTHORIZED',cases=64,chat_rows=256,source_member='accepted_cases.jsonl',
        chat_member='accepted_chat.jsonl',token_audit_member='root_token_audit.json',
        original53_audit_only=True,full_archive_audit_pending=True,human_manual_attestation_added=False,
        numeric_overlap_exact_hash_exceptions=14))
    c['pending_checkpoint_append']=migration;c['latest_all_data_union_recipe']=recipe_ref
    c['latest_finite_sgk_reconciliation']=s['latest_g2_finite_preparation_plan']
    c['latest_colab_runtime_observation']=obs;c['external_data_authoring_handoff']=s['external_data_authoring_handoff']
    context=raw('parent_context.md').decode('utf8')
    marker='### Nhật ký 22/10/2026 — hợp nhất 64 bài G2 dẫn xuất từ bàn giao Antigravity'
    assert marker not in context
    delta='\n\n'+marker+'\n'
    delta+='Giữ nguyên 8 ZIP gốc/53 bài/212 chat trong gói audit-only ID1Ji6l7rg-lpg81ddq3JG4gUeIDyOOGLYM; không đưa các bản lỗi gốc vào candidate. Ba agent chia kiểm/sửa; root hoàn tất actual full-field review và bản xuất cuối, không gọi finalreview là independent external hoặc human. Nhận 64 bài =53 dẫn xuất +11 nhánh hữu hạn mới; tái sinh đủ256 chat từ full đề/givens/request/student_work. 63 phép Fraction/Decimal, oracle và meaningful mutations theo lô, QA7 gắn cả source repair hash lẫn export hash; toàn256chat tokenizer pinned khôngtruncate, max1193token. Giữ đáp án hợp lệ; không đổi đáp án để qua gate.\n'
    delta+=f"Gói {b['url']} có{b['bytes']}byte SHA256{b['sha256']}, freshraw so toànbyte khớp. 14ngoại lệ chỉtrùng phép tính theo hash sauQA; exact protected questions bịloại, khôngđọc concept_challenge, khôngtuyênbố numeric benchmark độc lập. Query đủ1629842sourceversions khôngtrùngID hoặc exactproblemfieldhash; normalizedquestion toànkho còn theo fullaudit, khônggọi kiểmhiện tại là fullpass.\n"
    delta+=f"Đối chiếu actual38tasks/50constraints: đóng33task đềchữ/annotationđủ ({50-remaining_constraints}constraints), còn5task/{remaining_constraints}constraints cần bằngchứng đo/thực hành/quan sát thật;10assetmasters và1G3locator vẫnriêng. Không tựđóng bằngguard hoặc dữliệugiảđịnh.495core/165node giữ nguyên. Tổng acceptedcandidate1629922case/6502344chat;6502392rawchat theo currentrecipe gồm48eval; số historicalallincl6502456giữ phạmvilịch sử riêng. Đây khôngphải tổng train-only đãfullaudit.\n"
    delta+=f"Union mới38payload/219source/32chat; mọi prefix cũ giữ nguyên. Worker hiện chạy parentrecipe, chưa ép DBđangmở đổiidentity: {collision['committed_chat_rows']}chat committed tại{collision['observed_utc']}, issue regression_only cũ giữnguyên. pending_checkpoint_append.json ghi chínhxác migration cùngID sauworker dừng; khôngreset/khônglaunchworkertrùng. TRAINING_DATASET_READY=false; khôngtrain/GPU/weights/paidAPI/app/commit/push.299owner signoff và7baselinehash táikiểm giữ nguyên.\n"
    delta+='Bằngchứng/queue/recipe/code trong PROGRESS/antigravity_intake_20261022. Bốncontrol cùngIDs, STATEcuối; chỉxácnhận đồngbộ sau freshraw byte/hash. Skills applied: google-drive:google-drive.\n'
    dump('next_chat.json',c);dump('next_state.json',s)
    (R/'context_delta.txt').write_bytes(delta.encode('utf8'))
    (R/'next_context.md').write_bytes(raw('parent_context.md')+delta.encode('utf8'))
    assert raw('next_context.md').startswith(raw('parent_context.md'))
    evidence=['structural_intake.json','original_intake.json','original_intake_remote_verified.json',
        'bundle_remote_verified.json','bundle_local_receipt.json','manifest.json','root_content_review.json',
        'cloud_collision_check.json','pending_checkpoint_append.json','publish_latest_union_recipe.json',
        'next_uncovered_tasks.json','coverage_reconciliation.json','protected_exclusion_check.json',
        'root_numeric_checks.json','root_token_audit.json','root_qa7.jsonl','source_export_hashes.jsonl',
        'frozen_baseline_reverified.json','parent_controls_raw_verified.json','parent_state.json','parent_chat.json',
        'repaired_b1_cases.jsonl','repaired_b2_b4_cases.jsonl','repaired_b5_b8_cases.jsonl',
        'qa7_b1.jsonl','qa7_b2_b4.jsonl','repaired_b5_b8_qa7.jsonl','context_delta.txt',
        'repair_validation_b1.json','repair_validation_b2_b4.py','repair_validation_b5_b8.py',
        'review_b2_b4.json','review_b5_b8.json','peer_b1.json']
    with zipfile.ZipFile(R/'parent_progress.zip') as oldz,zipfile.ZipFile(R/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as nz:
        assert len(oldz.namelist())==len(set(oldz.namelist()))
        for info in oldz.infolist():nz.writestr(info,oldz.read(info.filename))
        for name in evidence:
            member='antigravity_intake_20261022/'+name;assert member not in oldz.namelist()
            nz.writestr(member,raw(name))
        for file in [Path(__file__),H/'validate_merge_antigravity_g2.py',H/'package_antigravity_g2_repair.py']:
            nz.writestr('antigravity_intake_20261022/'+file.name,file.read_bytes())
    with zipfile.ZipFile(R/'parent_progress.zip') as oldz,zipfile.ZipFile(R/'next_progress.zip') as nz:
        assert all(nz.read(n)==oldz.read(n) for n in oldz.namelist())
    files={k:dict(id=before[k]['id'],path=str(R/('next_'+k+ext)),bytes=len(raw('next_'+k+ext)),sha256=sha(raw('next_'+k+ext)))
        for k,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]}
    dump('prepared_control_updates.json',dict(controls=files,old_progress_members_preserved=True,
        state_must_be_written_last=True,training_started=False,TRAINING_DATASET_READY=False))
    print(json.dumps(dict(prepared=True,accepted_cases=s['accepted_cases'],candidate_chats=c['chat_rows'],
        physical_tasks_open=5,constraints_open=remaining_constraints,next_recipe_sha256=recipe_ref['sha256'],
        next_recipe_identity=migration['next_identity'],files=files)))
if __name__=='__main__':main()
