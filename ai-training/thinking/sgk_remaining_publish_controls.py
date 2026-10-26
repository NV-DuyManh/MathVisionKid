"""Stage append controls only after verified remote immutable bundle receipt."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,zipfile
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_remaining_20261020'
def read(p):return json.loads(p.read_text('utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    b=read(RUN/'bundle_remote_verified.json');assert b['fresh_raw_verified'] and b['all_bytes_equal']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json');report=read(RUN/'release/audit_report.json')
    assert state['accepted_cases']==1629691 and state['training_chat_rows']==6501420 and chat['chat_rows']==6501420
    assert not any(r['run_id']=='sgk_remaining_20261020' for r in state.get('sgk_finish_runs',[]))
    now=datetime.now(timezone.utc).isoformat();profile=read(RUN/'root_evidence/connector_profile.json')
    ref=dict(run_id='sgk_remaining_20261020',bundle=b,cases=36,chat_rows=144,by_grade=report['by_grade'],source_member='data/release/accepted_cases.jsonl',chat_member='data/release/accepted_chat.jsonl',token_audit_member='data/release/token_audit.json',acceptance_status='ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED',new_human_attestation=False,training_started=False)
    for k,d in [('accepted_cases',36),('new_cases',36),('training_chat_rows',144),('training_chat_rows_before_balancing',144),('all_available_chat_rows_including_evaluation_and_audit',144)]:state[k]+=d
    for k in ['by_grade','by_topic']:
        for key,count in report[k].items():state[k][key]=state[k].get(key,0)+count
    state.setdefault('sgk_finish_runs',[]).append(ref);state['current_drive_connection']=profile;state['updated_utc']=now
    state['status']='FINITE_SGK_BRANCH_RECONCILIATION_AND_FULL_ARCHIVE_DATA_ONLY_AUDIT_IN_PROGRESS';state['TRAINING_DATASET_READY']=False
    if (RUN/'reconciliation/candidate_adjudication.json').exists():
        state['latest_sgk_semantic_reconciliation']=dict(bundle_id=b['id'],member='data/reconciliation/candidate_adjudication.json',sha256=sha((RUN/'reconciliation/candidate_adjudication.json').read_bytes()),next_tasks_member='data/reconciliation/next_uncovered_tasks.json',next_tasks_sha256=sha((RUN/'reconciliation/next_uncovered_tasks.json').read_bytes()),remaining_global_master_tasks=54,asset_only_masters_separate=10,all_sgk_forms_covered=False)
    if (RUN/'stream_loader/files_receipt.json').exists():
        state['all_data_candidate_reader']=dict(bundle_id=b['id'],code_member='code/math_data_candidate_stream.py',receipt_member='data/stream_loader/files_receipt.json',receipt_sha256=sha((RUN/'stream_loader/files_receipt.json').read_bytes()),candidate_split_policy='Explicit train only; validation/test kept separate; no missing-split default',full_archive_audit_complete=False,training_started=False)
    recipe=RUN/'publish_latest_union_recipe.json';assert recipe.exists()
    state['latest_all_data_union_recipe']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member='sgk_remaining_20261020/publish_latest_union_recipe.json',sha256=sha(recipe.read_bytes()),payload_references=33,chat_members=27,declared_candidate_chat_rows=6501564,current_pedagogy_eval_rows_separate=48,full_archive_audit_complete=False)
    state['next_action']='Continue exact finite candidate/branch reconciliation and uncovered tasks; audit every declared source/chat member using data-only CPU checks. No training.'
    chat.setdefault('supplement_bundles',[]).append(ref);chat['chat_rows']+=144;chat['all_available_chat_rows_including_evaluation_and_audit']=state['all_available_chat_rows_including_evaluation_and_audit'];chat['current_drive_connection']=profile
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat_manifest.json',chat)
    regpath=HERE/'data/primary_math_teacher_20261016/drive_artifacts.json';reg=read(regpath)
    if reg.get('account_identity',{}).get('profile_id')!=profile['profile_id']:reg.setdefault('account_identity_history',[]).append(reg['account_identity'])
    reg['account_identity']=profile;reg['link_id']='current_connector_runtime';reg.setdefault('sgk_remaining_append_bundles',[]).append(b);reg['connection_binding_verified_utc']=now
    write(regpath,reg)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';before=context.read_bytes();assert before==(RUN/'prewrite_context.md').read_bytes()
    text=before.decode('utf-8');marker='### Nhật ký20/10/2026 — sgk_remaining_20261020 verified append'
    assert marker not in text;text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',text)
    header=f'<!-- CURRENT_CHECKPOINT sgk_remaining_20261020: {state["accepted_cases"]} cases; {state["training_chat_rows"]} candidate chat; SGK and full archive preparation IN_PROGRESS; NO TRAINING. Latest journal supersedes historical counts. -->\n'
    note=f'''\n\n{marker}\nTiếp tục sau đổi tài khoản, dùng connector hiện hành {profile['name']} ({profile['email']}, profile{profile['profile_id']}). Bốn control cũ được raw readback khớp byte/hash trước append; dữ liệu nhận diện bằng ID/hash, không link_id hay phiên agent. Gói94 trước vẫn giữ nguyên.\n\nNhận thêm36bài/144chat thuộc18representationmasters sau root đọc mọi actualfields và peerQA7/oracle độc lập, phân lớp{report['by_grade']}. {report['numeric_steps']} bước Fraction/Decimal; toàn144chat kiểm CPU tokenizer pinned, khôngweights/train. {report['hash_numeric_exception_cases']}case có ngoại lệ trùng phép đúnghash theo quyền đã cho; không tuyên bố benchmark số học độc lập. Mỗi bài có lý do, đơn vị, kiểm; initial+ba hint không điền đáp án. Nhãn ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED; không mở rộng299human signoff hoặc giả owner đã đọc nội dung mới.\n\n12structurepolished là bản dẫn xuất THAY12draft gốc, không cộng thêm12. Giữ parentcase/chat nguyênbyte và delta chính xác; mở rộng givens, dời kết luận chữ số từ bước chưa đủ lập luận sang bước đã đủ; không đổi đáp án để qua gate. Hai nhánh/master khác ràng buộc, biểu diễn hoặc lỗi đã cho. Phạm vi là originaltext/enrichment; không nhận kết quả ảnh/thực hành chưa có.\n\nBộ đọc candidate mới dùng unionrecipe cácpayload/members theohash, giữmọi nguồn hợp lệ và supplement; splittrain/validation/test rõ ràng, khôngnhập tậpđánhgiá vào train. Cursortask/SQLite có hashidentity và khôi phục idempotent; quyền đọc của tài khoản khác không suyra quyền sửa. Fullarchive token/linkage/split audit vẫn chưa hoàn tất, không đồng nhất sốchat quản lý với số đã audit. Candidate reconciliation ghi nhánh covered cósourceID/hash và nhánh cònmở; không blanket chứng nhận toànSGK/chươngtrình.\n\nTổng{state['accepted_cases']}case/{state['training_chat_rows']}candidatechat, gồm eval/audit{state['all_available_chat_rows_including_evaluation_and_audit']};495core/165node giữ nguyên. CHƯA TRAIN. Gói mới {b['url']} SHA256{b['sha256']}, {b['bytes']}bytes đãfreshraw so toànbyte. Bốn control dùng đúng IDcũ, STATE cập nhật cuối. Staging bounded; cleanup cũ bị automaticpolicy chặn, không retry/xóa hoặc tuyên bố đãdọn. Tiếp việc hữu hạn từcheckpoint và next_uncovered_tasks; không sinh sốhọc vôhạn.\n'''
    context.write_text(header+text+note,encoding='utf-8')
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        files=[RUN/'release/audit_report.json',RUN/'release/token_audit.json',RUN/'bundle_remote_verified.json',RUN/'publish_state.json',RUN/'publish_chat_manifest.json']
        files += [p for p in [RUN/'reconciliation/candidate_adjudication.json',RUN/'reconciliation/next_uncovered_tasks.json',RUN/'stream_loader/files_receipt.json',RUN/'publish_latest_union_recipe.json',RUN/'root_evidence/latest_union_scope.json',RUN/'final_receipt.json'] if p.exists()]
        for p in files:new.writestr('sgk_remaining_20261020/'+p.name,p.read_bytes())
        new.writestr('sgk_remaining_20261020/MATH_TRAINING_CONTEXT.md',context.read_bytes());new.writestr('sgk_remaining_20261020/drive_artifacts.json',regpath.read_bytes())
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:assert not new.testzip() and all(old.read(n)==new.read(n) for n in old.namelist())
    print(json.dumps(dict(accepted=state['accepted_cases'],candidate_chat=state['training_chat_rows'],controls_staged=True,training_started=False)))
if __name__=='__main__':main()
