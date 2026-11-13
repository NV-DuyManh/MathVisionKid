# Quy ước đặt tên và định dạng

Áp dụng cho code mới hoặc phần đang sửa; không đổi tên hàng loạt code cũ, API công khai, migration đã phát hành hoặc biên nhận nghiên cứu. Mã nguồn dùng tiếng Anh rõ nghĩa; giao diện/tài liệu nhóm có thể dùng tiếng Việt. Đây là quy ước dự án, không phải chứng nhận tiêu chuẩn doanh nghiệp.

| Đối tượng | Quy tắc / ví dụ |
| --- | --- |
| Thư mục tính năng | kebab-case: `lesson-review` |
| Java package | chữ thường, theo tính năng trong namespace hiện có `com.mathvisionkids.api` |
| Java class / record / enum | PascalCase: `LessonService`, `CreateLessonRequest` |
| React component | PascalCase `.tsx`: `VoicePlayer.tsx` |
| Hook | `use` + PascalCase: `useNarration.ts` |
| Hàm / biến / JSON field | camelCase: `prepareLesson`, `selectedVoice`; hàm thể hiện hành động |
| Boolean | `isReady`, `hasAudio`, `canRetry`; không ép thêm `is` vào câu đã rõ nghĩa |
| Hằng số / enum value / env | UPPER_SNAKE_CASE: `MAX_UPLOAD_BYTES`, `INTERNAL_API_KEY` |
| Python module / hàm / biến | snake_case: `speech_render.py`, `normalize_units` |
| CSS class | kebab-case theo trách nhiệm: `voice-player` |
| REST resource | danh từ số nhiều, kebab-case; giữ tương thích các route đang dùng |
| Bảng / cột / constraint SQL | snake_case: `lesson_attempts`, `created_at`; giữ schema hiện có |
| Migration Flyway | tiếp tục chuỗi version hiện tại, `V29__meaningful_change.sql`; không sửa migration đã chạy |
| Test | tên hành vi: `rejectsExpiredSession`, `test_voice_cache_keeps_accounts_separate` |
| Nhánh task mới | `feature/<task>` hoặc `bugfix/<task>` từ develop; mô tả kebab-case, có thể thêm `#123_` |
| Nhánh chốt phiên bản | `release/<major.minor.patch>` từ develop |
| Nhánh vá production | `hotfix/<major.minor.patch>_<task>` từ main/tag; backmerge về develop |
| Commit / PR | `fix(voice): preserve the selected voice across steps` |
| Tài liệu mới | kebab-case, ngày ISO nếu cần; giữ tên nguồn bàn giao để truy xuất |

Commit types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`, `revert`. Scope dùng khi giúp hiểu phần thay đổi. PR mới dùng Conventional Commit; không bắt mã CF/QA của café, không bịa issue. Breaking change dùng `!` và có hướng chuyển đổi. Nhánh cũ không bị rename/rewrite; chỉ PR chuyển tiếp được liệt kê trong `.github/git-flow.json` mới có ngoại lệ có hạn. Task mới luôn theo [Git Flow](git-flow.md).

UTF-8, newline cuối file, bỏ trailing whitespace; 2 spaces cho JS/TS/JSON/YAML/CSS, 4 cho Java/Python. `.editorconfig` hướng dẫn editor; không tự reformat toàn repo. Script Windows dùng CRLF. Giữ bytes của biên nhận/hash nghiên cứu; `.gitattributes` hiện có vẫn có hiệu lực.

Không dùng tên chung chung `data`, `manager`, `helper` khi cần làm rõ trách nhiệm. Không đưa tên học sinh, email cá nhân, token hoặc dữ liệu riêng tư vào tên file/nhánh. Lint kiểm tra những lỗi máy phát hiện được; ý nghĩa tên và hợp đồng vẫn cần reviewer.
