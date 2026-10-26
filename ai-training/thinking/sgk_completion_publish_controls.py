"""Stage data-only RUN5 on four existing IDs; coordinator verifies actual Drive I/O."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,zipfile
from sgk_completion_release import read,write,sha,RUN,HERE
def main():
    bundle=read(RUN/'bundle_remote_verified.json')
    assert bundle['fresh_raw_verified'] and bundle['all_bytes_equal']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json');report=read(RUN/'release/audit_report.json')
    assert state['accepted_cases']==1629745 and state['training_chat_rows']==6501636 and chat['chat_rows']==6501636
    assert not any(x['run_id']==RUN.name for x in state.get('sgk_finish_runs',[]))
    profile=read(RUN/'root_evidence/connector_profile.json');now=datetime.now(timezone.utc).isoformat()
    ref=dict(run_id=RUN.name,bundle=bundle,cases=36,chat_rows=144,by_grade=report['by_grade'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',token_audit_member='data/release/token_audit.json',acceptance_status='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',new_human_attestation=False,training_started=False)
    for k,d in [('accepted_cases',36),('new_cases',36),('training_chat_rows',144),('training_chat_rows_before_balancing',144),('all_available_chat_rows_including_evaluation_and_audit',144)]:state[k]+=d
    assert state['all_available_chat_rows_including_evaluation_and_audit']==6501892
    for k in ['by_grade','by_topic']:
        for label,n in report[k].items():state[k][label]=state[k].get(label,0)+n
    state.setdefault('sgk_finish_runs',[]).append(ref)
    state.update(updated_utc=now,current_drive_connection=profile,TRAINING_DATASET_READY=False,status='FINITE_SGK_FORMS_AND_ARCHIVE_DATA_PREPARATION_IN_PROGRESS')
    recipe=RUN/'publish_latest_union_recipe.json';assert recipe.exists()
    state['latest_all_data_union_recipe']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/publish_latest_union_recipe.json',sha256=sha(recipe.read_bytes()),payload_references=35,chat_members=29,declared_candidate_chat_rows=6501780,current_pedagogy_eval_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False,full_archive_audit_complete=False)
    q=RUN/'reconciliation/next_uncovered_tasks.json'
    state['latest_sgk_accepted_reconciliation']=dict(bundle_id=bundle['id'],member='data/reconciliation/next_uncovered_tasks.json',sha256=sha(q.read_bytes()),bound_run='sgk_final_forms_20261020',accepted_cases_bound=18,global_master_tasks=45,asset_only_masters_separate=10,run5_mapping_pending_accepted_hash_binding=True,all_sgk_forms_covered=False)
    projection=RUN/'post_acceptance_mapping/projection.json'
    if projection.exists():state['latest_sgk_prospective_reconciliation']=dict(bundle_id=bundle['id'],member='data/post_acceptance_mapping/projection.json',sha256=sha(projection.read_bytes()),status='PRESERVED_DRAFT_PROJECTION_RUN5_ACCEPTED_HASH_BINDING_PENDING',all_sgk_forms_covered=False)
    nb=read(RUN/'notebook/remote_verified.json')
    assert nb['id']=='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l' and nb['sha256']=='5d3a413c7bf67d716554d3a8c08af69d901921f66cafe48a62aa2b3628b5f893' and nb['fresh_raw_verified'] and nb['all_bytes_equal'] and not nb['colab_executed']
    state['latest_data_only_colab_notebook']={**nb,'verification_member':'data/notebook/remote_verified.json','uses_latest_state_and_all_candidate_recipe':True,'checkpoint_by_recipe_and_split':True,'data_preparation_only':True,'full_archive_audit_complete':False}
    state['next_action']='Bind reviewed36 export hashes to prospective SGK mapping, preserve original candidate/grade/asset residuals; finish exact finite missing branches and full archive CPU token/source-link/split audit. Data-only Colab notebook prepared but not executed. No training.'
    chat.setdefault('supplement_bundles',[]).append(ref);chat['chat_rows']+=144
    chat['all_available_chat_rows_including_evaluation_and_audit']=state['all_available_chat_rows_including_evaluation_and_audit'];chat['current_drive_connection']=profile
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    regpath=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';reg=read(regpath)
    if reg['account_identity'].get('profile_id')!=profile['profile_id']:reg.setdefault('account_identity_history',[]).append(reg['account_identity'])
    reg.update(account_identity=profile,link_id=profile['link_id'],connection_binding_verified_utc=now)
    assert not any(b['sha256']==bundle['sha256'] for b in reg.get('sgk_completion_append_bundles',[]))
    reg.setdefault('sgk_completion_append_bundles',[]).append(bundle);reg['latest_data_only_notebook']=nb;write(regpath,reg)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';prior=context.read_bytes()
    assert prior==(RUN/'prewrite_context.md').read_bytes()
    text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',prior.decode('utf-8'));marker='### Nhật ký21/10/2026 — sgk_completion_20261021 accepted36'
    assert marker not in text
    header=f'<!-- CURRENT_CHECKPOINT {RUN.name}: {state["accepted_cases"]} cases; {state["training_chat_rows"]} candidate chat; preparation IN_PROGRESS; NO TRAINING. Latest journal supersedes historical counts. -->\n'
    note=f'''\n\n{marker}\nTiếp tục theo yêu cầu chủ. Connector Hoai Nam profile103000002357306706048, link {profile['link_id']}, đã freshraw đối chiếu bốn control trước ghi; vẫn cùng IDs, không tạo lại folder hoặc giả danh tính giữa tài khoản. Link chỉ là binding truy cập, không phải khóa dữ liệu/task.\n\nNhận36bài/144chat originaltext các lớp1,3,4,5 sau root đọc actual problem/givens/request/studentwork/steps/reasons/explanations/answers/initial/all hints, QA7 và ba peer độc lập. Ba nhóm12: vật liệu/chi phí/chia phần/biên lưới/net/thể tích/lát hình/đáy-chiều cao; nhãn biên/multiplicity/que chung/đếm hình/gameinventory/bỏ cạnh/glyph; diện tích chia ghép/chồng lấp/đỉnh hình bình hành/thứ tự lớp/đường tròn tiếp xúc/cắt hình thang. {report['numeric_steps']}biểu thức Fraction/Decimal,36oracle khác phương pháp,115mutation, toàn144chat tokenizer pinned CPU pass. {report['hash_numeric_exception_cases']}case trùng phép được chấp nhận theo ngoại lệ đúnghash sauQA; không tuyên bố benchmark số học độc lập.\n\nBản measurement sửa duy nhất tên đoạn phân hoạch AD thành DE; giữ đáp án, parent rawhash, nguồn cũ và toàn bộ evidence. Chỉ bản dẫn xuất đã được kiểm mới vào accepted member. Nhãn ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED; nguồn AI ban đầu không đổi thành tác giả người.299ownerhuman signoffs frozen không được mở rộng. Source draft và export hash tách riêng, không chứng nhận humanreview cho bài tương lai.495core/165node giữ nguyên.\n\nReconciliation trong gói đã bind18accepted của RUN4 vào đúnghash:45globalmastertasks+10asset-only, nguyên204candidate/315occurrences/91G2 giữ nguyên. RUN5 projection nếu có chỉ là đối chiếu draft cần bind accepted36; không tự đóng alias lớp khác hoặc hình/thực hành. Còn các nhánh SGK hữu hạn và fullarchive token/source-link/split audit; TRAINING_DATASET_READY=false.\n\nTổng{state['accepted_cases']}case/{state['training_chat_rows']}candidatechat; kể cả eval/audit{state['all_available_chat_rows_including_evaluation_and_audit']}. Unionrecipe35payloadrefs/29chatmembers giữ toàn bộ supplement có descriptor/hash;48eval sư phạm hiện hành tách riêng, tổng train-only của kho cũ chưa xác minh.31payload cũ là historicalpins, không tuyên bố freshraw toànkho. Bốn append đã kiểm toànZIP/member/sourcechatlinks.\n\nNotebook Colab ID{nb['id']} đã cập nhật đúngfile cũ, freshraw hash{nb['sha256']} ({nb['bytes']}bytes). Đọc latestSTATE/PROGRESS và toànunion theohash, có checkpoint recipe/split, cache một payload trên Colab tạm;20Kchunk chỉ resume không chọn tập nhỏtrain.7cell kiểm syntax,bootstrapfixture/6tests pass; CHƯA chạy Colab/auth/fullarchive hoặc train. Notebook cũ được giữ trong bundle. Không weights/GPU/train/paidAPI/app/commit/push.\n\nBundle {bundle['url']} SHA256{bundle['sha256']} ({bundle['bytes']}bytes) đã rawreadback toànbyte/hash. PROGRESS/chat/context cập nhật cùngIDs, STATE cuối; remote receipt bốn control chỉ hoàn tất sau rawreadback. Không tuyên bố chuẩn bị xong toànbộ. Staging bounded đang giữ; cleanup cũ bị automaticpolicy chặn, không retry hoặc tuyên bố đã xóa.\n'''
    context.write_text(header+text+note,encoding='utf-8')
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        files=[RUN/'release/audit_report.json',RUN/'release/token_audit.json',RUN/'bundle_remote_verified.json',RUN/'publish_state.json',RUN/'publish_chat_manifest.json',recipe,RUN/'root_evidence/latest_union_scope.json',RUN/'notebook/remote_verified.json']
        for p in files:new.writestr(RUN.name+'/'+p.name,p.read_bytes())
        for p in sorted((RUN/'reconciliation').glob('*.json')):new.writestr(RUN.name+'/reconciliation/'+p.name,p.read_bytes())
        if projection.exists():
            for p in sorted(projection.parent.glob('*.json')):new.writestr(RUN.name+'/post_acceptance_mapping/'+p.name,p.read_bytes())
        new.writestr(RUN.name+'/MATH_TRAINING_CONTEXT.md',context.read_bytes());new.writestr(RUN.name+'/drive_artifacts.json',regpath.read_bytes())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert len(new.namelist())==len(set(new.namelist())) and not new.testzip()
        assert all(old.read(n)==new.read(n) for n in old.namelist())
    print(json.dumps(dict(accepted=state['accepted_cases'],candidate_chat=state['training_chat_rows'],all_including_evaluation_audit=state['all_available_chat_rows_including_evaluation_and_audit'],training_started=False)))
if __name__=='__main__':main()

