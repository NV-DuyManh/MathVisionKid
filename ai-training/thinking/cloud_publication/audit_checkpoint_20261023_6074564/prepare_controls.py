"""Append an actual fresh checkpoint proof without changing any dataset rows."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def load(n):return json.loads((R/n).read_bytes())
def save(n,v):(R/n).write_bytes((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
proofs=load('parent_controls_raw_verified.json')
for p in proofs:
    ext={'progress':'.zip','context':'.md','state':'.json','chat':'.json'}[p['kind']]
    b=(R/('parent_'+p['kind']+ext)).read_bytes()
    assert p['fresh_raw_readback_verified'] and len(b)==p['bytes'] and sha(b)==p['sha256']
o=load('runtime_observation.json');cp=o['checkpoint'];report=cp['report_at_snapshot']
assert o['worker_alive'] and o['final_metadata_alive'] and o['worker_error'] is None
assert cp['id']=='16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI' and cp['fresh_raw_readback_verified']
assert cp['sha256']=='013585962eb850fcdd0d6f9031e788a9c9bfb47441169328227bd76499dbf33e' and cp['bytes']==8680194048
assert report['identity']=='f0332df91020ace0fc48d88491fe97364d08826458d08c71ba4ec60524e25863'
assert report['unique_chat_rows_processed']==report['physical_chat_occurrences_processed']==6074564
assert report['source_versions_indexed']==1629906 and report['issues']=={'SOURCE_CHAT_LINKAGE_UNVERIFIED':60,'SOURCE_RAW_HASH_NOT_FOUND':60,'SOURCE_SPLIT_MISSING_OR_UNKNOWN':1}
assert not report['TRAINING_DATASET_READY'] and not report['training_started']
assert o['unique_chat_rows_processed']==o['committed_physical_chat_rows']>=6074564
s=load('parent_state.json');c=load('parent_chat.json')
assert s['accepted_cases']==1629922 and s['training_chat_rows']==6502344
assert s['owner_requested_pause']['active'] is False and s.get('pending_checkpoint_append') is None
member='audit_checkpoint_20261023_6074564/runtime_observation.json'
latest=dict(s['latest_colab_runtime_observation'],observed_utc=o['observed_utc'],
    runtime_status=o['worker_state'],worker_alive_at_observation=True,checkpoint=cp,
    committed_physical_chat_rows=o['committed_physical_chat_rows'],unique_chat_rows_committed=o['unique_chat_rows_processed'],
    last_verified_checkpoint_unique_chat_rows=6074564,current_issues=report['issues'],evidence_member=member)
for control in (s,c):
    control.setdefault('verified_v3_checkpoint_history',[]).append(deepcopy(control.get('latest_verified_v3_checkpoint')))
    control['latest_verified_v3_checkpoint']=cp
    control.setdefault('data_only_colab_observation_history',[]).append(deepcopy(control['latest_colab_runtime_observation']))
    control['latest_colab_runtime_observation']=latest
    control.setdefault('performance_decision',{}).update(
        bounded_read_cache_registered=True,bounded_read_cache_kib=1048576,
        read_cache_evidence_member='audit_checkpoint_20261023_5036356/read_cache_registered.json',
        status_report_cache_registered=True, status_report_cache_evidence_member='audit_checkpoint_20261023_5563144/status_cache_registered_corrected.json',
        scanner_adapter_files_changed=False,onepass_optimizer_applied=False)
    control['TRAINING_DATASET_READY']=False;control['training_started']=False
s['updated_utc']=datetime.now(timezone.utc).isoformat()
s['status']='FULL_CURRENT_ARCHIVE_AUDIT_RUNNING_STRUCTURAL15_ADAPTER_PENDING'
for control in (s,c):
    control['pending_structural15_adapter']={'status':'EXACT_HASH_BOUND_READ_TIME_ADAPTER_PREPARED_NOT_MERGED','bindings_sha256':'95d9fbf8536b908a6456256d8ff04175e8bd017cd34a406e190513844d316e87','source_cases':15,'chat_rows':60,'complete_builder_message_replays_verified':60,'messages_and_normalized_groups_preserved':True,'source_chat_payload_bytes_changed':0,'binding_evidence_member':'audit_checkpoint_20261023_6074564/bindings.json','new_human_signoffs':0,'held_two_field_artifact':'1DtwpVgFAiyyOIHxgFbQgnlDGWr75m6DQ','held_artifact_status':'NOT_SELECTED_DO_NOT_MERGE_GROUP_POLICY_WOULD_CHANGE'}
marker='### Nhật ký 23/10/2026 — checkpoint 6074564 chat đã raw-readback'
parent_context=(R/'parent_context.md').read_bytes();assert marker.encode() not in parent_context
delta=(f'\n\n{marker}\n'
       f'Worker CPU duy nhất tiếp tục từ checkpoint đã dừng, không sinh hoặc nhập lại lô. Đã lưu cùngID{cp["id"]} snapshot{cp["bytes"]}byte SHA256{cp["sha256"]}; fresh streaming raw readback khớp đủbyte/hash, report tại snapshot có6074564unique/physicalchat và1629906sourceversions. Raw parent findings hiện gồm regression_only1 và hash/linkage60+60; chưa fullscan, chưa train.\n'
       f'Quan sát{o["observed_utc"]}: worker đang chạy, đã commit{o["committed_physical_chat_rows"]}chat; uniqueCOUNT thực{o["unique_chat_rows_processed"]}, thread chốt metadata còn đợi đúng worker. Mốc đã lưu an toàn riêng6074564, không nhập nhằng với phần mới chỉ commit trong runtime.\n'
       'Tại cuối shard7, auditor V3 cũ ghi60 SOURCE_RAW_HASH_NOT_FOUND và60 SOURCE_CHAT_LINKAGE_UNVERIFIED cho15bài structural. Đã đọc đúng60chat, đối chiếu exact source canonical SHA với source_row_sha256/row_sha256 trên tất cả60; hash chuẩn hóa khớp hoàn toàn, còn rawlineSHA khác định dạng serialize. Phản hồi khớp đủsourceprojection trừcase_group: exporter chủ động tạo nhóm math_/text_ khác sourceID. Đã replay thật chat_records từ15source; toàn60system/user/assistant messages vànormalizedgroups khớp hash. QA7tiêu chí của15rawsource cóPASS_WITH_SCOPE_LIMITS, khôngtạo human signoff.\n'
       'Một bản dẫn xuất2trường đã chuẩn bị/upload20MBnhưngKHÔNGchọn hoặc gộp vì thaycanonicalgroup không phù hợp chính sách chia nhóm. Giữ artifact1DtwpVgFAiyyOIHxgFbQgnlDGWr75m6DQ nhưhistory; latestrecipe vẫn nguyênSHA1bb69c394c7eaaea7034125c6b3361eebbbe0d77e0715a8454331fbe7cee3ff8. Đang tạo adapter chỉ đọc exact15hash để giữ toànbộsource/chat/group gốc, phân biệtraw/canonicalSHA. Phảiđợi fullparent scan, giữ snapshotparentfrozen, tạochildDBriêng cóhistory rồi chạy lại60rowqua originalgates/tokenizer trướcchấpnhận. Không bỏgates hoặc xóa findings cũ.\n'
       'Giữ495core/165node/1980chat,299human exact-hash signoff, recipe/hash hiện hành và toàn bộ dữ liệu/history. Tổng candidate vẫn6502344chat; allsplitraw6502392. Năm task quan sát thật/7constraints,10assetmasters,1locatorG3 giữpending; chưa chứng nhận toànSGK/pháp lý hoặcTRAINING_DATASET_READY. Khôngtrain/GPU/weights/paidAPI/app/commit/push.\n'
       'PROGRESS/chat/context/state cùngIDs, state ghi cuối và đọc raw so byte/hash trước khi xác nhận sync.\n')
(R/'context_delta.txt').write_bytes(delta.encode());(R/'next_context.md').write_bytes(parent_context+delta.encode())
save('next_state.json',s);save('next_chat.json',c)
with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as new:
    assert len(old.namelist())==len(set(old.namelist()))
    for info in old.infolist():new.writestr(info,old.read(info.filename))
    for name in ['prepare_controls.py','runtime_observation.json','parent_controls_raw_verified.json','bindings.json','structural15_semantic_review.json','linkage60_crosswalk.json','derived_artifact_remote_verified.json','context_delta.txt']:
        member='audit_checkpoint_20261023_6074564/'+name;assert member not in old.namelist();new.writestr(member,(R/name).read_bytes())
with zipfile.ZipFile(R/'parent_progress.zip') as old,zipfile.ZipFile(R/'next_progress.zip') as new:
    assert all(old.read(n)==new.read(n) for n in old.namelist())
    assert len(new.namelist())==len(set(new.namelist()))
ids={p['kind']:p['id'] for p in proofs};prepared={}
for kind,ext in [('progress','.zip'),('chat','.json'),('context','.md'),('state','.json')]:
    p=R/('next_'+kind+ext);b=p.read_bytes();prepared[kind]={'id':ids[kind],'path':str(p),'bytes':len(b),'sha256':sha(b)}
save('prepared_control_updates.json',{'controls':prepared,'state_must_be_written_last':True,'new_case_count':0,'new_chat_count':0,'training_started':False})
print(json.dumps({'prepared':True,'checkpoint_unique_chat_rows':6074564,'controls':prepared}))
