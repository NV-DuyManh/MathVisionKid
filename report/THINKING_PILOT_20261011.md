# MathVisionKid — pilot giải toán trong notebook OCR, 11/10/2026

Báo cáo lịch sử được giữ nguyên để tham chiếu. Từ 11/10/2026, mọi cập nhật tiếp tục ghi tại [MATH_TRAINING_CONTEXT.md](../ai-training/MATH_TRAINING_CONTEXT.md), không tạo thêm báo cáo Markdown theo đợt.

Đã sửa và chạy trực tiếp notebook do chủ dự án cung cấp qua Colab MCP: https://colab.research.google.com/drive/17aUDHsE5hyYeDCFb3Z-iG8hRnGwvfcZM. Thêm 7 cell THINKING ở cuối; đối chiếu ID và source xác nhận cả 8 cell OCR ban đầu giữ nguyên. Bản sao trước sửa được lưu local và trên Drive. Không commit/push hoặc tích hợp adapter vào ứng dụng.

Trạng thái thực tế: `PILOT_COMPLETED_NOT_PRODUCTION`. Tiến trình huấn luyện kết thúc returncode=0; cell xuất artifact chạy thành công. Dữ liệu, adapter, optimizer/RNG checkpoint, prediction và báo cáo được ghi tại `/content/drive/MyDrive/ MathVisionKidAI/ai-training/thinking/math_text_pilot_v1/`. Tên thư mục có khoảng trắng đầu tên. Log xuất hiện trong kết nối Drive cá nhân; không thay quyền chia sẻ.

## Dữ liệu và huấn luyện

Trong các manifest nguồn được kiểm tra giới hạn (metadata và tối đa 100 dòng đầu mỗi manifest), chưa xác nhận được tập đề–lời giải–đáp số phù hợp để train reasoning. Các nhãn OCR không được dùng làm đáp số toán. Không tuyên bố đã kiểm kê toàn bộ Drive trong giai đoạn này.

Tạo riêng 1.670 mẫu sinh bằng chương trình, train 1.474 / validation 92 / test 104, gồm 12 họ bài lớp 1–5 và 10 mẫu hỏi lại/từ chối. Phép tính dùng phân số chính xác; `human_verified=false`. Gom nhóm cùng dữ kiện và những lượng hoán đổi tương đương vào cùng split, giữ cách diễn đạt riêng cho validation/test. Chưa phủ toàn bộ chương trình và chưa được giáo viên chứng nhận.

Qwen/Qwen3-0.6B, revision `c1899de289a04d12100db370d81485cdf75e47ca`; LoRA FP16 r16 alpha32, dropout0.05, lr1e-4, batch1, accumulation4. GPU Tesla T4. 32 optimizer steps = 128 lượt mẫu, chưa hoàn thành một epoch. Chỉ completion của assistant góp vào loss. Audit toàn bộ 1.474 mẫu train: 246–397 token, không cắt nhãn. Lưu trạng thái mỗi 8 bước. Loss bước đầu/cuối: 1,835391 / 0,066887; peak allocated VRAM 1,969 GiB.

Môi trường: Python3.13.15, torch2.11.0+cu130, transformers5.18.0, peft0.21.1, accelerate1.15.0. Sửa torchao0.10.0 không tương thích thành 0.17.0 trong cell huấn luyện và khởi chạy Python riêng, giữ nguyên torch/CUDA. Lần lỗi đầu không cập nhật trọng số; giữ nguyên baseline đo trước đó. Không dùng bitsandbytes/QLoRA.

## Kết quả đã xác minh

Chọn cố định trước baseline 14 mẫu validation và 14 mẫu test, mỗi tập gồm 12 bài đủ dữ kiện + 1 thiếu dữ kiện + 1 ngoài phạm vi. Chưa chạy hết 92/104 mẫu. Test không được dùng chỉnh hyperparameter hoặc chọn model. Chưa đo baseline test, không suy luận mức tăng test.

| Chỉ số | Baseline val | Adapter val | Adapter test |
|---|---:|---:|---:|
| Đáp số đúng | 6/12 | 8/12 | 7/12 |
| Đơn vị đúng | 5/12 | 12/12 | 12/12 |
| Phép tính các bước và đáp số nội bộ nhất quán | 5/12 | 10/12 | 10/12 |
| Đúng đáp số, đơn vị, phép tính và khớp kế hoạch nghiêm | 3/12 | 8/12 | 6/12 |
| Trạng thái hỏi lại/từ chối đúng | 0/2 | 0/2 | 0/2 |
| Parse JSON thành công | 14/14 | 14/14 | 14/14 |
| Output chạm giới hạn token | 0 | 0 | 0 |

Đã đối chiếu 28 prediction với đề và nhãn nguồn. Lỗi quan trọng: test hỏi 4+6 táo, model lấy 4+4=8; chia 27 bút cho 9 túi bị đổi thành 27/3=9; validation 3,1−0,7 kg bị đổi thành cộng; bài thiếu chiều rộng tự suy đoán hình vuông; hai dạng hình thang mất chia 2; bài ngoài phạm vi vẫn nhận giải. Kết quả JSON hợp lệ và phép tính nội bộ đúng không có nghĩa giải đúng đề hoặc giải thích có chất lượng sư phạm.

Kiểm tra kế hoạch nghiêm có false negative đã quan sát: test 47+13−1=59 dùng một bước hợp lệ, bị loại vì nhãn tham chiếu dùng hai bước. Đánh giá nghiêm hiện tại không phải chứng minh ngữ nghĩa tổng quát. Mẫu rất nhỏ nên không kết luận năng lực từng lớp hoặc hiệu quả trên đề thật.

15 unit tests dữ liệu/evaluator qua trên local và Colab. Chúng xác minh quy trình, không đo chất lượng giải toán. Đã kiểm SHA-256 adapter và đọc safetensors: 392 tensor, 196 tensor LoRA B khác zero. Chưa kiểm reload độc lập hoặc merge/quantize triển khai. Sau khi sửa hiển thị log tiến trình trong cell, chạy lại pilot đã hoàn tất xác nhận chỉ đọc báo cáo; log vẫn đúng 32 bước, không huấn luyện chồng. Lưu bản sao notebook hiện tại trong evidence, không có output hoặc secret.

## Artifact và bước tiếp theo

- [Log, báo cáo, adapter trên Drive](https://drive.google.com/drive/folders/1OCe2mgRt05ffKi1UmgcSdO4EjjZY2PM2)
- [ZIP adapter nghiên cứu](https://drive.google.com/file/d/1xZIzmZmFzWxJz5OdRPrPVHsKU-5AxmdL/view)
- Evidence local: `ai-training/thinking/evidence/pilot32_20261011/`.
- Adapter SHA-256: `70f93e90c0cb673a6b4623cb19cb3840900498391fc950358b5b6c6e296ef34d`.

Không phê duyệt production. Lần tiếp theo cần tập đề thật có lời giải được kiểm độc lập, tăng độ đa dạng train và mẫu thiếu dữ kiện/ngoài phạm vi, train trên đủ tập train và đánh giá đủ validation. Giữ nguyên test hiện tại; nếu điều chỉnh dựa trên các lỗi test đã đọc, phải bổ sung một test mới chưa xem trước khi đánh giá cuối. Bổ sung kiểm tra ngữ nghĩa cách giải và đánh giá sư phạm, không chỉ JSON/phép tính. OCR và solver văn bản hiện là hai mô hình riêng trong cùng dự án/notebook, chưa là một model thị giác hợp nhất.

## Skills Applied

- `google-drive:google-drive`
  - SKILL.md: `C:/Users/My PC/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.20/skills/google-drive/SKILL.md`
  - Why selected: đọc dữ liệu tiến độ/báo cáo trên Drive bằng connector.
  - Applied to: xác minh thư mục run, log huấn luyện và metadata ZIP.

Workspace `.agents/skills/` không có skill ML phù hợp; không áp dụng skill UI/design.
