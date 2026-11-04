# Dọn tệp và giữ bằng chứng

Một task mới dùng PR hoặc một thư mục ngày dưới `report/`. Không tạo thêm bản sao ở `reports/`. Build/log/cache và ảnh test riêng tư ở vùng ignored, không trong Git. Mục đích là giữ repo gọn và truy xuất được; số file ít không quan trọng hơn bảo toàn dữ liệu.

Trước khi dọn: kiểm kê bytes, tracked/untracked, nội dung, đường dẫn tham chiếu và nơi đang dùng. Không coi toàn bộ `runtime/`, `report/` hay tệp cũ là rác. Giữ model/dataset/ảnh gốc/ground truth, hash receipts, provenance đóng góp, tài liệu còn được tham chiếu và báo cáo hiện tại. `demoUI` giữ trên máy owner, không đưa Git.

Báo cáo UI thử nghiệm, output tạm hoặc bản sao đã thay thế không cần thiết có thể chuyển ra kho khôi phục ngoài checkout, kèm manifest đường gốc, hash và dung lượng. Dọn cache chỉ khi xác định có thể sinh lại và không thuộc tiến trình đang sử dụng. Không viết lại lịch sử Git, xóa volume Docker, dừng dự án khác hoặc quét xóa cả ổ để làm sạch repo.

Trên Windows, xác minh absolute path nằm trong vùng dự định trước mỗi recursive move/delete; không đưa danh sách PowerShell sang shell khác để xóa. Tệp không chắc chắn giữ lại; tệp cần loại có thể vào kho khôi phục/Recycle Bin thay vì xóa vĩnh viễn. Không xóa nhánh local hoặc file của chat khác đang sửa.

Khi nhiều chat làm chung checkout, mỗi chat giữ phạm vi rõ. Chat cleanup không git switch/reset/stash/add/commit/push và không sửa source/CI của chat triển khai. Review danh sách xóa riêng trước tích hợp; kết quả phải nêu dung lượng thực, nơi khôi phục và phần cố ý giữ.
