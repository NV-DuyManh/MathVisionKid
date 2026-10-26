"""Stage accepted71 plus exact residual queue on four existing Drive IDs."""
from datetime import datetime,timezone
import json,re,zipfile
from sgk_final_gaps_release import HERE,RUN,read,write,sha
def main():
    bundle=read(RUN/'bundle_remote_verified.json');assert bundle['fresh_raw_verified'] and bundle['all_bytes_equal']
    proof=read(RUN/'root_evidence/prewrite_verified.json')
    for n,v in zip(['prewrite_progress.zip','prewrite_chat.json','prewrite_state.json','prewrite_context.md'],proof['controls']):assert sha((RUN/n).read_bytes())==v['sha256']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json');report=read(RUN/'release/audit_report.json')
    assert state['accepted_cases']==1629781 and state['training_chat_rows']==6501780 and chat['chat_rows']==6501780
    assert not any(x['run_id']==RUN.name for x in state.get('sgk_finish_runs',[]))
    profile=read(RUN/'root_evidence/connector_profile.json');now=datetime.now(timezone.utc).isoformat()
    ref=dict(run_id=RUN.name,bundle=bundle,cases=71,chat_rows=284,by_grade=report['by_grade'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',token_audit_member='data/release/token_audit.json',acceptance_status='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',new_human_attestation=False,training_started=False)
    for k,d in [('accepted_cases',71),('new_cases',71),('training_chat_rows',284),('training_chat_rows_before_balancing',284),('all_available_chat_rows_including_evaluation_and_audit',284)]:state[k]+=d
    assert state['all_available_chat_rows_including_evaluation_and_audit']==6502176
    for k in ['by_grade','by_topic']:
        for label,n in report[k].items():state[k][label]=state[k].get(label,0)+n
    state.setdefault('sgk_finish_runs',[]).append(ref)
    state.update(updated_utc=now,current_drive_connection=profile,TRAINING_DATASET_READY=False,status='FINITE_SGK_FORMS_AND_ARCHIVE_DATA_PREPARATION_IN_PROGRESS')
    recipe=RUN/'publish_latest_union_recipe.json';assert recipe.exists()
    state.setdefault('all_data_union_recipe_history',[]).append(state['latest_all_data_union_recipe'])
    state['latest_all_data_union_recipe']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/publish_latest_union_recipe.json',sha256=sha(recipe.read_bytes()),payload_references=36,chat_members=30,declared_candidate_chat_rows=6502064,current_pedagogy_eval_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False,full_archive_audit_complete=False)
    q=RUN/'reconciliation/next_uncovered_tasks.json';assert q.exists()
    nq=read(q)
    state.setdefault('sgk_accepted_reconciliation_history',[]).append(state['latest_sgk_accepted_reconciliation'])
    state['latest_sgk_accepted_reconciliation']=dict(bundle_id=bundle['id'],member='data/reconciliation/next_uncovered_tasks.json',sha256=sha(q.read_bytes()),bound_run=RUN.name,accepted_cases_bound=71,counts=nq['counts'],all_sgk_forms_covered=False,text_math_models_authored_for_all30=True)
    state['latest_full_archive_audit_code']=dict(bundle_id=bundle['id'],member='code/math_data_full_audit.py',sha256=sha((HERE/'math_data_full_audit.py').read_bytes()),status='10_CPU_TOKENIZER_FIXTURE_TESTS_PASS_CLOUD_WHOLE_CORPUS_RUN_PENDING',all_source_members_before_chat=True,explicit_splits=True,read_time_raw_hash_derivation_only_if_unique_full_link=True,no_truncation=True,checkpoint_independent_of_google_account=True)
    state['latest_colab_runtime_observation']=dict(notebook_id='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l',date='2026-10-21',runtime='CPU_PYTHON3',drive_auth='SUCCEEDED_VISIBLE_CELL3_OUTPUT',candidate_chunk='CELL4_DATA_ONLY_RUNNING_LAST_OBSERVED_COMPLETION_UNVERIFIED',checkpoint_save_cell_executed=False,browser_control='DISABLED_BY_WORK_SETTING_LAST_TOOL_RESPONSE',training_started=False,warning='Published notebook-byte hash describes previous immutable publication; live autosave after execution has not been freshly readback here.')
    state['next_action']='Resume data-only CPU whole-archive source/hash/chat-link/token/split/group audit on Colab when browser access returns; verify/save any prior chunk checkpoint first, then append-only recipe migration, not restart/reset. Reconcile remaining exact source anchors,54 G2 grade/representation branches and10 asset-only tasks from latest queue; no number-only core rewrite, no training.'
    chat.setdefault('supplement_bundles',[]).append(ref);chat['chat_rows']+=284
    chat['all_available_chat_rows_including_evaluation_and_audit']=state['all_available_chat_rows_including_evaluation_and_audit']
    chat['current_drive_connection']=profile;chat['latest_finite_sgk_reconciliation']=state['latest_sgk_accepted_reconciliation']
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    regpath=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';reg=read(regpath)
    oldidentity=reg['account_identity']
    if oldidentity.get('profile_id')!=profile['profile_id']:reg.setdefault('account_identity_history',[]).append(oldidentity)
    reg.update(account_identity=profile,link_id=profile['link_id'],connection_binding_verified_utc=now)
    assert not any(b['sha256']==bundle['sha256'] for b in reg.get('sgk_final_gaps_append_bundles',[]))
    reg.setdefault('sgk_final_gaps_append_bundles',[]).append(bundle);write(regpath,reg)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';prior=context.read_bytes();assert prior==(RUN/'prewrite_context.md').read_bytes()
    text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',prior.decode('utf-8'));marker='### Nhật ký21/10/2026 — sgk_final_gaps_20261021 accepted71'
    assert marker not in text
    header=f'<!-- CURRENT_CHECKPOINT {RUN.name}:1629852cases;6502064candidatechat;495core/165nodes;NO TRAIN;whole archive audit pending. Latest journal supersedes historical counts. -->\n'
    note=f'''
\n{marker}
Theo yêu cầu tiếp tục chuẩn bị dữ liệu: nhận71bài/284chat cho30master còn thiếu với12bài lớp1,1lớp2,14lớp3,22lớp4,22lớp5. Root đọc actual problem/givens/request/studentwork/all steps/reasons/explanations/answers/initial/all3hints, QA7 gắn source rowhash; ba peer mới độc lập kiểm24+24+23bài. Tổng71oracle khácphươngpháp,71wrong-model mutations,59Fraction/Decimal steps; toàn284chat tokenizer pinned CPU đạt không cắt ngắn. Numeric overlap chỉ ngoại lệ đúnghash sauQA: {report['hash_numeric_exception_cases']}case, không tuyên bố benchmark độc lập. Không thay đáp số để qua gate.
\nHai nguồn tangram cha có inventory không chuẩn đã giữ nguyên audit; chỉ bản corrected có đúng2tamgiác lớn,1vừa,2nhỏ,1vuông,1bìnhhành mới vào accepted. DerivedG1 đổi hai cách nói180độ thành nửa vòng phù hợp lớp1. Tất cảparent/source/chat/delta/hash và24SVG/ảnhthamchiếu cómanifest, không giảđãđọc ảnhhoặcthựchành.
\n299ownerhuman signoffs và7policy/state/queue frozen giữ nguyênhash. Bài mới ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED, nguồn AI giữ nguyên, human_review_completed=false; chứng nhận quy trình không phải chủđãđọc bài mới. Source/export/draft rowhash tách riêng. Không viết lại495core/165node.
\nTổng1629852case/6502064candidatechat, kể cảeval/audit6502176. Union36payloadrefs/30chatmembers,48eval sư phạm hiện hành riêng; train-only toànkho chưa được xác minh.31payload cũ chỉ historicalpins;5append đã kiểm rawZIP/member/source-chatliênkết. Không xóa hay thay nguồn cũ. Queue reconciliation mới gắn đúng71exporthash và ghi counts {json.dumps(nq['counts'],ensure_ascii=False)}; phạm vi là exacttextbranches, giữ grade/SGKanchor/physical/assetlimitations và G2residualthực.
\nColab CPU đã xác thực Drive thành công; visiblecell3 cho thấy union cũ35payload/29members,training_started=false. Chỉcell4 kiểm dữ liệu20Kchunk đã chạy, kết thúc chưa quan sát được; celllưucheckpointchưa chạy. Sau đó công cụ báo localbrowseruse bịtắt trongWork, đồng thời người dùng thấy outputJavaScript/cookieerror. Không gọi lại OAuth hoặc train/Runall. Notebook autosave chưa rawreadback mới; giữ hashpublication cũ như lịch sử, không khẳngđịnh livebytescòntrùng.
\nFullArchiveAudit code chuẩn bị thêm: mọi declaredsources indextrướcchat, explicit splits khôngdefaulttrain, fullprompt/targetlinkgắn rawhashcũ chỉ khi unique, checkpointSQLite theo recipe/membercontent khôngtài khoản; account thay đổi vẫn dùng cùngDriveIDs/contentidentity.10tests CPU actualtokenizer PASS; đây là testcode/fixtures, không phải đã kiểm cả6.5triệu. Cần resume/savelivecheckpoint, append-onlyrecipe migration và fullarchiveaudit mới finalready. TRAINING_DATASET_READY=false;training_started=false. Không tải corpus6M xuốngmáy, staging71 hữu hạn phục vụ QA/upload; không GPU/weights/paidAPI/app/commit/push.
\nBundle {bundle['url']} SHA256{bundle['sha256']} ({bundle['bytes']}bytes) đã freshrawreadback đúng toànbyte/hash. Cập nhật PROGRESS/chat/contextcùngIDs, STATEcuối; chỉ xác nhận syncsau4rawreadbacks. Không hoàn tất xoá lịch vì finalcriteriachưađủ.
'''
    context.write_text(header+text+note,encoding='utf8')
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        files=[RUN/'release/audit_report.json',RUN/'release/token_audit.json',RUN/'bundle_remote_verified.json',RUN/'publish_state.json',RUN/'publish_chat_manifest.json',recipe,RUN/'root_evidence/latest_union_scope.json']
        for p in files:new.writestr(RUN.name+'/'+p.name,p.read_bytes())
        for p in sorted((RUN/'reconciliation').glob('*.json')):new.writestr(RUN.name+'/reconciliation/'+p.name,p.read_bytes())
        for n in ['sgk_final_gaps_release.py','sgk_final_gaps_root_review.py','sgk_final_gaps_union_recipe.py','sgk_final_gaps_reconcile.py','sgk_final_gaps_publish_controls.py','math_data_full_audit.py']:new.writestr(RUN.name+'/code/'+n,(HERE/n).read_bytes())
        new.writestr(RUN.name+'/MATH_TRAINING_CONTEXT.md',context.read_bytes());new.writestr(RUN.name+'/drive_artifacts.json',regpath.read_bytes())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert len(new.namelist())==len(set(new.namelist())) and not new.testzip()
        assert all(old.read(n)==new.read(n) for n in old.namelist())
    print(json.dumps(dict(accepted=state['accepted_cases'],candidate_chat=state['training_chat_rows'],all_including_evaluation_audit=state['all_available_chat_rows_including_evaluation_and_audit'],training_started=False,ready=False)))
if __name__=='__main__':main()

