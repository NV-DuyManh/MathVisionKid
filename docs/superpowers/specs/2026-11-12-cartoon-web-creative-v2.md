# MathVision Kids · Creative Direction và Design System v2

Phụ lục của [định hướng đã duyệt](./2026-11-12-cartoon-web-direction.md). Chủ dự án đã duyệt hướng Sổ tay Ngôi Sao và cho phép triển khai toàn bộ bốn web theo từng nhóm màn hình có thể kiểm chứng.

Portal công khai có một lối vào tài khoản chung mang nhãn **Đăng nhập**. Vai trò từ tài khoản quyết định đích sau đăng nhập. Các ảnh và kết quả cũ về mục lục ba vai trò bên dưới là bằng chứng lịch sử của prototype.

Mục tiêu là kiểm chứng nhận diện và khả năng hoàn thành tác vụ trên bốn web. Giữ nguyên dữ liệu, hợp đồng API, quyền, đăng nhập và nghiệp vụ. Áp dụng rủi ro và biện pháp giảm thiểu trong đặc tả gốc, đặc biệt với mã Expo dùng chung và ảnh học sinh.

## Ba cách tổ chức trải nghiệm

| Phương án | Cấu trúc và tương tác đặc trưng | Đánh đổi |
| --- | --- | --- |
| **Sổ tay Ngôi Sao** | Một thao tác tiếp theo được làm rõ trên từng trang. Student đi qua trang học và trang bài toán như mở hai trang vở, còn Teacher dùng cặp bài làm và quyết định. Admin dùng các hàng và lề thẳng để theo dõi bản ghi. | Cùng một ngôn ngữ ở cả bốn web. Cần kiểm soát họa tiết vở để ảnh thật và chữ luôn dễ đọc. |
| **Bản đồ học tập** | Không gian học được dẫn dắt bằng các điểm đến, mỗi điểm mở một nhóm hoạt động đã có. Portal cho thấy các lối vào. Teacher và Admin dùng cụm tác vụ như các điểm đến. | Mạnh ở định hướng cho trẻ. Khó chuyển sang hàng đợi và bảng nghiệp vụ. Dễ vô tình ngụ ý tiến độ hay mở khóa mà hệ thống không có. |
| **Xưởng toán** | Bố cục theo bàn thao tác, công cụ và khu vực kết quả. Student đi theo chuỗi chụp, xem, xử lý. Teacher đối chiếu bằng chứng bên cạnh công cụ. Admin tập trung trên thanh lọc và bảng. | Rõ thao tác và hợp màn làm việc. Portal khó kể câu chuyện học tập và tổng thể dễ mang cảm giác công cụ hơn ứng dụng cho trẻ. |

**Đề xuất chọn Sổ tay Ngôi Sao.** Ngôi sao nguyên bản đóng vai bạn đồng hành kiên nhẫn, chỉ dẫn bước tiếp theo và khích lệ trẻ khi gặp khó. Hình ảnh vở ô ly nối trực tiếp với cách học và ảnh bài làm của sản phẩm. Dùng sự biểu cảm có chủ đích của mascot và cách chia bài thành bước nhỏ làm nguyên tắc tham khảo. [Duolingo Illustration](https://design.duolingo.com/illustration/duo) · [LingoDeer Help Center](https://support.lingodeer.com/en/support/solutions/articles/61000306561-what-s-the-difference-between-lingodeer-and-lingodeer-plus-)

## Ngôn ngữ hình ảnh và token thử nghiệm

- **Bố cục.** Họa tiết ô ly nét mảnh ở vùng mở đầu Portal và Student. Chừa bề mặt phẳng cho công thức, ảnh, form và bảng. Teacher dùng lề để tách bằng chứng và quyết định. Admin dùng hàng rõ, căn số nhất quán và cột thao tác ổn định.
- **Ngôi sao.** Dùng PNG hiện có của nhóm, giữ dáng và tỷ lệ. Hiện lớn ở điểm đón Portal, vừa ở đầu bài hoặc phản hồi Student, nhỏ ở điểm đón và màn rỗng Teacher/Admin. Khu vực ảnh, điểm và xác nhận thao tác dành không gian cho dữ liệu. Illustration dùng đồ học tập, ô ly và nét chì cùng cách phối nét, ánh sáng, tỷ lệ.
- **Chữ.** Thử Nunito cho tiêu đề Portal/Student, Plus Jakarta Sans cho chữ đọc và giao diện vận hành, giữ fallback sẵn có. Mẫu type scale 14/16/20/28/40 px, nội dung Student bắt đầu 16 px. Kiểm tra dấu tiếng Việt, tên dài, chữ số tabular cho điểm và bảng. Giữ thẳng cột hàng đơn vị và hàng chục trong bài đặt tính.
- **Màu thử.** Mực `#172554`, nền giấy `#FFFBF0`, bề mặt `#FFFFFF`, hành động chung `#1D4ED8`, vàng sao `#F6C34E`, nhấn Teacher `#047857`, nhấn Admin `#4338CA`. Nút vàng dùng chữ mực. Trạng thái dùng semantic token riêng, kèm chữ và biểu tượng. Đo lại mọi cặp chữ/nền, hover, focus và trạng thái ở prototype trước khi khóa token.
- **Hình khối và chiều sâu.** Thử spacing 4/8/12/16/24/32 px. Thẻ học bán kính 20 px, bảng và panel vận hành 12 px. Nút chính Student có cạnh nổi và nén nhẹ khi bấm, Teacher/Admin dùng viền và elevation cho thứ tự thao tác. Dùng icon nét bo, cỡ 20/24 px, có nhãn cho thao tác quan trọng.
- **Motion.** Phản hồi bấm 120 ms, mở/đóng panel khoảng 180 ms. Animation hữu hạn theo thao tác, ưu tiên opacity/transform. Khi bật reduced motion, giữ phản hồi trạng thái bằng chữ/viền. Không trì hoãn thao tác để chờ mascot hoặc font. Kiểm tra ngân sách ảnh và font với baseline tải lạnh.
- **Kiến trúc.** Một bảng primitive → semantic → component. Chia sẻ ý nghĩa và giá trị qua adapter theme MUI và Expo Web, giữ component theo nền tảng. Chỉ cân nhắc trích gói token sau khi bốn mẫu chứng minh có giá trị dùng chung. Mã dùng chung Expo thay đổi thì chạy hồi quy native tương ứng.

Kiểm tra tĩnh bảng màu: mực/giấy 14,21:1, mực/vàng 8,98:1, trắng/xanh 6,70:1, trắng/xanh Teacher 5,48:1 và trắng/tím Admin 7,90:1. Đây là tỷ lệ của cặp màu đặc, cần đo lại trên UI có trạng thái và hiệu ứng. [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

## Prototype đại diện chạy trong trình duyệt

**Dấu hiệu nhận biết qua bố cục.** Portal dùng một nút Đăng nhập chung với bài toán minh họa ở trang chủ. Student giữ một trang bài ổn định với đề, vùng làm và vùng phản hồi. Khi đang làm, đề và nút xác nhận giữ vị trí. Khi trả lời sai, vùng phản hồi hiển thị kết quả và thao tác thật đang được phép, ngôi sao chỉ khích lệ. Teacher đặt ảnh và quyết định ở hai vùng trên desktop, xếp dọc trên mobile theo thứ tự ảnh, bằng chứng, điểm, hành động. Admin dùng các hàng theo nhịp sổ, đặt thanh lọc và nút thao tác ở vị trí ổn định.

| Mẫu | Luồng và trạng thái cần thao tác |
| --- | --- |
| Portal | Trang chủ → Đăng nhập → ứng dụng theo vai trò tài khoản. Kiểm tra khả năng nhìn thấy nút ở màn hẹp, thao tác Tab, lỗi đăng nhập và chuyển đúng đích. |
| Student Web | Mở `/study/` từ Portal → trang học → quiz hiện có → phản hồi. Kiểm tra tải, trả lời, sai, quay lại, không có bài và reduced motion. Thêm một checkpoint ảnh từ route preview/crop hiện có với ảnh tổng hợp để kiểm tra khung bài đặt tính và công cụ. |
| Teacher Web | Hàng đợi → mở bài → xem ảnh, zoom và trạng thái → chốt điểm thử trên môi trường cách ly → mở bài tiếp hoặc quay lại. Kiểm tra đề xuất/điểm chính thức, lỗi và focus. |
| Admin Web | Danh sách tài khoản → lọc → mở chi tiết → hộp thoại xác nhận hiện có. Kiểm tra bảng nhiều cột, hủy, thành công, lỗi và quyền trên fixture cách ly. |

Phương án dựng: tạo biến thể presentation cục bộ trên route và component thật, cô lập bằng cấu hình preview hoặc working tree được bảo vệ. Thử 390 × 844 và 1280 × 900, zoom 200%, Tab/Escape và reduced motion. Mỗi mẫu có route, nguồn dữ liệu, ảnh chụp và bằng chứng tương tác. Dữ liệu kiểm thử được ghi nhãn, giữ nguyên API, phân quyền và trạng thái nghiệp vụ. Đo thời gian tải lạnh và kiểm tra mạng trên cùng cấu hình với baseline.

Điểm vào triển khai là `LandingPage.tsx` và Portal Login, Expo `HomeDashboard.tsx` và route `quiz/[quizId]`, `ReviewQueuePage.tsx` và `SubmissionReviewPage.tsx`, `UsersPage.tsx` và `UserDetailPage.tsx`. Chụp baseline từ working tree hiện tại, ghi rõ các sửa đổi chưa commit và giữ bản sửa SSO. Dùng bộ Playwright web và Student riêng, bổ sung ca chỉ cho interaction mà bản mẫu thực sự thay đổi.

Ghi HEAD, danh sách tệp thay đổi và fingerprint các tệp đang sửa trước khi tạo preview. So sánh lại cuối lượt. Nếu cô lập bằng bản sao, giữ cả bản sửa SSO và tài liệu chưa track trong baseline so sánh. Không stash hay reset working tree. Trước khi chỉnh code, đọc Expo v57 theo AGENTS.md và đối chiếu API với phiên bản Expo đã pin của Student.

Playwright dùng fixture cách ly, từ chối network ngoài hợp đồng. Teacher chốt điểm và Admin khóa/mở khóa chỉ trong fixture, gồm cả thành công và lỗi. Student dùng `/study/quiz` → `/study/quiz/{quizId}` với fixture chọn, tải, trả lời và phản hồi. Các fixture phải kiểm tra payload thật của UI. Ghi rõ ca nào đã tái dùng và ca nào cần bổ sung trước khi tuyên bố kiểm chứng.

Kế thừa toàn bộ cổng nghiệm thu trong đặc tả gốc, gồm reflow 320 CSS px, vùng bấm chính Student 44 px và WCAG 2.2 AA. Kiểm tra trình đọc màn hình thông báo phản hồi bài học, tên các nút ảnh, dialog và vùng focus. Kiểm tra quay về Teacher/Admin giữ ngữ cảnh lọc và hàng theo hành vi hiện có. Nếu baseline thiếu hành vi đó, ghi riêng đề xuất trước khi sửa.

So sánh ba lượt tải lạnh trên cùng cấu hình mạng và viewport, dùng trung vị LCP/CLS và số byte font/illustration nạp. Ngưỡng thử nghiệm: LCP tăng tối đa 10%, CLS không tăng quá 0,02 và không vượt 0,1, tổng font/illustration tăng tối đa 100 KiB ở lượt đầu. Nếu vượt, tối ưu hoặc xin duyệt ngoại lệ có số đo.

## Mốc triển khai và nghiệm thu

1. Đã phản biện đặc tả với EGM Design Critic và Structural từ ngữ cảnh độc lập. Đã cập nhật bố cục đặc trưng từng vai trò, checkpoint ảnh của Student, cách ly thao tác ghi, bảo vệ working tree, accessibility và ngưỡng hiệu năng.
2. Dùng bốn prototype và các phát hiện từ EGM làm điểm xuất phát cho triển khai đã duyệt.
3. Mở rộng sang toàn bộ route trong đặc tả gốc. Đối chiếu bằng chứng theo route, vai trò, trạng thái và viewport trước khi nghiệm thu toàn bộ.

## Tiến độ bản chạy

Bốn điểm vào đã có presentation thử nghiệm chỉ bật bằng `VITE_NOTEBOOK_PREVIEW=true` hoặc `EXPO_PUBLIC_NOTEBOOK_PREVIEW=true` trên web. Portal preview cục bộ mở tại `http://127.0.0.1:15272/`. Chrome DevTools xác nhận mục lục có ba đích đúng route, ở 390 px mỗi liên kết cao 65 px và không tràn ngang. Teacher thử bố cục 7/5 cho ảnh và quyết định, Admin thử bảng theo nhịp sổ, Student thử trang quiz với vùng đề riêng.

Lượt Chromium đầu với API fixture đạt 8/8 ca cho lỗi đăng nhập, Teacher xác nhận chốt điểm khi đọc lại lỗi, bộ lọc Admin và Portal bàn giao Student. Lượt mở rộng đạt 6/6 ca Desktop Chrome và Pixel 7 cho quiz bắt đầu, sai, đúng, Teacher chốt điểm khi đọc lại lỗi, và Admin hủy, lỗi, thử lại thành công khi khóa tài khoản tổng hợp. Fixture quiz từ chối narration có chủ đích vì ca này kiểm tra phản hồi bằng chữ. Bốn tệp sửa SSO ban đầu khớp fingerprint kiểm tra trước và sau lượt thêm prototype.

### EGM Review Loop trên ảnh chụp và kết quả chạy

Design Critic kiểm tra sáu ảnh chụp. Structural kiểm tra báo cáo Playwright, dữ liệu mô phỏng, viewport và các điểm còn thiếu. Các phát hiện đã được xử lý trong bản preview gồm dời phản hồi Student xuống dưới nút để giữ vị trí nút, thay ảnh linh vật của fixture Teacher bằng ảnh bài tính tổng hợp, chỉ hiện lỗi một lần trong hộp thoại Admin và dùng nền đặc. Bảng Admin có vùng cuộn được gắn nhãn và nhận focus bằng bàn phím.

Lượt chạy lại đạt 8/8 tại 1280 × 900 và 390 × 844 với API mô phỏng, gồm Portal đăng nhập lại sau lỗi, Student kiểm tra vị trí nút trước và sau phản hồi sai, Teacher chốt thử với ảnh worksheet, và Admin từ danh sách đến chi tiết, hủy và khôi phục focus rồi thử lại sau lỗi. [Báo cáo Chromium](../../../.local-artifacts/notebook-v2-viewport-report/index.html)

Lượt bổ sung đạt 6/6 ở hai viewport. Student dùng file worksheet tổng hợp qua file chooser thật, xác nhận riêng tư, mở crop, xoay, đặt lại và xem trước. Chỉ POST đăng nhập được ghi, ảnh chưa gửi lên API. Teacher mở từ hàng đợi, quay lại bằng Back và liên kết, giữ tìm/lọc/sắp xếp trong phiên, và mở bài kế tiếp sau khi chốt. [Báo cáo kiểm tra luồng](../../../.local-artifacts/notebook-v2-route-report/index.html)

Chrome DevTools ở 320 px với reduced motion phát hiện cạnh phải nút đăng nhập ở x=341 và biểu trưng còn chạy animation. Sau sửa trong preview, cạnh phải ở x=304, viewport và scrollWidth đều 320, hai biểu trưng đầu trang đều có animationName `none`. Tab từ mục Học sinh chuyển đúng sang Giáo viên với outline nhìn thấy. Đây là kiểm chứng Portal, các web còn lại cần kiểm tra riêng.

Kiểm tra 320 px và zoom 200% đã có cho các màn đại diện bên dưới. Các route còn lại cần kiểm tra theo phạm vi của từng luồng. Hai mốc chưa đủ bằng chứng là trình đọc màn hình và Student native trên thiết bị thật.

Lượt kiểm tra bản triển khai đạt 100/100 ca Chromium cho Portal, Teacher và Admin, và 12/12 ca riêng cho bản export Student Web. Hai bộ dùng API fixture. Bằng chứng gồm đăng nhập và bàn giao phiên, tạo bài bằng bàn phím, chọn ảnh và giữ ảnh nháp, duyệt bài, xem danh sách lớp và nhật ký Admin, học và làm quiz Student. [Log Portal, Teacher và Admin](../../../.local-artifacts/remake/browser-remake-confirmed.log) · [Log Student](../../../.local-artifacts/remake/student-remake-latest.log)

Lượt Student tiếp theo đạt 12/12 ca Chromium. Ca Của em và Thành tích xác nhận số liệu từ lịch sử tổng hợp được lưu cục bộ, bộ lọc ghi chú, reflow 320 px và đăng xuất. Typecheck và 12/12 ca Jest điều hướng đạt. Portal dùng bản WebP 512 px của linh vật hiện có. Chromium ghi nhận 41.360 byte cho ảnh và 396.852 byte cho ba font Nunito nội bộ. Phép đo này ghi kích thước tài sản tải, còn LCP và CLS cần đo riêng. [Log Chromium Student](../../../.local-artifacts/remake/student-profile-achievements.log)

Quiz đạt 2/2 ca Chromium desktop và mobile khi bật reduced motion. Ca kiểm tra phản hồi sai qua vùng `aria-live`, vị trí nút gửi giữ nguyên và phần thưởng 3 sao xuất hiện ở opacity 1. Kiểm tra DOM này xác nhận thuộc tính vùng thông báo. Việc nghe thông báo bằng trình đọc màn hình cần kiểm tra riêng. [Log quiz](../../../.local-artifacts/remake/student-quiz-motion.log)

### Đo tải lạnh

Dựng production từ commit `7ff77e6` và worktree hiện tại. Các báo cáo prototype trước đó có ảnh và kiểm thử chức năng. Mốc đối chiếu hiệu năng dùng commit đã lưu vì chưa có bản build prototype tương ứng. Chromium chạy ba lượt tải lạnh cho mỗi phiên bản ở 1280 × 900 và 390 × 844, tắt cache, giới hạn mạng ở 10 Mbps tải xuống, 5 Mbps tải lên và độ trễ 40 ms. Server tĩnh dùng loopback và chặn mạng ngoài.

| Portal | LCP trung vị trước → sau | CLS trung vị trước → sau | Font và ảnh trước → sau |
| --- | ---: | ---: | ---: |
| 1280 px | 1.012 → 904 ms | 0,1832 → 0,0022 | 1.669.451 → 438.212 byte |
| 390 px | 960 → 888 ms | 0,0139 → 0,0045 | 1.669.451 → 438.212 byte |

Portal đạt các ngưỡng LCP, CLS và dung lượng theo phép so với commit đối chiếu. [Số đo từng lượt](../../../.local-artifacts/remake/cold-load/portal-metrics.log)

Student Web dùng phiên và hồ sơ tổng hợp qua API fixture. Bản đầu vượt ngân sách ảnh/font ở desktop, tăng 1.203.617 byte. Sau khi bỏ chờ ảnh trước khi mở giao diện web và dùng WebP theo kích thước hiển thị, cả hai viewport đạt ngưỡng so với commit đối chiếu.

| Student Web | LCP trung vị trước → sau | CLS trung vị trước → sau | Font và ảnh trước → sau |
| --- | ---: | ---: | ---: |
| 1280 px | 10.000 → 5.624 ms | 0,0069 → 0,0063 | 9.390.031 → 3.557.479 byte |
| 390 px | 12.352 → 4.764 ms | 0,0100 → 0,0111 | 9.959.254 → 3.615.949 byte |

Sau tối ưu, Student đạt 12/12 ca Chromium, 15/15 ca Jest về khởi động và điều hướng, cùng typecheck. [Số đo từng lượt](../../../.local-artifacts/remake/cold-load/student-optimized-metrics.log) · [Log Chromium](../../../.local-artifacts/remake/cold-load/student-optimized-browser.log) · [Log Jest](../../../.local-artifacts/remake/cold-load/student-startup-jest-final.log)

### Zoom 200% và reflow

Chromium dùng profile tạm và zoom tab 200% qua `chrome.tabs.setZoom`. Hai lượt kiểm tra giảm chiều rộng nội dung từ 1280 xuống 640 CSS px và từ 640 xuống 320 CSS px. Cả hai lượt đạt 4/4 ca trên bản production với API fixture. Portal mở đăng nhập bằng bàn phím và hiển thị lỗi. Student đổi lớp và mở gợi ý. Teacher mở ảnh toàn màn hình, Admin mở hộp thoại khóa tài khoản, và cả hai trả focus về nút mở khi nhấn Escape. Các màn được chụp không tràn ngang cấp trang.

[Ảnh và kết quả ở 640 CSS px](../../../.local-artifacts/remake/zoom/report/index.html) · [Ảnh và kết quả ở 320 CSS px](../../../.local-artifacts/remake/zoom/reflow-report/index.html)

### Che thông tin bằng bàn phím trên Student Web

Student Web có thể thêm và chỉnh vùng che bằng các trường số có nhãn. Khi vùng che thay đổi, hộp kiểm yêu cầu xác nhận lại. Hai ca Chromium desktop/mobile xác nhận trạng thái hộp kiểm, cây trợ năng của các trường, pixel vùng che trong ảnh chuyển sang bước cắt, và việc ảnh chưa được gửi qua API. Bản web dùng canvas trên ảnh nguồn để xuất JPEG sau khi che. Typecheck và bộ kiểm thử hợp đồng đạt. Việc nghe thông báo bằng trình đọc màn hình và kiểm tra trên thiết bị native thật còn mở. [Log Chromium](../../../.local-artifacts/remake/student-keyboard-mask-final.log) · [Báo cáo và cây trợ năng](../../../.local-artifacts/student-browser/report/index.html)

### Cắt và căn thẳng ảnh bằng bàn phím trên Student Web

Thanh trượt căn thẳng hỗ trợ phím mũi tên. Học sinh có thể chọn cạnh và thu hẹp hoặc mở rộng khung cắt từng bước. Ở viewport 320 × 300 CSS px, ảnh vẫn có vùng hiển thị và phần điều khiển cuộn được. Chromium xác nhận thay đổi góc bằng bàn phím, kích thước JPEG sau khi thu hẹp, và không gửi ảnh trong luồng xem trước. Bộ Student Chromium đạt 12/12 ca trên hai cấu hình. Typecheck và 15/15 ca hợp đồng đạt. Bản xem thử cục bộ đã phục vụ mã mới. [Báo cáo Chromium](../../../.local-artifacts/student-browser/report/index.html)

**Skills Applied** · `impeccable:impeccable` cho trải nghiệm chỉnh ảnh, `vercel-react-best-practices` (`.agents/skills/react-best-practices/SKILL.md`) và `fixing-accessibility` (`.agents/skills/fixing-accessibility/SKILL.md`) cho điều khiển web, `mathvision-quality` (`.agents/skills/mathvision-quality/SKILL.md`) cho kiểm tra ảnh xuất và hồi quy.

### Chi tiết đợt chấm trên Teacher Web

Tiến độ hiển thị số ảnh đã xử lý trên tổng số ảnh và đọc được qua thuộc tính của thanh tiến độ. Hành động tiếp tục tải ảnh hoặc vào hàng đợi nằm cạnh trạng thái đợt. Tên học sinh đi cùng tên truy cập của liên kết mở bài. Màu chữ trên các nhãn thành công, cảnh báo và lỗi đã chỉnh đạt từ 5,2:1 đến 6,8:1 trên nền nhãn tương ứng.

Chromium production preview với dữ liệu kiểm thử đạt 26/26 ca desktop/mobile cho lịch sử đợt chấm, tạo đợt và hàng đợi duyệt. Ca chi tiết đợt xác nhận mở bộ lọc lỗi bằng bàn phím, bỏ lọc và trở lại đúng bộ lọc danh sách. Build Teacher và 46/46 ca cấu hình, hợp đồng và hồi quy đạt trên worktree từ `7ff77e6`. Chrome DevTools MCP và Playwright MCP xác nhận bản local bảo vệ deep link bằng chuyển hướng đăng nhập. [Báo cáo Chromium](../../../.local-artifacts/browser/report/index.html)

**Skills Applied** · `impeccable:impeccable` cho bố cục chi tiết đợt, `vercel-react-best-practices` (`.agents/skills/react-best-practices/SKILL.md`) cho trình bày từ dữ liệu truy vấn hiện có, `fixing-accessibility` (`.agents/skills/fixing-accessibility/SKILL.md`) cho tương phản và ngữ nghĩa, `mathvision-quality` (`.agents/skills/mathvision-quality/SKILL.md`) cho xác minh bằng trình duyệt.

### Kết quả kiểm tra bài qua ảnh trên Student Web

Bố cục web đưa kết quả và bước tiếp theo lên trước, dùng tiêu đề có cấp và vùng thông báo lịch sự. Chromium chạy từ bước chọn ảnh qua cắt, gửi multipart JPEG đến API fixture và điều hướng theo phản hồi cho ba kết quả gồm ảnh mờ, ngoài phạm vi và bài làm đúng. Mỗi kết quả có nút chính cao ít nhất 44 CSS px, nhìn thấy trong viewport và mở được bằng Enter. Lượt Student đạt 18/18 ca Chromium desktop/mobile, 17/17 ca Jest định tuyến kết quả và 15/15 ca hợp đồng, cùng typecheck. Portal local phục vụ bản Student export đã cập nhật. Độ chính xác OCR, âm thanh của trình đọc màn hình và các nhánh nhận dạng khác cần kiểm chứng riêng. [Báo cáo Chromium](../../../.local-artifacts/student-browser/report/index.html)

**Skills Applied** · `impeccable:impeccable` cho thứ tự kết quả và hành động, `vercel-react-best-practices` (`.agents/skills/react-best-practices/SKILL.md`) cho phần trình bày theo nền tảng, `fixing-accessibility` (`.agents/skills/fixing-accessibility/SKILL.md`) cho ngữ nghĩa và nút, `mathvision-quality` (`.agents/skills/mathvision-quality/SKILL.md`) cho luồng gửi ảnh và kiểm tra hồi quy.

### Đăng nhập chung và lịch sử trình duyệt

Portal bỏ panel ô ly ở trang đăng nhập. Teacher và Admin chuyển các URL đăng nhập cũ về Portal và đổi vé dùng một lần qua màn tiếp nối có trạng thái tải ngay từ HTML. Student vào thẳng `/study/` và xác minh phiên song song với tải font. Khi trình duyệt khôi phục trang đã bảo vệ từ lịch sử, phiên được kiểm tra lại.

Core launcher báo `READY_FOR_CORE_DEMO`. Playwright MCP đăng nhập ba tài khoản phát triển với Spring local, sau đó đăng xuất và Back về trang chủ ở 440 CSS px. Form Portal không tràn ngang ở 320, 440, 768 và 1280 CSS px. Với cache tắt, tải xuống 10 Mbps và độ trễ 40 ms, một lượt cho mỗi vai trò đến tiêu đề trang đích mất Student 4.971 ms, Teacher 1.861 ms và Admin 2.066 ms. Đây là số đo Chromium giả lập. Các bộ kiểm tra trình duyệt có fixture đạt 14/14 ca luồng Portal/Teacher/Admin và 6/6 ca Student. Typecheck Student, 15 ca hợp đồng Student, 46 ca Teacher và 2 ca SSO Admin đạt.

**Skills Applied** · `impeccable:impeccable`, `vercel-react-best-practices`, `fixing-accessibility`, `mathvision-review`, `mathvision-quality`.
