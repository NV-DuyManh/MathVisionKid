# Dữ liệu lưu trữ trên Google Drive

Một phần ảnh và kết quả kiểm thử ít dùng của thư mục này đã chuyển vào ZIP riêng trên Drive.
Code/nhãn/model và dữ liệu đang dùng vẫn giữ local. Không suy ra kết quả bị thiếu là ảnh chưa được test.

Đọc `DU_LIEU_GOOGLE_DRIVE.md` ở gốc dự án và `docs/drive-archives.json`.
Drive: https://drive.google.com/drive/folders/1oOenOCeNdsHRprk3c8yNNmdp9ZYRE2Lh

Đường dẫn tương đối để chọn khôi phục: `ai/handoff/incoming`
Dùng `py -3 scripts/data/restore_drive_archive.py --list`, rồi chọn ID phù hợp và `--prefix` đường dẫn này.
Khôi phục kết quả/preview cần dùng trước khi chạy lại audit hoặc so sánh lịch sử.
