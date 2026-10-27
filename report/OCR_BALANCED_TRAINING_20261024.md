# OCR chữ, số và phân số — lượt huấn luyện 24/10/2026

Đã thực sự chạy hai ứng viên, mỗi ứng viên 8 epoch, trên 1.247 mẫu TRAIN. Ứng viên recurrent tiến bộ rõ trên VAL số mới, nhưng cả hai hồi quy ở bộ bài cũ. **Không thay model của app.** Trọng số production, cấu hình chạy và các màn hình được bảo vệ đều giữ nguyên.

## Kết quả đo

Các điểm dưới đây so với **parent thử nghiệm math_focus/run_control**, không phải một so sánh chỉ thay trọng số production. Parent và ứng viên cùng vocab, cùng resize giữ tỷ lệ và cùng cách giải mã greedy CTC. CER là số lỗi ký tự chia số ký tự tham chiếu, càng thấp càng tốt.

| Phép đo | Parent | CTC head | BiLSTM + CTC head |
|---|---:|---:|---:|
| VAL mới: đúng toàn vùng / 65 | 19 | 31 | **44** |
| VAL mới: CER, 187 ký tự | 41,71% | 24,06% | **13,90%** |
| VAL mới: lỗi chữ số/dấu | 34 | 28 | **20** |
| DEV cũ: đúng toàn vùng / 95 | **53** | 41 | 34 |
| DEV cũ: CER, 1.097 ký tự | **9,57%** | 10,94% | 11,85% |
| DEV cũ: lỗi chữ số/dấu | **30** | 34 | 33 |
| Chữ tiếng Việt DEV: lỗi ký tự / 494 | **29** | 31 | 34 |
| Chữ tiếng Việt DEV: đúng toàn vùng / 22 | **9** | 8 | 7 |
| Tử/mẫu DEV: đúng toàn vùng / 11 | 7 | 7 | 7 |
| Nhiều số 0 DEV: lỗi chữ số/dấu | **4** | 6 | 6 |
| Nhiều số 0 DEV: đúng chuỗi số/dấu / 8 | **5** | 3 | 3 |

VAL mới được dùng chọn checkpoint, nên điểm này không phải điểm kiểm thử cuối độc lập. DEV cũ đã được dùng ở nhiều vòng trước, cũng không phải tập đánh giá độc lập mới. Chưa đo toàn luồng ảnh trang → phát hiện vùng → ghép phân số hai chiều. Kết quả 7/11 là crop tử/mẫu riêng lẻ, không phải 7/11 phân số hoàn chỉnh.

## Dữ liệu và cách train

- Giữ 501 TRAIN cũ hợp lệ, gồm **136 dòng prose** nhận supervised CTC trực tiếp và 62 crop tử/mẫu. Hai nhãn TRAIN không chắc chắn tiếp tục bị loại. Giữ nguyên 95 DEV tách theo trang, không dùng để chọn checkpoint trong lượt này.
- Đọc gói thật `arithmetic_ocr_line_full_v1_2.zip` từ Drive. Manifest chứa 5.481 crop: 882 được bên cung cấp đánh dấu `HUMAN_VERIFIED`, 4.599 là synthetic. Không nhầm với fixture 9 ảnh tổng hợp trong repo.
- Nhóm chữ tay của gói gồm 749 TRAIN, 65 VAL, 68 TEST. Rà trực quan 12 TRAIN trước khi chạy và loại 3 crop cắt nét; còn **746 TRAIN mới**, cộng 501 cũ thành 1.247. Không dùng ảnh tổng hợp hoặc nhãn do model tự sinh.
- Xác minh manifest SHA256, TSV split, crop SHA256 và kích thước. Metadata source/crop không trùng giữa split, không trùng 72 trang của bộ cũ và không trúng hash HOLDOUT bị cấm. Hash ảnh trang của gói là metadata bên cung cấp; lượt này không mở lại ảnh trang gốc để xác minh chúng.
- Giữ nguyên full vocab **321 lớp** của parent. CNN đông cứng; một ứng viên cập nhật CTC head, một ứng viên thêm BiLSTM. LR head `1e-5`, LR BiLSTM `2e-6`, batch 8, seed `20261024`, 8 epoch mỗi ứng viên. Prose trọng số 4, tử/mẫu 3, còn lại 1; KL retention 2 trên 409 TRAIN parent đọc đúng hoàn toàn. Teacher chỉ làm regularization, không tạo nhãn mới.
- Chọn checkpoint theo ít lỗi ký tự trên 65 VAL số, rồi số vùng đúng. Cả hai chọn epoch 8. Chốt cả hai checkpoint và hash **trước khi mở 95 DEV cũ**. Không chỉnh hyperparameter rồi train tiếp sau khi thấy điểm DEV.
- Chạy bằng Python/PyTorch CPU hiện có, tổng 379,99 giây. GPU có trên máy nhưng môi trường torch của lượt này không hỗ trợ CUDA; không báo đã train GPU hoặc cloud.

Nguồn Parquet chữ tiếng Việt có 59.247 supplied TRAIN và 1.000 supplied TEST. Manifest hiện vẫn `provided_unverified`, `training_eligible=false`; lượt này không ngầm nâng nhãn đó thành giáo viên xác minh hoặc đưa vào train. Đây cũng là nguồn tiền huấn luyện của baseline theo model card, không phải dữ liệu đánh giá mới độc lập. Các JPG alias byte-exact không được đếm thành mẫu mới.

## Lỗi chất lượng crop đã tìm ra

Sau khi chốt lượt chạy, audit bổ sung kiểm tra toàn bộ 746 TRAIN mới: hash và kích thước đều khớp, nhưng 431 crop có mực chạm biên; 400 vượt ngưỡng cảnh báo dải biên. Đây là heuristic cần rà, không phải kết luận 400 nhãn sai.

Rà trực quan thêm 24 crop từ 24 trang, chọn độc lập với dự đoán model: 10 rõ, 6 cắt nét nhưng còn nhận ra, 7 cần đối chiếu nét lân cận, 1 cắt quá nhiều để xác nhận toàn nhãn. Ví dụ `src_07f36c61_row_01_4bd44006`, nhãn cung cấp `-354`, mất nhiều nét ở phía trên. `HUMAN_VERIFIED` trong manifest không bảo đảm crop còn nguyên ký tự.

Đã lập hàng đợi **17 mẫu cần đối chiếu nguồn cho lượt tiếp theo**: 3 crop loại trước train và 14 crop có vấn đề từ audit bổ sung. Không sửa nhãn bằng phép tính hoặc dự đoán model, không hồi tố thay TRAIN hay điểm của lượt đã hoàn tất. Cần lấy lại ngữ cảnh ảnh gốc trước khi sửa box; thêm viền trắng không phục hồi được nét đã mất.

## Kiểm chứng và quyết định phát hành

- Self-check packed LSTM, độ dài thật, loại DEV/HOLDOUT/nhãn cách ly, phân biệt chuỗi số 0: đạt. Compile Python đạt; loss, gradient và tensor checkpoint hữu hạn.
- Một tiến trình Python mới đọc lại đúng 65 VAL vào RAM, kiểm tra SHA/kích thước, nạp checkpoint serialize và suy luận lại parent + recurrent: **65/65 chuỗi đầu ra của mỗi model khớp chính xác với kết quả đã lưu**. Không đọc TEST/HOLDOUT.
- Tính lại metric 95 DEV từ chuỗi dự đoán đã lưu khớp kết quả train. 46 file dependency không đổi; 66 kiểm tra hash kế thừa đều khớp tại baseline. Baseline dependency được lập sau khi tiến trình train khởi chạy nhưng không có agent nào sửa các file đó.
- Checkpoint chỉ thay tensor `fc.*` hoặc `rnn.*`; CNN không đổi. Tất cả input đóng băng và file UI được bảo vệ khớp hash cuối lượt.
- Production OCR vẫn SHA256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`. Không commit/push, không đổi runtime, không sao chép ảnh nguồn ra đĩa.

**Cả hai ứng viên bị loại khỏi production** do hồi quy chữ, biểu thức và chuỗi nhiều số 0. Mọi split của gói số được đánh dấu `seen_by_yolo_training=YES`, writer_id không có; không được gọi đây là bằng chứng độc lập toàn pipeline hoặc khác người viết. TEST 68 crop chữ tay và HOLDOUT vẫn chưa đọc pixel.

Ưu tiên tiếp theo: đối chiếu và sửa crop từ ảnh gốc, bổ sung chữ tiếng Việt/tử-mẫu đã rà theo trang/người viết, sau đó đánh giá recognizer chữ và recognizer số riêng. Chưa có bằng chứng rằng tăng epoch tiếp trên cùng dữ liệu sẽ giải quyết các hồi quy này.

## Tệp tái lập

Tất cả tệp sau nằm ở `ai-training/datasets/drive_math/math_balanced_expansion_20261024/`:

- `train.py`, `policy_visual_reviewed.json`, `train.log`: code, cấu hình và log thực thi. `policy.json` là bản chuẩn bị ban đầu **chưa chạy**, đã được thay bằng policy có 3 loại trừ trước train; không dùng bản đó để tái lập kết quả.
- `balanced_head.pth`, `balanced_recurrent.pth`, `frozen_candidates.json`: hai checkpoint thử nghiệm và hash chốt.
- `result.json`, `release_gate.json`: dự đoán, metric và lý do không phát hành.
- `verification.json`, `dependency_audit_before.json`, `dependency_audit_after.json`, `final_integrity.json`: bằng chứng kiểm chứng.
- `pixel_quality_followup.json`, `next_run_source_review.json`: audit crop và hàng đợi đối chiếu nguồn.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Công cụ Python cho huấn luyện và đánh giá OCR; registry chưa có skill chuyên OCR/training.
  - Applied to: Tái sử dụng CRNN, reader Drive RAM-only, preprocessing, CTC packing và metrics hiện có; dùng PyTorch/stdlib đã cài, không thêm framework hoặc thay code app.
