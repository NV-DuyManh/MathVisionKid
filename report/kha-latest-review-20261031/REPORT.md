# Review nhánh Kha mới nhất — 31/10/2026

Nguồn: [PR #11](https://github.com/NV-DuyManh/MathVisionKid/pull/11), head `94f56bb18e82163cc509b3b4ee915920d24f6df7`, base `ca6629e94a4cad82b2f3d6de5398f7a5a4dbadaa`. Hai commit mới `3fbab4a` và `94f56bb` giữ nguyên tác giả `deptraivodich <khatruong2k5@gmail.com>`. Review và thử nghiệm thực hiện trên checkout tách riêng; không dùng dữ liệu thử để chấm bài học sinh thật.

## Kết luận và phần được nhận

Đủ điều kiện tích hợp sau sửa tính di động của khởi động MinIO. Không merge nguyên trạng cấu hình riêng máy Kha.

- Voice Quiz: deadline tổng bao trùm transport/refresh; hủy request khi đổi giọng/bài, rời màn hình hoặc đưa app vào nền; không nhận audio trả muộn của tác vụ cũ. Lỗi mở player cho phép tải lại. Hai render khác nhau được chạy đồng thời trong giới hạn; yêu cầu trùng vẫn dùng chung kết quả.
- AI TTS: giữ chunk thành công và chỉ retry empty-audio tối đa một lần trong deadline gốc. Giữ đúng hai giọng đang dùng; không thay âm sắc hoặc bịa WAV khi provider lỗi.
- Sao: hoàn thành có hướng dẫn nhận 1 sao; PRACTICE không thưởng, CHALLENGE giữ kỷ lục tốt nhất. Backend quyết định điểm; gửi lại cùng request không tăng số lượt/sao.
- Timer: hiển thị giờ khi thời gian dài, dùng đồng hồ monotonic cho phần tăng trên client, không sửa timestamp server hoặc reset để nhận sao.
- Diagnostics Celery: tăng thời gian dành cho import/khởi tạo tiến trình trên Windows lên 20 giây; ping worker vẫn giới hạn 2,5 giây.

## Phát hiện đã xử lý trước merge

**P1 — image MinIO riêng máy.** Nhánh nguồn yêu cầu `mathvision-minio-local:2024.01.28`, `pull_policy: never`. Image đó không có trên máy chủ dự án. Tag registry cũ cũng bị từ chối khi kiểm tra manifest; chỉ giữ cache máy chủ sẽ làm clone mới không khởi động được.

Tái sử dụng `infra/production/storage/Dockerfile` đã có: tải đúng release MinIO/mc, kiểm tra SHA-256 cho AMD64/ARM64. Launcher chọn và kiểm tra image hiện đang sở hữu dữ liệu; cài mới build image chung `mathvision-storage:2024.01.28`. Không đổi image/volume cũ, không tự nhận volume mồ côi, không pull một bản mới để thay dữ liệu. Kiểm thử thật xác nhận config hash của dịch vụ MinIO cũ không đổi, nên bản sửa không yêu cầu tái tạo container đang dùng.

**Tính lặp lại của cài đặt.** Hướng dẫn dùng `npm ci` và Python `requirements-lock.txt`, không dùng cài dependency không khóa phiên bản. Không đưa key, đường dẫn tài khoản cá nhân hoặc model weights vào Git. Các máy cần cùng cấu hình năng lực/model theo manifest; clone không tự sao chép database và thông tin bí mật của người khác.

Đã thêm kiểm thử cancel/background của Voice Quiz và giới hạn diagnostics; bỏ cảnh báo dependency hook mới trong phần sửa, chỉnh thụt dòng. Hai báo cáo chỉ mô tả launcher/cấu hình riêng máy nguồn được loại khỏi cây tích hợp (77 dòng); báo cáo Voice nguồn giữ rõ nhãn bằng chứng của tác giả và liên kết tới review này. Không thêm dependency.

## Kiểm thử độc lập

| Nhóm | Bằng chứng |
|---|---|
| Student đầy đủ | 1.272/1.272 tests, 111/111 suites đạt trong lượt cuối, 52,046 giây |
| AI giọng Quiz/bài học/phát âm | 95 tests đạt |
| Backend | Lượt chốt bật cả MinIO thật: 480/480 ca đạt, không bỏ qua; JAR build thành công |
| HTTP thật Spring → FastAPI → Edge TTS | 34 checks đạt, hai dạng toán × hai giọng, kiểm tra PCM, cache, khóa lời giải và sao/idempotency |
| Migration dữ liệu cũ | Flyway V27 trên PostgreSQL riêng: 5 tình huống có hướng dẫn, giữ kỷ lục, PRACTICE, độc lập, snapshot cũ; giữ số lượt và mọi trường lịch sử ngoài điểm được điều chỉnh có ledger |
| Cài mới | PostgreSQL rỗng chạy đủ 27 migration; `student`, `admin`, `teacher` với mật khẩu demo đăng nhập đúng vai trò |
| MinIO cài mới | Build từ nguồn/checksum thành công; container tạm có health tốt và S3 ghi/đọc đúng byte, không mount dữ liệu thật |
| MinIO dữ liệu cũ | Image/container/volume và Compose config hash giữ nguyên; binary server/client khớp release |
| Launcher/diagnostics | 15 tình huống MinIO, 9 Python tests cùng 5 subtests, dotenv/port guards đạt |
| TypeScript/Expo | Typecheck, Expo Android export và JAR build đạt; lint không lỗi, còn 3 cảnh báo cũ ngoài phạm vi |

Hai lượt Student trước có một ca `tutorScreen` vượt ngưỡng 5 giây ở vị trí khác nhau. Không tăng timeout hoặc bỏ assertion; chạy riêng 66 ca đạt và lượt đầy đủ cuối cùng đạt cả 1.272. File test và màn hình đó không đổi so với main. Không quy kết nguyên nhân cho thay đổi Quiz khi chưa có bằng chứng.

Harness HTTP ban đầu so sánh toàn bộ response idempotent, gồm `serverNow` luôn thay đổi. Đã sửa phép đo để so attempt, điểm và số lượt — không sửa sản phẩm nhằm làm xanh phép so sai đó.

## Hiệu năng và giới hạn

Trong lượt HTTP thật cuối: tạo mới khoảng **14,17–25,17 giây**, cache **39,72–61,25 ms**. Phép đo trực tiếp hai giọng đồng thời trước đó: khoảng 10,41/13,14 giây. Provider có lượt empty-audio rồi phục hồi bằng retry; không coi đó là bảo đảm không bao giờ lỗi. Đây là hiệu năng server trên máy phát triển, không phải thời gian chạm nút đến tiếng phát trên điện thoại.

Chưa xác nhận nghe qua loa/micro/tua trên Expo Go Android/iPhone trong lượt review này. Android export và kiểm thử lifecycle dùng test doubles không thay thế nghiệm thu thiết bị. Cài mới có tải mạng và build lần đầu; không thể cam kết mọi mạng, phần cứng, khóa dịch vụ hoặc provider cho kết quả/thời gian giống hệt. Giữ chung backend khi cần dùng chung tài khoản/dữ liệu; mỗi clone local là môi trường dữ liệu độc lập.

MinIO vẫn giữ release cũ để tương thích dữ liệu, không phải tuyên bố bản đó còn được upstream hỗ trợ bảo mật. ARM64 có checksum trong Dockerfile/resolver; phép build mới trong lượt này là AMD64. Không có kiểm thử máy vật lý thứ hai.

Nhật ký và script đo riêng: `.local-artifacts/kha-latest-review-20261031/` trên máy chủ dự án; không đưa snapshot dữ liệu, token, WAV thử và dependency/build outputs lên Git. Các tiến trình HTTP QA và container MinIO tạm đã được dừng; database chính không nhận dữ liệu thử. Báo cáo nguồn trong PR là bằng chứng do tác giả bàn giao, không được gộp thành phép thử do người review tự thực hiện.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa tối thiểu, dùng renderer/player và Dockerfile sẵn có.
  - Applied to: MinIO portable startup, diagnostics và regression bổ sung.
- `ponytail-review`
  - SKILL.md: `.agents/skills/ponytail-review/SKILL.md`
  - Why selected: nhận phần cần thiết và bỏ cấu hình/báo cáo riêng máy.
  - Applied to: diff hai commit Kha và đối chiếu chức năng đã có trên main.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React async lifecycle và tránh công việc trùng.
  - Applied to: cancel request, kiểm tra controller identity, cleanup và đổi Quiz/giọng.
