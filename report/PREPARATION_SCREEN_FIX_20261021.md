# Tách màn hình chuẩn bị bài học — 21/10/2026

## Thay đổi

Sau khi học sinh bấm bắt đầu, trạng thái “Chuẩn bị các bước học” chiếm riêng màn hình và được căn giữa trong vùng an toàn. Phần đề, ảnh, công cụ và các thao tác khác không còn nằm cùng màn hình chờ. Bàn phím đóng khi bắt đầu chuẩn bị.

Dùng lại `RecognitionProgress` và luồng yêu cầu hiện có, không thêm route hoặc thư viện. Nhận được bài học thì chuyển sang nội dung học. “Dừng chờ” hủy yêu cầu, trở về đề đã xác nhận và giữ ảnh. Phản hồi đến muộn sau khi hủy bị bỏ qua; học sinh có thể thử lại. Nếu yêu cầu thất bại, màn hình chờ kết thúc và hiển thị lỗi cùng thao tác thử lại tại đề bài.

## Kiểm chứng

- Jest Student: **839/839**, 60 suites, gồm 48 kiểm thử trang hướng dẫn.
- TypeScript và ESLint trang hướng dẫn: đạt.
- Xuất web: đạt.
- Bundle phát triển Android do máy chủ Expo đang chạy trả về: HTTP 200, có màn hình chuẩn bị mới. QR hiện tại tiếp tục dùng được.
- Trình duyệt với API trì hoãn có kiểm soát: đạt tại 320×740, 390×844, 820×1180, 1440×1000 và 844×390; kiểm tra màn hình chờ riêng, hủy, phản hồi muộn, thử lại, chuyển bài học và lỗi 503.
- Trên các màn hình dọc đã kiểm tra, nút dừng nằm trong khung nhìn ngay khi bắt đầu. Màn hình thấp vẫn có vùng cuộn bên trong thành phần tiến trình để giữ nội dung sử dụng được.
- Đã xem ảnh chụp màn hình trình duyệt ở kích thước điện thoại và laptop. Đây không phải bằng chứng thử trên điện thoại vật lý.

Bằng chứng: `scratch/preparation-qa/results.json` và các ảnh `scratch/preparation-qa/preparing-*.png`. API bài học trong kiểm thử trình duyệt được điều khiển để quan sát trạng thái chờ và các tình huống hủy/lỗi; không gọi model cho bộ kiểm tra này.

Không sửa backend/chấm bài, không huấn luyện, không commit/push. Các thay đổi trước đợt này được giữ nguyên.

## Triển khai

Đã xuất bản portal/Student web lên https://mathvisionkid-portal.vercel.app/study/. Deployment `dpl_DyZSbMFeWbeK18yq9UvJfkhUvN2o` đã sẵn sàng và được gắn vào tên miền production. Kiểm tra tải trang và bundle mới qua tên miền thật, cùng khả năng truy cập API được bảo vệ, được ghi tại `scratch/preparation-qa/public-deployment-check.json`. Chỉ cập nhật giao diện; backend vẫn dùng phiên đang chạy hiện tại.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: sửa luồng và bố cục trạng thái chờ trên điện thoại, tablet, laptop.
  - Applied to: màn hình tập trung, trạng thái bận rõ ràng, nút hủy và bố cục thích ứng.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: thay đổi điều kiện render trong trang React Native/web.
  - Applied to: dùng trực tiếp trạng thái yêu cầu hiện có; giữ kiểm soát hủy, phản hồi muộn và số lần gọi API.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đúng vị trí render gây lỗi với thay đổi nhỏ.
  - Applied to: tái sử dụng thành phần tiến trình, không thêm lớp điều hướng hoặc phụ thuộc mới.
