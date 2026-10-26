# MathVisionKid — model giải toán tiếng Việt, bước thử đầu tiên

Ngữ cảnh, báo cáo mới nhất và bước tiếp tục được duy trì tại [MATH_TRAINING_CONTEXT.md](../MATH_TRAINING_CONTEXT.md). Đọc và cập nhật chính file đó sau mỗi đợt làm; không tạo báo cáo Markdown mới cho từng đợt.

Đợt dữ liệu11/10 đã hoàn tất bộ kiểm `scope_planner_v1`: 2.116 mẫu, schema kế hoạch có tham chiếu dữ kiện, runtime chặn kế hoạch sai,41 tests local và26 tests Colab. Code bắt đầu ở `scope_contract.py`; dữ liệu/SFT/schema ở `data/scope_planner_v1/`, evidence ở `evidence/scope_planner_v1/`. Khi kết thúc đợt11/10 chưa train adapter mới; SFT đã hoàn tất12/10 như đoạn dưới. Bộ kiểm hỗ trợ32 cách diễn đạt cố định của bốn dạng toán cơ bản; không nhận là solver toàn bộ lớp1–5. Các kết quả pilot ở phần còn lại thuộc run cũ.

Ngày12/10/2026 đã train adapter planner một epoch đủ1.852 mẫu/463 bước. Raw-plan accuracy đạt133/133 validation và131/131 synthetic dev-test; reload/audit qua. 46 tests local/31 tests Colab qua. Đây là kiểm tra nhiệm vụ kế hoạch có schema và bộ tính cho bốn dạng, chưa phải accuracy giải mọi đề thật hoặc lời giải sư phạm. Evidence ở `evidence/planner_sft_20261012/`; chi tiết và link ZIP trong file ngữ cảnh duy nhất phía trên. Không huấn luyện lại pilot hoặc dùng dev-test đã đọc làm test cuối độc lập.

Model nền: `Qwen/Qwen3-0.6B`. Đây là phần giải toán bằng văn bản, đứng sau bước đọc và xác nhận đề. Không biến checkpoint CRNN/OCR thành LLM, không dùng lỗi sai của học sinh làm lời giải chuẩn.

Đã thêm và thực thi phần THINKING ngay trong notebook Colab đang dùng:
https://colab.research.google.com/drive/17aUDHsE5hyYeDCFb3Z-iG8hRnGwvfcZM

Chạy riêng phần THINKING cuối notebook. Các cell OCR phía trên vẫn là quy trình gộp checkpoint cũ; không dùng Run all để bắt đầu phần toán.

## Dữ liệu và phạm vi

`dataset.py` tạo 1.670 mẫu có đề tiếng Việt, giải thích ngắn, kế hoạch phép tính, đơn vị và đáp số: train 1.474, val 92, test 104. Gồm 12 họ bài từ lớp 1–5: cộng/bớt, gộp sách, nhóm bằng nhau, chia đều, thêm rồi bớt, tổng–hiệu, cộng phân số cùng mẫu, diện tích chữ nhật, cộng/trừ thập phân, diện tích hình thang. Có một số mẫu yêu cầu bổ sung dữ kiện và từ chối ngoài phạm vi.

Nguồn là mẫu sinh bằng chương trình. `human_verified=false`; không ghi gold hoặc nhận là lời giải giáo viên đã duyệt. Phép tính được kiểm bằng phân số chính xác. Các biến thể của cùng dữ kiện, kể cả hoán đổi các lượng có thể đổi chỗ, ở cùng split. Val/test dùng cách diễn đạt riêng.

Đây là dữ liệu thử quy trình, chưa phủ toàn bộ chương trình toán Việt Nam và chưa phải benchmark đề thật của học sinh. Mẫu hỏi lại/từ chối còn ít. Backend vẫn cần giới hạn lớp/dạng toán; fine-tune không xóa kiến thức khác của model nền.

## Pilot

Colab được kiểm tra thực tế: Tesla T4, Python 3.13.15, PyTorch 2.11.0+cu130, Transformers 5.18.0, PEFT 0.21.1. LoRA FP16, rank 16, alpha 32, learning rate 1e-4, batch 1, tích lũy 4, giới hạn 1.024 token. Pilot chạy 32 bước cập nhật, tương đương 128 lượt mẫu; chưa phải huấn luyện đủ cả tập qua nhiều epoch.

Chỉ phần assistant góp vào loss. Mẫu quá dài bị chặn thay vì cắt mất đáp số. Đo model nền trước train; dùng cùng 14 mẫu validation cố định để so sánh và 14 mẫu test cố định sau train. Không dùng test chọn checkpoint. Số lượng đánh giá nhỏ được ghi rõ trong báo cáo.

Đo riêng JSON hợp lệ, đáp số, đơn vị, phép tính trong từng bước và khớp kế hoạch mẫu. Khớp kế hoạch là kiểm tra nghiêm với template; có thể loại một cách giải tương đương. Phép tính đúng không tự chứng minh giải thích tiếng Việt có chất lượng sư phạm.

Adapter và trạng thái optimizer/RNG được lưu mỗi 8 bước, hỗ trợ tiếp tục pilot đúng dữ liệu/model revision. Model gốc được ghim theo commit Hugging Face trong `config.json`. Chạy lại pilot đã hoàn tất chỉ đọc báo cáo; không huấn luyện chồng lên nó. Adapter cần model nền để chạy, chưa phải file model hợp nhất/quantized.

## Nơi lưu trên Drive

Tên thư mục thật có một khoảng trắng đầu tên:

```text
/content/drive/MyDrive/ MathVisionKidAI/ai-training/thinking/math_text_pilot_v1/
  ocr_cells_before_thinking_20261011.json
  source_inspection.json
  src/
  data/{train,val,test}.jsonl
  data/dataset_report.json
  runs/qwen3_06b_lora_pilot32_seed20261011/
    config.json
    token_audit.json
    fixed_eval_ids.json
    baseline_val.jsonl
    training_log.jsonl
    resume_state.pt
    adapter/
    candidate_val.jsonl
    candidate_test.jsonl
    completed_run.json
```

Pilot đã hoàn tất ngày 11/10/2026. [Kết quả và log trên Drive](https://drive.google.com/drive/folders/1OCe2mgRt05ffKi1UmgcSdO4EjjZY2PM2). [ZIP adapter nghiên cứu](https://drive.google.com/file/d/1xZIzmZmFzWxJz5OdRPrPVHsKU-5AxmdL/view).

| Chỉ số | Model nền, validation | Adapter, validation | Adapter, test |
|---|---:|---:|---:|
| Đáp số đúng trên 12 bài đủ dữ kiện | 6/12 | 8/12 | 7/12 |
| Phép tính nội bộ nhất quán | 5/12 | 10/12 | 10/12 |
| Đơn vị đúng | 5/12 | 12/12 | 12/12 |
| Kế hoạch khớp nghiêm với mẫu | 3/12 | 8/12 | 6/12 |
| Hỏi lại/từ chối đúng trên 2 mẫu | 0/2 | 0/2 | 0/2 |
| JSON parse được trên 14 mẫu | 14/14 | 14/14 | 14/14 |

Tập test có một cách giải gộp bước hợp lệ bị kiểm tra kế hoạch nghiêm loại. Chỉ số phép tính nội bộ cũng có thể đạt khi model lấy sai dữ kiện hoặc chọn sai phép toán. Ví dụ test `4 + 6` bị đổi thành `4 + 4 = 8`; đề thiếu chiều rộng bị tự suy đoán thành hình vuông. Không sử dụng adapter này cho học sinh ở trạng thái hiện tại. Chưa đo model nền trên test nên không kết luận cải thiện test so với model nền.

Đã chạy 32 bước, 128 lượt mẫu, loss từ 1,835 xuống 0,067; 10.092.544 tham số LoRA được huấn luyện. SHA-256 adapter: `70f93e90c0cb673a6b4623cb19cb3840900498391fc950358b5b6c6e296ef34d`. Kiểm tra file bằng safetensors xác nhận 196 tensor LoRA B khác zero; chưa phải kiểm tra reload độc lập trên máy triển khai. `evidence/pilot32_20261011/` chứa báo cáo, đối chiếu prediction và bằng chứng giữ nguyên 8 cell OCR.

Môi trường Colab có torchao 0.10.0 không tương thích PyTorch 2.11. Cell THINKING huấn luyện cài torchao 0.17.0 và chạy tiến trình Python mới; không thay torch/CUDA. Lần lỗi đầu chưa cập nhật trọng số, baseline đã được giữ nguyên.

## Kiểm tra local

```powershell
python -m unittest discover -s ai-training/thinking -p 'test_*.py' -v
python ai-training/thinking/dataset.py --output ai-training/thinking/data/pilot_v1
```

15 test kiểm tra dữ liệu, cách chia tập, provenance, tính toán và evaluator đã qua trên local và Colab. Không dùng test kỹ thuật để tuyên bố độ chính xác model.

Skills applied: `google-drive:google-drive` — đọc metadata và log Drive trong khi Colab chạy. Workspace không có skill ML phù hợp; không tải các skill UI/design.
