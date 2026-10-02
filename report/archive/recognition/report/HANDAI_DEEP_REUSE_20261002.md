# Đối chiếu HandAI và cập nhật MathVision — 2026-10-02

## Kết luận

MathVision đã ngang HandAI riêng về model OCR đang phục vụ và đầu ra CRNN trên ảnh mới. Chưa có bằng chứng độ chính xác OCR vượt HandAI. Một số đường truyền dữ liệu, xử lý điểm và bảo vệ nội dung toán của MathVision đã được sửa thêm; đây là cải thiện tích hợp/an toàn, không phải model mới hoặc kết quả huấn luyện mới.

Đối chiếu working tree `E:/HandAI` với `E:/MathVisionKid`, không chỉ tên phiên bản trong README. HEAD nguồn `12b8659e0e726cc63463f9a31b1ece42f241214f`, HEAD MathVision `9c2834efaef9cb428ae33024defde00fb36a5c25`; các sửa chưa commit cũng được xét. Trước đợt này có 172 file AI, 150 file backend và 52 file mobile giống nhau. Các file khác được phân loại riêng ở cuối báo cáo và `reuse-inventory.json`.

Quét toàn repo nguồn (kể cả file ignored, loại môi trường ảo/node_modules/.git) theo .pth/.pt/.onnx/.safetensors chỉ thấy một file trọng số: `ocr/crnn_vi_handwriting_v1/best_cer.pth`. MathVision tải đúng cùng checkpoint, SHA-256 `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941`. Không tìm thấy checkpoint OCR v2 đang phục vụ trong HandAI để lấy sang. Các trọng số phát hiện/toán riêng có ở MathVision không được đánh giá bằng ảnh văn bản này.

## Test ảnh người dùng

Ảnh PNG 1078×683, SHA-256 `56e218a182ff1bcd111b8a9a0615288dcb85439585844d1f3852fd610b8ca285`, có 9 dòng. Chạy endpoint FastAPI với CRNN thật trên CPU; cùng interpreter/môi trường cho cả hai repo, tắt cloud và canonical khi đo OCR gốc. Kết quả gốc, box và điểm từng dòng giống nhau hoàn toàn.

Tham chiếu được chép bằng mắt từ ảnh để đo lần này; Unicode NFC, chuẩn hóa khoảng trắng, giữ hoa/thường và dấu câu. Đây là một ảnh hồi quy do chủ dự án cung cấp, không phải tập test độc lập. Tham chiếu không được gửi vào model hoặc advisor, không đăng ký làm canonical. Chi tiết 18 lỗi trên 324 ký tự có trong `image-evaluation.json`.

| Cách chạy | Dòng phát hiện | Dòng khớp hoàn toàn | Lỗi ký tự / 324 | CER |
|---|---:|---:|---:|---:|
| HandAI riêng, ảnh gốc, CRNN | 9 | 2 | 18 | 5,56% |
| MathVision, ảnh gốc, CRNN | 9 | 2 | 18 | 5,56% |
| Gợi ý Groq thật, ảnh gốc | 9 | 3 | 13 | 4,01% |
| MathVision final sau advisor | 9 | 2 | 18 | 5,56% |
| Thử thu nhỏ 800 px + JPEG quality 80 như hướng nguồn | 9 | 3 | 13 | 4,01% |
| Thử cắt lề trái bằng tay tại x=92, CRNN | 9 | 5 | 6 | 1,85% |

Gợi ý cloud được đo tách biệt với final: Groq SUCCESS nhưng Gemini chưa có kết quả cả trang thành công, nên final không tự nhận các sửa từ một advisor. Groq sửa được `cắp → cặp`, `găắp/cắc → gặp/các` và khoảng trắng; nhưng dòng đầu thêm `tích tắc` thay cho `từ` trong bản chép đối chiếu. Điểm Groq tự báo cao vẫn có thể đi kèm sửa sai. Các đổi hoa/thường/dấu câu cũng bị tính lỗi trong phép đo nghiêm ngặt này.

Cắt lề đã bỏ phần logo/kẻ lề gây nhiễu nhưng vẫn còn `KChi`, `tiện`, `găp/cắc`. Đó là biến thể đầu vào thủ công, không phải chức năng tự cắt mới đã triển khai. Không suy ra một tỷ lệ chính xác chung hoặc khả năng nhận phép tính từ số CER này. Thử nén 800 px có lợi trên ảnh này nhưng làm `tiếng → tếng` ở dòng đầu; chưa đủ căn cứ để áp dụng nén mọi ảnh, đặc biệt ảnh phép tính nhỏ hoặc tọa độ dòng đã chọn.

## Advisor thật và lỗi được phát hiện

Không in hoặc ghi khóa API vào minh chứng. Có cấu hình Groq/Gemini, không dùng mock trong các lần chạy live này.

1. Trước sửa mới: Groq gọi HTTP 1 lần và SUCCESS; Gemini HTTP 0, UNAVAILABLE.
2. Phát hiện nhánh document chỉ lấy singleton Gemini mà không khởi tạo lần đầu, trong khi nhánh một dòng có khởi tạo. Đưa khởi tạo về getter chung.
3. Phát hiện document gửi `key_entry.key`/chuỗi object, trong khi pool có trường `raw_key`. Đã sửa trường header.
4. Bổ sung phân loại lỗi HTTP, timeout/network, tôn trọng không quét khóa khi 429 không cho rotate; model-unavailable/bad-request dừng. Wrapper dùng model thực trong cấu hình và metadata nhất quán.
5. Một lần gọi Gemini thật với ảnh và yêu cầu đọc dòng đầu SUCCESS. Điều này chỉ xác nhận đường gọi API, không xác nhận kết quả sửa 9 dòng.
6. Luồng cả trang theo giới hạn hiện tại 18 giây vẫn UNAVAILABLE. Thử chẩn đoán timeout 45 giây, tối đa 1 lần gọi: Gemini trả HTTP 503 `SERVER_ERROR_5XX`, Groq SUCCESS. Cấu hình thử 45 giây không được ghi vào môi trường production. Không giả lập Gemini thành công và không thay model sang một model khác để che lỗi.

Các file `new-image-*.json` ghi từng lần thực tế; `new-image-mathvision-advised-45s.json` là lần có phân loại lỗi 503. HTTP 7 lần ở các thử trước là retry/failover, không phải 7 model độc lập. Luồng batch bình thường một request cho toàn bộ các dòng, retry có thể thêm request.

## Những phần đã tận dụng thêm

- Backend một dòng: lưu và trả điểm thực cùng `confidenceSource`; lọc điểm không hữu hạn, sai khoảng hoặc không có nguồn. Dùng migration V16 đã đồng bộ nguyên bản trước đó; không tạo migration trùng.
- React Native/browser: giữ URI blob/data qua draft/crop, web multipart gửi Blob chứa byte thật qua client backend có auth. Native giữ hợp đồng file hiện tại.
- Advisor: null/nguồn điểm được giữ đúng trong types; chỉ chấp nhận bằng chứng provider SUCCESS, loại Local-Advisor và dữ liệu mâu thuẫn/outage. Không lấy điểm OCR làm điểm AI; giữ số 0 thực.
- Màn hình kết quả dùng helper chung thay bản sao cũ có thể gán SUCCESS chỉ vì còn text. Dùng điểm CRNN có provenance. Khi chọn OCR khác với chữ đang lưu, gửi verdict CORRECTED và chữ thực đã chọn, tránh backend hiểu nhầm là giữ chữ AI đang lưu. Giữ chức năng chấm toán của MathVision.
- Cập nhật AI muộn giữ phần chữ/verdict người dùng đã sửa; explicit null xóa điểm cũ, không giữ điểm cũ qua `??`.
- Màn hình chọn dòng: ảnh và box dùng cùng canvas theo tỷ lệ khi ảnh dọc chạm giới hạn chiều cao. Không nhập loader có phần trăm tiến độ suy đoán hoặc các thông báo developer từ bản độc lập.
- Tái sử dụng bộ tính metrics có tham chiếu độc lập: CER/WER, dòng đúng, ảnh duy nhất theo SHA, chỉ so trước/sau AI trên cùng tập dòng, không cộng sửa tay thành AI gain, loại sample/demo, chỉ tính trung bình điểm có nguồn. Đã nối metadata thật vào store và JSON export `measuredMetrics`, có getter `getMeasuredMetrics()`; Set tránh tìm tuyến tính lặp lại trong tập dòng đã ghép.
- Tái sử dụng formatter, sửa trường hợp NaN/Infinity thành thiếu số đo và dùng cho điểm từng dòng. Bộ kiểm tra source về confidence, URI, paired metrics và backend persistence cũng được đưa sang; giữ các kiểm tra riêng của MathVision.

Không copy nguyên mobile HandAI vì nó loại bỏ curriculum/chấm toán và dùng cấu hình/router cho ứng dụng độc lập. Các bảng benchmark mẫu, model-version mặc định và công thức dashboard cũ chưa được thay toàn diện ở MathVision: chúng không phải bằng chứng độ chính xác; dùng `measuredMetrics`/minh chứng thực cho đánh giá. Phần history mới có đổi storage/browser persistence và UI độc lập, cần xử lý riêng nếu làm lại dashboard nghiên cứu. Không coi các màn hình report, loader hay script xuất hình capstone là model mạnh hơn.

## Kiểm tra

- Student Mobile: 23 suites, 244 tests pass; có kiểm tra gửi byte ảnh web, nguồn điểm, gợi ý cũ, explicit null, bảo vệ sửa tay và xuất metrics không lấy lựa chọn làm tham chiếu.
- Sau tối ưu Set: 7 ca paired metrics/export pass.
- TypeScript `--noEmit`: pass.
- Python: 23 file, 224 ca; 215 pass, 9 fail. Tập 9 ca fail đúng như trước cập nhật, liên quan tách dòng/geometry/cờ review; không phát sinh ca fail mới trong nhóm đã chạy.
- Nhóm transport Gemini/score/settings/counter: 38 pass, không gọi mạng thật trong unit tests.
- Backend: full suite 148 tests pass với H2 profile test; tổng đếm và từng lớp ở `verification.json`. Nhóm multiline có 9 ca pass, gồm 4 ca từ nguồn và các ca kiểm tra SHA/ảnh/điểm 0 đã có ở MathVision.
- `git diff --check`: pass. Không huấn luyện, commit hoặc push; không có minh chứng thiết bị vật lý hoặc full stack end-to-end trên ứng dụng đang chạy.

Các sửa nằm trong working tree. Tiến trình backend/AI đang chạy cần nạp lại để dùng mã mới; mobile cần nạp bundle mới. Backend vẫn giữ quyền auth/RBAC. Chưa hợp nhất HandAI nhận chữ với model nhận phép tính thành kết quả chấm toán có chứng cứ vùng; cần đánh giá riêng bằng ảnh lời giải có cả chữ và phép tính. Đây là khoảng cách cần kiểm chứng tiếp để kết luận chất lượng MathVision vượt HandAI trên mục tiêu dự án.

## Kết quả từng dòng

| Dòng | OCR gốc | Gợi ý Groq thật | Bản chép đối chiếu bằng mắt |
|---:|---|---|---|
| 1 | : KChi tiếng chuông tì chiếc đồng hồ | Khi tiếng chuông tích tắc chiếc đồng hồ | Khi tiếng chuông từ chiếc đồng hồ |
| 2 | -" báo thức reo lên, em vui vẻ thức đậny. | báo thức reo lên, em vui vẻ thức dậy. | báo thức reo lên, em vui vẻ thức dậy. |
| 3 | Đầu tiên, em đánh răng, rửa mặt cho | Đầu tiên, em đánh răng, rửa mặt cho | Đầu tiên, em đánh răng, rửa mặt cho |
| 4 | thật sạch. tiếp theo,em vui vẻ ăn sáng | thật sạch. Tiếp theo, em vui vẻ ăn sáng | thật sạch. tiếp theo, em vui vẻ ăn sáng |
| 5 | cùng gia đình. sau đó em nhanh nhẹn | cùng gia đình. Sau đó, em nhanh nhẹn | cùng gia đình. sau đó em nhanh nhẹn |
| 6 | thay quần áo đồng phục cho gọn gàng | thay quần áo đồng phục cho gọn gàng | thay quần áo đồng phục cho gọn gàng. |
| 7 | Cuối cùng, em đeo cắp lên vai rồi để | Cuối cùng, em đeo cặp lên vai rồi để | Cuối cùng, em đeo cặp lên vai rồi để |
| 8 | mẹ chởem đi học em cảm thấy rất | mẹ chở em đi học. Em cảm thấy rất | mẹ chở em đi học. em cảm thấy rất |
| 9 | háo hức đến trường để găắp cô và cắc bạn | háo hức đến trường để gặp cô và các bạn | háo hức đến trường để gặp cô và các bạn. |

## Danh sách phần khác của nguồn và quyết định tái sử dụng

| Nhóm | File khác ở HandAI | Quyết định |
|---|---|---|
| ai-service | `app/api/ocr.py` | MathVision delta kept |
| ai-service | `scripts/generate_capstone_figures.py` | Excluded: capstone figure-generation tool, no inference capability or new trained weights |
| ai-service | `tests/test_confidence_integrity.py` | MathVision delta kept |
| backend/src | `main/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineService.java` | MathVision verified-image/raw-score delta kept |
| backend/src | `main/java/com/mathvisionkids/api/ocr/OcrPilotService.java` | Ported score provenance or added source regression cases; existing MathVision cases kept |
| backend/src | `main/java/com/mathvisionkids/api/ocr/OcrTrial.java` | Ported score provenance or added source regression cases; existing MathVision cases kept |
| backend/src | `main/java/com/mathvisionkids/api/ocr/OcrTrialResponse.java` | Ported score provenance or added source regression cases; existing MathVision cases kept |
| backend/src | `test/java/com/mathvisionkids/api/ocr/multiline/OcrMultilineServiceTest.java` | Ported score provenance or added source regression cases; existing MathVision cases kept |
| backend/src | `test/java/com/mathvisionkids/api/ocr/OcrConfidenceTest.java` | Ported score provenance or added source regression cases; existing MathVision cases kept |
| apps/mobile/src | `__tests__/gallery.test.tsx` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `__tests__/handAiAnalyticsAndFlow.test.ts` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `__tests__/handaiAnalyticsCompact.test.tsx` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `__tests__/handAiDashboardMetrics.test.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `__tests__/handAiFlowFixV5.test.ts` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `__tests__/handAiGuestRouting.test.ts` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `__tests__/handAiHistoryManagement.test.tsx` | Standalone UI/history-specific tests not applicable without that UI; MathVision existing flow tests retained and selected measured-confidence fixture clarified |
| apps/mobile/src | `app/(tabs)/index.tsx` | Excluded standalone rebranding and removal of MathVision curriculum/grading features |
| apps/mobile/src | `app/(tabs)/profile.tsx` | Excluded standalone rebranding and removal of MathVision curriculum/grading features |
| apps/mobile/src | `app/_layout.tsx` | Excluded standalone error screen exposing technical error messages; existing MathVision runtime retained |
| apps/mobile/src | `app/camera.tsx` | Excluded standalone rebranding and removal of MathVision curriculum/grading features |
| apps/mobile/src | `app/evaluation-history.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `app/handai-analytics.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `app/handai-trial-analytics.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `app/index.tsx` | Excluded navigation failure fallback that bypasses intended authenticated startup routing |
| apps/mobile/src | `app/ocr-pilot/multiline-result.tsx` | Partial: shared advisor helper replaces unsafe duplicate, tagged raw scores, accurate feedback verdict when keeping different OCR. MathVision grading retained |
| apps/mobile/src | `app/ocr-pilot/multiline-review.tsx` | Partial: same image/box canvas fixes portrait geometry. Excluded fabricated progress, direct-service health checks, URI-only skip/cache, shortened request timeout |
| apps/mobile/src | `components/ocr/OCRProgressLoader.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/ComparisonCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/DatasetCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/ErrorInsightCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/HistoryCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/index.ts` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/MetricCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/PerformanceCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/ReportCard.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/SectionHeader.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/StatusBadge.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/StoredLineReview.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/report/TrendSparkline.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `components/ui/AppHeader.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `config/apiResolver.ts` | Excluded: standalone HandAI/local/direct AI service routing; MathVision backend remains auth/RBAC authority |
| apps/mobile/src | `config/env.ts` | Excluded: standalone HandAI/local/direct AI service routing; MathVision backend remains auth/RBAC authority |
| apps/mobile/src | `screens/HandAiTrialAnalyticsScreen.tsx` | Excluded standalone report/history/loader UI: no additional OCR model or decoder. Full research dashboard/history migration is a separate UI/storage change; portable measurement logic reused |
| apps/mobile/src | `services/analytics/handAiAnalyticsStore.ts` | Partial: independent-reference/paired-AI measured metrics, score source, image hash, sample markers, JSON export. Existing legacy dashboards/formulas and storage retained; their example/default metrics are not evaluated evidence |
| apps/mobile/src | `services/analytics/handAiDashboardMetrics.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `services/api/apiClient.ts` | Kept 60s backend timeout; source 20s may terminate working OCR/advisor requests |
| apps/mobile/src | `services/api/OcrPilotService.ts` | Partial: web image bytes, null/provenance contract. Kept authenticated backend; excluded URI cache, unconditional resize and short/broken timeout, progress-only APIs |
| apps/mobile/src | `services/draft/submissionDraftStore.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `services/image/__tests__/imagePipeline.test.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `services/image/imagePipeline.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `utils/__tests__/suggestionConfidenceIntegrity.test.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `utils/metricFormat.ts` | Adapted: finite-only formatting; reused for unknown line confidence |
| apps/mobile/src | `utils/mobileAsyncAdvisor.ts` | Adapted: preserve user edits, include provenance, clear explicit null instead of retaining stale scores |
| apps/mobile/src | `utils/ocrConfidence.ts` | Ported; behavior verified, paired-session lookup uses a Set |
| apps/mobile/src | `utils/suggestionDedupe.ts` | Ported; behavior verified, paired-session lookup uses a Set |

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Tận dụng mã OCR có sẵn, sửa đúng đường gọi thật và tránh nhập toàn bộ ứng dụng độc lập.
  - Applied to: Python advisor, backend provenance, loại bỏ bản sao helper, kiểm tra và phân loại khả năng tái sử dụng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Hợp đồng dữ liệu và cập nhật bất đồng bộ của React Native.
  - Applied to: Multipart browser, cập nhật advisor giữ lựa chọn người dùng, kết quả/canvas; dùng Set cho tra cứu tập dòng so sánh trong metrics. Không thêm dependency.
