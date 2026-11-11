# Teacher Web Reliability Implementation Plan

> Hướng phát triển đã được duyệt. Luồng chốt điểm vòng 1 đã được kiểm chứng cục bộ trên `Loc/Teacher-features`. Vòng 2 và pilot vẫn đang mở.

**Mục tiêu** — Giáo viên tiểu học có thể đi từ danh sách lớp tới điểm chính thức và biết chính xác cần làm gì với từng bài AI chưa xử lý được.

**Kiến trúc** — Tiếp tục dùng Portal/SSO, Teacher Web và Spring API hiện có. Spring quyết định quyền, trạng thái và kết quả chấm. Teacher Web hiển thị bước tiếp theo, làm mới tiến độ có giới hạn và xử lý riêng kết quả lưu điểm với việc tải lại dữ liệu.

**Công nghệ** — React 19, TypeScript, Vite, MUI, TanStack Query, Spring Boot, PostgreSQL, lưu trữ ảnh riêng tư và worker AI bất đồng bộ.

**Cơ sở yêu cầu** — Hồ sơ Capstone và các đề xuất nghiệp vụ dưới đây. Nhánh `Loc/Teacher-features` tách từ `origin/main` tại `48c1c7a95966391842a05c80794298207d05cc55`, sau PR #49.

## Phạm vi và nguồn yêu cầu

- [C1SE.01 Project Plan](<E:/DuyTan/C1SE/Document/3. C1SE.01_Project_Plan.pdf>), trang PDF 6 (trang nội dung 1), mô tả một phép đặt tính cộng hoặc trừ số tự nhiên 1–6 chữ số trên mỗi ảnh, đợt 1–30 ảnh, giáo viên quyết định điểm cuối cùng. Các trang PDF 12–13 đặt các chức năng này trong Sprint 2–3 và dành giai đoạn tiếp theo cho tích hợp, pilot và nghiệm thu.
- [MathVisionKid Sprint Backlog](<E:/DuyTan/C1SE/Document/MathVisionKid_Sprint1_2_3_FIXED (1).xlsx>), `Product Backlog` dòng 8, 13–14, 18, 22–23, 28, 31–32, ghi yêu cầu tạo bài tập, chọn học sinh, upload JPG/PNG, theo dõi bất đồng bộ, xem bằng chứng, chốt điểm, phân quyền và hoàn thành luồng đến hàng đợi mà không cần hỗ trợ kỹ thuật. Mục tiêu hiệu năng ở dòng 32 là AI p95 ≤ 12 giây mỗi ảnh đã cắt trong môi trường được khai báo.
- `Sprint 2 Backlog` dòng 8–40 đánh dấu các đầu việc nền tảng đã làm. `Sprint 3 Backlog` dòng 10–15 và 36–38 còn liệt kê kiểm tra ảnh, xử lý lỗi/thử lại và tích hợp. Đây là dữ liệu lập kế hoạch. Bằng chứng thực tế của phiên này nằm ở phần kiểm chứng.
- Phạm vi vòng đầu gồm Teacher Web và phần API phục vụ Teacher. Giữ định dạng `/api/v1`, kiểm tra quyền ở Spring, che thông tin trước upload, truy cập ảnh có xác thực, quyết định điểm có audit và giới hạn ảnh hiện hành. Dùng ảnh tổng hợp trong kiểm thử. Student Mobile, huấn luyện AI và phát hành thuộc quyết định riêng của chủ dự án.

## Hiện trạng và ưu tiên

Luồng chính đã có trên nhánh khảo sát. Portal cấp phiên Teacher. Giáo viên mở lớp và danh sách học sinh, tạo bài tập theo lớp và thang điểm, gán và che thông tin trên ảnh, gửi đợt chấm, theo dõi trạng thái, mở ảnh gốc đã che và quyết định điểm. API đã có kiểm tra quyền sở hữu, điểm hợp lệ và khóa bản ghi khi quyết định. PR #49 bổ sung trình xem ảnh và kịch bản nghiệm thu riêng cho dịch vụ thật.

| Mức | Bằng chứng | Tác động và hướng xử lý |
| --- | --- | --- |
| P1 | `NEEDS_CONFIRMATION` và `NEEDS_RETAKE` vào hàng đợi, nhưng cả giao diện và API chỉ nhận quyết định ở một tập trạng thái khác. [BatchResponse.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/batch/BatchResponse.java#L15), [InternalAiCallbackController.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/analysis/InternalAiCallbackController.java#L145), [SubmissionReviewPage.tsx](../../../apps/teacher-web/src/pages/SubmissionReviewPage.tsx#L140), [SubmissionService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/submission/SubmissionService.java#L465) | Giáo viên thấy việc cần làm nhưng không có bước tiếp theo. Cho chấm thủ công có lý do khi bằng chứng đủ. Với ảnh thực sự không đọc được, hướng dẫn thay ảnh và giữ bài ở trạng thái cần xử lý. |
| P1 | Màn hình hàng đợi coi mảng rỗng là đã xử lý xong. Nó chỉ hỏi danh sách chờ duyệt, trong khi API loại bài đang chạy và thất bại. [ReviewQueuePage.tsx](../../../apps/teacher-web/src/pages/ReviewQueuePage.tsx#L30), [ReviewQueuePage.tsx](../../../apps/teacher-web/src/pages/ReviewQueuePage.tsx#L83), [BatchResponse.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/batch/BatchResponse.java#L15) | Giáo viên mở lại đường dẫn lúc đợt mới xử lý một phần có thể hiểu rằng tất cả đã xong. Dùng tiến độ và số bài lỗi của cùng đợt để quyết định thông báo và đường dẫn tiếp theo. |
| P1 | Hai thao tác quyết định nối POST và GET trong cùng mutation. Nếu POST trả 204 rồi GET gặp lỗi, giao diện đi vào nhánh báo lưu thất bại. [SpringTeacherService.ts](../../../apps/teacher-web/src/services/api/SpringTeacherService.ts#L143), [SubmissionReviewPage.tsx](../../../apps/teacher-web/src/pages/SubmissionReviewPage.tsx#L58) | Giáo viên có thể thử gửi lại một điểm đã chốt. Ghi nhận POST thành công ngay, làm mới dữ liệu độc lập, và khi kết quả POST không rõ thì kiểm tra trạng thái trước khi gửi lại. |
| P2 | Hàng đợt gần đây trên Dashboard dùng `ListItem` có `onClick`, thiếu nút hoặc liên kết để đi bằng bàn phím. [DashboardPage.tsx](../../../apps/teacher-web/src/pages/DashboardPage.tsx#L275) | Dùng liên kết có focus rõ, đồng thời kiểm tra bố cục tên dài và ba chỉ số trên màn hẹp. |
| P2 | Dashboard lấy đầu ngày UTC, tương ứng 07:00 ở Việt Nam. Bài gửi từ 00:00 đến trước 07:00 giờ Việt Nam có thể không được tính vào “hôm nay”. [DashboardService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/dashboard/DashboardService.java#L46) | Chốt một múi giờ thống nhất cho bộ đếm và ngày hiển thị. Với pilot Việt Nam, đề xuất `Asia/Ho_Chi_Minh` và test mốc trước, đúng và sau nửa đêm. |
| P2 | Một hàng đợi có thể gọi thêm 30 request chi tiết, một request lỗi làm cả `Promise.all` lỗi. Dashboard và danh sách đợt cũng truy vấn bài theo từng đợt trong lịch sử. [SpringTeacherService.ts](../../../apps/teacher-web/src/services/api/SpringTeacherService.ts#L113), [DashboardService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/dashboard/DashboardService.java#L44), [BatchService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/batch/BatchService.java#L191) | Mẫu truy vấn đã xác nhận trong code. Mức chậm trên lớp thật cần đo. Ưu tiên hợp đồng trả tóm tắt hàng đợi có quyền truy cập nếu số request hoặc tỉ lệ lỗi ảnh hưởng pilot. |

**Quy tắc phân quyền cần duyệt.** Khi Admin đổi giáo viên phụ trách, code cập nhật giáo viên của lớp. Các đợt và bài nộp cũ vẫn kiểm tra theo chủ đợt. Chưa xác minh yêu cầu bàn giao lịch sử hoặc tình huống này trên môi trường tích hợp. Đề xuất quyền xem ảnh và chốt điểm dựa trên phân công đang có hiệu lực, với việc bàn giao đợt còn mở do Admin quyết định và lưu audit. Chốt quy tắc này trước khi mở thêm thao tác ghi điểm. [AdminService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/admin/AdminService.java#L428), [BatchService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/batch/BatchService.java#L213), [SubmissionService.java](../../../backend/business-api/src/main/java/com/mathvisionkids/api/submission/SubmissionService.java#L356)

## Quy tắc nghiệp vụ đề xuất

| Thuật ngữ | Nghĩa trong Teacher Web |
| --- | --- |
| Bài tập | Đề mục của một lớp, có dạng phép tính và thang điểm. Một bài tập có thể có nhiều đợt chấm. |
| Đợt chấm | Nhóm ảnh gửi cho một bài tập. Tiến độ xử lý ảnh và tiến độ chốt điểm được hiển thị riêng. |
| Bài nộp | Một ảnh bằng chứng gắn với học sinh trong đợt. Nếu thay ảnh, giữ liên kết với bài nộp ban đầu để giáo viên theo dõi được lịch sử. |
| Điểm đề xuất | Kết quả hỗ trợ từ AI, có thể chưa có. Nút duyệt chỉ khả dụng khi có đề xuất hợp lệ và giáo viên xem được ảnh. |
| Điểm chính thức | Quyết định giáo viên đã lưu và có audit. Chấm thủ công khi AI chưa kết luận cần ảnh đủ rõ, điểm trong thang và lý do. Ảnh chưa thể đọc cần hướng xử lý riêng, không tự ghi điểm 0. |

Đề xuất duyệt **luồng chấm và xử lý ngoại lệ trước**, vì lỗi xuất hiện ở công đoạn mà giáo viên cần ra quyết định chính thức. Ưu tiên thứ hai là giảm thao tác lặp lại và cải thiện khả năng truy cập. Báo cáo điểm hoặc nhập danh sách chỉ đưa vào phạm vi sau khi xác minh giáo viên thực sự cần trong quy trình hiện tại và đã có quy tắc dữ liệu phù hợp.

## Ca nghiệm thu cần ưu tiên

- Đã lưu điểm nhưng tải lại gặp 503. Giáo viên thấy quyết định đã được ghi nhận và có thể thử tải lại. Vòng 1, mục 1.
- Mất phản hồi khi gửi quyết định. Giáo viên có cách kiểm tra điểm trước khi thao tác tiếp. Vòng 1, mục 1.
- Hàng đợi rỗng trong lúc xử lý hoặc khi có bài lỗi. Màn hình hiển thị đúng công việc còn lại. Vòng 1, mục 2.
- Ảnh mờ hoặc đề xuất trống. Giáo viên chỉ có những thao tác phù hợp với bằng chứng đang có. Vòng 1, mục 3.
- Mất quyền lớp giữa lúc mở bài và lưu hoặc có hai phiên lưu đồng thời. API xác minh quyền ở lần ghi và chỉ lưu một quyết định. Vòng 1, mục 3.

## Vòng 1 · Chốt điểm đáng tin cậy

### 1. Phân biệt đã lưu điểm và tải lại dữ liệu

**Tệp chính** — `apps/teacher-web/src/services/api/{TeacherService,SpringTeacherService,MockTeacherService}.ts`, `pages/SubmissionReviewPage.tsx`, `tests/api-contracts.test.mjs` và `tests/review-fixes-regression.test.mjs`.

- [ ] Thêm ca POST trả 204 rồi GET trả 503, và ca POST bị ngắt trước khi nhận phản hồi nhưng GET sau đó trả điểm đã chốt.
- [ ] Giữ endpoint hiện hành. Cho `approveSubmission(submissionId: string)` và `overrideSubmission(submissionId: string, score: number, reason: string)` trả `Promise<void>` sau POST thành công. Trang lấy dữ liệu cập nhật qua React Query. Cập nhật ca contract cũ đang yêu cầu adapter tự GET sau khi ghi. Nếu biết POST đã thành công, giao diện thông báo đã lưu dù tải lại lỗi. Khi chưa biết POST có thành công, cho kiểm tra lại trước khi gửi tiếp.
- [ ] Chạy `npm run test:config --workspace=teacher-web` và các ca trình duyệt. Xác nhận người dùng thấy đúng kết quả, thao tác không tự gửi lần hai và tải lại hiển thị điểm chính thức.

### 2. Dùng trạng thái của đợt để hiển thị hàng đợi

**Tệp chính** — `apps/teacher-web/src/pages/{ReviewQueuePage,BatchDetailPage}.tsx`, `apps/teacher-web/tests/review-fixes-regression.test.mjs`, `tests/browser/teacher-review.spec.mjs`.

- [ ] Thêm ca đợt có 3/30 ảnh đã xử lý và hàng đợi rỗng, đợt chỉ có bài thất bại, đợt chờ ảnh và đợt đã chốt toàn bộ.
- [ ] Đọc chi tiết đợt qua query `['batch', batchId]` hiện có. Dùng `status`, `processedCount`, `pendingReviewCount`, `failedCount` và `finalizedCount` để hiển thị trạng thái. Cập nhật có giới hạn khi đang xử lý và cho thử lại khi tải lỗi. Điều kiện “đã chốt toàn bộ” cần đối chiếu số đã chốt với số bài trong đợt.
- [ ] Kiểm tra trên desktop và màn hẹp. Mở đường dẫn trực tiếp hoặc quay lại từ một bài đang duyệt phải thấy cùng tiến độ. Bài lỗi có đường dẫn tới chi tiết và thông báo bước tiếp theo.

### 3. Cho giáo viên xử lý bài AI không chắc chắn

**Tệp chính** — `backend/business-api/src/main/java/com/mathvisionkids/api/{submission/SubmissionService,batch/BatchResponse}.java`, `apps/teacher-web/src/pages/SubmissionReviewPage.tsx`, `TeacherReviewWorkflowIntegrationTest.java` và `tests/browser/teacher-review.spec.mjs`.

- [ ] Thêm ca bài `NEEDS_CONFIRMATION` có ảnh đọc được, bài `NEEDS_RETAKE` có ảnh không đọc được, bài chưa có đề xuất, bài đã chốt, và tài khoản không còn được phân lớp. Xác nhận 0 là điểm hợp lệ nếu được chủ động nhập và có lý do. Kiểm tra hai lần ghi đồng thời chỉ tạo một quyết định.
- [ ] Sau khi chủ dự án duyệt quy tắc, dùng `POST /api/v1/teacher/submissions/{id}/override` cho chấm thủ công ở trạng thái được phép. Giữ kiểm tra quyền sở hữu, thang điểm, lý do, tính bất biến của điểm đã chốt và audit. Chỉ cho duyệt đề xuất khi có đề xuất hợp lệ. Ở ca cần ảnh mới, vòng đầu hiển thị lý do và giữ bài cần xử lý. Đường thay ảnh trên cùng bài nộp thuộc vòng 2, sau khi chốt cách lưu lịch sử.
- [ ] Chạy `gradlew.bat test --tests '*TeacherReviewWorkflowIntegrationTest' --tests '*BatchUploadTransactionTest' --tests '*TeacherSubmissionImageTest'` với profile `test`, sau đó chạy thử browser và kịch bản dịch vụ riêng. Kiểm tra quyết định tồn tại sau reload, ảnh riêng tư và bộ đếm phản ánh đúng trạng thái.

### Kết quả vòng 1

- Teacher Web xác nhận lưu điểm riêng với việc tải lại dữ liệu. Khi phản hồi lưu bị mất, giáo viên kiểm tra lại trạng thái trước khi gửi tiếp. Hàng đợi dùng số liệu của đợt để phân biệt đang xử lý, lỗi, chờ ảnh và đã chốt hết.
- Spring yêu cầu `imageLegible: true` để chấm thủ công bài `NEEDS_CONFIRMATION` và ghi xác nhận vào audit. Bài `NEEDS_RETAKE` chờ ảnh thay thế. Giáo viên phải vừa là chủ đợt vừa đang phụ trách lớp. Việc bàn giao đợt cũ thuộc một luồng riêng.
- Kiểm tra cuối trên thay đổi hiện tại đạt 46/46 ca Teacher Web, 18/18 ca Chromium cho chốt điểm và hàng đợi, 8/8 ca Spring cho quy trình duyệt. Lint giữ 4 cảnh báo sẵn có. Kiểm thử trình duyệt trên PostgreSQL, MinIO, Redis, Spring, FastAPI và Celery cách ly đạt 8/8 kiểm tra, gồm upload một ảnh tổng hợp, khớp hash ảnh, lưu điểm qua reload và hàng đợi hết việc. Worker dùng nhận diện fixture. Số liệu này chưa đo độ chính xác hay độ trễ của OCR thật.

## Vòng 2 · Khôi phục bài lỗi và giảm thao tác

- Đã triển khai thay ảnh cho bài `NEEDS_RETAKE` trên cùng bài nộp. Teacher Web dùng lại trình che thông tin, Spring kiểm tra quyền và JPEG tối đa 8 MB, lưu bản ảnh mới cùng audit và phát job sau commit. Ảnh cũ nằm trong kho riêng, giao diện dùng bản mới nhất, callback cũ không đổi kết quả mới. Chạy 38 ca Spring tập trung, 46 ca Teacher Web và 22 ca Chromium. Smoke trên stack cách ly đạt 9 kiểm tra và PostgreSQL ghi nhận cùng bài nộp đã chốt với hai ảnh và hai job hoàn thành. Trạng thái ban đầu được tạo bằng fixture ảnh trống qua bộ chuyển loopback. Độ chính xác và độ trễ OCR thật còn cần đo.
- Đã thêm “Thử xử lý lại” cho lỗi kỹ thuật trên ảnh hiện có. Spring xác nhận điều kiện và quyền, giữ phiên bản ảnh, tạo lượt xử lý mới sau commit và lưu audit. Giao diện yêu cầu đọc lại trạng thái nếu mất phản hồi trước khi có thể gửi thêm. Xác minh endpoint bằng Spring với H2 và gateway kiểm thử, và xác minh hành vi trình duyệt với API giả lập.
- Hàng đợi đã giữ bộ lọc, từ khóa và cách sắp xếp khi mở bài, quay lại hoặc tải lại trong cùng đợt và phiên đăng nhập. Từ khóa nằm trong trạng thái điều hướng của trình duyệt. Dashboard đã có liên kết mở đợt bằng bàn phím. Bộ đếm “Tổng bài hôm nay” và ngày hiển thị trên Dashboard dùng `Asia/Ho_Chi_Minh`, gồm bài nộp đúng 00:00 và loại bài từ 00:00 ngày kế tiếp.
- Hàng đợi tải tóm tắt qua `GET /api/v1/teacher/batches/{batchId}/review-summary`; API `/review` vẫn trả mảng ID. Chromium với API tổng hợp đo 3/12/32 request dữ liệu trước sửa và 2/2/2 sau sửa cho 1/10/30 bài. Một lượt desktop ghi thời gian đến khi đủ thẻ hiển thị là 214/282/332 ms trước và 299/301/306 ms sau; số đo đơn lẻ trên fixture chưa xác định độ trễ thực tế. Spring/PostgreSQL 16 cách ly đã trả 30 bản ghi có đúng thứ tự và phần tóm tắt điểm, độ tin cậy, bằng chứng. Đo Dashboard với lịch sử nhiều đợt và đo tải lạnh vẫn là công việc riêng.

## Vòng 3 · Nghiệm thu pilot

- Đã chạy luồng 1 và 30 ảnh tổng hợp qua Chromium, Spring, PostgreSQL 16, MinIO, Redis và worker `FIXTURE` trong môi trường cách ly. Đợt 30 có 30 ảnh khác nhau gán cho 30 học sinh, khớp 30/30 SHA-256 theo học sinh, không có ảnh xử lý lỗi. Chốt một bài, tải lại giữ điểm và hàng đợi còn 29 bài. Lượt chạy quan sát hoàn tất xử lý sau 5.695 ms từ khi gửi request upload, gồm thời gian polling, với một lượt fixture. Kịch bản tái chạy có ở [hướng dẫn kiểm thử trình duyệt](../../engineering/browser-testing.md#nghiệm-thu-bằng-dịch-vụ-thật).
- Quan sát giáo viên tự tạo đợt và vào hàng đợi theo tiêu chí Capstone. Ghi số lần phải nhờ trợ giúp, thời gian tới bài đầu tiên và điểm gây nhầm. Đo riêng p95 AI theo ảnh đã cắt và thời gian upload đến khi có kết quả. Ghi môi trường, số mẫu, loại ảnh và số thất bại cùng các số đo.
- Xác minh nhu cầu xuất bảng điểm, xử lý học sinh trùng trong nhiều đợt, và thao tác với tên tiếng Việt không dấu. Nếu có nhu cầu xuất điểm, chốt phiên bản bài nộp, phạm vi lớp, ai được xuất và trường được phép xuất trước khi xây.

## Kiểm chứng trong phiên khảo sát

| Kiểm tra | Kết quả và giới hạn |
| --- | --- |
| `npm run test:config --workspace=teacher-web` | 41/41. JSDOM ghi cảnh báo `requestSubmit` trong một nhóm test. |
| `npm run lint --workspace=teacher-web` | Exit 0, 4 cảnh báo React hooks/Fast Refresh. |
| `npm run build:teacher` và `npm run test:production --workspace=teacher-web` | Build thành công với URL HTTPS `.test`, 2/2 test bundle. Vite cảnh báo chunk lớn. |
| `npm run check:governance` | 9/9 sau khi chạy lại với quyền tạo kho Git tạm. Lần chạy sandbox lỗi ở `git init` của test hygiene. |
| Playwright `loading`, `workflows`, `teacher-review` | 34/34 trên Chromium desktop và viewport mobile. Portal/Teacher/Admin chạy bản build thật, API dùng dữ liệu tổng hợp. |
| Playwright khảo sát Teacher | 8/8 lần tái hiện có chủ đích trên hai viewport: hàng đợi rỗng báo hoàn tất khi mới xử lý 3/30 ảnh, bài cần xác nhận/chụp lại thiếu thao tác, POST duyệt trả 204 nhưng GET 503 làm UI báo lỗi, và hàng Dashboard thiếu điều khiển bàn phím. Kịch bản tạm tại `.local-artifacts/teacher-audit/audit.spec.mjs`. |
| Spring `TeacherReviewWorkflowIntegrationTest`, `BatchUploadTransactionTest`, `TeacherClassControllerTest`, `TeacherDashboardControllerTest`, `TeacherSubmissionImageTest` | 26/26 với H2, storage và gateway được mô phỏng ở các ca liên quan. Lần đầu `--offline` thiếu Spring Boot plugin trong cache. |
| Chrome DevTools MCP, website công khai | Truy cập Teacher với phiên trống chuyển sang Portal và hiển thị form đăng nhập. Chưa xác định revision của bản triển khai hoặc kiểm tra sau đăng nhập trên website công khai. [Teacher PC Preview](https://mathvisionkid-teacher.vercel.app/) |

Phiên này chưa nghiệm thu dịch vụ OCR/AI, PostgreSQL, MinIO và Redis cùng nhau, chưa đo p95 AI và chưa quan sát giáo viên sử dụng. Docker daemon không chạy khi kiểm tra. Dữ liệu tổng hợp và H2 xác nhận hành vi trong phạm vi đã nêu.

## Skills Applied

- `superpowers:writing-plans` và `domain-modeling` — tách vòng triển khai, xác định điểm đề xuất, điểm chính thức và vòng đời bài nộp.
- `mathvision-review` và `mathvision-quality` — đối chiếu nguồn ở đúng revision, rà soát phân quyền và quyết định điểm, chạy kiểm thử theo rủi ro.
- `web-design-guidelines` và `fixing-accessibility` — kiểm tra ngữ nghĩa điều hướng và trạng thái trên Teacher Web. [Vercel Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)
- `superpowers:brainstorming`, `superpowers:dispatching-parallel-agents` và `superpowers:verification-before-completion` — chọn thứ tự cải thiện, khảo sát song song và đối chiếu kết quả trước khi bàn giao.
