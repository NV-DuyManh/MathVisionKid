"""Build replacement of the existing Drive data-only Colab notebook."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
OUT=HERE/'cloud_publication/sgk_completion_20261021/notebook'
def cell(kind,text):
    return dict(cell_type=kind,metadata={},source=text.splitlines(keepends=True),**(dict(execution_count=None,outputs=[]) if kind=='code' else {}))
def main():
    bootstrap=(HERE/'math_data_drive_bootstrap.py').read_text('utf-8')
    intro="""# MathVisionKid — chuẩn bị toàn bộ dữ liệu trên Colab

Notebook đọc toàn bộ member ứng viên được công bố theo STATE/PROGRESS và hash, gồm mọi gói bổ sung. Gói cân bằng nhỏ cũ giữ làm lịch sử/diagnostic, không dùng thay toàn kho.

Chỉ kiểm dữ liệu: không weights, trainer, GPU hoặc huấn luyện. Đăng nhập tài khoản có quyền đọc cùng ID Drive. Payload tạm nằm trong runtime Colab, tối đa một payload cache mỗi lúc, không tải kho về máy cá nhân.

Mỗi lần xử lý một đoạn tiếp nối; chạy tiếp sẽ tới các dòng/member chưa xử lý, không chọn tập nhỏ cố định. Train/validation/test giữ split gốc; sealed/pilot/challenge và history không tự vào train. Tổng candidate chưa phải tổng train-only đã kiểm. Full archive token/linkage/split audit vẫn pending.
"""
    setup="""from google.colab import auth
auth.authenticate_user()
import google.auth
from googleapiclient.discovery import build
from pathlib import Path
import json,sys,sqlite3,hashlib
credentials, _ = google.auth.default()
drive_api = build('drive','v3',credentials=credentials,cache_discovery=False)
ROOT = Path('/content/mathvisionkid_data_only')
ROOT.mkdir(parents=True,exist_ok=True)
"""
    setup+="exec(compile("+repr(bootstrap)+", 'math_data_drive_bootstrap.py', 'exec'), globals())\n"
    setup+="""reader = GoogleDriveReader(drive_api)
state,recipe,recipe_pointer = latest_controls(reader)
code_receipt = bootstrap_code(reader,state,ROOT/'code')
sys.path.insert(0,str(ROOT/'code'))
from math_data_candidate_stream import CandidateStream,DataOnlyConsumer
from exhaustive_colab_loader import load_qwen_tokenizer,tokenize_assistant_only
print(scope_receipt(state,recipe,recipe_pointer))
"""
    run="""FOLDER_ID='19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
SPLIT='train'  # Chỉ đổi rõ thành validation/test khi cần kiểm split đó.
ROWS_PER_RUN=20000  # Đoạn công việc tiếp nối, không chọn tập train cố định.
TOKENIZE=True  # Chỉ tokenizer pinned, không model weights.
cache=LazyDriveCache(reader,recipe,ROOT/'payload_cache')
stream=CandidateStream(recipe,cache,split=SPLIT)
checkpoint_name=f'MathVisionKid_DATA_ONLY_{SPLIT}_{stream.identity[:24]}.sqlite'
query=f"'{FOLDER_ID}' in parents and name = '{checkpoint_name}' and trashed = false"
matches=drive_api.files().list(q=query,fields='files(id,name,size,appProperties)',supportsAllDrives=True,includeItemsFromAllDrives=True).execute().get('files',[])
if len(matches)>1:
    raise RuntimeError('Checkpoint trùng tên: giữ nguyên tất cả, cần xác định ID trước khi tiếp.')
checkpoint_ref=matches[0] if matches else None
DB=ROOT/checkpoint_name
if not DB.exists() and checkpoint_ref:
    raw_db=reader.read(checkpoint_ref['id'],int(checkpoint_ref['size']))
    pin=checkpoint_ref.get('appProperties',{}).get('data_sha256')
    if not pin or hashlib.sha256(raw_db).hexdigest()!=pin:
        raise RuntimeError('Checkpoint thiếu hoặc sai hash; không tự khởi tạo lại.')
    DB.write_bytes(raw_db)
consumer=DataOnlyConsumer(DB,stream)
tokenizer=load_qwen_tokenizer() if TOKENIZE else None
span={'rows':0,'max_sequence_tokens':0,'max_completion_tokens':0,'source_links_not_reverified_here':0}
def data_only_check(row,provenance):
    if tokenizer is not None:
        item=tokenize_assistant_only(row,tokenizer)
        span['max_sequence_tokens']=max(span['max_sequence_tokens'],len(item['input_ids']))
        span['max_completion_tokens']=max(span['max_completion_tokens'],item['completion_tokens'])
    span['rows']+=1
    if provenance.get('sourcehash_origin')!='ORIGINAL_FIELD_VERIFIED_AGAINST_PINNED_SOURCE_MEMBER':
        span['source_links_not_reverified_here']+=1
try:
    progress=consumer.consume(data_only_check,max_rows=ROWS_PER_RUN)
finally:
    consumer.close()
print({'progress':progress,'this_work_span_only':span,'full_archive_linkage_split_audit_complete':False,'training_started':False})
"""
    checkpoint="""# Lưu cùng ID sau khi xử lý thành công và SQLite đã đóng.
from googleapiclient.http import MediaFileUpload
checkpoint_sha=hashlib.sha256(DB.read_bytes()).hexdigest()
properties={'data_sha256':checkpoint_sha,'recipe_identity':stream.identity,'split':SPLIT,'purpose':'DATA_ONLY_NO_TRAINING'}
if checkpoint_ref:
    fresh=drive_api.files().get(fileId=checkpoint_ref['id'],fields='id,appProperties',supportsAllDrives=True).execute()
    if fresh.get('appProperties',{}).get('data_sha256')!=checkpoint_ref.get('appProperties',{}).get('data_sha256'):
        raise RuntimeError('Checkpoint đã được cập nhật; không ghi đè tiến độ mới.')
    checkpoint_result=drive_api.files().update(fileId=checkpoint_ref['id'],body={'appProperties':properties},media_body=MediaFileUpload(str(DB),mimetype='application/vnd.sqlite3',resumable=True),fields='id,name,size,appProperties',supportsAllDrives=True).execute()
else:
    checkpoint_result=drive_api.files().create(body={'name':checkpoint_name,'parents':[FOLDER_ID],'appProperties':properties},media_body=MediaFileUpload(str(DB),mimetype='application/vnd.sqlite3',resumable=True),fields='id,name,size,appProperties',supportsAllDrives=True).execute()
verified_db=reader.read(checkpoint_result['id'],int(checkpoint_result['size']))
if hashlib.sha256(verified_db).hexdigest()!=checkpoint_sha:
    raise RuntimeError('Raw readback checkpoint không khớp; không tuyên bố lưu thành công.')
checkpoint_ref=checkpoint_result
receipt={'checkpoint_id':checkpoint_result['id'],'checkpoint_sha256':checkpoint_sha,'progress':progress,'this_work_span_only':span,'training_started':False,'TRAINING_DATASET_READY':False,'full_archive_token_linkage_split_audit_complete':False}
(ROOT/'last_data_only_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(receipt)
"""
    cells=[cell('markdown',intro),cell('code','# Chỉ thư viện tokenizer đã pin từ pipeline.\n%pip -q install transformers==5.16.1\n'),cell('code',setup),
      cell('markdown','Checkpoint chỉ chứa tiến độ/hash/ID. Mỗi recipe/split dùng một SQLite trong thư mục Drive gốc, chạy lại cập nhật cùng ID. Chỉ một notebook ghi mỗi lúc; SQLite không là khóa phân tán Drive. Recipe thay đổi cần chuyển checkpoint append-only, không xóa bản cũ để ép chạy.\n'),
      cell('code',run),cell('code',checkpoint),cell('markdown','Runtime mất kết nối: chạy lại để tải checkpoint đúng ID/hash và tiếp nối. stream_exhausted chỉ chứng minh đọc hết member của split/recipe này; không tự chứng minh mọi nguồn liên kết đúng hoặc các split độc lập. Cần source–chat/group/question/canonical audit theo queue trước công bố sẵn sàng train. Không đổi split hoặc bỏ bài hợp lệ để qua gate. Notebook chưa được chạy trên Colab trong phiên chuẩn bị này.\n')]
    for c in cells:
        if c['cell_type']=='code':
            ast.parse(''.join(s for s in c['source'] if not s.lstrip().startswith('%')))
    doc=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python'),accelerator='none',mathvisionkid=dict(training_started=False,full_archive_audit_complete=False,selection='ALL_DECLARED_CANDIDATE_MEMBERS',fixed_existing_notebook_id='1TeCoP57miKmhESZVKWFqD-XqZmQd5u4l')),nbformat=4,nbformat_minor=5)
    OUT.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode()
    (OUT/'MathVisionKid_DATA_ONLY_COLAB.ipynb').write_bytes(raw)
    receipt=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),cells=len(cells),code_cells_syntax_checked=True,cloud_runtime_executed=False,training_started=False,full_archive_audit_complete=False,bootstrap_helper_sha256=hashlib.sha256(bootstrap.encode()).hexdigest(),old_notebook_preserved=True)
    (OUT/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
if __name__=='__main__':main()

