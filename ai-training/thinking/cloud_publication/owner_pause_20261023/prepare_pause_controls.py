"""Preserve every prior progress member; publish only a verified owner pause."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
P=R.parent/'continued_archive_check_20261022'
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(name):return json.loads((R/name).read_bytes())
def save(name,value):(R/name).write_bytes((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())

def main():
    observation=load('owner_pause_observation.json');pause=observation['pause_receipt']
    assert not observation['worker_alive'] and not observation['owner_pause_confirmation_alive']
    assert pause['state']=='PAUSED_BY_OWNER_AT_FRESH_RAW_VERIFIED_CHECKPOINT'
    assert pause['member_cursors_equal_saved_snapshot'] and pause['prior_issues_preserved']
    assert pause['tokenizer_hook_restored'] and not pause['worker_alive']
    proof=pause['checkpoint'];assert proof['fresh_raw_readback_verified']
    assert proof['id']=='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
    assert proof['report_at_snapshot']['identity']=='f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
    assert pause['unique_chat_rows_saved']==proof['report_at_snapshot']['unique_chat_rows_processed']
    assert pause['physical_chat_rows_saved']==proof['report_at_snapshot']['physical_chat_occurrences_processed']
    assert proof['report_at_snapshot']['source_versions_indexed']==1629906
    assert proof['report_at_snapshot']['issues'].get('SOURCE_SPLIT_MISSING_OR_UNKNOWN')==1
    parent=load('parent_controls_raw_verified.json')
    for k,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        assert sha((P/('next_'+k+ext)).read_bytes())==parent[k]['sha256']
    s=json.loads((P/'next_state.json').read_bytes());c=json.loads((P/'next_chat.json').read_bytes())
    assert s['accepted_cases']==1629922 and s['training_chat_rows']==6502344
    assert s.get('pending_checkpoint_append') is None
    owner_pause={'active':True,'requested_utc':pause['requested_utc'],
        'verified_utc':pause['verified_utc'],'reason':'Owner explicitly requested save, stop, and continue in the next session.',
        'do_not_auto_resume':True,'resume_requires_new_owner_instruction':True,
        'checkpoint':proof,'unique_chat_rows_saved':pause['unique_chat_rows_saved'],
        'physical_chat_rows_saved':pause['physical_chat_rows_saved'],
        'evidence_member':'owner_pause_20261023/owner_pause_receipt.json'}
    s.setdefault('data_only_colab_observation_history',[]).append(deepcopy(s.get('latest_colab_runtime_observation',{})))
    latest=dict(s.get('latest_colab_runtime_observation',{}),
        observed_utc=observation['observed_utc'],worker_alive_at_observation=False,
        runtime_status='PAUSED_BY_OWNER_AT_FRESH_RAW_VERIFIED_CHECKPOINT',checkpoint=proof,
        committed_physical_chat_rows=pause['physical_chat_rows_saved'],
        unique_chat_rows_committed=pause['unique_chat_rows_saved'],
        last_verified_checkpoint_unique_chat_rows=pause['unique_chat_rows_saved'],
        source_versions_indexed=1629906,live_status_cell='3vI_dXfrnsz1',
        current_issues=proof['report_at_snapshot']['issues'],
        full_archive_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False,
        evidence_member='owner_pause_20261023/owner_pause_observation.json')
    for control in (s,c):
        control['owner_requested_pause']=owner_pause
        control['DO_NOT_AUTO_RESUME']=True
        control['latest_colab_runtime_observation']=latest
        control['latest_verified_v3_checkpoint']=proof
        control['final_metadata_check']={'state':'PAUSED_BY_OWNER_AWAITING_RESUME',
            'prior_controlled_stop_evidence_preserved':True,'training_started':False}
        control.setdefault('performance_decision',{}).update(query_indexes_applied=True,
            query_index_evidence_member='owner_pause_20261023/sqlite_report_index_evidence.json',
            scanner_adapter_files_changed=False,onepass_optimizer_applied=False)
        control['TRAINING_DATASET_READY']=False;control['training_started']=False
    s['latest_data_only_notebook']=load('notebook_remote_verified.json')
    s['status']='PAUSED_BY_OWNER_AT_FRESH_RAW_VERIFIED_CHECKPOINT'
    s['updated_utc']=datetime.now(timezone.utc).isoformat()
    s['next_action']='DO NOT AUTO RESUME. Owner requested save and stop until the next session. All audit threads are stopped. Wait for a new explicit owner instruction. Then restore exact existing checkpoint ID16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI at the saved SHA/recipe identity, never reset or rerun generation/append64. Claim a new single worker only after verifying no old audit worker is alive; retain all cursors/issues and query indexes. Re-register the finite final metadata checker after resume. No training.'
    marker='### Nhật ký 23/10/2026 — chủ yêu cầu lưu checkpoint và dừng đến phiên sau'
    context=(P/'next_context.md').read_bytes();assert marker.encode() not in context
    text=(f'\n\n{marker}\n'
        'CHỦ ĐÃ YÊU CẦU DỪNG: không tự tiếp tục bởi heartbeat hoặc ô setup cũ. Chỉ resume sau tin nhắn mới của chủ. Đây là tạm dừng theo yêu cầu, không phải phát hiện lỗi dữ liệu. Không tạo lịch mới hoặc tự đoán giờ chạy ngày mai.\n'
        f'Đã dừng trước hàng mới bằng kiểm soát exception, để consume gốc rollback tối đa phần transaction256 chưa commit; sau đó chính worker lưu và raw-readback checkpoint. Đã lưu {pause["unique_chat_rows_saved"]} chat unique / {pause["physical_chat_rows_saved"]} lượt chat vật lý; không mất phần đã commit. Nguồn1629906 đã index đủ; kho hiện hành vẫn6502392rawchat, dự kiến6502344candidate +48eval. Chưa fullscan, chưa train.\n'
        f'Checkpoint cùng ID{proof["id"]}: {proof["bytes"]}byte, SHA256{proof["sha256"]}, raw đọc mới khớp toàn bộ. Snapshot portable trong Colab đối chiếu lại hash, mọi member cursor và issue bằng đúng workingDB cuối. Hook tokenizer đã trả về bản gốc; worker audit, thread chốt metadata và thread xác nhận pause đều đã kết thúc.\n'
        'Giữ raw generic worker exit OwnerRequestedDataOnlyPause trong receipt; đã phân loại lại trạng thái là PAUSED_BY_OWNER, không xóa finding regression_only. Thread chốt metadata từ chối kết luận trên partialscan; raw controlled-stop evidence được giữ. Chỉ mục truy vấn3nonunique đã tạo và nằm trong checkpoint; fixture so báo cáo/cursor/issue trước-sau đạt, source/chat/nhãn/đáp án không bị sửa. Không áp dụng thử nghiệm onepass.\n'
        'Tiếp nối sau này phải dùng đúng checkpoint và recipe f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863 / SHA1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8; không chạy lại append64 hoặc bộ sinh. Giữ495core/165node/1980corechat và299signoff human; chưa đóng5task quan sát thật,10assetmaster,1locatorG3 hoặc chứng nhận toànSGK.\n'
        'Đã giữ đầy đủ PROGRESS cũ, thêm evidence/code/nguồn notebook của pha tạm dừng. Notebook, PROGRESS, chat, context và state dùng đúng IDs; state ghi cuối, mỗi file phải có fresh raw readback. Không train/GPU/weights/paidAPI/app/commit/push.\n')
    (R/'context_delta.txt').write_bytes(text.encode());(R/'next_context.md').write_bytes(context+text.encode())
    save('next_state.json',s);save('next_chat.json',c)
    with zipfile.ZipFile(P/'next_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        assert len(old.namelist())==len(set(old.namelist()))
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for path in sorted(R.iterdir()):
            if not path.is_file() or path.name.startswith('next_') or path.suffix not in ('.json','.py','.txt','.ipynb'):continue
            if path.name in ('prepared_control_updates.json','four_controls_remote_verified.json'):continue
            member='owner_pause_20261023/'+path.name;assert member not in old.namelist();new.writestr(member,path.read_bytes())
    with zipfile.ZipFile(P/'next_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip') as new:
        assert all(old.read(name)==new.read(name) for name in old.namelist())
        assert len(new.namelist())==len(set(new.namelist()))
    ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
    controls={}
    for kind,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        path=R/('next_'+kind+ext);data=path.read_bytes();controls[kind]={'id':ids[kind],'path':str(path),'bytes':len(data),'sha256':sha(data)}
    save('prepared_control_updates.json',{'controls':controls,'state_must_be_written_last':True,'owner_pause_active':True,'new_case_count':0,'new_chat_count':0,'training_started':False})
    print(json.dumps({'prepared':True,'saved_chat_rows':pause['unique_chat_rows_saved'],'checkpoint_sha256':proof['sha256'],'controls':controls}))

if __name__=='__main__':main()
