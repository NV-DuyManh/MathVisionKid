# Thử model công thức và phối hợp OCR — 22/10/2026

**Có tín hiệu cải thiện trong nhánh thử riêng:** CRNN kết hợp PP-FormulaNet_plus-S để gợi ý tầng bị bỏ trống tăng từ **7/11 lên 9/11 vùng tử–mẫu DEV đúng**, và từ **2/5 lên 4/5 phân số đầy đủ đúng**. Đây là tập nhỏ trên một trang DEV đã dùng trước đó; chưa đủ bằng chứng để thay model trong ứng dụng hoặc gọi là kết quả nghiên cứu độc lập.

Không fine-tune hay thay trọng số trong lượt này. Đã chạy model chuyên công thức thật trên ảnh Drive, kiểm tra nhánh phối hợp offline và lập hồ sơ rà nguồn. Không cập nhật nhãn TRAIN từ dự đoán.

## Đã thử những gì

Theo [tài liệu chính thức PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/formula_recognition.en.md), model công thức trả về LaTeX. Lượt này tải đúng trọng số chính thức PP-FormulaNet_plus-S và PP-FormulaNet_plus-M vào thư mục thí nghiệm ngoài Git, ghi hash gói tải và kiểm tra từng file giải nén khớp gói.

Tạo môi trường Python riêng `ai-training/.venv-formula`; phiên bản chính: PaddlePaddle 3.2.2, PaddleOCR 3.3.2, PaddleX 3.3.10. Không cài chúng vào runtime ứng dụng. Ảnh gốc và crop chỉ xử lý trong RAM từ Drive G:, không tải ảnh mới vào các thư mục người dùng từng xóa, không gửi ảnh sang dịch vụ AI bên ngoài.

Ba cấu hình:

1. **S:** PP-FormulaNet_plus-S với crop gốc.
2. **M:** PP-FormulaNet_plus-M với crop gốc.
3. **S-ink:** bản S với góc nhìn đen–trắng từ bộ `_ink(neutral=True)` hiện có của dự án. Giữ các nét được phát hiện, nền trắng, quay về crop gốc nếu tỷ lệ nét dưới 0,5%. Không giải toán hoặc sửa ký tự trong bước này. Đây là nhánh thí nghiệm; lọc màu có thể bỏ nét chì/đen khi ảnh có cả mực màu.

## Dữ liệu và quy trình chấm

Đóng băng 167 yêu cầu từ **16 ảnh gốc Drive**:

- 73 vùng toán DEV đã có, trong đó có 11 vùng tử/mẫu.
- 62 vùng tử/mẫu TRAIN đủ điều kiện. Chỉ dùng để đánh giá ở lượt này, không nhận gradient.
- 32 crop ghép phân số: 27 TRAIN và 5 DEV. Ghép theo vai trò đã rà, cùng nguồn/split, tử ở trên mẫu và giao nhau theo chiều ngang. Không dùng giá trị nhãn để chọn cặp. Chín vùng thành phần không ghép được một cách duy nhất được giữ riêng, không tự thêm tầng còn thiếu.

Đã xem trong RAM 32 crop ghép: có đúng hai tầng và gạch phân số tương ứng. Một số crop còn nét lân cận/dấu phép tính ở mép; vì vậy đây là chẩn đoán trên bố cục được hỗ trợ bằng metadata, không phải hệ thống tự phát hiện phân số toàn trang. Kiểm tra của agent không thay thế xác nhận nhãn độc lập của giáo viên.

Hash ảnh gốc và pixel của 135 crop thành phần khớp hồ sơ trước. Crop ghép có hash riêng để tái lập. Hai vùng mơ hồ và nguồn HOLDOUT tiếp tục bị loại trước khi đọc/chấm.

S và S-ink hoàn tất **167/167** yêu cầu mỗi cấu hình. M đã lưu **164/167**, gồm đủ **73 vùng toán DEV + 5 crop phân số DEV**; ba yêu cầu TRAIN cuối chưa hoàn tất. Tổng có **498 lần suy luận được lưu**, không gọi đây là 498 mẫu độc lập.

## Chất lượng khi dùng model công thức đơn lẻ

| Cấu hình | Đúng 73 vùng toán DEV | Đúng 11 vùng tử/mẫu DEV | Đúng 5 crop phân số DEV |
|---|---:|---:|---:|
| CRNN đối chứng thí nghiệm | 53/73 | 7/11 | 2/5 khi ghép hai bản đọc thành phần |
| S, crop gốc | 15/73 | 4/11 | 3/5 |
| M, crop gốc | 29/73 | 4/11 | 3/5 |
| S-ink | 19/73 | 5/11 | 2/5 |

**Các số ở bảng này dùng cùng phép chuẩn hóa trình bày toán:** bỏ khoảng trắng/ngoặc nhóm TeX, thống nhất cách viết dấu chia và số mũ, giữ nguyên chữ số, dấu ngoặc toán và quan hệ tử–mẫu. Không rút gọn hoặc tính toán để chấm đúng. `x` không bị đổi thành `×`; `13` khác `3`, `300` khác `30`.

Do chuẩn hóa trình bày, đối chứng ở đây là 53/73; số khớp toàn chuỗi theo phép chuẩn hóa khoảng trắng cũ là 44/73. Không trộn hai thước đo này hoặc so bảng này trực tiếp với 53/95 của báo cáo cũ. Không có số đo mới về độ chính xác toàn bộ ứng dụng.

Model công thức riêng lẻ **chưa phù hợp để thay CRNN** trên tập này. S-ink có sửa được một số trường hợp nhưng cũng gây nhiều hồi quy; chưa có bằng chứng áp dụng bộ lọc đó cho mọi ảnh là tốt.

Bản M có các lần sinh LaTeX lặp dài, một crop mất **177,09 giây**. Controller dừng tiến trình sau khoảng **984 giây tính từ lúc khởi chạy** khi vượt ngân sách dự kiến 15 phút; một yêu cầu đang chạy không thể được ngắt bởi kiểm tra thời gian giữa hai yêu cầu. Giữ nguyên log và các giả thuyết đã lưu, không chấm ba yêu cầu chưa có kết quả là đọc sai hoặc đọc đúng. Summary M được tổng hợp lại từ JSONL đã lưu sau khi dừng; không chạy lại model để điền dữ liệu thiếu.

S hoàn tất phần đọc nguồn/suy luận trong 137,66 giây, S-ink 171,61 giây; không gồm tải và khởi tạo model. Thời gian M tính từ tiến trình và có yêu cầu bị ngắt, nên không dùng ba số này như phép benchmark tốc độ tương đương.

## Nhánh phối hợp đã chấm riêng

Quy tắc offline nằm trong `scripts/data/fraction_draft.py`:

1. Nếu CRNN đã đọc đủ hai tầng thì giữ nguyên, dù model công thức có bản đọc khác.
2. Nếu CRNN bỏ trống hoặc đánh dấu `?` ở một tầng, chỉ đề xuất điền khi model công thức trả về đúng một phân số hoàn chỉnh, cả hai tầng đều đọc được và khớp mọi tầng CRNN còn đọc được.
3. Nếu không thỏa điều kiện thì giữ bản đọc CRNN. Không dùng nhãn tham chiếu hoặc đáp án toán trong lựa chọn này.
4. Mọi kết quả đều là `MODEL_DRAFT`, `needs_source_review=true`, `training_eligible=false`, kể cả khi các model đồng ý. Mẫu số 0 vẫn được giữ đúng bản đọc và chuyển rà soát, không sửa bằng suy luận toán.

| Nguồn gợi ý khi CRNN thiếu tầng | Đúng 11 thành phần DEV sau phối hợp | Đúng 5 phân số DEV sau phối hợp | Cặp được điền thêm |
|---|---:|---:|---:|
| S, crop gốc | **9/11** | **4/5** | 2 |
| M, crop gốc | 8/11 | 3/5 | 1 |
| S-ink | 8/11 | 3/5 | 1 |

Hai trường hợp S giúp điền là `3/[rỗng] → 3/5` và `6/[rỗng] → 6/7`. Hai chữ số mẫu `5` và `7` được nhìn thấy trong ảnh nguồn. Không thay các phân số CRNN đã đọc đủ dù S đoán khác.

Lỗi `13/2` bị CRNN đọc thành `3/2` vẫn được giữ nguyên và yêu cầu rà nguồn: S có đọc ra `13/2`, nhưng quy tắc không tự ghi đè một tầng không rỗng. Một vùng `13` DEV chưa ghép được cặp cũng chưa được sửa. Đây là hai lỗi còn lại trong 11 vùng tử/mẫu; không giấu chúng để báo điểm đẹp hơn.

Trên 27 cặp TRAIN có đủ kết quả S, nhánh phối hợp giữ 24/27, không tăng. Trên 62 thành phần TRAIN giữ 58/62. Với M chỉ có 24/27 crop cặp TRAIN được lưu, nên không dùng tổng đó để xếp hạng TRAIN trực tiếp với S.

**Quy tắc phối hợp được đề xuất sau khi xem lỗi phát triển.** Kết quả 9/11 và 4/5 là tín hiệu để nghiên cứu tiếp, có tính thích nghi với DEV; không phải kiểm định độc lập hoặc chứng minh độ chính xác tương lai. Tính không ghi đè tầng đã đọc cũng giải thích vì sao số trường hợp từng đúng không giảm trong quy tắc này, không phải bằng chứng model dự phòng luôn đáng tin.

## Dữ liệu cho bước tiếp theo

Đã lập hồ sơ rà nguồn cho 32 cấu trúc phân số và chín vùng chưa ghép được, với nguồn Drive, hộp cắt, bản đọc gốc và các gợi ý. Có 79 bản ghi cần rà khi tính riêng các cấu hình; không phải 79 ảnh mới hay 79 nhãn đúng mới.

Tất cả giữ ngoài tập huấn luyện. **Chưa bổ sung được một tập ảnh mới đã có nhãn độc lập**, chưa có xác nhận giáo viên và chưa chứng minh độc lập người viết/nguồn tiền huấn luyện. Không đổi DEV thành TRAIN. Cần rà đúng phạm vi crop và nhãn trước khi dùng các hồ sơ này cho nghiên cứu hoặc fine-tune model công thức.

## Kiểm tra và phạm vi thay đổi

- 10 kiểm thử chuẩn hóa/bố cục và bốn kiểm thử chọn gợi ý được viết trước, quan sát thất bại rồi chạy đạt sau triển khai. Chạy cuối cùng cùng ba kiểm thử nhãn nháp trước đó: **17/17 đạt**.
- Bộ kiểm thử bố cục phân số và tách nét hiện có chạy lại: **45/45 đạt**. Đây là 62 kiểm thử phần mềm, không phải 62 ảnh thật được nhận diện đúng.
- Tiến trình mới đọc ảnh Drive và tái lập đúng **11/11 bản đọc CRNN thành phần DEV** và **5/5 bản đọc S của crop phân số DEV**, gồm cả những bản đọc sai. Kiểm tra pixel nguồn và hash model trước/sau.
- Giữ nguyên trọng số/vocabulary production, model đối chứng, file che tên/cắt ảnh và các thành phần UI được bảo vệ. Không thêm route model vào API, không đổi hành vi Student, không commit/push/deploy.

[Bảng so sánh và các trường hợp](ocr-formula-probe-20261022/comparison.json) · [Hồ sơ rà nguồn](ocr-formula-probe-20261022/research-review-pack.json) · [Kiểm chứng](ocr-formula-probe-20261022/verification.json) · [Môi trường thử](ocr-formula-probe-20261022/environment-freeze.txt).

Model, bản đọc thô đầy đủ và recipe nằm ngoài Git tại `ai-training/datasets/drive_math/formula_probe_20261022/`. Không thể đọc các kết quả trong báo cáo này như thay đổi đã được triển khai vào ứng dụng.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: tái sử dụng bộ đọc Drive, tách nét và baseline đã có.
  - Applied to: probe offline nhỏ, quy tắc điền tầng thiếu, không tạo bộ định tuyến production.
- `superpowers:using-superpowers`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/using-superpowers/SKILL.md`
  - Why selected: định tuyến quy trình thử nghiệm trong phạm vi người dùng đồng ý.
  - Applied to: đọc skill phù hợp, giới hạn thay đổi ứng dụng/model.
- `superpowers:test-driven-development`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/test-driven-development/SKILL.md`
  - Why selected: chuẩn hóa và chọn gợi ý sai có thể làm đẹp điểm hoặc đổi số học sinh.
  - Applied to: kiểm thử giữ chữ số, giữ tầng, không tính toán để sửa và không biến dự đoán thành nhãn.
- `superpowers:verification-before-completion`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/superpowers/6.4.2/skills/verification-before-completion/SKILL.md`
  - Why selected: chỉ báo cải thiện sau phép đo và kiểm chứng nguồn/model thật.
  - Applied to: tái lập dự đoán trong tiến trình mới, kiểm tra hash, báo rõ phần M chưa hoàn tất và giới hạn DEV.
