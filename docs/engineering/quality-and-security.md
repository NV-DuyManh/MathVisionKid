# Chất lượng, bảo mật và review

## Mức độ finding

- P0: sự cố nghiêm trọng đang diễn ra, lộ secret/dữ liệu riêng tư hoặc sai dữ liệu diện rộng; dừng rollout liên quan và báo owner.
- P1: hỏng luồng chính, sai quyền, lẫn tài khoản, sai phép tính/đơn vị hoặc mất dữ liệu có thể tái hiện; chặn merge phần bị ảnh hưởng.
- P2: lỗi hành vi có cách tránh; ghi trigger/tác động để ưu tiên đúng.
- P3: cải thiện nhỏ; không nâng thành blocker vì sở thích.

Finding nêu revision, file/line, trigger, expected/actual, tác động, cách kiểm chứng. Phân biệt lỗi đã xác minh với nghi ngờ. Người review không tự giải quyết discussion của người khác khi chưa thống nhất. AI/CI hỗ trợ review; áp dụng quyền merge theo Git Flow: người có quyền write cần approval của người khác, riêng owner NV-DuyManh được miễn approval. Required checks/discussions và đích PR đúng vẫn bắt buộc với tất cả; agent chỉ merge khi owner cho phép.

## Kiểm tra theo rủi ro

| Thay đổi | Kiểm chứng |
| --- | --- |
| Docs / governance / skill | Registry, liên kết và policy tests; không cần chạy lại mọi model |
| React web | Lint, type/build, kiểm thử phiên/lỗi/UI liên quan; màn hẹp và keyboard khi bị ảnh hưởng |
| Student | Typecheck, contracts, Jest; browser/Expo/thiết bị ghi riêng |
| Backend | Gradle test với profile test; success, validation, ownership và hết quyền |
| Migration | Chạy PostgreSQL dùng một lần, nâng schema cũ nếu thay tương thích dữ liệu |
| Tutor / speech / catalog | Phân số, đơn vị, sai/thiếu dữ kiện, timeout/quota, retry, hai giọng, cache phân tách tài khoản |
| OCR / model | Geometry, transcript và toán đo riêng; ground truth người duyệt và held-out split có nguồn |
| Release | Revision, checks, smoke môi trường đích, rollback; merge không đồng nghĩa deploy |

Không viết test chỉ lặp lại thuật toán. Không thay timeout/bỏ assertion để làm xanh. Không gọi cloud/live TTS trong PR CI; fixture/provider mock và dữ liệu tổng hợp phải ghi rõ. Training chỉ khi owner cho phép, có dataset split, cấu hình và số đo; không dùng kết quả model làm nhãn đúng tự động.

## Bảo mật

Không commit `.env`, khóa, ảnh học sinh, database, trọng số hoặc dữ liệu nghiên cứu riêng tư. Không xuất token/header auth vào log, artifact hoặc ảnh. CI mặc định read-only, không triển khai từ PR; pin action theo SHA. PR title/body/path là dữ liệu không tin cậy: không nội suy vào shell hoặc chạy code PR trong `pull_request_target` có quyền ghi.

Dependency dùng lockfile; không `audit fix --force`, không nâng Expo/React/ML major hàng loạt. Dependabot chỉ mở PR, không tự duyệt/merge. Secret scanning/push protection là lớp bổ sung, không thay review staged diff và xử lý thu hồi khóa nếu đã lộ.

## Bảo toàn VPS dùng chung

Owner cho phép cập nhật MathVisionKid, đồng thời yêu cầu giữ nguyên các phần khác đã có trên server. Quy tắc này áp dụng cả khi có quyền quản trị hoặc owner đã giao triển khai tự động:

- Chỉ thay đổi tài nguyên MathVisionKid thuộc phạm vi được giao. Xác minh đường dẫn thực và nhãn Compose trước mỗi thao tác ghi; tên giống dự án không tự chứng minh quyền sở hữu. Với VPS hiện tại, thư mục ứng dụng là `/home/dtu/mathvisionkid`, Compose project là `mathvisionkid`. Không chạm các dịch vụ khác cùng máy.
- Chụp inventory ID/image/mount của container, hash cấu hình cần bảo toàn và kiểm tra dung lượng trước triển khai. Sao lưu DB/cấu hình trong thư mục backup mới của ứng dụng, xác minh backup đọc được. Không ghi đè bản backup cũ.
- Dựng bản phát hành trong thư mục mới theo revision đã kiểm thử. Chỉ thay container ứng dụng đã được phép và dùng `--no-deps` khi cập nhật một service; không recreate DB, Redis, MinIO, gateway hoặc service khác nếu không có yêu cầu riêng. Migration chỉ thêm tương thích và phải có kiểm chứng PostgreSQL/backup trước khi chạy.
- Không xóa/ghi đè dữ liệu đang có, volume, model/dataset, secret hoặc cấu hình ngoài phạm vi. Không dùng `docker system prune`, dọn/xóa hàng loạt container/image/volume, `compose down -v`, reboot, hoặc đổi SSH, firewall, tài khoản hay package hệ thống để tiện deploy. Phiên đăng nhập không tự cho phép cài khóa SSH hoặc lưu mật khẩu.
- Sau triển khai, so lại ID/mount của mọi container ngoài phạm vi và hash cấu hình bảo vệ với inventory trước đó. Nếu lệch, dừng bước ghi tiếp theo và kiểm tra nguyên nhân. Rollback chỉ tác động phần ứng dụng vừa thay; không restore đè DB đang nhận dữ liệu mới hoặc thay phần khác để làm smoke xanh.
- Báo rõ source revision, phần đã thay, phần đã xác minh giữ nguyên, kết quả smoke và giới hạn. Không coi health xanh là bằng chứng dữ liệu/dịch vụ khác còn nguyên.

## Bằng chứng kiểm thử và dọn dẹp

Ghi passed / failed / not run và lý do, exact command/revision. Không coi health xanh là tutor/TTS hoạt động; kiểm tra endpoint có xác thực. Không cam kết mọi bài/thiết bị không bao giờ lỗi hoặc 1–3 giây nếu chưa đo đủ.

Giữ báo cáo mới nhất, biên nhận nghiên cứu/hash và attribution. Báo cáo UI thử nghiệm cũ không còn tham chiếu có thể lưu trữ ngoài checkout; không nhân đôi thư mục report/reports cho task mới. Tệp tạm vào `.local-artifacts/`, không commit log/build/DB/ảnh riêng tư. Dọn phải có danh sách và đường khôi phục; không xóa model/dataset hoặc sửa lịch sử Git để giảm dung lượng.
