"""Stage reviewed18 release on existing four controls; Drive I/O by coordinator."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,zipfile
from sgk_final_forms_release import read,write,sha,RUN,HERE
def main():
    bundle=read(RUN/'bundle_remote_verified.json');assert bundle['fresh_raw_verified'] and bundle['all_bytes_equal']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json');report=read(RUN/'release/audit_report.json')
    assert state['accepted_cases']==1629727 and state['training_chat_rows']==6501564 and chat['chat_rows']==6501564
    assert not any(x['run_id']=='sgk_final_forms_20261020' for x in state.get('sgk_finish_runs',[]))
    profile=read(RUN/'root_evidence/connector_profile.json');now=datetime.now(timezone.utc).isoformat()
    ref=dict(run_id='sgk_final_forms_20261020',bundle=bundle,cases=18,chat_rows=72,by_grade=report['by_grade'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',token_audit_member='data/release/token_audit.json',acceptance_status='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',new_human_attestation=False,training_started=False)
    for k,d in [('accepted_cases',18),('new_cases',18),('training_chat_rows',72),('training_chat_rows_before_balancing',72),('all_available_chat_rows_including_evaluation_and_audit',72)]:state[k]+=d
    for k in ['by_grade','by_topic']:
        for label,n in report[k].items():state[k][label]=state[k].get(label,0)+n
    state.setdefault('sgk_finish_runs',[]).append(ref);state['updated_utc']=now;state['current_drive_connection']=profile;state['TRAINING_DATASET_READY']=False
    state['status']='FINITE_SGK_FORMS_AND_ARCHIVE_DATA_PREPARATION_IN_PROGRESS'
    recipe=RUN/'publish_latest_union_recipe.json';assert recipe.exists()
    state['latest_all_data_union_recipe']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member='sgk_final_forms_20261020/publish_latest_union_recipe.json',sha256=sha(recipe.read_bytes()),payload_references=34,chat_members=28,declared_candidate_chat_rows=6501636,current_pedagogy_eval_rows_separate=48,historical_split_totals_pending_full_archive_audit=True,actual_train_only_row_total_verified=False,full_archive_audit_complete=False)
    projection=RUN/'reconciliation_projection.json'
    if projection.exists():state['latest_sgk_prospective_reconciliation']=dict(bundle_id=bundle['id'],member='data/reconciliation_projection.json',sha256=sha(projection.read_bytes()),status='DRAFT_HASH_BASED_PROJECTION_REQUIRES_ACCEPTED_HASH_ADJUDICATION',all_sgk_forms_covered=False)
    state['next_action']='Resume finite remaining candidate constraints from exact queue; validate prospective mapping against accepted18 hashes. Complete full archive CPU token/source-link/split audit. No training.'
    chat.setdefault('supplement_bundles',[]).append(ref);chat['chat_rows']+=72;chat['all_available_chat_rows_including_evaluation_and_audit']=state['all_available_chat_rows_including_evaluation_and_audit'];chat['current_drive_connection']=profile
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    regpath=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';reg=read(regpath)
    if reg['account_identity'].get('profile_id')!=profile['profile_id']:reg.setdefault('account_identity_history',[]).append(reg['account_identity'])
    reg['account_identity']=profile;reg['link_id']=profile['link_id'];reg.setdefault('sgk_final_forms_append_bundles',[]).append(bundle);reg['connection_binding_verified_utc']=now;write(regpath,reg)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';prior=context.read_bytes();assert prior==(RUN/'prewrite_context.md').read_bytes()
    text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',prior.decode('utf-8'));marker='### Nhật ký21/10/2026 — sgk_final_forms_20261020 accepted18'
    assert marker not in text
    header=f'<!-- CURRENT_CHECKPOINT sgk_final_forms_20261020: {state["accepted_cases"]} cases; {state["training_chat_rows"]} candidate chat; preparation IN_PROGRESS; NO TRAINING. Latest journal supersedes historical counts. -->\n'
    note=f'''\n\n{marker}\nChủ yêu cầu tiếp tục. Sau đổi tài khoản, connector Hoai Nam profile103000002357306706048 đã đọc cùng bốn control IDs và raw bytes/hash của checkpoint trước, không khởi tạo lại/nhân folder. Binding hiện hành {profile['link_id']} chỉ dùng lúc truy cập, không là danh tính dữ liệu hoặc khóa task.\n\nNhận18 bài/72chat originaltext lớp5/enrichment sau root đọc đủ actual problem/givens/request/studentwork/steps/reasons/explanations/answers/initial/ba hints và peer QA7/hash/oracle khác phương pháp. Hai nhóm12+6: dấu phẩy khoảng mở, danh tính thẻ thập phân, hệ số diện tích/thể tích, sơn6/5mặt, chiều cao tam giác/đỉnh song song; chọn dấu phân số, đường ngắn nhất có thời gian/chi phí hai lượt và tối ưu chỉ4mặt bên. {report['numeric_steps']}biểu thức Fraction/Decimal pass; peer còn kiểm tính toán trong prose và mô hình hữu hạn. Toàn72chat tokenizer pinned CPU pass; không weights/GPU/train. {report['hash_numeric_exception_cases']}case ngoại lệ trùng phép đúnghash đã được chủ cho phép sauQA; không tuyên bố benchmark số học độc lập.\n\nNhãn ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED, nguồn/tác giả ban đầu giữ đúng; không mở rộng299human signoff sang bài mới. Source reviewed draft và export hash tách riêng; giữ toàn bộ case/chat gốc.495core/165node giữ nguyên. Các nhánh mới giúp bù thiếu rõ ràng nhưng chưa tự đóng toànSGK: RUN3 còn54mastertask và10asset-only; projection nhánh mới cần xác nhận bằng acceptedhash trước cập nhật queue. Không coi kiến thức text là kết quả đo ảnh/thực hành đã xảy ra.\n\nTổng{state['accepted_cases']}case/{state['training_chat_rows']}candidatechat, kể cả eval/audit{state['all_available_chat_rows_including_evaluation_and_audit']}. Unionrecipe34payloadrefs/28chatmembers bao gồm mọi supplement có descriptor/hash, thiếu nguồn sẽ dừng;48eval sư phạm hiện hành tách riêng. Tổng train-only thực của kho cũ chưa xác minh; không gọi candidatepool là train-only đã audit. Fullarchive CPU token/linkage/split audit vẫn pending. Reader14tests và actual4364trainreplay trước vẫn là boundedscope.\n\nGói {bundle['url']} SHA256{bundle['sha256']} ({bundle['bytes']}bytes) đã freshraw so toànbyte/hash. PROGRESS/chat/state/context cập nhật đúngIDs, STATE cuối; raw readback bốn control xác nhận sau upload. Staging bounded; cleanup cũ bị automaticpolicy chặn nên không retry hoặc tuyên bố đã xóa. Chưa train; tiếp exactqueue hữu hạn, không sinh vôhạn.\n'''
    context.write_text(header+text+note,encoding='utf-8')
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        files=[RUN/'release/audit_report.json',RUN/'release/token_audit.json',RUN/'bundle_remote_verified.json',RUN/'publish_state.json',RUN/'publish_chat_manifest.json',recipe,RUN/'root_evidence/latest_union_scope.json']
        if projection.exists():files.append(projection)
        for p in files:new.writestr('sgk_final_forms_20261020/'+p.name,p.read_bytes())
        new.writestr('sgk_final_forms_20261020/MATH_TRAINING_CONTEXT.md',context.read_bytes());new.writestr('sgk_final_forms_20261020/drive_artifacts.json',regpath.read_bytes())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:assert not new.testzip() and all(old.read(n)==new.read(n) for n in old.namelist())
    print(json.dumps(dict(accepted=state['accepted_cases'],candidate_chat=state['training_chat_rows'],all_including_evaluation_audit=state['all_available_chat_rows_including_evaluation_and_audit'],training_started=False)))
if __name__=='__main__':main()
