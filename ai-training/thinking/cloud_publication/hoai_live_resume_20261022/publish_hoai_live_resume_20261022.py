"""Publish observed Colab data-only progress without changing corpus rows."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import ast,json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/hoai_live_resume_20261022'
PREP=HERE/'cloud_publication/mcp_prepare_20261022'
MCP=Path.home()/'.codex/integrations/colab-mcp'
BASE=HERE/'data/primary_math_teacher_20261016'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8'))
def stdout(path,key=None,cell=None):
    result=read(path);assert not result['is_error']
    content=result['structured_content']
    outputs=content['outputs'] if cell is None else next(c for c in content['cells'] if c['id']==cell)['outputs']
    for o in outputs:
        if o.get('name')!='stdout':continue
        for line in ''.join(o['text']).splitlines():
            try:v=ast.literal_eval(line)
            except (ValueError,SyntaxError):continue
            if isinstance(v,dict) and (key is None or key in v):return v
    raise ValueError('Required actual output absent')
def main():
    names=['progress.zip','chat.json','context.md','state.json']
    for ref,name in zip(read(RUN/'prewrite_raw_verified.json'),names):
        b=(RUN/('prewrite_'+name)).read_bytes();assert len(b)==ref['bytes'] and sha(b)==ref['sha256']
    state=read(RUN/'prewrite_state.json');chat=read(RUN/'prewrite_chat.json')
    restore=stdout(MCP/'hoai_restore_observed4.json','checkpoint_sha256','Vao4Dg9FRbXL')
    assert restore['checkpoint_sha256']=='ce71cd2e8d0c4e891333acf336e22152a7092cd4d0a1a3d3f42cf1d8a2409bde'
    assert restore['source_versions_indexed']==1523689 and restore['members_complete']==190
    live=stdout(MCP/'hoai_live_actual_status_final.json','worker_alive')
    worker=live['stored_status'];checkpoint=worker['checkpoint'];snapshot=checkpoint['report_at_snapshot']
    assert live['worker_alive'] and worker['state']=='RUNNING_DATA_ONLY'
    assert checkpoint['id']==restore['checkpoint_id']=='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI'
    assert checkpoint['fresh_raw_readback_verified'] and snapshot['source_versions_indexed']>restore['source_versions_indexed']
    assert not worker['training_started'] and not snapshot['training_started']
    assert not worker['gpu_used'] and not worker['model_weights_loaded']
    assert worker['recipe_sha256']==state['latest_all_data_union_recipe']['sha256']==restore['recipe_sha256']
    review=read(PREP/'hoai_resume_peer_review.json')
    code=(PREP/'hoai_worker_resume_existing_v3.py').read_bytes()
    assert sha(code)==review['reviewed_source_sha256']==read(PREP/'hoai_worker_derivation.json')['derived_sha256']
    assert not review['findings']
    notebook=read(RUN/'notebook_remote_verified.json')
    assert notebook['fresh_raw_verified'] and notebook['all_mcp_sources_saved']
    pins={name:sha((BASE/name).read_bytes()) for name in ['owner_acceptance_policy.json','owner_human_attestations.json','owner_human_signoffs.jsonl','data_build_state.json','authoring_queue.json','supplementary_queue.json','coverage_adjudication_queue.json']}
    assert pins==read(HERE/'cloud_publication/data_resume_20261022/frozen_baseline_verified.json')['sha256']
    write(RUN/'frozen_baseline_verified.json',dict(sha256=pins,raw_source_unchanged=True,human_snapshot_rows=299))
    write(RUN/'restore_actual_receipt.json',restore)
    write(RUN/'worker_actual_observation.json',live)
    write(RUN/'checkpoint_actual_verified.json',checkpoint)
    for name in ['hoai_worker_resume_existing_v3.py','hoai_worker_derivation.json','hoai_resume_peer_review.json','hoai_restore_existing_v3.py','hoai_bootstrap_args.json','hoai_status_args.json','hoai_status_live_update_args.json','hoai_worker_diagnostic_args.json','hoai_cursor_probe_args.json','ANTIGRAVITY_DATA_HANDOFF_20261022.md','antigravity_prompt_remote_verified.json']:
        (RUN/name).write_bytes((PREP/name).read_bytes())
    for name in ['hoai_cpu_probe_run.json','hoai_auth_bootstrap_run.json','hoai_restore_observed4.json','hoai_live_actual_status_final.json','hoai_diagnostic_run.json','hoai_cursor_probe_run.json']:
        (RUN/name).write_bytes((MCP/name).read_bytes())
    for name in ['build_hoai_worker_resume.py','build_hoai_resume_args.py',Path(__file__).name]:
        (RUN/name).write_bytes((HERE/name).read_bytes())
    now=datetime.now(timezone.utc).isoformat()
    observation=dict(notebook_id=notebook['id'],chrome_profile='Hoai',transport='OFFICIAL_GOOGLE_COLAB_MCP',observed_utc=live['observed_utc'],worker_alive_at_observation=live['worker_alive'],runtime_status=worker['state'],checkpoint=checkpoint,restored_parent=restore,live_report=worker.get('report'),live_status_cell='oAVNfUYnTCHb',evidence_progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',evidence_member=RUN.name+'/worker_actual_observation.json',full_archive_audit_complete=False,TRAINING_DATASET_READY=False,training_started=False)
    state['data_only_colab_observation_history'].append(state['latest_colab_runtime_observation'])
    state['latest_colab_runtime_observation']=observation
    state['status']='FINITE_SGK_APPEND_ACCEPTED_FULL_ARCHIVE_AUDIT_RUNNING_DATA_ONLY'
    state['updated_utc']=now
    state['latest_data_only_notebook']=notebook
    handoff=dict(id='15gExlfFt7QM2tBcnY8vAwZd3Rn3RAzB-',sha256=sha((PREP/'ANTIGRAVITY_DATA_HANDOFF_20261022.md').read_bytes()),scope='FINITE_SGK_CONTENT_AUTHORING_AND_QA_SEPARATE_FROM_CODEX_ARCHIVE_AUDIT',prompt_prepared=True,external_agents_running_verified=False,global_control_writes_reserved_to_codex=True)
    state['external_data_authoring_handoff']=handoff
    chat['latest_colab_runtime_observation']=observation
    chat['external_data_authoring_handoff']=handoff
    assert state['accepted_cases']==1629858 and state['training_chat_rows']==6502088
    write(RUN/'publish_state.json',state);write(RUN/'publish_chat.json',chat)
    context=(RUN/'prewrite_context.md').read_text('utf8')
    marker='### Nhật ký 22/10/2026 — Chrome Hoai đã chạy lại audit thật qua MCP'
    assert marker not in context
    context+='\n\n'+marker+'\nCPU và xác thực Drive trên hồ sơ Hoai đã hoạt động. Khôi phục đúng checkpoint V3 ID16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI, 2321960960byte SHA256ce71cd2e8d0c4e891333acf336e22152a7092cd4d0a1a3d3f42cf1d8a2409bde trực tiếp vào Colab; toàn raw hash và SQLite quick_check đạt, metadata trước/sau không đổi. Bên trong đã có1523689source/190member,0chat; không reset/V2/nhâncheckpoint.\n'
    context+=f"Worker tiếp nối đúng một kernel, cùng ID checkpoint, kiểm thêm source. Snapshot mới đã raw streaming readback xác minh: {checkpoint['bytes']}byte SHA256{checkpoint['sha256']}; source={snapshot['source_versions_indexed']}, chat={snapshot['unique_chat_rows_processed']}, member={snapshot['members_complete']}/249. Quan sát runtime {live['observed_utc']}: worker_alive={live['worker_alive']}; đây là mốc quan sát, không bảo đảm máy sẽ chạy mãi. Tiếp theo dùng ô trạng thái oAVNfUYnTCHb, không chạy lại worker khi còn sống.\n"
    context+='Finding regression_only cũ vẫn giữ, không tự vào train; toàn kho chưa pass. Worker chỉ đọc/kiểm source-chat/hash/split/token, tokenizer pin5.16.1 và revision cũ; không weights/GPU/train. Header resume chỉ attach ID/hash đã xác minh, có peer static review gắn exact hash, không files.create; optimistic writer guard không phải khóa phân tán. Snapshot/code/status/peer/provenance được giữ trong PROGRESS/hoai_live_resume_20261022. Không thêm case/chat hoặc đổi 299signoff; core495/165 và queue SGK còn lại không tự đóng.\n'
    context+='Prompt Antigravity ID15gExlfFt7QM2tBcnY8vAwZd3Rn3RAzB- đã raw-verify, chỉ giao soạn/QA/xuất gói bổ sung; chưa xác minh agent ngoài đang chạy, không để bên ngoài ghi đè control/audit của Codex. Notebook cùng ID đã raw-readback nguồn các ô MCP; không tạo notebook mới. Bốn control cập nhật cùngIDs, STATE cuối; chỉ xác nhận sync sau rawreadback. TRAINING_DATASET_READY=false; không tuyên bố hoàn tất chuẩn bị/toàn SGK.\n'
    (RUN/'publish_context.md').write_bytes(context.encode('utf8'))
    (HERE.parent/'MATH_TRAINING_CONTEXT.md').write_bytes(context.encode('utf8'))
    excluded={'prewrite_progress.zip','prewrite_chat.json','prewrite_context.md','prewrite_state.json','publish_state.json','publish_chat.json','publish_context.md','publish_progress.zip','four_controls_remote_verified.json'}
    additions={p.name:p.read_bytes() for p in RUN.iterdir() if p.is_file() and p.name not in excluded}
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
        names=old.namelist();assert len(names)==len(set(names))
        for entry in old.infolist():new.writestr(entry,old.read(entry.filename))
        for name,b in additions.items():
            member=RUN.name+'/'+name;assert member not in names;new.writestr(member,b)
    with zipfile.ZipFile(RUN/'prewrite_progress.zip') as old,zipfile.ZipFile(RUN/'publish_progress.zip') as new:
        assert all(old.read(name)==new.read(name) for name in old.namelist())
        assert sha(new.read(RUN.name+'/worker_actual_observation.json'))==sha((RUN/'worker_actual_observation.json').read_bytes())
    write(RUN/'local_publication_receipt.json',dict(created_utc=now,checkpoint=checkpoint,live_observation_utc=live['observed_utc'],new_case_count=0,new_chat_count=0,old_progress_members_preserved=True,frozen_policy_and_source_hashes_unchanged=True,training_started=False))
    print(json.dumps(dict(source_at_verified_snapshot=snapshot['source_versions_indexed'],members_at_verified_snapshot=snapshot['members_complete'],new_case_count=0,training_started=False)))
if __name__=='__main__':main()
