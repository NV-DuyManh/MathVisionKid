# Teacher Web Reliability Implementation Plan

> Mốc hiện tại là hoàn thiện Teacher Web trên `Loc/Teacher-features`. Tiêu chí bàn giao gồm luồng giáo viên qua stack cách ly, phân quyền, tính toàn vẹn dữ liệu và hồi quy trình duyệt. Đánh giá model thật và pilot là phần việc nghiệm thu cấp dự án sau mốc này. Xem [báo cáo tiến độ hiện tại](../../../report/teacher-web-reliability-session-2026-11-12.md).

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

Các mục dưới đây đã triển khai và được kiểm tra trong phạm vi ghi tại “Kết quả vòng 1”. Ca ảnh không đọc được dùng fixture để xác minh trạng thái và bước xử lý. Pilot với giáo viên và model thật ở vòng 3.

### 1. Phân biệt đã lưu điểm và tải lại dữ liệu

**Tệp chính** — `apps/teacher-web/src/services/api/{TeacherService,SpringTeacherService,MockTeacherService}.ts`, `pages/SubmissionReviewPage.tsx`, `tests/api-contracts.test.mjs` và `tests/review-fixes-regression.test.mjs`.

- [x] Thêm ca POST trả 204 rồi GET trả 503, và ca POST bị ngắt trước khi nhận phản hồi nhưng GET sau đó trả điểm đã chốt.
- [x] Giữ endpoint hiện hành. Cho `approveSubmission(submissionId: string)` và `overrideSubmission(submissionId: string, score: number, reason: string)` trả `Promise<void>` sau POST thành công. Trang lấy dữ liệu cập nhật qua React Query. Cập nhật ca contract cũ đang yêu cầu adapter tự GET sau khi ghi. Nếu biết POST đã thành công, giao diện thông báo đã lưu dù tải lại lỗi. Khi chưa biết POST có thành công, cho kiểm tra lại trước khi gửi tiếp.
- [x] Chạy `npm run test:config --workspace=teacher-web` và các ca trình duyệt. Xác nhận người dùng thấy đúng kết quả, thao tác không tự gửi lần hai và tải lại hiển thị điểm chính thức.

### 2. Dùng trạng thái của đợt để hiển thị hàng đợi

**Tệp chính** — `apps/teacher-web/src/pages/{ReviewQueuePage,BatchDetailPage}.tsx`, `apps/teacher-web/tests/review-fixes-regression.test.mjs`, `tests/browser/teacher-review.spec.mjs`.

- [x] Thêm ca đợt có 3/30 ảnh đã xử lý và hàng đợi rỗng, đợt chỉ có bài thất bại, đợt chờ ảnh và đợt đã chốt toàn bộ.
- [x] Đọc chi tiết đợt qua query `['batch', batchId]` hiện có. Dùng `status`, `processedCount`, `pendingReviewCount`, `failedCount` và `finalizedCount` để hiển thị trạng thái. Cập nhật có giới hạn khi đang xử lý và cho thử lại khi tải lỗi. Điều kiện “đã chốt toàn bộ” cần đối chiếu số đã chốt với số bài trong đợt.
- [x] Kiểm tra trên desktop và màn hẹp. Mở đường dẫn trực tiếp hoặc quay lại từ một bài đang duyệt phải thấy cùng tiến độ. Bài lỗi có đường dẫn tới chi tiết và thông báo bước tiếp theo.

### 3. Cho giáo viên xử lý bài AI không chắc chắn

**Tệp chính** — `backend/business-api/src/main/java/com/mathvisionkids/api/{submission/SubmissionService,batch/BatchResponse}.java`, `apps/teacher-web/src/pages/SubmissionReviewPage.tsx`, `TeacherReviewWorkflowIntegrationTest.java` và `tests/browser/teacher-review.spec.mjs`.

- [x] Thêm ca bài `NEEDS_CONFIRMATION` có ảnh đọc được, bài `NEEDS_RETAKE` từ fixture, bài chưa có đề xuất, bài đã chốt, và tài khoản không còn được phân lớp. Xác nhận 0 là điểm hợp lệ nếu được chủ động nhập và có lý do. Kiểm tra hai lần ghi đồng thời chỉ tạo một quyết định.
- [x] Dùng `POST /api/v1/teacher/submissions/{id}/override` cho chấm thủ công ở trạng thái được phép. Giữ kiểm tra quyền sở hữu, thang điểm, lý do, tính bất biến của điểm đã chốt và audit. Chỉ cho duyệt đề xuất khi có đề xuất hợp lệ. Ở ca cần ảnh mới, vòng đầu hiển thị lý do và giữ bài cần xử lý. Đường thay ảnh trên cùng bài nộp thuộc vòng 2.
- [x] Kiểm tra các ca Spring với profile `test`, sau đó chạy thử browser và kịch bản dịch vụ riêng. Kiểm tra quyết định tồn tại sau reload, ảnh riêng tư và bộ đếm phản ánh đúng trạng thái.

### Kết quả vòng 1

- Teacher Web xác nhận lưu điểm riêng với việc tải lại dữ liệu. Khi phản hồi lưu bị mất, giáo viên kiểm tra lại trạng thái trước khi gửi tiếp. Hàng đợi dùng số liệu của đợt để phân biệt đang xử lý, lỗi, chờ ảnh và đã chốt hết.
- Spring yêu cầu `imageLegible: true` để chấm thủ công bài `NEEDS_CONFIRMATION` và ghi xác nhận vào audit. Bài `NEEDS_RETAKE` chờ ảnh thay thế. Giáo viên phải vừa là chủ đợt vừa đang phụ trách lớp. Việc bàn giao đợt cũ thuộc một luồng riêng.
- Kiểm tra cuối trên thay đổi hiện tại đạt 46/46 ca Teacher Web, 18/18 ca Chromium cho chốt điểm và hàng đợi, 8/8 ca Spring cho quy trình duyệt. Lint giữ 4 cảnh báo sẵn có. Kiểm thử trình duyệt trên PostgreSQL, MinIO, Redis, Spring, FastAPI và Celery cách ly đạt 8/8 kiểm tra, gồm upload một ảnh tổng hợp, khớp hash ảnh, lưu điểm qua reload và hàng đợi hết việc. Worker dùng nhận diện fixture. Số liệu này chưa đo độ chính xác hay độ trễ của OCR thật.

## Vòng 2 · Khôi phục bài lỗi và giảm thao tác

- Đã triển khai thay ảnh cho bài `NEEDS_RETAKE` trên cùng bài nộp. Teacher Web dùng lại trình che thông tin, Spring kiểm tra quyền và JPEG tối đa 8 MB, lưu bản ảnh mới cùng audit và phát job sau commit. Ảnh cũ nằm trong kho riêng, giao diện dùng bản mới nhất, callback cũ không đổi kết quả mới. Chạy 38 ca Spring tập trung, 46 ca Teacher Web và 22 ca Chromium. Smoke trên stack cách ly đạt 9 kiểm tra và PostgreSQL ghi nhận cùng bài nộp đã chốt với hai ảnh và hai job hoàn thành. Trạng thái ban đầu được tạo bằng fixture ảnh trống qua bộ chuyển loopback. Độ chính xác và độ trễ OCR thật còn cần đo.
- Đã thêm “Thử xử lý lại” cho lỗi kỹ thuật trên ảnh hiện có. Spring xác nhận điều kiện và quyền, giữ phiên bản ảnh, tạo lượt xử lý mới sau commit và lưu audit. Giao diện yêu cầu đọc lại trạng thái nếu mất phản hồi trước khi có thể gửi thêm. Xác minh endpoint bằng Spring với H2 và gateway kiểm thử, và xác minh hành vi trình duyệt với API giả lập.
- Hàng đợi đã giữ bộ lọc, từ khóa và cách sắp xếp khi mở bài, quay lại hoặc tải lại trong cùng đợt và phiên đăng nhập. Từ khóa nằm trong trạng thái điều hướng của trình duyệt. Dashboard đã có liên kết mở đợt bằng bàn phím. Bộ đếm “Tổng bài hôm nay” và ngày hiển thị trên Dashboard dùng `Asia/Ho_Chi_Minh`, gồm bài nộp đúng 00:00 và loại bài từ 00:00 ngày kế tiếp.
- Hàng đợi tải tóm tắt qua `GET /api/v1/teacher/batches/{batchId}/review-summary`; API `/review` vẫn trả mảng ID. Chromium với API tổng hợp đo 3/12/32 request dữ liệu trước sửa và 2/2/2 sau sửa cho 1/10/30 bài. Một lượt desktop ghi thời gian đến khi đủ thẻ hiển thị là 214/282/332 ms trước và 299/301/306 ms sau; số đo đơn lẻ trên fixture chưa xác định độ trễ thực tế. Spring/PostgreSQL 16 cách ly đã trả 30 bản ghi có đúng thứ tự và phần tóm tắt điểm, độ tin cậy, bằng chứng. Đo Dashboard với lịch sử nhiều đợt và đo tải lạnh vẫn là công việc riêng.

## Vòng 3 · Nghiệm thu Teacher Web

- Đã chạy luồng 1 và 30 ảnh tổng hợp qua Chromium, Spring, PostgreSQL 16, MinIO, Redis và worker `FIXTURE` trong môi trường cách ly. Đợt 30 có 30 ảnh khác nhau gán cho 30 học sinh, khớp 30/30 SHA-256 theo học sinh, không có ảnh xử lý lỗi. Chốt một bài, tải lại giữ điểm và hàng đợi còn 29 bài. Lượt chạy quan sát hoàn tất xử lý sau 5.695 ms từ khi gửi request upload, gồm thời gian polling, với một lượt fixture. Kịch bản tái chạy có ở [hướng dẫn kiểm thử trình duyệt](../../engineering/browser-testing.md#nghiệm-thu-bằng-dịch-vụ-thật).
- Chốt hồi quy desktop/mobile cho luồng đăng nhập, lớp, giao bài, tải ảnh, xử lý lỗi, duyệt và xem kết quả. Ba kịch bản tạo đợt trước đây timeout ở bước chọn học sinh đã dùng lại fixture đúng hợp đồng Spring. Xem kết quả tại checklist cuối.
- Đối chiếu kết quả hồi quy với bằng chứng stack thật, kiểm tra thay đổi cuối về quyền và dữ liệu, rồi cập nhật báo cáo bàn giao Teacher Web.

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

Phiên khảo sát ban đầu dùng API mô phỏng và H2. Các lượt tích hợp sau đó ở Vòng 1–3 dùng PostgreSQL, MinIO, Redis và worker ở chế độ `FIXTURE`. Nghiệm thu với OCR thật, đo p95 AI và quan sát giáo viên sử dụng vẫn đang mở.

## Đối chiếu nhánh Teacher Web

| Hạng mục | Trạng thái và bằng chứng |
| --- | --- |
| Chốt điểm, đọc lại sau khi mất phản hồi, chấm thủ công bài ảnh đọc được | Đã có trên nhánh `Loc/Teacher-features`. Playwright mô phỏng lỗi mạng và OCR không chắc chắn. Kịch bản tích hợp 30 ảnh kiểm tra điểm chính thức còn nguyên sau tải lại và 29 bài vẫn chờ duyệt. |
| Thay ảnh và thử xử lý lại | Cả hai thao tác đã triển khai. Kịch bản stack cách ly xác nhận thay ảnh riêng tư trên cùng bài nộp và xử lý lại bằng worker fixture. Ca HTTP 503 từ adapter giữa Spring và FastAPI phát hiện đợt từng báo `COMPLETED` dù job lỗi. Sau bản sửa, đợt báo `FAILED`, giáo viên thử lại từ chi tiết bài và chốt điểm sau callback. PostgreSQL xác nhận một ảnh, hai job (`SUPERSEDED`, `COMPLETED`) và một sự kiện audit retry. |
| Quyền và dữ liệu | Spring/H2 kiểm tra phân công lớp, chủ đợt, từ chối học sinh sửa ảnh thuộc đợt và bỏ qua callback cũ. Kịch bản stack cách ly xác nhận tài khoản ngoài phạm vi nhận 403 với chi tiết bài, ảnh và hai thao tác chấm điểm. |
| Hàng đợi và Dashboard | Playwright xác nhận hàng đợi dùng 2 request cho 1, 10 và 30 bài. Dashboard chuyển sang truy vấn tổng hợp theo đợt trong DB. Hibernate/H2 ghi nhận trước sửa 5 và 25 câu SQL với 1 và 21 đợt. Sau sửa là 2 câu trong cả hai trường hợp. Bộ đếm Dashboard khớp chi tiết ba đợt trên PostgreSQL cách ly. Tổng vẫn gồm lịch sử và danh sách hiển thị tối đa 10 đợt. Chưa đo độ trễ tải thật. |
| Tạo bài và mất phản hồi | Đã triển khai migration V30 sau khi duyệt. Chromium với Spring và PostgreSQL cách ly đã ngắt phản hồi `201` sau khi lưu, tải lại và gửi lại. API trả `200` với cùng ID và chỉ có một bản ghi. Hai request đồng thời cùng khóa cũng trả cùng ID. Hai thao tác riêng vẫn tạo được bài cùng tiêu đề. |
| Pilot và OCR thật | Chưa có quan sát giáo viên hoặc số đo chất lượng và p95 cho model chấm phép tính. Cần trọng số YOLO đúng manifest và bộ ảnh bài làm đã khử định danh có nhãn đối chiếu. |

Nút “Xử lý ngay” dùng `nextReviewBatchId` từ truy vấn tổng hợp sẵn có và mở hàng đợi của đợt gần nhất còn bài chờ duyệt, kể cả đợt nằm ngoài 10 đợt gần đây. Playwright tái hiện nút mở danh sách chung trước bản sửa. Trên PostgreSQL cách ly, Chromium đăng nhập qua Portal, mở đúng đợt cũ và hiển thị bài chờ khi cả 10 đợt mới hơn đều trống. Ca này kiểm chứng điều hướng và hợp đồng API, không chạy model.

Kết quả chạy lại sau bản sửa chọn lớp: 64/64 Playwright trên desktop và viewport mobile với API mô phỏng, 46/46 ca cấu hình và hành vi Teacher Web, TypeScript thành công. Spring đạt 577 ca, bỏ qua 2. Các ca Spring lỗi ở lần đầu dùng bài thuộc đợt để kiểm tra nộp độc lập hoặc kỳ vọng đợt chỉ có job lỗi báo `COMPLETED`. Lần chạy lại dùng đúng loại bài nộp và kiểm tra đợt lỗi hiện trong chi tiết đợt, ngoài hàng đợi duyệt.

### Chống tạo trùng khi mất phản hồi

Teacher Web tạo một UUID cho thao tác lưu và dùng lại UUID khi thử gửi cùng nội dung. Spring kiểm tra quyền hiện tại của giáo viên trước khi xử lý. PostgreSQL lưu UUID tùy chọn trên bài tập và áp ràng buộc duy nhất theo giáo viên và UUID. Gửi lại cùng UUID và nội dung trả về bài đã tạo. Gửi cùng UUID với nội dung khác trả `409`. Thao tác tạo bài mới dùng UUID mới để giáo viên vẫn có thể chủ động giao bài cùng tiêu đề. Migration bổ sung cột nullable và ràng buộc, dữ liệu cũ giữ nguyên.

PostgreSQL cách ly xác nhận V30, hai request đồng thời, xung đột `409` và hai thao tác chủ động có cùng nội dung. Chromium trên stack thật xác nhận chỉ có một bản ghi sau khi mất phản hồi và tải lại. Ca quyền lớp bị thu hồi được kiểm tra bằng Spring/H2. Các biên nhận nằm tại `.local-artifacts/teacher-round1/assignment-idempotency-postgres.json` và `.local-artifacts/teacher-round1/assignment-idempotency-browser.json`.

### Đánh giá cấp dự án sau mốc Teacher Web

Hai hoạt động có thể chạy độc lập. Benchmark model cần trọng số đã xác minh và ảnh ẩn danh có nhãn đối chiếu để đo chất lượng đề xuất và độ trễ. Pilot UX cần giáo viên và kịch bản thực tế, có thể dùng fixture nếu mục tiêu chỉ là quan sát thao tác. Pilot đánh giá mức tiết kiệm công chấm cần kết quả model thật. Mục tiêu Capstone về AI p95 và quan sát giáo viên được giữ tại đây cho lần nghiệm thu cấp dự án.

1. Lấy trọng số YOLO từ chủ dự án và đối chiếu SHA-256 với `ai/runtime/models/model_manifest.json`. Trọng số chỉ định hiện thiếu tại đường dẫn cấu hình. Checkpoint CRNN dùng cho ảnh dòng chữ cắt sẵn thuộc pipeline khác.
2. Chuẩn bị tập ảnh bài làm đã khử định danh, có nhãn được đối chiếu độc lập. Ghi phạm vi phép cộng và trừ, độ dài số, tiêu chí ảnh không đọc được và nguồn ảnh. Tách mẫu pilot khỏi tập dùng để tinh chỉnh. Harness đánh giá hiện có ghi trạng thái sẵn sàng của dữ liệu và provenance, chưa thực hiện benchmark đầy đủ.
3. Chọn revision và khởi động stack cách ly với `RUNTIME_MODE=MODEL`. Kiểm tra `/ready` báo đúng mode, Redis, worker và model sẵn sàng. Kiểm tra provenance của kết quả từng job trước khi ghi nhận là model thật. Chạy smoke một ảnh trước khi chạy đợt 1–30 ảnh theo [hướng dẫn tích hợp](../../engineering/browser-testing.md#nghiệm-thu-bằng-dịch-vụ-thật).
4. Đo riêng p95 AI mỗi ảnh đã cắt theo mục tiêu ≤ 12 giây và thời gian upload đến kết quả. Ghi số mẫu, môi trường, phiên bản model, các lỗi và số ca model yêu cầu xác nhận. Một lượt fixture hoặc một mẫu smoke không đủ để nghiệm thu p95.
5. Quan sát giáo viên tự tạo bài, gán ảnh, theo dõi và chốt điểm. Ghi thời gian tới bài đầu tiên, số lần cần trợ giúp và điểm gây nhầm. Giáo viên quyết định điểm chính thức trong mọi lượt.

### Tiến độ bổ sung · 12/11/2026

- Đã thêm duyệt bài tiếp theo sau khi xác nhận lưu. Kịch bản tích hợp 30 ảnh mở bài khác trong cùng đợt và vẫn ghi đúng một điểm chính thức. Chrome DevTools MCP kiểm tra trực tiếp luồng duyệt tiếp và quay lại bộ lọc chờ duyệt tại viewport 390 px.
- Trang lịch sử có bộ lọc đợt chờ duyệt và có bài lỗi. Spring/H2 xác nhận truy vấn danh sách đợt dùng 2 câu SQL cho 1 hoặc 21 đợt. Trên PostgreSQL cách ly, 21 dòng tóm tắt khớp dữ liệu chi tiết.
- Đã thêm lưu và mở ảnh tiếp theo, xác nhận che riêng từng ảnh. Bản tích hợp 30 ảnh kiểm tra 30 xác nhận độc lập, 30/30 SHA-256 đúng học sinh, 0 lỗi và 29 bài còn chờ sau khi chốt một bài. FastAPI và provenance kết quả đều ở chế độ `FIXTURE`.
- Ảnh chưa gửi được bảo vệ khi tải lại hoặc rời trang. Đã sửa lỗi từng làm mất ảnh khi dùng Back trong SPA. Khi kết nối lại, chỉ cho gửi nếu đợt còn mở. Nếu đợt đã nhận ảnh từ tab khác, giữ bản nháp và khóa gửi thêm.
- Đã tái hiện mất phản hồi tạo đợt chấm trước V31: hai `201` với hai ID, một đợt trống và một đợt nhận ảnh. Migration khóa UUID tùy chọn theo giáo viên đã triển khai trên stack cách ly sau khi được duyệt.
- [x] Thêm khóa riêng cho đợt, áp ràng buộc duy nhất theo giáo viên và đối chiếu bài tập khi phát lại. Kiểm tra quyền hiện tại trước khi trả lại đợt. Client giữ khóa theo phiên, bài tập và mục lịch sử của thao tác.
- [x] Nghiệm thu stack cách ly. Chromium xác nhận mất phản hồi sau khi lưu, phát lại cùng ID, một lần upload và một dòng lịch sử. PostgreSQL xác nhận V31, hai yêu cầu đồng thời, xung đột 409, thu hồi quyền 403, khóa độc lập theo giáo viên, hai thao tác riêng và phát lại sau khi đợt đã nhận ảnh.
- [x] Xác nhận trước khi bỏ bản nháp bằng Browser Back/Forward. Chrome DevTools MCP tái kiểm sau SSO cho thấy giữ ảnh khi ở lại và cho phép đi tiếp khi xác nhận rời trang. Ảnh nháp nằm trong bộ nhớ trang.
- [x] Chốt hồi quy Playwright với API mô phỏng. Lượt cuối trên mã bàn giao đạt 94/94 sau khi sửa fixture lớp theo DTO `userId/displayName`. Kiểm thử kết nối lại cũng xác nhận giữ ảnh đã che và khóa gửi nếu đợt đã nhận ảnh. [Log hồi quy](../../../.local-artifacts/teacher-round1/final-playwright-regression.log)
- [x] Kiểm chứng Chromium trên stack cách ly với FastAPI `FIXTURE`. Đợt 30 ảnh đạt 11 kiểm tra, 30/30 ảnh khớp hash, 0 lỗi, chốt một bài rồi mở bài tiếp theo. Kịch bản mất phản hồi và Back xác nhận hai phản hồi 201/200 cùng ID, một lần gửi ảnh, một dòng lịch sử và bản nháp được giữ khi chọn ở lại. [Biên nhận 30 ảnh](../../../.local-artifacts/teacher-round1/e2e-teacher-web-final-rerun-30/teacher-live-results.json) · [Biên nhận gửi lại và Back](../../../.local-artifacts/teacher-round1/duplicate-batch-live-results.json)
- [x] Rà soát độc lập và kiểm chứng bằng Chrome DevTools MCP trên stack cách ly. Mở danh sách lớp và form giao bài chọn sẵn lớp, kiểm tra đợt 30/30, mở hàng đợi, duyệt một bài tổng hợp và mở bài tiếp theo. Hai vấn đề về bản nháp được sửa trước bàn giao.

[Báo cáo phiên nghiệm thu](../../../report/teacher-web-reliability-session-2026-11-12.md) ghi rõ môi trường, hồi quy và biên nhận.

## Skills Applied

- `superpowers:writing-plans` và `domain-modeling` — tách vòng triển khai, xác định điểm đề xuất, điểm chính thức và vòng đời bài nộp.
- `mathvision-review` và `mathvision-quality` — đối chiếu nguồn ở đúng revision, rà soát phân quyền và quyết định điểm, chạy kiểm thử theo rủi ro.
- `web-design-guidelines` và `fixing-accessibility` — kiểm tra ngữ nghĩa điều hướng và trạng thái trên Teacher Web. [Vercel Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)
- `superpowers:brainstorming`, `superpowers:dispatching-parallel-agents` và `superpowers:verification-before-completion` — chọn thứ tự cải thiện, khảo sát song song và đối chiếu kết quả trước khi bàn giao.
