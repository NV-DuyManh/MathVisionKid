# Bảng so sánh model MathVisionKid — 13/10/2026

Model trong Drive là **TeacherMath v3: Qwen3-1.7B + LoRA**, thuộc phần giải toán. Nó không thay thế CRNN đọc ảnh hoặc YOLO phát hiện vùng bài.

**Kết luận:** adapter mới cải thiện đáp số kèm đơn vị và tuân thủ hướng dẫn so với Qwen3-1.7B gốc trong gói. Chưa chứng minh tốt hơn Qwen3.8-27B/Gemini đang dùng; cả hai dịch vụ bị 429 trước khi hoàn tất mẫu chung. Không thay model, deploy, train hoặc push Git trong lượt đánh giá này.

## Phạm vi và cách kiểm tra

- OCR: 39 file checkpoint (35 cặp weights–vocab khác nhau): 31 OCR dòng tổng quát, 4 bộ đọc riêng số. Các bản trùng hash được gộp và giữ alias.
- Đã chạy inference mới trên cùng 95 dòng DEV (1.097 ký tự, 432 ký tự số/toán tử) và 50 ô số đã đối chiếu ảnh gốc, từ 23 nguồn Drive. Không đọc 5 HOLDOUT đang dành riêng.
- 95 dòng DEV đã được dùng nhiều lần, lịch sử TRAIN của từng model khác nhau; 50 ô số thuộc nguồn TRAIN. Đây là so sánh kỹ thuật trên dữ liệu đã biết, **không phải độ chính xác độc lập trên mọi ảnh**.
- Gói TeacherMath: kiểm tra 19 hash trong bundle và hash adapter, chấm lại 5 × 262 đầu ra đã lưu bằng các hàm chấm thuần đã đọc. Không chạy lại mạng Qwen3-1.7B trên máy này: môi trường không có CUDA, Transformers/PEFT hoặc weights nền.
- 262 ví dụ TeacherMath là dữ liệu tự soạn bằng template; 173 bài giải, 59 gợi ý, 30 bài cần hỏi lại/từ chối. Kết quả định dạng/đường giải chặt không chứng nhận chất lượng sư phạm.
- Các phần phát hiện và xoay ảnh có nhiệm vụ riêng; không trộn mAP với CER hoặc tỷ lệ đáp án thành một điểm tổng.

## 1. Giải toán: thứ hạng trong gói Drive trên cùng 173 bài

Xếp theo **đúng đáp số và đơn vị**, sau đó đúng số. Đây là các chế độ suy luận của 3 bộ weights, không phải 5 model được huấn luyện khác nhau. Chế độ suy luận khác nhau có thể đổi thứ hạng.

| Hạng | Model/chế độ | Đúng số | Đúng số + đơn vị | Đúng đường giải/schema chặt | Gợi ý an toàn theo kiểm tra máy | Hỏi lại/từ chối đúng |
|---:|---|---:|---:|---:|---:|---:|
| 1 | TeacherMath v3 adapter, thinking | 167/173 (96.5%) | 164/173 (94.8%) | 134/173 | 25/59 | 27/30 |
| 2 | TeacherMath v3 adapter, no-thinking | 113/173 (65.3%) | 113/173 (65.3%) | 96/173 | 59/59 | 30/30 |
| 3 | Qwen3-1.7B base, thinking | 165/173 (95.4%) | 101/173 (58.4%) | 1/173 | 0/59 | 3/30 |
| 4 | Qwen3-1.7B base, no-thinking | 138/173 (79.8%) | 91/173 (52.6%) | 0/173 | 0/59 | 4/30 |
| 5 | Qwen3-0.6B base, no-thinking | 76/173 (43.9%) | 52/173 (30.1%) | 0/173 | 0/59 | 0/30 |

Theo báo cáo đánh giá ngữ nghĩa bằng AI kèm gói, adapter thinking có 19/173 bài giải mắc lỗi nghiêm trọng; 30/59 gợi ý lộ đáp án. 137/173 lời giải được đánh giá phù hợp vai trò, nhưng chỉ 15/59 gợi ý phù hợp. Các nhận định này do AI đánh giá, chưa được giáo viên độc lập xác nhận. Vì vậy 96,5% đúng số **không có nghĩa 96,5% bài học tốt**.

## 2. Model đang gọi trong dự án

Mẫu chung đóng băng trước khi gọi: 20 câu, mỗi lớp 1–5 có 2 bài giải, 1 gợi ý và 1 trường hợp hỏi lại/từ chối. Cùng đề và JSON đầu vào chỉ gồm lớp, đề, chế độ; không gửi đáp án chuẩn cho model. Giới hạn đầu ra 2.048 token. API reasoning và môi trường khác Qwen local nên vẫn cần đọc các giới hạn.

| Model | Vai trò | Hoàn thành | Đáp số + đơn vị đúng trên bài đã trả | Trạng thái |
|---|---|---:|---:|---|
| qwen/qwen3.8-27b | Chính | 4/20 | 2/2 | HTTP 429 |
| gemini-3.6-flash | Dự phòng | 6/20 | 4/4 | HTTP 429 |
| qwen/qwen3.6-27b | Tên model dự phòng được cấu hình | Không kiểm tra tiếp | — | Health/catalog ghi model_not_found; không đủ dữ liệu xếp hạng |

**Không xếp Groq/Gemini cao hay thấp hơn TeacherMath từ các mẫu này:** Groq mới trả 4 câu lớp 1, Gemini trả 6 câu lớp 1–2. Số đúng 2/2 hoặc 4/4 quá ít và độ phủ khác nhau. HTTP 429 là lỗi giới hạn dịch vụ, được tách khỏi lỗi toán; không thử key khác hoặc retry để vượt quota.

## 3. OCR dòng tổng quát: toàn bộ 31 cặp trên cùng 95 dòng

Xếp theo ít lỗi số/toán tử, rồi nhiều dòng đúng trọn vẹn, rồi ít lỗi ký tự. Resize chung giữ tỷ lệ (cao 64, rộng 64–1.024), greedy CTC. Kết quả dưới đây không phải cấu hình resize cố định của production. Hạng bằng nhau khi cả ba chỉ số bằng nhau.

| Hạng | Checkpoint | Lỗi số/toán tử / 432 | Dòng đúng / 95 | CER (thấp hơn tốt hơn) |
|---:|---|---:|---:|---:|
| 1 | `math_all_20261013/math_focus/run_control` | 30 | 53 | 9.57% |
| 1 | `math_all_20261013/math_focus/run_weighted` | 30 | 53 | 9.57% |
| 3 | `continuation_20261013/run_head` | 30 | 53 | 9.75% |
| 4 | `continuation_20261013/warm_start` | 31 | 53 | 9.85% |
| 5 | `math_all_20261013/math_layout_retry_20261013/head_candidate_private_v2.pth` | 31 | 52 | 9.66% |
| 6 | `continuation_20261013/run_recurrent` | 31 | 52 | 9.94% |
| 7 | `math_all_20261013/expanded_math_review/run_weighted` | 32 | 52 | 9.75% |
| 8 | `math_all_20261013/expanded_math_review/run_recurrent_resilient` | 32 | 51 | 10.12% |
| 9 | `new2_20261011_266/training_broader/run_warm_anchor` | 33 | 52 | 9.48% |
| 10 | `math_all_20261013/run_pages_head` | 33 | 51 | 10.03% |
| 11 | `math_all_20261013/run_pages_visual` | 33 | 50 | 8.93% |
| 12 | `new2_20261012_24/run_recurrent` | 35 | 52 | 10.30% |
| 13 | `all_recognition_20261011/run_prose` | 35 | 51 | 9.85% |
| 14 | `math_all_20261013/math_more_20261013/run_cnn_only` | 35 | 51 | 10.30% |
| 15 | `all_recognition_20261011/run_stable` | 36 | 51 | 10.12% |
| 16 | `all_recognition_20261011/run_short_prose` | 36 | 51 | 10.39% |
| 17 | `new2_20261011_266/training_followup/run_warm_anchor` | 37 | 53 | 10.30% |
| 18 | `new2_20261011_266/training_mixed/run_warm_anchor` | 38 | 51 | 10.57% |
| 19 | `new2_20261011_266/training_mixed/run_warm` | 42 | 46 | 11.85% |
| 20 | `new2_20261011_266/training_expanded/run02` | 46 | 39 | 12.67% |
| 21 | `new2_20261011_266/training_expanded/run01` | 60 | 40 | 13.49% |
| 22 | `new2_20261011_266/training_mixed/run_cold` | 70 | 25 | 14.40% |
| 23 | `new2_20261011_266/training_expanded/development_preserve_prose/run01` | 72 | 25 | 15.31% |
| 24 | `new2_20261011_266/training/run02` | 72 | 25 | 15.59% |
| 25 | `candidate_visual_20261008/run01` | 74 | 18 | 16.41% |
| 26 | `new2_20261011_266/training/run01` | 83 | 18 | 17.68% |
| 27 | `candidate_fields_20261008/run01_aspect` | 93 | 15 | 19.69% |
| 28 | `candidate_recurrent_20261008/run01` | 96 | 16 | 19.42% |
| 29 | `candidate_line_20261008/run01` | 98 | 13 | 22.33% |
| 30 | `CRNN 320 lớp đang sử dụng` | 105 | 15 | 25.43% |
| 31 | `CRNN 237 lớp cũ, không đang phục vụ` | 333 | 2 | 52.69% |

**Control cấu hình đang phục vụ:** cùng weights CRNN 320 lớp với resize cố định 64 × 1.024 có CER 40.11%, 242/432 lỗi số/toán tử, 3/95 dòng đúng trên mẫu này. Khác biệt resize là một phần kết quả; không quy mọi chênh lệch cho weights.

Một số checkpoint thử nghiệm tốt hơn weights production trên bộ toán đã biết này, nhưng không model nào được tự động promote: bảng này không thay thế kiểm tra độc lập, hồi quy văn bản thường, bố cục ảnh và tiêu chí phát hành.

## 4. Bộ chỉ đọc số: 4 cặp riêng trên cùng 50 ô số

Chỉ phù hợp ô số không dấu đã xác minh. Không được dùng để đọc lời văn, biểu thức hoặc phân số xếp tầng. Điểm là đầu ra raw, chưa xóa khoảng trắng.

| Hạng | Checkpoint | Ô đúng / 50 | Lỗi số / 90 ký tự | CER |
|---:|---|---:|---:|---:|
| 1 | `candidate_numbers_20261008/run02_visual_dev_only` | 48 | 2 | 2.22% |
| 2 | `candidate_numbers_20261008/run03_contrast_dev_only` | 47 | 3 | 3.33% |
| 3 | `candidate_numbers_20261008/run06_expanded_dev` | 47 | 3 | 3.33% |
| 4 | `candidate_numbers_20261008/run01` | 46 | 4 | 4.44% |

## 5. Các model phát hiện và định hướng

| Model | Vai trò | Tình trạng so sánh |
|---|---|---|
| YOLOv8n MathVision | Phát hiện vùng bài | Hai file `math_detection_yolo11n.pt` và `yolov8n_mathvision_det_v1.pt` có cùng SHA-256 `e78f8fa5…`; là cùng weights, không phải hai model để xếp hơn/kém. Manifest gọi kiến trúc YOLOv8n. |
| PP-OCRv3 ONNX 2023may | Phát hiện vùng chữ | Đang dùng; không có detector cùng nhiệm vụ khác với bộ nhãn chung để xếp hạng. |
| PP-OCR mobile v2 orientation classifier | Phân loại hướng chữ | Model thử cho định hướng; chưa có kiểm thử chung độc lập để xếp hạng chất lượng. |

## Nguồn và kiểm tra bảo toàn

- Gói được chủ dự án cung cấp: [TeacherMath v3 trên Drive](https://drive.google.com/drive/folders/1cBCKxNB3CdOr6wL06xpNEYOxbLc4YiVi).
- Adapter SHA-256: `20e99388093c5f7caa1aacaac2a6014cdc0bfd4b4b1bb6f25b5a593ea8beae8d`.
- Toàn bộ bảng OCR có CSV kèm theo: `report/MODEL_LEADERBOARD_20261013.csv`, gồm alias và hash của cả 35 cặp.
- Evidence riêng: `ai-training/datasets/drive_math/model_comparison_20261013/` — frozen policies, mọi prediction/metrics, kiểm tra hash, lỗi API tách riêng. Không đưa hidden thinking vào báo cáo.
- Gói có `production_approved=false`; weights nền 1.7B/0.6B không được tải về máy để rerun. Chỉ adapter và đầu ra kèm gói được kiểm tra từ Drive.
- Các hash weights/vocab/source benchmark giữ nguyên sau kiểm tra. Không lưu ảnh gốc, crop, ZIP hay Parquet vào thư mục phase; các thư mục ảnh đã xóa vẫn vắng mặt.
- Không train, thay cấu hình, cài thư viện GPU, mua dịch vụ, deploy hay commit/push.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: reuse inspected scorers, CRNN/CTC, bounded Drive source reader and existing verified references.
  - Applied to: source-preserving OCR inference, checkpoint/vocab deduplication, supplied-result recalculation, common small provider benchmark and task-separated reports.
