# Hoàn thiện nhận diện dòng và tránh bỏ sót khi ảnh dài — 2026-10-05

Đã chạy lại **64.457 ảnh khác nội dung**, đối chiếu toàn bộ với bản cũ và
xác minh **83.649 danh tính nguồn** trong bộ ảnh đã lấy từ Drive. Không có
lỗi thực thi hoặc lỗi xác minh nguồn/tọa độ trong lượt này. Khôi phục thêm
một dòng chữ thật từng trả rỗng; sửa giới hạn âm thầm 30 dòng và luồng
yêu cầu cắt nhỏ ảnh. **Chưa thể kết luận nhận diện hoàn hảo**: còn 23 ảnh
có chữ trả rỗng, 10 ca bố cục khó đã biết và hai biên dòng tham chiếu chưa
khớp đủ. Chạy thành công không thay thế nhãn hình học hoặc bản chép chữ chuẩn.

## Phạm vi và bản đối chiếu

Lượt này dùng bộ nguồn Drive đã giữ tại máy từ lần kiểm kê trước, gồm ảnh
trang vở, ảnh cắt trong ZIP, ảnh nhúng trong Parquet và ảnh tham chiếu.
Không thực hiện một lần liệt kê Drive mới để xác nhận các tệp vừa được
thêm sau lần kiểm kê. Không suy ra độ chính xác OCR chữ hoặc khả năng
hướng dẫn giải toán trên toàn bộ bộ ảnh từ kết quả phân vùng dòng.

- Bản cuối: `runtime13-bounded-complete-lines-20261005`, cache
  `text-regions-v8`.
- Trước khi sửa, lưu bản runtime12 bất biến:
  `infra/local-runtime/logs/line-refine-round2-20261005/runtime12-baseline.zip`
  gồm 129.086 tệp kết quả, nhãn và bằng chứng cũ. SHA-256:
  `bc76b58ff8f1398b6fbf93e546daed3454503c84d8ba6407a245c927d95113bd`.
- Báo cáo `DRIVE_LINE_REFINEMENT_20261005.md` giữ số liệu lịch sử runtime12;
  kết quả chuẩn và danh sách trạng thái hiện tại đã được cập nhật runtime13.
- Trọng số detector giữ nguyên. Không huấn luyện model, không commit/push,
  không sửa/xóa ảnh trên Drive trong lượt này.

## Thay đổi đã triển khai

### Khôi phục một dòng sáng trên bảng tối

Giữ điều kiện kiểm tra dải bảng tối và bằng chứng thân chữ độc lập. Chỉ
khi lần phát hiện trên ảnh đảo sáng ở tỉ lệ 2× trả rỗng mới thử tỉ lệ lớn
hơn, giới hạn 4× và cạnh dài 1.280 pixel. Khung được mở tới thành phần chữ
gần cùng dòng để giữ đầu câu, dấu và nét kéo xuống. Không nới điều kiện
nền, không tạo khung toàn ảnh chỉ để tránh kết quả rỗng.

Ảnh Parquet #1694, ID `parquet_3bdcc2050bb1e9575be5d3bca496bc21`, kích
thước 515 × 61: trước không có khung; sau có một khung `[0, 0, 515, 61]`
qua đường xử lý đầy đủ. Đã xem trực tiếp dải chữ bắt đầu bằng “Luyện chữ…”.
26 ca chữ từng bị sót được kiểm tra lại: một ca cải thiện trong
lượt này; ba ca đã khôi phục ở runtime12 giữ nguyên. 139 ảnh âm đã duyệt
vẫn không có vùng chữ giả. Ca mới vẫn có trạng thái `needs_review`, không
được tự nâng thành nhãn hình học hoặc dữ liệu huấn luyện chuẩn.

### Bỏ giới hạn âm thầm ở luồng OCR nhiều dòng

API OCR, màn hình xem/sửa dòng và backend lưu kết quả cùng hỗ trợ tối đa
**200 dòng** thay cho 30. API dò thêm vùng thứ 201 để phát hiện vượt giới
hạn và trả trạng thái cần kiểm tra/cắt nhỏ; không mặc định phần đã trả là
toàn bộ trang. Backend từ chối yêu cầu trên 200 dòng trước khi ghi dữ liệu.

Trong ứng dụng, ảnh vượt giới hạn có thông báo “Chọn một vùng nhỏ hơn nhé”
và thao tác quay lại cắt ảnh, giữ ảnh hiện tại cùng phần che thông tin riêng
tư. Xóa một vài dòng không làm mất cảnh báo vượt giới hạn. Kết quả nhận
diện hoặc callback lấy kích thước từ ảnh cũ không được thay thế ảnh đã
cắt lại; rời màn hình cũng hủy lượt đang chạy.

### Luồng hướng dẫn giải giữ giới hạn riêng, yêu cầu chia ảnh rõ ràng

Luồng camera/hướng dẫn giải dùng ngân sách **35 dòng**, 6.000 ký tự bài
làm, 4.000 ký tự đề và 2.500 token đầu ra. Không coi nâng OCR nhiều dòng
lên 200 là nâng khả năng đọc trọn bài của luồng này.

Nếu kiểm tra dòng vật lý hoặc bản đọc ban đầu/đối chiếu phát hiện vượt
sức chứa, trả `UNREADABLE`, `needsCrop: true`, không trả nội dung dở dang
như một bài hoàn chỉnh. Cờ này đi qua kiểm tra kiểu dữ liệu của AI,
backend và ứng dụng; giao diện hướng dẫn chia ảnh thành từng phần rồi cắt
lại. Tiếp tục giữ điều kiện khớp dòng vật lý trước khi gắn tọa độ lên bài.
Đây là kiểm tra bảo thủ: chữ quá mờ, nhiều cột hoặc dòng phân mảnh vẫn có
thể khiến kiểm tra số dòng bỏ sót; không bảo đảm nhận ra mọi trang vượt sức chứa.

## Kết quả chạy toàn bộ ảnh

| Bộ ảnh khác nội dung | Đã kiểm tra | Có vùng chữ | Trả rỗng | Lỗi thực thi |
| --- | ---: | ---: | ---: | ---: |
| Trang vở và ảnh cắt | 4.205 | 4.056 | 149 | 0 |
| Parquet | 60.247 | 60.225 | 22 | 0 |
| Ảnh tham chiếu quan trọng | 5 | 5 | 0 | 0 |
| **Tổng** | **64.457** | **64.286** | **171** | **0** |

Audit phân vùng cục bộ giới hạn 200 vùng/ảnh; không ảnh nào vượt giới hạn
này. Toàn bộ khung được kiểm tra trong kích thước ảnh gốc. Có 102.525
vùng, tăng một vùng so với 102.524 của runtime12. Đối chiếu từng ảnh với
ZIP bất biến xác nhận **chỉ một ảnh đổi khung** (#1694); mọi khung còn lại
giữ nguyên. Ảnh gốc, pixel, kích thước và danh tính nguồn được bảo toàn.
Lượt audit này không chạy CRNN/AI cloud để đo độ đúng của bản chép chữ.

Kiểm kê cuối xác minh đủ 83.649/83.649 danh tính nguồn, tương ứng 64.457
ảnh RGB khác nhau: 1.278 nguồn trang vở Drive, 2.975 mục ZIP, 5 ảnh Drive
tham chiếu, 60.247 hàng Parquet và 19.144 nguồn `train` trùng byte với
Parquet. Không chạy lại bản trùng để tăng số ảnh kiểm thử.

Danh sách trạng thái đã kiểm tra được cập nhật chữ ký bản cuối
`1d2c1de4a608dc99b13fe3d9183aa00aad0c4e887e6ffca81121044bd789e962`.
Ledger vẫn có 83.649 nguồn; giữ nguyên toàn bộ lịch sử kiểm tra đầu tiên.
Không đánh dấu dự đoán chưa duyệt thành nhãn chuẩn. Đối chiếu ZIP xác nhận
184 tệp nhãn đã duyệt giữ nguyên từng byte; lượt xác minh tham chiếu độc
lập kiểm tra 178 đường dẫn nhãn. Hai số này là hai phạm vi bằng chứng
khác nhau, không cộng lại thành số nhãn mới.

## Độ đúng trên bộ tham chiếu và các ca còn khó

- 31/31 ảnh tham chiếu dương có đúng số dòng; 6/6 tham chiếu âm giữ đúng.
- 22 ảnh có nhãn hình học gồm 148 dòng: khớp một-một 146 dòng ở IoU ≥ 0,5;
  20/22 ảnh khớp đủ. Hai biên chưa khớp ở ảnh #11 và #59 giữ nguyên.
- 147 nhãn đếm riêng khớp 144 ảnh; toàn bộ 139 ảnh đếm 0 vẫn không có vùng
  chữ. Ba ca lệch: #688 có 7 vùng so với 10 dòng, #1278 có 18 vùng so với
  12 dòng học sinh, và ảnh luyện số #3218 có 0 vùng so với một dòng.
- Gộp bỏ bản trùng trong các bộ tham chiếu: 175/178 ảnh đúng số vùng.
  Đây là tham chiếu đã dùng khi phát triển, không phải tập kiểm thử độc
  lập để suy ra độ chính xác chung trên Drive. Đúng số vùng cũng không
  chứng minh khung đúng nội dung hoặc chữ đọc đúng.

171 ảnh trả rỗng gồm 139 nền không chữ đã duyệt, 9 mảnh chữ bị cắt mất
nội dung, **22 ảnh Parquet có chữ còn bị sót và một ảnh luyện số**. Giữ
nguồn và phân loại riêng; không xóa ảnh có chữ vì detector chưa đọc được.

Mười ca bố cục khó còn lại: ảnh #660 có khung gộp trên screenshot đệm đen;
#688 luyện chữ đơn lẻ; #1081 nối qua gáy vở; #829/#857 ảnh hai trang nằm
ngang; #1250 số/phép tính bị phân mảnh; #1278 lấy cả logo/nội dung nền;
#100/#101/#115 nhóm phân số chưa đúng. Đã thử detector hiện có, xử lý
viền đen, hướng xoay và gộp phân số riêng, nhưng bằng chứng trực quan
vẫn cho thấy sót ký hiệu hoặc nối nhầm lời văn nên không đưa các phép
sửa này vào bản chính. Cần nhãn hình học theo đúng phạm vi bài học sinh
cho các bố cục này trước khi đánh giá một thay đổi rộng hơn.

## Kiểm thử và dịch vụ chạy thật

| Kiểm tra | Kết quả bản cuối |
| --- | --- |
| AI offline | 1.100 đạt; 4 cảnh báo lifespan hiện có; 9 bộ cần dịch vụ sống không được tính là đã đạt |
| Ứng dụng mobile | 40 bộ, 438 kiểm thử đạt |
| TypeScript | `npx tsc --noEmit` đạt |
| Backend phần OCR/tutor/auth/ownership | 5 lớp, 99 kiểm thử đạt, không lỗi/bỏ qua |
| Công cụ hợp nhất dữ liệu riêng | 7 kiểm thử đạt; fixture 20 ảnh thật/2 nhãn đã duyệt cho kết quả và nhãn giống từng byte với công cụ nối tiếp |
| Tính toàn vẹn cuối | 13 hash mã/model khớp bản đóng băng; hash ZIP baseline khớp; `git diff --check` đạt |

Các kiểm thử giới hạn đi qua handler HTTP hoặc hành vi màn hình, gồm
41/200 dòng và dòng cuối, vùng thứ 201, kết quả AI vượt giới hạn, dữ liệu
cờ sai kiểu, callback ảnh cũ, cắt lại cùng phiên ảnh, giữ cảnh báo khi thử
lại lỗi và rời màn hình. Những kiểm thử OCR lớn mô phỏng vùng/model chữ,
không thay thế kiểm thử độ chính xác trên ảnh nguồn.

FastAPI bản cuối chạy thật trả 200 cho health/readiness và detect-lines:
ảnh tham chiếu có ba dòng, không dùng cloud line assistance, Groq/Gemini
OCR calls bằng 0. Kiểm tra tutor HTTP bằng ảnh tổng hợp 37 dòng xanh:
không xác thực trả 401; có xác thực trả 200 với `needsCrop: true`, không
trả dòng/đề dở dang, không cần đọc cloud. Spring Boot bản cuối có health
`UP`. Chỉ nêu bằng chứng API cục bộ và kiểm thử tự động; không có kiểm
thử điện thoại thật do agent thực hiện trong lượt này.

Audit toàn bộ ảnh và kiểm thử offline không gọi OCR cloud. Các phép dò
tình trạng provider lúc khởi động dịch vụ là phạm vi khác; health/readiness
cục bộ không xác nhận dịch vụ AI hướng dẫn giải trên cloud đã sẵn sàng.

## Bằng chứng có thể kiểm tra lại

- Kết quả từng ảnh: `ai-training/datasets/drive_math/` trong ba batch
  `all_notebooks_recheck_20261005`, `parquet_20261005`, `meeting_refs_20261005`.
- Trạng thái nguồn và bộ tham chiếu:
  `ai-training/datasets/drive_math/inventory/final_tested_sources_20261005.jsonl`,
  `final_coverage_summary_20261005.json`, `final_reference_comparison_20261005.json`.
- Thư mục bằng chứng lượt cuối:
  `infra/local-runtime/logs/line-refine-round2-20261005/`, gồm
  `runtime13-frozen-manifest.json`, `runtime12_to_13_comparison.json`,
  `final-source-integrity.json`, `ai-offline.xml`, `mobile-tests-final.log`,
  `capacity/java-final-suite.json`, `api-live-final.json`, `api-capacity-final.json`.
- Ca phục hồi và các ảnh chữ còn sót:
  `infra/local-runtime/logs/line-polish-20261005/recovery/approved_validation.json`,
  `chalk_second_1694.png`, `remaining_writing_catalog.json`.
- Các thử nghiệm bố cục không đạt:
  `infra/local-runtime/logs/line-refine-20261005/hard-layouts/FINAL_VERDICT.md`.
- Bằng chứng công cụ hợp nhất:
  `infra/local-runtime/logs/line-polish-20261005/round2/fast_merge_fixture_evidence.json`.

Ảnh/dataset/log phát triển tiếp tục được Git ignore. Đã giữ bản chép chữ
cung cấp trong Parquet/ZIP, nhưng không mặc định đó là transcription hay
khung dòng đã được duyệt chính xác.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa detector và giới hạn thực tế bằng đường xử lý hiện có.
  - Applied to: phục hồi dải bảng tối, giới hạn OCR/tutor, kiểm tra dữ liệu,
    giữ nhãn chuẩn và các thử nghiệm hồi quy; không thêm dependency.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: thay đổi màn hình React Native và vòng đời tác vụ bất đồng bộ.
  - Applied to: hủy nhận diện khi rời màn hình, chặn kết quả/callback cũ,
    nhận ảnh cắt lại và giữ trạng thái yêu cầu cắt nhỏ.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: người học cần hiểu cách xử lý khi ảnh vượt sức chứa.
  - Applied to: thông báo ngắn, nút cắt ảnh rõ ràng và dễ chạm, giữ ảnh cùng
    nội dung che riêng tư, sử dụng màu/chữ của giao diện hiện có.

Đã đọc tài liệu Expo phiên bản 57 tại
<https://docs.expo.dev/versions/v57.0.0/> trước khi sửa mã ứng dụng.
