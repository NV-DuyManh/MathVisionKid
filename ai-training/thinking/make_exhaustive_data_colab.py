"""Create the data-only notebook for the small balanced release ZIP on Drive."""
import json
from pathlib import Path


def make_notebook(path):
    cells = []
    def add(kind, text):
        cell = {"cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)

    add("markdown", """# MathVisionKid — kiểm dữ liệu trên Colab
Notebook chỉ tải gói training view cân bằng nhỏ từ **đúng thư mục Drive hiện có**. Không tải 14 phần corpus, không tải model weights, không khởi chạy GPU hay huấn luyện. Các shard cũ vẫn được giữ nguyên trên Drive. Mã loader, manifest và dữ liệu nằm trong ZIP; notebook mở ZIP vào vùng tạm của Colab, không vào máy cá nhân.

Chạy các ô theo thứ tự. Đăng nhập tài khoản có quyền đọc thư mục nguồn khi Colab yêu cầu. Hai tập validation/test là dữ liệu mới dành riêng để đánh giá, đã cô lập khỏi train theo nhóm, câu hỏi và phép tính canonical. Sealed challenge cũ không được đọc. Kết quả kiểm này không phải độ chính xác của model.
""")
    add("code", """# Chỉ cài thư viện tokenizer theo phiên bản đã kiểm; không cài trainer.
%pip -q install transformers==5.16.1
""")
    add("code", """from google.colab import auth
auth.authenticate_user()
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pathlib import Path
import hashlib, io, json, sys, zipfile

FOLDER_ID = '19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n'
BUNDLE_NAME = 'MathVisionKid_BALANCED_COLAB_BUNDLE.zip'
credentials, _ = google.auth.default()
drive_api = build('drive', 'v3', credentials=credentials, cache_discovery=False)
matches = drive_api.files().list(
    q=f"'{FOLDER_ID}' in parents and name = '{BUNDLE_NAME}' and trashed = false",
    fields='files(id,name,size,md5Checksum)', supportsAllDrives=True,
    includeItemsFromAllDrives=True).execute().get('files', [])
if len(matches) != 1:
    raise RuntimeError(f'Cần đúng một gói {BUNDLE_NAME}; tìm thấy {len(matches)}.')
remote = matches[0]
if int(remote['size']) > 100 * 1024 * 1024:
    raise RuntimeError('Gói cân bằng vượt giới hạn tạm 100 MiB; không tải toàn bộ corpus.')
buffer = io.BytesIO()
download = MediaIoBaseDownload(buffer, drive_api.files().get_media(fileId=remote['id']), chunksize=1024*1024)
done = False
while not done:
    _, done = download.next_chunk(num_retries=3)
raw = buffer.getvalue()
if len(raw) != int(remote['size']) or hashlib.md5(raw).hexdigest() != remote['md5Checksum']:
    raise RuntimeError('Byte/hash của gói vừa tải không khớp Drive.')
ROOT = Path('/content/mathvisionkid_selected_data')
ROOT.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    for member in archive.infolist():
        target = (ROOT / member.filename).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            raise RuntimeError('Đường dẫn ZIP không an toàn.')
    archive.extractall(ROOT)
RELEASE = ROOT / 'balanced_release'
sys.path.insert(0, str(RELEASE))
from exhaustive_colab_loader import (
    ManifestStream, load_qwen_tokenizer, full_token_audit,
    tokenized_stream, save_json, asdict, pad_batch)
print('Đã mở gói nhỏ', remote['id'], 'SHA256', hashlib.sha256(raw).hexdigest())
""")
    add("code", """manifest = json.loads((RELEASE / 'MathVisionKid_BALANCED_TRAINING_MANIFEST.json').read_text('utf-8'))
if not manifest.get('TRAINING_DATASET_READY'):
    raise RuntimeError('Manifest chưa được công bố train-ready.')
stream = ManifestStream(manifest, RELEASE)
tokenizer = load_qwen_tokenizer()  # Chỉ tokenizer chính thức, revision được cố định.
receipt = full_token_audit(stream, tokenizer)
expected = json.loads((RELEASE / 'qwen_full_selected_token_audit.json').read_text('utf-8'))
for key in ('unique_samples', 'unique_cases', 'selected_rows_sha256', 'max_sequence_tokens',
            'max_completion_tokens', 'by_mode', 'by_split'):
    if receipt[key] != expected[key]:
        raise RuntimeError(f'Kiểm toán lại khác bản công bố: {key}')
save_json(ROOT / 'colab_fresh_token_audit.json', receipt)
print({k:v for k,v in receipt.items() if not k.endswith('histogram')})
""")
    add("code", """# Smoke test và resume ở dòng CHƯA tiêu thụ tiếp theo. Không chạy training.
cursor_path = ROOT / 'loader_consumer_cursor.json'
cursor = json.loads(cursor_path.read_text('utf-8')) if cursor_path.exists() else None
train_stream = stream.for_split('train')
iterator = tokenized_stream(train_stream, tokenizer, cursor)
item, next_cursor = next(iterator)
batch = pad_batch([item])
assert len(batch['input_ids'][0]) == len(batch['labels'][0])
print(item['sample_id'], item['split'], len(item['input_ids']))
save_json(cursor_path, asdict(next_cursor))  # Chỉ ghi cursor sau khi xử lý thành công.
iterator.close()
resumed = tokenized_stream(train_stream, tokenizer, json.loads(cursor_path.read_text('utf-8')))
following, following_cursor = next(resumed)
assert following['sample_id'] != item['sample_id']
resumed.close()
print('Streaming/resume và mask đạt; không khởi chạy huấn luyện.')
""")
    notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                "nbformat": 4, "nbformat_minor": 5}
    Path(path).write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return notebook


if __name__ == "__main__":
    make_notebook(Path(__file__).parent / 'cloud_publication/resume_20261018/MathVisionKid_DATA_ONLY_COLAB.ipynb')
