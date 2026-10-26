"""Prepare controls after exact same-ID checkpoint append and fresh readback."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
R=H/'cloud_publication/resume_after_g2_20261022'
sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(name):return (R/name).read_bytes()
def load(name):return json.loads(raw(name))
def dump(name,v):(R/name).write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def main():
    obs=load('verified_runtime_observation.json');m=obs['migration'];proof=m['checkpoint']
    assert m['stage']=='APPEND_CHECKPOINT_RAW_VERIFIED_WORKER_RESUMED' and proof['fresh_raw_readback_verified']
    assert obs['audit_worker_alive'] and obs['actual_chat_rows_committed']>=1078352
    assert proof['id']=='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
    assert obs['actual_source_versions']==1629906 and obs['journal_mode']=='wal'
    assert m['prior_member_cursors_unchanged'] and m['prior_issues_preserved']
    assert obs['issues']=={'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1}
    before=load('parent_controls_raw_verified.json')
    accepted=load('../antigravity_intake_20261022/four_controls_remote_verified.json')['controls']
    assert all(before[k]['sha256']==accepted[k]['sha256'] for k in before)
    s=load('parent_state.json');c=load('parent_chat.json')
    assert s['accepted_cases']==1629922 and s['training_chat_rows']==6502344
    applied=deepcopy(s['pending_checkpoint_append'])
    assert applied['next_identity']==m['next_identity']
    applied.update(transition_performed=True,checkpoint=proof,prior_cursor_and_issue_rows_preserved=True,
        fresh_raw_readback_verified=True,evidence_member='resume_after_g2_20261022/verified_runtime_observation.json')
    s.setdefault('checkpoint_append_history',[]).append(applied)
    s['latest_applied_checkpoint_append']=applied;s['pending_checkpoint_append']=None
    c['latest_applied_checkpoint_append']=applied;c['pending_checkpoint_append']=None
    oldobs=s.get('latest_colab_runtime_observation',{})
    s.setdefault('data_only_colab_observation_history',[]).append(oldobs)
    current=dict(oldobs,observed_utc=obs['observed_utc'],worker_alive_at_observation=True,
        runtime_status='RUNNING_DATA_ONLY',unique_chat_rows_committed=obs['actual_chat_rows_committed'],
        source_versions_indexed=obs['actual_source_versions'],executing_recipe_identity=m['next_identity'],
        pending_next_recipe_identity=None,checkpoint=proof,
        evidence_member='resume_after_g2_20261022/verified_runtime_observation.json',
        live_status_cell='huPQdp9b7Ssa',current_issues=obs['issues'],journal_mode='wal',
        full_archive_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False)
    s['latest_colab_runtime_observation']=current;c['latest_colab_runtime_observation']=current
    s['latest_verified_v3_checkpoint']=proof;c['latest_verified_v3_checkpoint']=proof
    notebook=load('notebook_remote_verified.json')
    s.setdefault('data_only_notebook_publication_history',[]).append(s.get('latest_data_only_notebook'))
    s['latest_data_only_notebook']=notebook
    s['status']='FULL_ARCHIVE_AUDIT_RUNNING_WAL_LOCK_REPAIR_AND_G2_APPEND_APPLIED'
    s['updated_utc']=datetime.now(timezone.utc).isoformat()
    s['next_action']='Use MCP DATA_ONLY notebook1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l and status cellhuPQdp9b7Ssa. Continue the one existing V3 worker/Drive checkpoint16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI with recipe identityf0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863. The64case/256chat append is already committed; never count, reinsert or migrate it again. Preserve existing diagnostic and finish all251members before final split disposition. Five actual-observation tasks, ten asset masters and one G3 locator remain separate. No training.'
    s['TRAINING_DATASET_READY']=False;s['training_started']=False
    marker='### Nhật ký 22/10/2026 — nối checkpoint 64 bài và sửa khóa SQLite'
    context=raw('parent_context.md');assert marker.encode() not in context
    delta='\n\n'+marker+'\n'
    delta+='Đã kết nối lại MCP trên đúng Chrome Hoai/notebook DATA_ONLY sau khi local MCP host dừng. User xác nhận kết nối. Helper local nay từ chối notebook OCR17aUDHsE5hyYeDCFb3Z-iG8hRnGwvfcZM và dùng data_only_connection.json; không chạy nhầm notebook hoặc Runall. Mốc thực tế worker cũ dừng vì OperationalError database is locked, đã giữ log và checkpoint cha6edaf07aa5e133ea5cf3cb4c04d30278fd9deb90ce62d0c4f95a32ac92ccad87 với1078096chat.\n'
    delta+='Tái kiểm actual64source/256chat qua frozenV3, issues{}, max1193token, assistantmask/link/split đủ; đây là bounded integration không phải full6.5Mpass. Kiểm fixture tái hiện DELETE reader chặn writer, WAL cho writer commit và reader vẫn giữ snapshot; backup đổi DELETE, mở readonly/quick_check đạt. Kiểm append-only trên exact recipe219source/32chat: cursor/issue fixture giữ nguyên, reordered/staleidentity bị từ chối.\n'
    delta+='Runtime chuyển WAL và busy_timeout120000ms, đóng rootreaders; giữ auditor/adapter frozen. Nối đúng64source+256chat một lần vào workingDBcũ; mọi220membercursor cũ và issue cũ giữ nguyên. Sourceversions1629906, chat1078352 ởsnapshot; các số này khác acceptedlogicalcases1629922 vì phạm vi index nguồn. Không tăng tổng bài/chat thêm lần nữa. Lần upload đầu gặp RedirectMissingLocation; giữ lỗi và tiếp nối publication snapshot đãkiểm, không reinsert; dùng HTTP client chuẩn xử lý resumable308.\n'
    delta+=f"Checkpoint cùngID{proof['id']} đã freshraw streaming readback đủ{proof['bytes']}byte SHA256{proof['sha256']}. Parent snapshot giữ nguyên trongruntime. Recipe identity{m['next_identity']} và SHA1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8 đượcáp dụng; pending_checkpoint_append đã hoàn tất. Worker CPU duy nhất đã chạy lại. Quan sát{obs['observed_utc']}: {obs['actual_chat_rows_committed']}chat committed, issue regression_only vẫn1, chưa fullarchivepass.\n"
    delta+='Tổng vẫn1629922acceptedcandidate/6502344candidatechat, core495/165; còn5actual-observationtasks/7constraints,10assetmasters/1G3locator. Không mở rộng299human signoff, không đổi nguồn frozen, khôngtrain/GPU/weights/paidAPI/app/commit/push. Notebook nguồn/outputs được lưu đúngID, parent29cellsource giữ nguyên. Evidence/code trong PROGRESS/resume_after_g2_20261022; bốncontrol cùngIDs vàSTATEcuối, chỉ xác nhận đồng bộ sau rawreadback. Skills applied: google-drive:google-drive; computer-use cho quan sát kết nối browser.\n'
    (R/'context_delta.txt').write_bytes(delta.encode());(R/'next_context.md').write_bytes(context+delta.encode())
    dump('next_chat.json',c);dump('next_state.json',s)
    names=['state_grounding.json','mcp_connection_status.json','mcp_connection_status_after_owner.json',
        'open_data_only_connection.json','runtime_probe_full.json','bounded_g2_v3_integration.json',
        'sqlite_lock_repair_checks.json','migration_source_pins.json','migration_started.json',
        'migration_observation_1.json','migration_observation_2.json','publication_retry_started.json',
        'verified_runtime_observation.json','notebook_remote_verified.json','notebook_savepoint_prepared.json',
        'parent_controls_raw_verified.json','parent_state.json','parent_chat.json','context_delta.txt',
        'migrate_and_resume_runtime.py','retry_checkpoint_publication_runtime.py','finalize_verified_resume_function.py']
    with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        assert len(old.namelist())==len(set(old.namelist()))
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for name in names:
            member='resume_after_g2_20261022/'+name;assert member not in old.namelist();new.writestr(member,raw(name))
        for file in [Path(__file__),H/'colab_audit_mcp_control.py',H/'check_g2_v3_append_integration.py']:
            new.writestr('resume_after_g2_20261022/'+file.name,file.read_bytes())
    with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip') as new:
        assert all(old.read(name)==new.read(name) for name in old.namelist())
    files={k:dict(id=before[k]['id'],path=str(R/('next_'+k+ext)),bytes=len(raw('next_'+k+ext)),sha256=sha(raw('next_'+k+ext)))
        for k,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]}
    dump('prepared_control_updates.json',dict(controls=files,state_must_be_written_last=True,
        old_progress_members_preserved=True,new_case_count=0,new_chat_count=0,training_started=False))
    print(json.dumps(dict(prepared=True,committed_chat_rows=obs['actual_chat_rows_committed'],
        checkpoint_sha256=proof['sha256'],old_progress_preserved=True,accepted_cases_unchanged=s['accepted_cases'],files=files)))
if __name__=='__main__':main()
