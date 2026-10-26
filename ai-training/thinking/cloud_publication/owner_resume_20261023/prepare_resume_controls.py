"""Append verified resume evidence and preserve every existing progress member."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,zipfile

R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(n):return json.loads((R/n).read_bytes())
def save(n,v):(R/n).write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())

def main():
    observation=load('runtime_observation.json')
    restore=observation['restore_status']['restore_receipt']
    assert restore['fresh_raw_readback_verified'] and restore['query_indexes_preserved']
    assert restore['checkpoint_sha256']=='3c7cb05061c0040812111a6bb73a0709cc59a244493dc135a3b95aa389bf0648'
    assert observation['worker_alive'] and observation['committed_physical_chat_rows']>=4427328
    assert observation['final_metadata_alive']
    s=load('parent_state.json');c=load('parent_chat.json')
    assert s['latest_all_data_union_recipe']['sha256']=='1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8'
    assert s['accepted_cases']==1629922 and s['training_chat_rows']==6502344
    assert s.get('pending_checkpoint_append') is None
    expected={'progress':'d9a12f3204749f86b8038fb816c3deaf668e9df934535de4a9d48515d1dd9855',
              'chat':'3fc35f8aa203292a94953afd4558d054b692c3a7ae46b62449b8b25bcc8397f8',
              'context':'99f5f02b630dd9d6d5622c17bae3fdff114343e00af7987ce892856ea136cf86',
              'state':'c731223ac0a1278fddc2054f05cb7fe1d4d2b5b1bad7049d3348e5f6fd414092'}
    for kind,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        assert sha((R/('parent_'+kind+ext)).read_bytes())==expected[kind]
    resume={'owner_instruction':'tiếp tục','active':True,'observed_utc':observation['observed_utc'],
            'prior_pause_preserved':True,'restore_receipt':restore,'new_case_count':0,'new_chat_count':0,
            'evidence_member':'owner_resume_20261023/runtime_observation.json','training_started':False}
    latest=dict(s.get('latest_colab_runtime_observation',{}),observed_utc=observation['observed_utc'],
        worker_alive_at_observation=True,runtime_status=observation['worker_state'],
        committed_physical_chat_rows=observation['committed_physical_chat_rows'],
        unique_chat_rows_committed=observation['unique_chat_rows_processed'],
        source_versions_indexed=1629906,checkpoint=observation['checkpoint'],
        full_archive_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False,
        live_status_cell='NGRT7K_nW2sP',evidence_member=resume['evidence_member'])
    for control in (s,c):
        control.setdefault('owner_pause_history',[]).append(deepcopy(control['owner_requested_pause']))
        control['owner_requested_pause']=dict(control['owner_requested_pause'],active=False,
            do_not_auto_resume=False,resume_requires_new_owner_instruction=False,
            resumed_by_explicit_owner_instruction='tiếp tục',resumed_utc=observation['observed_utc'])
        control['DO_NOT_AUTO_RESUME']=False
        control['latest_owner_resume']=resume
        control.setdefault('data_only_colab_observation_history',[]).append(deepcopy(control.get('latest_colab_runtime_observation',{})))
        control['latest_colab_runtime_observation']=latest
        control['latest_verified_v3_checkpoint']=observation['checkpoint']
        control['final_metadata_check']={'state':observation['final_metadata_status']['state'],
            'registered_for_resumed_single_worker':True,'prior_pause_evidence_preserved':True,'training_started':False}
        control['TRAINING_DATASET_READY']=False;control['training_started']=False
    s['latest_data_only_notebook']=load('notebook_remote_verified.json')
    s['status']='FULL_CURRENT_ARCHIVE_AUDIT_RESUMED_FROM_OWNER_PAUSE'
    s['updated_utc']=datetime.now(timezone.utc).isoformat()
    s['next_action']='Continue the one existing CPU worker from exact verified same-ID checkpoint/current251member recipe. Do not regenerate, reinsert G2 append64, or reset any cursor. Wait for full current-text token/link/split scan, exact diagnostic adjudication and source/chat anti-join. Physical observation/asset/source-locator requirements remain separate. No training.'
    marker='### Nhật ký 23/10/2026 — chủ yêu cầu tiếp tục, khôi phục đúng checkpoint đã dừng'
    context=(R/'parent_context.md').read_bytes();assert marker.encode() not in context
    text=(f'\n\n{marker}\n'
          'Tin nhắn mới “tiếp tục” của chủ đã hủy yêu cầu tạm dừng trước đó; giữ nguyên lịch sử pause. Colab cũ hết runtime, đã mở lại MCP trên Chrome Hoai và chỉ chạy setup tokenizer/auth/data-only; không Runall, không train.\n'
          f'Khôi phục đúng Drive checkpoint ID{restore["checkpoint_id"]}, {restore["checkpoint_bytes"]}byte, SHA{restore["checkpoint_sha256"]}; fresh streaming raw readback trong Colab và metadata trước/sau khớp. SQLite quick_check/config/225con trỏ đã khởi tạo trong251member khai báo, cursor SHA/224complete/4427328samples+occurrences/1629906sources/issue/index đều được kiểm đúng snapshot đã dừng.\n'
          'Giữ recipe f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863 / SHA1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8. Không soạn thêm, không chạy lại append64, không tăng tổng. Một agent gpt-6-luna rà code khôi phục/orchestration; đây là peer review bằng agent, không human signoff.\n'
          f'Quan sát {observation["observed_utc"]}: một worker CPU đang chạy, {observation["committed_physical_chat_rows"]}chat đã commit; thread chốt metadata đã đăng ký lại cho đúng worker này. Checkpoint đã lưu gần nhất vẫn {observation["checkpoint"]["report_at_snapshot"]["unique_chat_rows_processed"]}chat đến lần save/rawcheck kế tiếp. Không gọi partialscan là toàn kho pass.\n'
          'Auditor/adapter frozen không đổi; hai encoding tokenizer độc lập, batch256/commit256, outerspan200000, WAL và3queryindex giữ nguyên. Dùng HTTP client chuẩn cho resumable upload. Writer guard là một kernel đã quan sát + optimistic hash, không giả distributed atomic CAS.\n'
          'Giữ evidence hai lỗi orchestration đã sửa trước khi xử lý hàng mới: root từng giả định sai partialDB phải có251cursor (thực tế225lazycursor), và remote-name tokenizer thiếu metadata_commit_hash nên adapter từ chối. Đã sửa phép kiểm225/251 đúng exactcursorhash và reload actual local immutable HFsnapshot revision70d244cc86ccca08cf5af4e1e306ecf908b1ad5e; không tự điền commitmetadata, không thaygate. Readonly sequential prefetch kiểm lại đủbyte/hash để giảm đọc đĩa; không đổi checkpoint.\n'
          'Giữ495core/165node/1980chat và299human exact-hash signoff. Các pending5task quan sát thật/7constraints,10assetmasters,1locatorG3 chưa được đóng bằng dữ liệu giả. Nguồn thực1629906 khác bộ đếm lịch sử1629922; chênh16 chưa chứng minh nguyên nhân. Raw issue regression_only giữ nguyên. Chưa full ready, chưa train/GPU/weights/paidAPI/app/commit/push.\n'
          'Notebook và4control cập nhật đúngIDs; PROGRESS giữ nguyên mọi member cũ; STATE ghi cuối và chỉ xác nhận sync sau fresh raw byte/hash readback. Skills applied: google-drive:google-drive.\n')
    (R/'context_delta.txt').write_bytes(text.encode());(R/'next_context.md').write_bytes(context+text.encode())
    save('next_state.json',s);save('next_chat.json',c)
    names=['restore_saved_checkpoint.py','prepare_resume_worker.py','parent_worker_function.py','resumed_worker_function.py','launch_single_worker.py',
           'finalizer_setup.py','prepare_resume_controls.py','runtime_observation.json','frozen_baseline_verified.json',
           'parent_controls_raw_verified.json','notebook_remote_verified.json','context_delta.txt',
           'agent_resume_review.json','continue_verified_restore.py','resume_claimed_worker.py','restore_assertion_diagnosis.json',
           'launch_latest.json','claimed_worker_resume_run.json','restore_verified.json','readonly_checkpoint_prefetch.py',
           'runtime_status.py','mcp_phase_control.py','notebook_parent_drive.ipynb']
    with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        assert len(old.namelist())==len(set(old.namelist()))
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for name in names:
            member='owner_resume_20261023/'+name;assert member not in old.namelist()
            new.writestr(member,(R/name).read_bytes())
    with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip') as new:
        assert all(new.read(n)==old.read(n) for n in old.namelist())
        assert len(new.namelist())==len(set(new.namelist()))
    ids={'progress':'1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX','chat':'1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6','context':'13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9','state':'1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme'}
    controls={}
    for k,e in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
        p=R/('next_'+k+e);b=p.read_bytes();controls[k]={'id':ids[k],'path':str(p),'bytes':len(b),'sha256':sha(b)}
    save('prepared_control_updates.json',{'controls':controls,'state_must_be_written_last':True,'owner_pause_active':False,'training_started':False})
    print(json.dumps({'prepared':True,'controls':controls}))

if __name__=='__main__':main()
