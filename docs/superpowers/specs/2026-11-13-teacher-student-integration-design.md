# Teacher–Student Integration

**Trạng thái** · Đề xuất chờ duyệt. PR #59 vẫn mở tại `bab688e`. Thiết kế dựa trên nhánh này và `develop` tại `3f5d18b`.

## Cơ sở và lựa chọn

Capstone Proposal trang 11–14, 22–25 và Architecture Design Document mục 4.5–4.6 mô tả Teacher tải ảnh theo đợt và Student tự luyện, cùng nguyên tắc điểm chính thức do giáo viên quyết định. Hộp bài được giao và tự tham gia lớp là mở rộng sản phẩm. Mục tiêu bảo vệ ảnh trẻ em trong tài liệu gồm mục đích sử dụng, consent, retention và xóa dữ liệu. Cần xác minh các kiểm soát đã vận hành trước pilot.

Spring quản lý quyền, Flyway quản lý schema và AI chạy nội bộ. `classroom_students` là roster hiện tại. Assignment đã có lớp, giáo viên, phép tính, thang điểm và khóa tạo lại. Student upload ảnh tự luyện hiện tạo Submission riêng, thiếu Assignment và Batch. Teacher review hiện bắt buộc Batch thuộc giáo viên đang phụ trách. TeacherDecision duy nhất theo submission lưu điểm chính thức. Phản hồi Student hiện đọc phân tích AI, chưa trả quyết định giáo viên. Quiz tự luyện và bài được giao là hai nguồn học tập riêng.

Phương án A mở rộng từ lớp Admin đã quản lý và giao một bài có thể nộp/chấm/trả điểm. Phương án B làm kết quả theo đợt đã có trước, có giá trị đối soát nhưng chưa kết nối hai vai trò. Phương án C làm tạo lớp và lời mời trước, giải quyết onboarding nhưng chưa giúp lớp giao và trả bài. Đề xuất A, tái dùng thiết kế kết quả theo bài ở bước tổng hợp và dùng mã/QR/link sau.

## Roadmap

1. **Bài được giao có vòng đời hoàn chỉnh.** Lớp hiện có, Teacher giao bài cộng/trừ có đề/hướng dẫn, Student nhận và gửi một ảnh đã xem riêng tư, Teacher chấm và trả điểm, Student xem điểm và nhận xét. Teacher có tiến độ theo bài từ roster đã giao.
2. **AI hỗ trợ chấm bài được giao.** Tích hợp job bền vững, đối chiếu đề đã giao và hiển thị bằng chứng cho Teacher. Ảnh không đúng đề, kết quả không chắc chắn và AI lỗi vẫn có đường chấm tay. Callback chỉ cập nhật analysis của lần xử lý còn hiệu lực. Điểm đã trả giữ nguyên.
3. **Điều hành nhiều lớp.** Tìm/lọc bài và học sinh, hàng chờ ưu tiên, sổ điểm nhiều bài, lịch sử nộp và trả điểm. Chốt quy tắc nộp muộn, trả lại để nộp lại, sửa điểm có lịch sử và chuyển giáo viên trước khi mở rộng các thao tác này.
4. **Teacher tạo lớp và mời học sinh.** Admin vẫn quản lý tài khoản, phân công/chuyển giáo viên và can thiệp roster có audit. Teacher được quyền tạo/quản lý lớp mình theo chính sách trường. Mã 6 số ngắn hạn, link/QR mang token ngẫu nhiên, thu hồi/xoay mã, giới hạn thử và yêu cầu đăng nhập. Đề xuất học sinh gửi yêu cầu tham gia, giáo viên duyệt, thêm roster idempotent. Lời mời không lộ danh sách lớp hay dữ liệu học sinh.

Chọn Submission có liên kết người nhận. Cách dùng Batch cho mọi ảnh giảm thay đổi màn review nhưng buộc tạo đợt không có ý nghĩa nghiệp vụ và trộn quyền của hai nguồn. Chọn snapshot người nhận kết hợp kiểm tra quyền hiện tại. Chỉ dựa roster động sẽ làm lịch sử “đã giao” thay đổi khi chuyển lớp. Chấm và trả trong một giao dịch giảm trạng thái cần giải thích. Nếu trường muốn duyệt điểm theo đợt trước khi công bố, thiết kế thêm trạng thái điểm nháp ở lát cắt sau. Việc gọi AI ngay khi nhận ảnh giúp tái sử dụng grading, đồng thời thêm vấn đề xác thực đúng đề và khôi phục job. Đề xuất bắt đầu bằng chấm tay có giá trị độc lập và giữ pipeline AI hiện tại cho nguồn batch.

## Lát cắt 1 · Chính sách đề xuất

- Teacher chỉ phát hành bài trong lớp mình đang phụ trách. Bổ sung nội dung đề/hướng dẫn bắt buộc khi phát hành và snapshot tên bài, đề, phép tính, thang điểm cùng người nhận. Snapshot là bằng chứng đã giao, roster hiện tại vẫn là thẩm quyền truy cập. Tạo Assignment dành cho batch cũ không tự giao. Tách phát hành rõ ràng, idempotent. Học sinh mới không tự nhận bài cũ. Khi rời lớp, chặn nộp, giữ lịch sử cá nhân và kết quả đã trả theo chính sách lưu giữ. Chuyển giáo viên khóa thao tác trên bài cũ cho cả người cũ lẫn người mới trong lát cắt này. Cần quyết định chuyển quyền trước pilot có đổi giáo viên.
- Một bài chính thức cho mỗi người nhận. Trùng request trả lại cùng kết quả. Mất mạng hoặc lỗi lưu ảnh được thử lại trên cùng bản ghi theo trạng thái. Chưa hỗ trợ lần làm thứ hai. Batch giấy và Student Web phải có nguồn rõ ràng. Bài batch cũ không tự thành bài Student Web, không cộng trùng, không chọn điểm đại diện từ nhiều bài. Nếu cần nhập bài giấy cho bài đã phát hành, cần chính sách đối soát riêng.
- Submission mới liên kết người nhận, Assignment và Student. Teacher thấy đề đã đóng băng cạnh ảnh và xác nhận ảnh đọc được, đúng đề trước khi chấm. Nếu sai đề hoặc ảnh không đọc được, ghi trạng thái cần xử lý kèm phản hồi, không tự cho 0. Nghiệm thu bằng ảnh giải đúng phép tính khác đề. Giữ quyền Batch hiện hành theo nguồn. Tái dùng ảnh, kiểm tra quyền, phần hiển thị review và TeacherDecision. Lát cắt 1 không phát sinh job AI cho nguồn bài được giao.
- Một thao tác rõ ràng **Chấm và trả điểm** ghi quyết định và công bố đồng thời. Chỉ trả cho chính học sinh điểm chính thức, thang điểm tại thời điểm giao, nhận xét dành cho học sinh và thời điểm trả. Lý do override nội bộ tách khỏi nhận xét. Điểm 0 là điểm hợp lệ. Bài chưa trả để trống điểm. Admin không đọc ảnh hay sửa điểm. Teacher xem số người đã giao, chưa nộp, chờ chấm, đã trả, và trạng thái rời lớp rõ ràng.
- Ảnh đã che, kiểm tra quyền trước khi nhận/đọc ảnh, kiểm tra loại và kích thước phía máy chủ, không đưa ảnh hay tên trẻ vào log/biên nhận. Dùng dữ liệu tổng hợp và PostgreSQL cách ly cho nghiệm thu. Chỉ mở pilot ảnh thật khi trường/chủ dự án xác nhận consent, retention, xóa ảnh và người chịu trách nhiệm.

| Tác nhân | Quyền đề xuất cho nguồn Student Web |
| --- | --- |
| Student đang trong lớp, thuộc snapshot | Đọc bài của mình và gửi ảnh một lần. Sau khi trả điểm, đọc kết quả của mình. |
| Student rời lớp hoặc vào lại | Khi rời lớp, chỉ đọc metadata kết quả đã trả của mình theo retention, ảnh và phân tích khóa. Khi vào lại, người có tên trong snapshot lấy lại quyền cho cùng bản ghi, không tạo lần nộp mới. |
| Teacher giao bài và đang phụ trách lớp | Đọc tiến độ và ảnh của bài đã nộp hợp lệ, kể cả bài đã nộp trước lúc học sinh rời lớp, trong thời hạn cho phép. Chấm và trả điểm với quyền còn hiệu lực. |
| Teacher ngoài lớp, Teacher cũ hoặc người mới được phân công | Không đọc ảnh hay sửa điểm của bài cũ. Bài đang chờ được giữ, khóa thao tác cho đến khi có quy tắc bàn giao. |
| Admin | Quản lý tài khoản, roster và phân công. Không có quyền xem ảnh, phân tích hay chấm điểm qua vai trò Admin. |

Kiểm tra quyền trước mọi truy vấn danh sách, bộ đếm, chi tiết và tải ảnh. Khi ghi, phát hành/nộp/chấm và thay đổi roster/phân công cùng tuân thủ một thứ tự khóa theo lớp rồi tài nguyên. Giao dịch chốt sau thay đổi quyền phải đọc lại quyền và từ chối nếu mất quyền. Tiến độ chỉ đếm người nhận của lần giao, dùng một nhóm trạng thái chính cho mỗi người và cờ rời lớp riêng. Kết quả batch giữ nguồn và quyền riêng.

## Kế hoạch triển khai lát cắt 1 · Sau duyệt

1. **Phát hành và danh sách người nhận.** Mở rộng module assignment và Flyway sau version thực tế. Tạo bản ghi phát hành bất biến và người nhận unique theo bài/học sinh. Viết test trước cho hai lần phát hành đồng thời, quyền và roster. Dự kiến `POST /api/v1/teacher/assignments/{id}/publish` và `GET /api/v1/student/assignments`, detail theo ID. Danh sách 25 mục mặc định, tối đa 50, sắp theo thời điểm giao giảm dần rồi ID. Giữ envelope lỗi hiện có.
2. **Nộp ảnh.** `POST /api/v1/student/assignments/{id}/submission` nhận multipart và khóa retry, trả `202` cùng ID/trạng thái cho bản ghi đã nhận. Đặt chỗ duy nhất theo người nhận và lưu checksum/key để phân biệt replay với payload khác (409). Đặt object key riêng theo submission, giữ trạng thái nhận/lỗi bền vững và cơ chế đối soát object theo bản ghi khi tiến trình khởi động lại. Sau khi lưu xác thực mới chuyển sang chờ chấm. Dùng lại privacy/crop, khóa object trong lúc chưa sẵn sàng. Detail Student là nguồn đọc trạng thái, nếu đang nhận ảnh thì poll 2–5 giây có backoff, dừng khi sẵn sàng, lỗi hoặc rời màn. Kiểm thử trùng request, lỗi object store, restart trước/sau khi lưu và rời lớp trong lúc tải.
3. **Duyệt và trả.** Tái dùng màn review cùng thẩm quyền TeacherDecision. Tất cả đường ghi cho nguồn mới đi qua cùng giao dịch kiểm tra quyền, khóa bản ghi, ghi điểm và công bố một lần. Chặn mutation batch cũ trên nguồn mới. Retry cùng quyết định trả lại kết quả, quyết định khác sau chốt trả 409. Điểm nguyên từ 0 đến thang đã giao, lưu người chấm và thời điểm, DTO Student chỉ mở điểm/nhận xét sau trả. Kiểm thử 0, ngoài thang, người khác, Admin, mất quyền, hai Teacher request cạnh tranh và gọi thẳng endpoint cũ.
4. **UI và nghiệm thu xuyên vai trò.** Teacher theo dõi tiến độ theo bài, tìm/lọc học sinh, mở bài và quay về đúng ngữ cảnh. Student thấy Bài được giao, gửi ảnh, mở Kết quả. Chạy MCP với Teacher phụ trách, Teacher khác, Admin, hai học sinh trong lớp và một ngoài lớp trên backend local và PostgreSQL cách ly. Đối chiếu DB, API và UI, gồm thử ID ảnh/điểm chéo tài khoản, grade 0, ảnh đúng phép tính nhưng sai đề và cả hai nguồn bài. Chạy migration, build/typecheck, kiểm tra desktop/mobile, bàn phím, tải chậm và mất phiên, rồi Quality gate.

**Giới hạn nghiệm thu đề xuất** · Đo lớp 50 học sinh và tối đa 50 ảnh một bài, theo giới hạn ảnh máy chủ hiện hành đã xác minh ở đầu triển khai. Đo số truy vấn ở 1 và 50 học sinh, không truy vấn từng học sinh. Đối soát upload thử lại bằng dữ liệu tổng hợp. Spring chịu trách nhiệm đối soát object và kiểm tra truy cập. Trước khi mở pilot, chỉ định người xử lý yêu cầu xóa và thời hạn cho object, ảnh dẫn xuất, metadata và kết quả. 

| Tình huống nghiệm thu | Kết quả phải quan sát |
| --- | --- |
| Teacher giao bài cho hai học sinh, học sinh ngoài lớp mở ID trực tiếp | Hai bản ghi người nhận. Hai học sinh thấy đúng đề. API từ chối học sinh ngoài lớp và không gửi nội dung hoặc số liệu. |
| Hai request nộp đồng thời hoặc tiến trình dừng ngay sau khi lưu ảnh | Tối đa một bài có thể chấm. Replay cùng payload về cùng ID. Nội dung khác xung đột khi đã nhận. Object chưa xác thực không thể đọc, được đối soát hoặc dọn theo trạng thái bền vững. |
| Rời lớp trong lúc tải, chuyển giáo viên trong lúc chấm | Nếu thay đổi quyền hoàn tất trước lần ghi cuối, giao dịch nộp hoặc trả điểm bị từ chối. Không xuất hiện điểm hay ảnh đã nhận giả trên UI. |
| Teacher xem ảnh đúng phép tính nhưng sai đề, hoặc ảnh không đọc được | UI hiện trạng thái cần xử lý và phản hồi được phép. Không ghi điểm. Lát cắt đầu giữ bài để giáo viên xem và liên hệ học sinh. Luồng gửi lần hai cần chính sách riêng. |
| Teacher chấm điểm 0 và hai lần chốt cạnh tranh | Trước khi trả, Student không thấy điểm. Sau khi trả, chính học sinh thấy `0 / thang điểm` và nhận xét. Chỉ có một TeacherDecision, tiến độ lớp tăng một. Teacher khác, Admin và người học khác không đọc được điểm hoặc ảnh. |
| Teacher mở bài giấy từ đợt chấm cũ | Quyền review và phép đếm theo đợt giữ nguyên. Tổng hợp Student Web chỉ đếm người nhận của lần giao và không nhập dữ liệu batch vào kết quả. |

## Phản biện EGM

Hai reviewer ngữ cảnh mới, Design Critic và Structural, cùng dùng Feature Spec Standard. Findings đã đưa vào bản này gồm đúng đề so với đúng phép tính, actor matrix và quyền sau chuyển lớp, ghi điểm và công bố nguyên tử, khóa/idempotency và khôi phục upload, cách tách nguồn batch, cùng ca nghiệm thu truy cập trực tiếp. Hoãn dispatch AI cho nguồn mới sang lát cắt riêng để bổ sung job bền vững và nghiệm thu callback muộn. Quy tắc chuyển giáo viên, trả lại để nộp lại, chính sách retention và giới hạn pilot còn chờ duyệt.

## Git Flow

Sau khi PR #59 vào develop, fetch và xác minh revision chứa thay đổi cần tái dùng. Tách worktree sạch và nhánh `feature/teacher-student-assignments` từ develop mới nhất, PR về develop. Nếu #59 còn mở khi cần triển khai, giữ thiết kế và không ghép diff nền chưa duyệt vào PR mới. Bản nháp hiện chỉ thêm tài liệu.
