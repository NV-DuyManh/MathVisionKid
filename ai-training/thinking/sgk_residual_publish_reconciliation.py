"""Publish additive accepted36 reconciliation to existing controls, zero data count delta."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,zipfile,hashlib
HERE=Path(__file__).resolve().parent;PUB=HERE/'cloud_publication';RUN=PUB/'sgk_residual_20261021';OLD=PUB/'sgk_completion_20261021'
def read(p):return json.loads(p.read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
def main():
    receipt=read(OLD/'four_controls_remote_verified.json');assert receipt['status']=='PASS_ALL_FOUR_CONTROL_RAW_BYTES'
    originals=[OLD/'publish_progress_index.zip',OLD/'publish_chat_manifest.json',OLD/'publish_state.json',HERE.parent/'MATH_TRAINING_CONTEXT.md']
    for p,ref in zip(originals,receipt['controls']):assert sha(p.read_bytes())==ref['sha256']
    assert read(HERE/'exhaustive_cloud_reference.json')==read(originals[2])
    state,chat=read(originals[2]),read(originals[1]);v=read(RUN/'reconciliation/validation.json')
    assert v['status']=='PASS' and v['accepted_cases_bound']==36 and v['remaining_global_master_tasks']==30
    assert state['accepted_cases']==1629781 and state['training_chat_rows']==6501780
    state.setdefault('sgk_accepted_reconciliation_history',[]).append(state['latest_sgk_accepted_reconciliation'])
    state['latest_sgk_accepted_reconciliation']=dict(progress_id='1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX',member=RUN.name+'/reconciliation/next_uncovered_tasks.json',sha256=sha((RUN/'reconciliation/next_uncovered_tasks.json').read_bytes()),bound_run=OLD.name,accepted_cases_bound=36,finite_text_tasks_discharged=15,global_master_tasks=30,partial_master_tasks=11,never_appended_missing_masters=19,asset_only_masters_separate=10,all_sgk_forms_covered=False)
    state['latest_sgk_prospective_reconciliation']['status']='SUPERSEDED_BY_ACCEPTED_RUN5_HASH_BINDING_ORIGINAL_PROJECTION_PRESERVED'
    state['updated_utc']=datetime.now(timezone.utc).isoformat()
    state['next_action']='Use accepted-hash-bound sgk_residual_20261021 exactqueue:30globaltasks (19unworked,11partial),10asset-only and91G2 dispositions retained. Finish substantive missing grade/constraint branches; full archive CPU token/source-link/split audit pending. No train.'
    state['TRAINING_DATASET_READY']=False
    write(RUN/'publish_state.json',state)
    chat['latest_finite_sgk_reconciliation']=state['latest_sgk_accepted_reconciliation']
    write(RUN/'publish_chat_manifest.json',chat)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md';text=re.sub(r'^<!-- CURRENT_CHECKPOINT[^\n]*-->\n','',context.read_text('utf8'))
    marker='### Nhật ký21/10/2026 — accepted36 reconciliation, remaining30'
    assert marker not in text
    text=f'<!-- CURRENT_CHECKPOINT {RUN.name}:1629781cases;6501780candidatechat;30globalmastertasks+10asset-only;preparation IN_PROGRESS;NO TRAINING. -->\n'+text
    text+=f'''\n\n{marker}\nRUN5 bundle đã cập nhật và freshraw đối chiếu đúng toànbyte/hash cả PROGRESS/chat/STATE/context. Dẫn xuất adjudication mới từ projection frozen: bind đủ36accepted source rowhash với parentdraft/rootQA7 và bundleID1yFKMT2AzRNZKr6IW9Gp2zTaBC_iMdj31.20candidate relations được đối chiếu;15finite text tasks đủ bằng chứng trong phạm vi cụ thể. Còn30globalmastertasks=19chưa cóappend+11partial, cùng10asset-only riêng. Hai master collection/dissection còn alias lớp4 hoặc3/4; vật liệu còn phạm vi thiết kế mở, không đóng chỉ bằng menu hữu hạn. Không mở rộng text thành năng lực đọc ảnh/thực hành.\n\nNguyên204candidate fields,315occurrences,167masters,91G2 giữ nguyên ngoài overlay/history; không xóa bài hoặc dữ liệu. Queue cũ45 và projection vẫn trong bundle cũ, gắn parenthash trong dẫn xuất mới. Không tăng case/chat lần nữa:1629781case/6501780candidatechat,6501892includingeval/audit.495core/165node vẫn đủ. Bộchuẩn bị chưafinal;fullarchiveaudit và các nhánh SGK cụ thể còn tiếp. Không train/GPU/weights/paidAPI/app.\n\nMapping/code/evidence lưu bổ sung trong PROGRESS cùngID, không tạo bundle/fileDrive mới hoặc nhânpayload36. Latestunion35payloads/29chatmembers giữ nguyên, notebookdata-only7cells chưa chạyColab. Bốn control cập nhật đúngIDs với STATE cuối và chỉ xác nhận sync sau freshrawreadback.\n'''
    context.write_text(text,encoding='utf8')
    write(RUN/'publication_scope.json',dict(schema='accepted_sgk_reconciliation_publication.v1',accepted_case_delta=0,chat_row_delta=0,accepted_cases=1629781,candidate_chat_rows=6501780,finite_text_tasks_discharged=15,global_master_tasks_remaining=30,asset_only_masters_separate=10,full_archive_audit_complete=False,training_started=False,all_sgk_forms_covered=False,parent_four_control_receipt_sha256=sha((OLD/'four_controls_remote_verified.json').read_bytes())))
    with zipfile.ZipFile(originals[0]) as old,zipfile.ZipFile(RUN/'publish_progress_index.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as new:
        for info in old.infolist():new.writestr(info,old.read(info.filename))
        for p in sorted((RUN/'reconciliation').glob('*.json')):new.writestr(RUN.name+'/reconciliation/'+p.name,p.read_bytes())
        for p in [RUN/'publish_state.json',RUN/'publish_chat_manifest.json',RUN/'publication_scope.json']:new.writestr(RUN.name+'/'+p.name,p.read_bytes())
        for n in ['sgk_residual_reconcile_run5.py','sgk_residual_publish_reconciliation.py']:new.writestr(RUN.name+'/code/'+n,(HERE/n).read_bytes())
        new.writestr(RUN.name+'/MATH_TRAINING_CONTEXT.md',context.read_bytes())
    with zipfile.ZipFile(originals[0]) as old,zipfile.ZipFile(RUN/'publish_progress_index.zip') as new:
        assert len(new.namelist())==len(set(new.namelist())) and not new.testzip()
        assert all(old.read(n)==new.read(n) for n in old.namelist())
    print(json.dumps(read(RUN/'publication_scope.json')))
if __name__=='__main__':main()

