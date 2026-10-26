# MathVisionKid — hoàn tất phần dữ liệu bổ sung, CHƯA HUẤN LUYỆN

Bạn là agent điều phối Antigravity. Hãy thực hiện công việc dữ liệu bên dưới, không chỉ trả kế hoạch. Bạn được phép tạo tối đa 3 agent con đồng thời với model phù hợp việc soạn/kiểm toán tiểu học. Giao task nhỏ, hữu hạn, có task_id và tiêu chí nghiệm thu. Nếu môi trường không hỗ trợ agent con, làm tuần tự và nói rõ; không giả đã có agent chạy.

## Mục tiêu và phân công với Codex

Hoàn thành các nhánh SGK thực sự còn thiếu trong queue hiện hành, kiểm nội dung rồi xuất một gói bổ sung có evidence trên Google Drive. Bộ lõi 495 bài/165 node đã đủ, không soạn lại. Codex phụ trách kiểm toàn kho và checkpoint Colab. Antigravity chỉ phụ trách bổ sung nội dung cùng evidence; không điều khiển notebook/checkpoint audit của Codex, không tự huấn luyện.

Giữ mọi dữ liệu nguồn, bài accepted, bản cũ và lịch sử. Sửa bằng bản dẫn xuất có provenance/hash, không ghi đè/xóa nguồn. Không sinh vô hạn hoặc nhân bài chỉ bằng thay số. Phạm vi kết thúc theo task/constraint, không theo dung lượng Drive.

## Bước 1 — resume từ Google Drive, không khởi tạo lại

Folder hiện có: `19ZxkfKVIggdcbSfsAdCtG1ibfJ0CRN3n`.

Đọc các file theo ID hiện có, bằng tài khoản được chủ dự án cho phép và có quyền truy cập. Tài khoản có thể đổi; dùng ID và hash để nhận diện dữ liệu, không phụ thuộc email.

- STATE: `1TLoQIbrRVmgsg-2uiUujCfM3HrK62Yme`.
- PROGRESS ZIP: `1D5RvQ5-V3DtYZfGxmlmvvPlVz9I-SxeX`.
- CHAT manifest: `1tkSQoAlxXXRUg2AwYfvqsFKVEmM_LmR6`.
- Context duy nhất: `13gdIPQTFKcekoQQtgo0TXc7RgeadzIN9` (`MATH_TRAINING_CONTEXT.md`).

STATE mới nhất là nguồn ưu tiên. Từ STATE, đọc `latest_sgk_accepted_reconciliation`, `latest_all_data_union_recipe`, `latest_cloud_preparation_inventory` nếu có; tải đúng member trong PROGRESS và so SHA256. Đọc policy, tutor_contract, owner_human_attestations, owner_human_signoffs, build state và queues hiện hành trong gói. Nếu tên/member thay đổi, theo pointer có hash và context, không đoán hoặc tạo queue mới để thay thế.

Mốc tham chiếu 22/10, phải kiểm lại trước khi dùng: 1.629.858 case records, 6.502.088 candidate chat; 37 payload/218 source member/31 chat member. Đây không phải số dạng toán hoặc tổng train-only đã kiểm. Queue gần nhất là `data_resume_20261022/next_uncovered_tasks.json`: 38 G2 task/50 candidate constraints, 10 asset-only master và 1 locator G3 còn thiếu. Có 3 G2 task/4 nhánh đã đóng bằng 6 bài mới; không nhận lại. Queue cũ và mọi nhận xét đã nhận giữ làm history.

Đọc actual constraints, source receipts, nearest accepted rows và `minimal_required_specific_branches` của từng task trước khi soạn. Cùng tên master hoặc từ khóa không chứng minh đã bao phủ. Không lấy ví dụ lớp khác để tự đóng yêu cầu lớp 2. Phân biệt bài toán có mô tả văn bản đầy đủ với năng lực đọc hình/thực hành thật.

Nếu chỉ có quyền local workspace, đọc các control nhỏ đã có tại `D:\nhom6\train thử\MathVisionKid\ai-training` để định hướng, nhưng đối chiếu STATE/Drive trước khi nhận việc. Không tải toàn corpus hoặc SQLite audit lớn về máy chủ dự án. Dữ liệu tạo ra và gói kết quả phải lên Drive; có thể dùng bộ nhớ hoặc vùng tạm hữu hạn để xử lý, không để lại kho lớn trên PC.

## Bước 2 — chia agent, tránh làm trùng

Tạo bảng giao việc từ task_id còn pending, sắp xếp ổn định, lưu danh sách task_id và parent queue hash.

1. Agent A: một nửa task G2 còn thiếu, mỗi lô tối đa 3–5 task, theo đầy đủ constraint.
2. Agent B: nửa còn lại; không trùng task_id của A. Khi task cần hình hoặc quan sát, chỉ làm phần có đủ evidence và ghi phần còn thiếu.
3. Agent C: kiểm toán/sư phạm độc lập các lô A/B; trong lúc chờ, xác minh 1 locator G3 và 10 asset-only master bằng nguồn/asset thật. Không biến việc chưa tìm được thành đã đủ.

Agent soạn không tự duyệt cuối cùng bài của mình. Điều phối đọc lại actual nội dung và hợp nhất sau báo cáo kiểm. Nếu có lô pending/reviewer đang chạy từ trước, hợp nhất hoặc xác định rõ quyền sở hữu trước khi giao lô mới. Không tranh ghi file chung giữa agent.

## Bước 3 — yêu cầu nội dung và kiểm

- Dùng schema neutral và tutor_contract hiện hành. Tạo ví dụ gốc, phù hợp lớp, biểu diễn/ngữ cảnh đa dạng; giữ nguồn SGK/receipt đúng cấp và trang. SGK là nguồn xác định dạng bài, không chứng minh bài do agent tạo tự động đúng.
- Lời giải từng bước giải thích vì sao chọn phép tính/quan hệ, ghi đơn vị, đối chiếu đáp án với yêu cầu và cách kiểm ngược.
- Initial guidance và cả 3 hint không tiết lộ đáp số/nhãn cuối hoặc chép toàn lời giải. Tăng dần hỗ trợ thật, diễn đạt tự nhiên cho học sinh.
- Phản hồi sai chỉ dựa đề và student_work thực sự cung cấp; không suy diễn suy nghĩ kín hoặc mô tả hình chưa đọc. Thiếu ảnh/dữ kiện/dụng cụ thì hỏi thiếu đúng phần đó.
- Mỗi lô cần oracle khác phương pháp với lời giải/builder, Fraction/Decimal khi thích hợp, kiểm đơn vị và điều kiện biên; kiểm mutation sai có ý nghĩa. Chia dư phải đối chiếu cả thương/dư và điều kiện số dư với givens. Không thay đáp án chỉ để qua validator.
- Người kiểm phải đọc actual đề, givens, request, student_work, mọi steps/reasons/explanations/answers, initial và tất cả hint. Parser/keyword pass chỉ là kiểm kỹ thuật, không là semantic proof.
- Ghi QA đủ 7 tiêu chí theo policy hiện hành, gắn đúng source_row_sha256 đã đọc; giữ riêng draft/source/export hashes và provenance của mọi sửa đổi.
- Kiểm trùng ID, group, đề và overlap theo policy. Numeric-only overlap chỉ được xét ngoại lệ theo đúng hash sau QA; không dùng blanket bypass, không tuyên bố benchmark còn độc lập với phép tính đó. Không đọc concept_challenge_v4, sealed/pilot để điều chỉnh dữ liệu.
- Kiểm tokenizer đã pin theo contract trên TOÀN BỘ chat mới, không truncate. Đây chỉ là tokenizer, không tải model weights hay Trainer.

## Nhãn và quyền chấp nhận

Chủ đã cho phép soạn, tự QA và chấp nhận trước; không cần hỏi lại từng lô. Bài mới chỉ accepted sau các kiểm thực tế, dùng nhãn accepted của policy/export hiện hành (mốc hiện tại: `ACCEPTED_VALIDATED_OWNER_PREAUTHORIZED`).

Giữ tác giả/nguồn AI ban đầu, không gắn nhãn độ chính xác thấp chỉ vì nguồn AI, cũng không bịa độ chính xác 100%. `human_verified`, `teacher_certified`, `owner_human_reviewed` chỉ được áp khi có owner attestation khớp đúng nội dung/hash. Snapshot 299 signoff cũ không mở rộng sang bài tương lai. Owner attestation không phải credential nghề nghiệp hoặc independent external review.

Không sửa owner signoff/frozen V3/V4, không nhập quarantine/seed cũ chỉ vì có quyền chấp nhận mới. Nội dung sai chưa sửa không được promoted accepted; giữ nguyên evidence và ghi pending thật.

## Bước 4 — xuất Drive và bàn giao một lần

Không ghi các control chung STATE/PROGRESS/CHAT/context hoặc notebook/SQLite audit trong lúc Codex đang phụ trách chúng. Giữ một manifest kết quả riêng để Codex kiểm và hợp nhất một lần; việc này tránh hai công cụ ghi đè trạng thái nhau.

Xuất gói bổ sung hữu hạn vào folder Drive hiện có, tối thiểu gồm:
`accepted_cases.jsonl`, `accepted_chat.jsonl`, `qa7.jsonl`, oracle/negative-test evidence, tokenizer receipt, `coverage_delta.json`, `pending_remaining.json`, source/draft/export hash mapping và manifest file/member SHA256.

coverage_delta phải liệt kê từng task_id/candidate constraint được đáp ứng, các accepted row hash chứng minh nó, phần chưa đủ, parent queue/recipe hash. Text-only không đóng claim đọc ảnh/thực hành. Không giả nguồn G3 bằng nguồn G4 hoặc G2. Không xóa bài dư, nguồn, lịch sử hay asset cũ.

Trước upload, kiểm có kết quả cùng run_id/hash chưa; không tạo folder mới hoặc upload ZIP cùng byte lần nữa. Upload xong phải tải raw readback mới, so số byte/SHA256 toàn gói và manifest; chỉ sau đó báo sync thành công. Nếu connector không có write/raw readback thì ghi blocker cụ thể, không giả đã lưu. Không tạo public link/quyền chia sẻ mới ngoài yêu cầu.

Báo cáo cuối ngắn, cụ thể: task đã đóng/còn lại, số case/chat mới (không cộng lại bản cũ), kiểm đã chạy thật, giới hạn nguồn/asset, URL và ID Drive, bytes/SHA256, cùng chỉ dẫn merge. Không tuyên bố toàn kho sẵn sàng train nếu kiểm toàn kho do Codex phụ trách chưa hoàn tất.

KHÔNG TRAIN, GPU, weights, paid API, Run All, launcher, sửa app, production, commit/push. Không sửa lỗi kết nối Colab; phần đó chủ dự án đang thao tác tay với Codex. Hoàn tất phần soạn/QA/xuất độc lập trong phạm vi dữ liệu được giao.
