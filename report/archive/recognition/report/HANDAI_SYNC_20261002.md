# Đồng bộ phần nhận dạng Hand AI vào MathVision Kids

Ngày: 2026-10-02. Nguồn đối chiếu: `E:/HandAI`, HEAD `12b8659`; MathVision trước cập nhật: HEAD `9c2834e`. Đối chiếu working tree thực tế, gồm model local không được Git lưu. Không sửa mã nguồn HandAI riêng, không huấn luyện, không commit/push.

## Kết luận

HandAI riêng có cải tiến pipeline hữu ích, nhưng không có checkpoint CRNN mới hơn tại đường dẫn runtime đang dùng. Đã đồng bộ các cải tiến OCR tương thích vào MathVision. Phần YOLO nhận dạng toán, bộ phân tích đặt tính, kiểm tra quy tắc và chính sách chấm toán giữ nguyên.

Checkpoint `best_cer.pth` ở hai repo có cùng SHA-256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`; vocabulary cùng SHA-256 `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d`. Không sao chép lại trọng số giống nhau. Cấu hình v2 có trong hai repo, không phải bằng chứng có model v2 đang phục vụ.

## Phần đã cập nhật

- Tách dòng dày bằng chiếu ngang vùng mực xanh/tím, giữ các đường tách dòng hiện có cho trường hợp khác.
- Giữ điểm tin cậy chưa biết là `null`, bảo toàn điểm đo bằng 0, loại NaN/Infinity và điểm ngoài [0,1]. Phân biệt `CRNN_CTC_SOFTMAX` với `AI_SELF_REPORTED`; điểm softmax chưa được hiệu chỉnh thành xác suất toàn dòng đúng.
- Đọc `.env.local` đúng thứ tự; không sao chép môi trường, khóa API hay tài khoản từ HandAI.
- Lớp đối chiếu AI sử dụng ảnh gốc thật; không dựng ảnh trắng và không lấy điểm OCR giả làm điểm advisor. Backend kiểm tra SHA-256 ảnh lưu trước khi gửi; mobile giữ nguồn điểm trong payload xác nhận.
- Backend ưu tiên tái sử dụng `rawOcrText` đã nhận dạng thay vì gọi OCR lần hai hoặc gán nhầm kết quả OCR thành `CANONICAL_EXACT`.
- Bổ sung nguồn điểm vào DTO/entity và migration V16 nguyên bản từ HandAI. Không tự gán nguồn cho điểm lịch sử. Cột `ocr_trials.confidence_source` trong migration nguyên bản được giữ để tương thích lịch sử migration; đợt này chỉ đồng bộ luồng nhiều dòng.
- Điều chỉnh riêng cho MathVision: hai advisor đồng ý vẫn phải qua kiểm tra an toàn; không tự đổi số/dấu phép tính, không áp dụng khi thiếu điểm hoặc chỉ là gợi ý. Trường hợp cần xác nhận giữ nguyên OCR và trả `NEEDS_REVIEW`.
- Sửa ignore `runtime/` thành `/runtime/`, thêm danh sách cho phép mã AI và metadata. 176 file AI local trước đây bị bỏ qua nay xuất hiện để review/lưu Git, phần lớn là mã nền đã có, không phải 176 file viết mới. Credentials, môi trường ảo, trọng số, ảnh debug và ảnh thật ngoài fixture kiểm tra được giữ ngoài danh sách này.

Không thay giao diện hoặc mang dashboard nghiên cứu của HandAI vào MathVision. Đợt này nâng phần OCR hiện có; chưa triển khai ghép kết quả hai model thành một bài giải đầy đủ trong luồng chấm toán.

## Bằng chứng nhận dạng

Cùng fixture `OWNER_POEM_12_LINES.png`, SHA-256 `310ec47f900be24e375d37a57080bcf09498ff3a7c90d595945286a0532b3746`:

| Chỉ tiêu | Trước cập nhật | Sau cập nhật |
|---|---:|---:|
| Số box dòng phát hiện | 7 | 12 |
| Số dòng tham chiếu | 12 | 12 |
| Dòng khớp hoàn toàn, giữ dấu câu/hoa thường | Không tính do không đủ cặp dòng | 4/12 |
| Lỗi ký tự / ký tự tham chiếu | Không tính do không đủ cặp dòng | 8/194 |
| CER | Không so sánh trực tiếp | 4,12% |

Sau cập nhật đã chạy endpoint `/internal/v1/ocr/detect-lines` qua FastAPI TestClient với CRNN thật trên CPU. Tắt advisor cloud, tắt canonical override; không sửa kết quả bằng tay. Chuẩn hóa Unicode NFC và khoảng trắng, giữ hoa/thường và dấu câu. Tham chiếu lấy từ bản chép trong minh chứng HandAI đã có; đây là một ảnh hồi quy, không phải tập kiểm tra độc lập. Không suy ra độ chính xác chung hoặc độ chính xác nhận dạng toán từ phép đo này. Báo cáo HandAI trên ảnh JPEG khác ghi CER 4,64%, không dùng làm so sánh trước/sau với fixture PNG này.

Minh chứng: `handai_sync_20261002/handai-before.json`, `handai_sync_20261002/handai-after.json`, `handai_sync_20261002/verification.json`. Diff riêng các file Python đồng bộ nằm ở `handai_sync_20261002/ai-runtime-changes.patch`; không chạy patch lần nữa trên working tree đã cập nhật.

## Kiểm tra

- Trước cập nhật: nhóm 16 file kiểm tra AI, 153 pass / 9 fail.
- Sau cập nhật cuối: nhóm 19 file kiểm tra AI, 182 pass / 9 fail; đúng 9 ca lỗi trước đó, không phát sinh ca lỗi mới trong nhóm đã chạy. Danh sách tên ca lỗi lưu trong `verification.json`.
- Nhóm kiểm tra mới/điều chỉnh riêng: 30 pass, gồm nhận dạng logits thật, nguồn điểm, ảnh advisor thật, cấu hình, 12 dòng, bộ đếm request và bảo vệ nội dung toán trước advisor.
- Backend: full suite 142 pass với profile `test` dùng H2; sau thêm hai ca kiểm tra ảnh/hash, chạy lại 13 ca thuộc ba lớp OCR liên quan, tất cả pass.
- Student Mobile: 18 suites / 199 tests pass; TypeScript `--noEmit` pass. Có cảnh báo `act` từ kiểm tra UI sẵn có.
- `git diff --check` pass. Không có bằng chứng kiểm tra trên thiết bị thật.

Lần chạy backend ban đầu không chọn profile test đã gặp checksum migration V16 trên PostgreSQL local. Đã dùng nguyên migration V16 từ nguồn thay cho bản rút gọn; không chạy Flyway repair hoặc chỉnh lịch sử DB. Các kiểm tra tiếp theo dùng profile test/H2. Chưa xác minh lại khởi động stack thật hoặc áp dụng migration lên DB mới.

## Giới hạn còn lại và sử dụng

Chín lỗi nền liên quan tách dòng sát nhau, bỏ sót/gộp dòng và cờ cần review vẫn còn. Chưa chứng minh cải thiện tổng quát trên tập bài toán học sinh; chưa gọi Groq/Gemini thật trong đợt kiểm tra. Trọng số local vẫn cần cung cấp khi dựng máy mới; các fixture ảnh cũ không thuộc danh sách cho phép cần có riêng để chạy một số kiểm tra lịch sử.

Cần khởi động lại backend và dịch vụ AI để tiến trình đang chạy nạp mã mới; mobile cần nạp lại bundle. Cấu hình mặc định bridge OCR của luồng chấm toán không bị tự đổi sang chế độ khác. Bước tiếp theo phù hợp là đánh giá các ảnh lời giải toán có cả chữ và phép tính, rồi tích hợp việc ghép vùng/chứng cứ của hai model.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Đồng bộ OCR với thay đổi nhỏ, tái sử dụng pipeline và model có sẵn.
  - Applied to: OCR Python, hợp đồng backend, kiểm tra hồi quy; không thêm dependency hoặc framework.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Hợp đồng dữ liệu của ứng dụng React Native cần giữ metadata OCR khi truyền lên backend.
  - Applied to: `OcrPilotService` và kiểm tra payload; giữ payload gọn, không thêm lượt gọi mạng hoặc state UI.
