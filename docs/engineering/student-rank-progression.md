# Student rank progression

Student Web và Mobile dùng chung bảng mốc từ GET /api/v1/student/rank-milestones và rank từ profile/leaderboard. Backend là nguồn sự thật; không cấp sao từ UI.

| Hạng | Mốc sao từng bậc |
| --- | --- |
| Sắt III, II, I | 0, 3, 6 |
| Đồng III, II, I | 9, 12, 15 |
| Bạc III, II, I | 18, 21, 24 |
| Vàng III, II, I | 27, 30, 33 |
| Bạch Kim V, IV, III, II, I | 37, 42, 47, 52, 57 |
| Kim Cương V, IV, III, II, I | 62, 67, 72, 77, 82 |
| Cao Thủ | 87 |
| Đại Cao Thủ | 122 |
| Thách Đấu | 162 |
| Huyền Thoại | 162 và vị trí toàn hệ thống 1–200 |

Sao mỗi bậc là hiệu hai mốc kế tiếp (Vàng I cần 4 sao). Cao Thủ cần 35, Đại Cao Thủ cần 40. Thách Đấu lên Huyền Thoại theo vị trí toàn hệ thống, không theo vị trí khối. Rank.progress/goal là tiến độ bậc hiện tại, bằng 0 khi không còn mốc sao tiếp theo; masterStars là số sao vượt mốc Cao Thủ. Tổng sao, ledger, quy tắc xác minh hoạt động và điều kiện riêng tư không thay đổi.

Hệ danh hiệu được ngừng theo yêu cầu sản phẩm. API giữ selectedTitle (null) và titles (mảng rỗng) để client cũ đọc được. Ứng dụng bỏ qua selectedTitle trong request và giữ nguyên lựa chọn danh hiệu đã lưu. V41 bổ sung hai cột tùy chọn cho đường tu luyện. Bản phát hành loại V42 thử nghiệm để bảo toàn các cột và lựa chọn cũ. Hạng cao nhất từng đạt Top 200 vẫn được lưu qua reached_challenger.

Ảnh rank là thiết kế được người dùng duyệt, cắt và tách nền từ ảnh tham chiếu, có manifest SHA-256; không dùng ảnh học sinh. Sắt dùng SVG. Ba asset Đồng/Bạc/Vàng được chuẩn hóa vùng hình với kích thước hiển thị chung. Không đưa bộ ảnh nguồn dư thừa hoặc tài liệu riêng tư vào commit.

Kiểm tra ranh giới từng sao, Top 200, migration PostgreSQL với dữ liệu tổng hợp, kiểm thử Student và trình duyệt responsive. Ảnh kiểm tra mock không phải chứng cứ trên thiết bị vật lý.

## Mixed-version rollout and rollback

Clients opt in using the existing X-MathVision-Client header value student-rank-v2 on profile GET/PUT/photo, leaderboard and rank-milestones. Without this opt-in the server returns the previous ranking semantics (scheme 1); no change to privacy, stars or eligibility. Scheme 2 is the current ranking. Missing scheme means legacy; the new client shows server rank names and does not derive per-division progress from legacy group milestones. A profile/milestone scheme mismatch displays a recovery notice rather than incorrect guidance. The retired title feature stays retired on both schemes. Admin enable/disable captures Top 200 history before and after changing student eligibility within the same transaction and reward lock. Historical periods missed before this fix cannot be reconstructed from current position alone.

Before applying V41 in a shared environment, create a timestamped PostgreSQL backup and verify restoration in an isolated instance. Record the build revision and migration version. If a developer database already applied experimental V42, validate the release against a separate disposable database or restore a pre-V42 snapshot to a separate database. Keep the original database and its Flyway history intact.
