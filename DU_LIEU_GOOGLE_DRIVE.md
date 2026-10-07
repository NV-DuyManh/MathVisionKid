# Dữ liệu MathVision Kids trên Google Drive

**Code và các thành phần chạy app ở máy; ảnh nguồn và tài liệu kiểm thử ít dùng ở Drive.** Không cần tải toàn bộ dữ liệu xuống để mở app hoặc nhận diện một batch mới.

Tài liệu này dành cho người tiếp quản dự án và các trợ lý AI. Bắt đầu tại thư mục gốc của repo. Cài và chạy app theo [hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md); phần dưới giải thích cách tìm và khôi phục dữ liệu riêng.

## Dữ liệu nằm ở đâu?

| Thành phần | Vị trí và cách dùng |
| :--- | :--- |
| Code, logo/ảnh giao diện, model đang dùng, thư viện và mẫu kiểm thử runtime | Giữ ở thư mục dự án. App cần đọc nhanh và ổn định. |
| Ảnh nguồn OCR | Đọc qua ổ Google Drive đã mount. `ai-training/datasets/drive_math/storage_sources.json.gz` là chỉ mục riêng của máy, ánh xạ 83.733 định danh nguồn sang file, thành viên ZIP hoặc dòng ảnh trong Parquet. |
| ZIP nguồn và ảnh tham chiếu | `G:\My Drive\Dự án\MathVisionKid\Dữ liệu OCR\Nguồn`. Giữ cả bản ZIP đầy đủ và bản đã lọc. |
| Bộ dữ liệu chia sẻ C1SE.01 | Shortcut trong thư mục MathVisionKid. Đường dẫn thực có thể ở `G:\.shortcut-targets-by-id\...\C1SE.01`; file `.lnk` không phải thư mục ảnh. |
| Nhãn, kết quả cloud, danh sách ảnh đã chọn, helper, chỉ mục nguồn và lịch sử ảnh đã test | Bản đang dùng giữ tại `ai-training/datasets/drive_math`. Đây là dữ liệu riêng, không có đầy đủ trên Git. |
| Preview, kết quả local/baseline cũ, inventory lớn và chứng cứ lịch sử | ZIP lưu trữ trong [thư mục Drive riêng](https://drive.google.com/drive/folders/1oOenOCeNdsHRprk3c8yNNmdp9ZYRE2Lh), tương ứng `G:\My Drive\Dự án\MathVisionKid\Lưu trữ`. Khôi phục phần cần dùng trước khi mở hoặc chạy lại công cụ cũ. |

Danh mục [docs/drive-archives.json](docs/drive-archives.json) ghi ID, tên ZIP, SHA-256, dung lượng và số file. Mỗi ZIP chứa `_ARCHIVE_MANIFEST.json` với đường dẫn gốc, hash, dung lượng và thời gian sửa của từng file. Không suy ra tên ZIP từ ID; dùng helper đọc danh mục.

## Người mới vào dự án

1. Xin chủ dự án quyền truy cập thư mục Drive riêng và bộ dữ liệu C1SE.01. Tài khoản đăng nhập phải thấy đúng các thư mục đó; không cần đổi chia sẻ thành công khai.
2. Cài Google Drive for desktop, chọn **Stream files**, rồi mở ổ Drive trong File Explorer. Không chọn **Mirror files** hoặc đánh dấu toàn bộ dataset **Available offline**.
3. Cài môi trường theo [hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md): Windows/PowerShell, Python 3.12, Node.js 22.13+, JDK 21 và Docker Desktop. Model weights và API key cần chủ dự án cung cấp riêng.
4. Chỉ nếu cần tiếp tục kiểm thử OCR trên **bản clone mới có thư mục dataset trống**, khôi phục metadata riêng và ledger như dưới đây. Không làm bước này đè lên dự án đang có lịch sử kiểm thử mới hơn.

```powershell
py -3 .\scripts\data\restore_drive_archive.py --list
py -3 .\scripts\data\restore_drive_archive.py --id private-metadata-20261007
py -3 .\scripts\data\restore_drive_archive.py --id ledger-backup-20261007
```

Ledger được khôi phục vào `ai-training/datasets/drive_math/ledger.sqlite3`. Đây là snapshot SQLite nhất quán, giúp nhận biết ảnh đã test để tránh chạy lặp. Snapshot có thể khác byte với ledger đang có dù cùng nội dung; nếu helper báo xung đột, **dừng và kiểm tra**, không xóa ledger hiện tại để vượt qua lỗi.

Các đường dẫn nguồn trong chỉ mục riêng có thể gắn với ổ G và shortcut trên máy chủ dự án. Nếu máy khác mount sang ổ khác hoặc đổi thư mục nguồn, phải kiểm tra và xác minh lại ánh xạ theo hash trước khi chạy audit. `--drive-root` bên dưới chỉ đổi nơi tìm ZIP lưu trữ; nó không tự sửa chỉ mục ảnh nguồn.

Nếu chỉ muốn chạy app, không cần khôi phục hàng trăm nghìn file kiểm thử:

```powershell
.\RUN_MATHVISION.bat
```

Mở Docker Desktop trước. Giữ terminal của launcher để quét QR và test điện thoại; xem [hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md) để cấu hình nhận diện thật.

## Lấy lại đúng phần cần dùng

Helper [scripts/data/restore_drive_archive.py](scripts/data/restore_drive_archive.py) chỉ dùng thư viện chuẩn Python. `--list` đọc danh mục local, không cần Drive đang mount và không giải nén ảnh.

Ví dụ cần xem lại batch `new2_20261006_84`:

```powershell
$batchPath = 'ai-training/datasets/drive_math/new2_20261006_84'
py -3 .\scripts\data\restore_drive_archive.py --id audit-results-20261007 --prefix $batchPath
py -3 .\scripts\data\restore_drive_archive.py --id review-images-20261007 --prefix $batchPath
```

`--prefix` là đường dẫn tương đối từ gốc repo, dùng dấu `/`. Chọn một batch, thư mục con hoặc một file cụ thể. Bỏ `--prefix` sẽ khôi phục toàn bộ ZIP và cần đủ dung lượng trống; nội dung được kiểm tra trong vùng tạm trước khi đưa về đường dẫn gốc.

Nếu Drive mount thành ổ H:

```powershell
py -3 .\scripts\data\restore_drive_archive.py --id review-images-20261007 `
  --prefix 'ai-training/datasets/drive_math/new2_20261006_84/review_sheets' `
  --drive-root 'H:\My Drive\Dự án\MathVisionKid\Lưu trữ'
```

Có thể dùng `--repo-root 'D:\MathVisionKid'` nếu chạy helper từ nơi khác. Thư mục đích phải có `docs/drive-archives.json`. Để kiểm tra một bản backup đang xung đột, tạo thư mục khôi phục riêng, chép danh mục vào thư mục `docs` của nó, rồi dùng `--repo-root` trỏ đến đó; giữ nguyên dữ liệu đang dùng.

Helper xác minh SHA-256 của cả ZIP trước khi khôi phục, kiểm tra từng file, giữ thời gian sửa gốc, bỏ qua file local giống hệt và **không ghi đè file khác nội dung**. Đường dẫn thoát khỏi repo, symlink hoặc junction tại đích đều bị từ chối. Không tự giải nén rồi chép đè để né những kiểm tra này.

| ID lưu trữ | Khi nào cần khôi phục? |
| :--- | :--- |
| `audit-results-20261007` | Kết quả local, baseline và manifest kết quả. Cần trước khi so sánh hoặc tiếp tục audit lịch sử để tránh tính lại. |
| `review-images-20261007` | Overlay, review sheet, crop và ảnh phục vụ kiểm tra. Cần trước khi mở ảnh review hoặc chạy lại công cụ tạo sheet/probe cũ. |
| `history-20261007` | Inventory lớn, danh sách alias và dữ liệu acquisition lịch sử. Cần cho báo cáo coverage/integrity cũ. |
| `evidence-20261007` | Chứng cứ và đầu ra chẩn đoán theo ngày. Cần khi truy vết các lần sửa/test trước. |
| `scratch-20261007` | Ảnh và bản export thử nghiệm ít dùng. Không cần cho app đang chạy. |
| `parquet-tools-20261007` | Bản thư viện Parquet độc lập cũ. Chỉ cần cho extractor lịch sử phụ thuộc bản này; bộ đọc hiện tại dùng `pyarrow` trong venv. |
| `handoff-20261007` | Gói bàn giao và bản sao cũ. Chỉ khôi phục khi thực sự cần kiểm tra chúng. |
| `private-metadata-20261007` | Backup nhãn, kết quả cloud, danh sách chọn, helper và chỉ mục riêng. Dùng cho bản clone mới hoặc phục hồi riêng. Bản đang dùng vẫn giữ local. |
| `ledger-backup-20261007` | Backup lịch sử ảnh đã test. Dùng cho dataset mới trống hoặc thư mục phục hồi riêng. Ledger hiện tại vẫn giữ local. |
| `storage-evidence-20261007` | Danh sách file đã chuyển, biên nhận hash, kiểm tra khôi phục và chứng cứ đồng bộ. Dùng để truy vết đợt chuyển dữ liệu, không cần khôi phục để chạy app. |

Đọc `--list` để biết các ID thực sự có trong danh mục hiện tại. Những file đã được Git theo dõi, gồm dữ liệu quarantine, vẫn ở repo.

## Tiếp tục kiểm thử OCR

Đọc [quy trình kiểm thử Drive](docs/DRIVE_DATA_STORAGE.md) trước khi chọn batch. Bộ đọc chung kiểm tra hash từng ảnh; Drive mất kết nối, thiếu ảnh hoặc byte nguồn thay đổi sẽ báo lỗi, không thay ảnh khác hay bịa kết quả.

Trước khi chạy công cụ lịch sử:

- Khôi phục `local_regions` và baseline cần dùng trước khi chạy `compare.py` hoặc resume audit. Thiếu chúng có thể làm công cụ tính lại thay vì so sánh lần chạy cũ.
- Khôi phục preview trước khi mở review sheet, chạy `make_sheets.py` hoặc probe đọc đường dẫn ảnh local.
- Khôi phục `crossdataset_aliases_20261005.jsonl`, `embedded_rows.jsonl` hoặc `dimension_index.jsonl` trước các báo cáo coverage/Parquet lịch sử tương ứng.
- Giữ kết quả cloud và queue hiện tại để tránh gọi API lặp. Không coi dự đoán OCR hoặc nhãn nháp là nhãn đúng đã duyệt; không tự train model chỉ vì dữ liệu đã khôi phục.

## Vì sao không đưa mọi thứ lên G?

Ổ G là cửa vào dữ liệu cloud, không phải ổ SSD mới. Drive vẫn tải/cache file trên máy khi mở; một lần khôi phục ZIP có thể cần tải cả ZIP để xác minh hash. Dung lượng hiển thị cho G trong File Explorer có thể phản ánh ổ chứa cache, còn hạn mức tài khoản xem ở Google One.

Code, thư viện, model đang dùng và SQLite đang ghi cần filesystem local ổn định. Chạy trực tiếp `.venv`, `node_modules` hoặc ledger từ Drive streaming dễ chậm và lỗi khóa file. API key/`.env` không đưa vào ZIP bàn giao hoặc repo; người dùng tự cấu hình bằng thông tin được cấp riêng.

Sau khi Drive xác nhận đồng bộ đầy đủ và bản trên cloud đã được đối chiếu, mới cân nhắc dọn bản local không cần dùng nữa. Không xóa thủ công cache Drive đang có upload chờ. Việc lưu trữ này không phải lần train model và không chứng minh độ chính xác nhận diện.

Đợt chuyển ngày 07/10/2026 đã dọn 292.250 bản file local sau khi xác minh. Chín ZIP tạm tại `infra/local-runtime/storage-offload-20261007/staging` vẫn còn vì bộ xét duyệt tự động chặn bước xóa; chúng trùng các gói đã xác nhận trên Drive, không phải dữ liệu cần cho app. Xem [báo cáo chuyển dữ liệu](report/DRIVE_COLD_STORAGE_OFFLOAD_20261007.md) để biết phần đã hoàn tất và phần còn giữ.
