"""Record automatic cleanup rejection without retrying deletion."""
from pathlib import Path
from datetime import datetime,timezone
import json,zipfile

HERE=Path(__file__).resolve().parent
RUN=HERE/'cloud_publication/sgk_page_audit_20261019'
def read(p):return json.loads(p.read_text('utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def main():
    receipt_path=HERE/'cloud_publication/sgk_page_audit_20261020_publication_receipt.json'
    receipt=read(receipt_path)
    receipt['temporary_staging'].update(status='CLEANUP_REJECTED_BY_AUTOMATIC_POLICY_STAGING_REMAINS',rejection='blocked by policy; no more specific reason supplied',attempted_action='Remove-Item -LiteralPath exact verified run directory -Recurse -Force',rejected_utc=datetime.now(timezone.utc).isoformat(),retry_attempted=False)
    write(receipt_path,receipt)
    state=read(RUN/'publish_state.json')
    state['local_storage']['current_run_staging']=receipt['temporary_staging']
    write(RUN/'publish_state.json',state);write(HERE/'exhaustive_cloud_reference.json',state)
    context=HERE.parent/'MATH_TRAINING_CONTEXT.md'
    text=context.read_text('utf-8')
    note='\n\nCleanup checkpoint 20/10/2026: gói mới và cả bốn control đã raw-readback khớp toàn byte/hash. Lệnh dọn đệ quy đúng thư mục staging bị kiểm soát tự động từ chối với thông báo "blocked by policy", không có lý do chi tiết hơn. Không thử lệnh xóa khác để vượt chặn. Khoảng 65 MB staging còn tại thinking/cloud_publication/sgk_page_audit_20261019; dữ liệu chuẩn và evidence mới đã có trên Drive. Final publication receipt nhỏ ghi đầy đủ hash và trạng thái còn staging. Chưa train.\n'
    assert 'Cleanup checkpoint 20/10/2026:' not in text
    context.write_text(text+note,encoding='utf-8')
    cleanup_note=dict(status=receipt['temporary_staging']['status'],temporary_staging=receipt['temporary_staging'],training_started=False,bundle=receipt['bundle'])
    write(RUN/'cleanup_policy_status.json',cleanup_note)
    target=RUN/'publish_progress_index.zip';temp=RUN/'progress_cleanup_status.tmp.zip'
    replacements={'sgk_page_audit_20261019/publish_state.json':(RUN/'publish_state.json').read_bytes(),'sgk_page_audit_20261019/MATH_TRAINING_CONTEXT.md':context.read_bytes(),'sgk_page_audit_20261019/cleanup_policy_status.json':(RUN/'cleanup_policy_status.json').read_bytes()}
    with zipfile.ZipFile(target) as src,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as dst:
        for info in src.infolist():
            if info.filename not in replacements:dst.writestr(info,src.read(info.filename))
        for name,b in replacements.items():dst.writestr(name,b)
    with zipfile.ZipFile(RUN/'source_progress_index.zip') as old,zipfile.ZipFile(temp) as new:
        assert not new.testzip() and all(old.read(n)==new.read(n) for n in old.namelist())
    temp.replace(target)
    print(json.dumps(dict(cleanup_blocked=True,staging_bytes=receipt['temporary_staging']['bytes'],progress_state_context_staged_for_same_id_update=True)))
if __name__=='__main__':main()
