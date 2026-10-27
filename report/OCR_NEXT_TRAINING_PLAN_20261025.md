# Kế hoạch cải thiện OCR có kiểm chứng — 25/10/2026

Mục tiêu là ứng viên chữ và toán đủ điều kiện thay model hiện tại. Không thể chứng minh model “hoàn hảo” trên mọi ảnh; tiêu chí phát hành giữ nguyên: exact ≥95%, CER ≤2%, không mất các transcript/số/dấu/đơn vị đang đúng, kèm acceptance độc lập và chú thích toàn trang đầy đủ.

## Điểm xuất phát

Vòng trước đạt 19/22 vùng số VAL và 76/86 vùng số chẩn đoán; prose VAL còn 20 lỗi/197 ký tự. Bản số vẫn có hồi quy `22 → 21`; bản chữ đổi một dòng cũ `cá dữ` thành `cá cữ`. Vì vậy chưa thay model trong app.

Audit TRAIN mới xác nhận bản số đọc đúng 225/225 vùng vở cũ, nhưng còn 11 lỗi trong 58 vùng số mới. Số 0 và số lặp đều còn lỗi dù đủ timestep CTC. Không đưa những lỗi DEV/VAL/chẩn đoán vào TRAIN.

## Các bước và quyết định

1. **Đóng băng dữ liệu và cách chọn trước train.** Giữ 1.459 TRAIN số và 677 TRAIN fulltext đã rà, các SHA nguồn và split không giao nhau. Chỉ dữ liệu TRAIN có gradient; VAL dùng chọn/loại checkpoint. Không mở pixel TEST/HOLDOUT. Mỗi thử nghiệm mới có thư mục, policy và code hash riêng; không sửa bằng chứng vòng trước.
2. **Số: thử giữ encoder và đối chiếu teacher gốc.** Hai recipe 20 epoch ×240 updates: một recipe giữ CNN, cập nhật RNN/head từ ứng viên tốt nhất; một recipe cập nhật từ original reduced13. KL chỉ dùng teacher đọc đúng transcript TRAIN. Sampling theo nguồn giữ hàng đợi xuyên epoch, đảm bảo log coverage thật. Bảo vệ từng dòng đúng trong hợp các đối chứng trên old65 và 19 dòng new22 hiện đúng; không bù lỗi dòng này bằng dòng khác.
3. **Chữ: thử retention mạnh và guard từng dòng.** Hai recipe 30 epoch ×100 updates, chỉ head chữ; LR1e-5, KL2/KL8. Guard bảo vệ hợp transcript đúng của parent gốc và bản chữ trước trên old22/new39, số/dấu và đơn vị đo đang đúng. Tái tính VAL full CRNN trên CPU mỗi epoch. Hai bước 2–3 đã hoàn tất 100 epoch theo lịch cố định nhưng chưa qua guard; không phát hành checkpoint cập nhật của chúng.
4. **Thử một giả thuyết khác về chữ, thay vì lặp lại lịch cũ.** Chỉ cho cập nhật nguyên âm tiếng Việt có/không dấu và chữ hoa, giữ phụ âm thường/số/dấu/blank cố định. Mask được định nghĩa bằng bảng chữ cái, không chọn ký tự riêng theo lỗi VAL. Hai recipe LR1e-5 và3e-5, KL2, cùng 677 TRAIN và guard ở bước3. Chốt mask, seed, số bước, recipe trước chạy; checkpoint không đạt guard sẽ bị loại, kể cả khi tổng CER giảm.
5. **Nạp lại và chấm độc lập với bước train.** Chọn bằng VAL trước khi đọc DEV/chẩn đoán; sau đó chạy oldDEV95/16, cùng bốn trang chẩn đoán, 31 cặp phân số và57 đề xuất hình học cố định. So từng transcript, số0/số lặp, dấu toán và đơn vị literal với original cùng ứng viên trước. Không chọn lại recipe bằng điểm chẩn đoán. Tất cả đối chứng phải tái lập, sai roundtrip thì chặn đánh giá.
6. **Rà khả năng tăng dữ liệu hoặc đổi backbone.** Kiểm inventory/checkpoint thật trong Drive và nguồn mô hình tiếng Việt chính thức. Chỉ thử model mới khi xác minh weights/vocab/license/cách tiền xử lý; phải đo baseline trên cùng protocol trước fine-tune. Không tuyên bố “model tốt hơn” chỉ theo tên hoặc điểm quảng cáo. Nếu các thử nghiệm có kiểm soát vẫn bão hòa, cần thêm transcript chữ có dấu/nét mảnh, số lặp/đơn vị từ nguồn mới được rà nhãn và tách người viết, thay vì tăng epoch vô hạn trên cùng vài trăm crop.

## Điều kiện phát hành và giới hạn

**Cập nhật sau thực hiện:** hoàn tất cả bước thử nghiệm số và chữ nêu trên:6trial/160epoch cố định. Bản nguyên âm/chữ hoa mới giữ được các dòng đúng của hai đối chứng trên các tập đã kiểm và giảm DEV105→104lỗi, nhưng còn xa ngưỡng phát hành. Các trial số bị loại. Đối chứng VietOCR chưa tải đủ weights nên chưa benchmark. [Kết quả và bằng chứng thực hiện](OCR_GUARDED_TRAINING_RESULTS_20261025.md).

- Mọi checkpoint phải có hash, shape/finite, log epoch/coverage, và roundtrip transcript CPU sau lưu/nạp. Epoch0 giữ parent phải được gọi là từ chối cập nhật, không gọi là cải thiện.
- Ngoài tổng CER/exact, bất kỳ mất dòng đang đúng, mất chữ số/dấu hay đổi đơn vị đúng đều chặn phát hành. Helper đơn vị chỉ là kiểm tra bổ sung cho các đơn vị đã định nghĩa và token trong ngoặc, không phải parser mọi đơn vị tiếng Việt.
- VAL/DEV và bốn trang đã xem nhiều vòng là dữ liệu phát triển. Chưa có xác nhận giáo viên độc lập, tách người viết hoặc tách dữ liệu tiền huấn luyện; chú thích trang còn một phần nên chưa chấm precision/đọc toàn trang.
- Head số13 lớp không thay được nhận diện chữ tiếng Việt hoặc phân tích bố cục phân số2D. Việc ghép recognizer chữ/toán với detector chỉ được đưa vào app sau kiểm thử toàn tuyến.
- Runtime app, giao diện, model production và Git được giữ nguyên trong các thử nghiệm này. Báo cáo kết quả thực tế sẽ ghi cả thử nghiệm thất bại và các điều kiện còn thiếu.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Controlled OCR training and regression validation in the existing Python pipeline.
  - Applied to: Reuse the CRNN/data loaders, restrict each hypothesis, keep frozen evidence, and reject regressions without adding a new training framework.
