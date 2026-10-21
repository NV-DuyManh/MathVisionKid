# Trang chủ Student — thu gọn theo ảnh 1

Ngày 21/10/2026. Đã sửa mã trong working tree theo yêu cầu chủ sở hữu. Chưa commit/push/deploy.

## Xem kết quả

- [Ảnh mẫu, trước khi sửa và giao diện mới](student-home-compact-20261021/index.html). Có chọn Điện thoại / Tablet / Laptop và xem cả trang.
- [Ảnh mới ở khung điện thoại 390 px](student-home-compact-20261021/screenshots/after-390.png).
- Các ảnh app là ảnh chụp bản web export thật, dùng tài khoản và lịch sử kiểm thử cô lập. Không phải ảnh AI dựng giao diện, không phải bằng chứng thiết bị vật lý.

## Đã thay đổi

1. Đưa lại dòng giới thiệu dưới logo và giảm khoảng cách đầu trang.
2. Thu gọn khối chào, nút chụp từ cao 56 xuống 48 px; chừa vùng riêng cho lời giới thiệu để không bị linh vật chạm vào chữ.
3. Giữ các minh họa đã được chọn. Ba thẻ tiện ích chuyển về nền hồng, xanh lam, xanh lá dịu, thêm dấu chuyển tiếp nhỏ; tại màn hẹp, bỏ dấu trang trí để nhãn không bị ép xuống dòng.
4. Trên điện thoại: Chào em → Tiện ích nhanh → Chuỗi học tập → Bài học gợi ý. Máy tính chuyển thành hàng nhỏ phía dưới. Các bài gợi ý nằm cạnh nhau khi đủ rộng, xếp dọc trên màn hẹp hoặc khi cỡ chữ lớn.
5. Tablet có bốn tiện ích và chuỗi học tập trước phần hành trình. Laptop giữ khối chào và chuỗi học tập cạnh nhau, có hành trình và lựa chọn lớp.
6. Khi cỡ chữ thiết bị lớn, dành toàn bộ chiều ngang cho phần giới thiệu, ẩn hình trang trí trong khối chào để giữ nội dung dễ đọc.

Ở cùng khung 390 × 844 và cùng dữ liệu kiểm thử:

| Thành phần | Trước | Sau |
|---|---:|---:|
| Vị trí nút chụp, tính từ đầu viewport | 258 px | 214 px |
| Chiều cao nút chụp | 56 px | 48 px |
| Vị trí tiêu đề Tiện ích nhanh | 377 px | 306 px |
| Vị trí tiêu đề Chuỗi học tập | 1.019,5 px | 534 px |

Nguồn đo: [before-qa.json](student-home-compact-20261021/before-qa.json), [after-qa.json](student-home-compact-20261021/after-qa.json).

## Phạm vi mã

- `apps/student-mobile/src/components/home/HomeDashboard.tsx`: bố cục, tỷ lệ, thứ tự nội dung và nhãn truy cập nút riêng tư.
- `apps/student-mobile/src/components/ui/StudentPageHeader.tsx`: thu gọn kiểu header trang chủ. Kiểu compact đang dùng ở ba tab khác giữ nguyên.
- `apps/student-mobile/src/app/(tabs)/index.tsx`: padding và giới hạn bề rộng nội dung trang chủ.

Không đổi luồng chụp/nhận diện, kết quả chấm, dữ liệu thành tích, voice/video hay bộ icon điều hướng. Không thêm dependency hoặc tài sản ảnh mới. Nút trợ giúp tiếp tục mở mẹo chụp; không tạo nút thông báo khi chưa có chức năng tương ứng.

## Kiểm tra

- Toàn bộ Student: **869/869 tests, 67 suites đạt** — [jest-results.json](student-home-compact-20261021/jest-results.json).
- Sau chỉnh cuối về khoảng chữ, dấu trang trí và nhãn truy cập: **13 tests liên quan trang chủ/điều hướng đạt**; TypeScript và ESLint của ba file đạt.
- Web export: 32 route, kiểm tra cấu hình địa chỉ dịch vụ đạt.
- Android và iOS: xuất hai bundle Hermes thành công, 77 asset.
- Browser: **16 ảnh sau chỉnh**, gồm viewport và cả trang ở 320, 360, 390, 414, 768, 1024, 1440, 1920 px; 16 ảnh trước chỉnh ở cùng kích thước. Không tràn ngang, không ảnh hỏng, không nút nằm ngoài chiều ngang, không page error.
- Kiểm tra chuỗi học tập xuất hiện trước bài gợi ý và hiện ngay khi vào trên khung điện thoại từ 360 px; máy tính, đóng máy tính, trợ giúp, đóng trợ giúp hoạt động; nút riêng tư cuối trang vẫn cuộn tới được phía trên thanh điều hướng.
- SHA-256 của che tên, cắt ảnh, AppHeader, AppButton và theme giữ nguyên: [protected-after.json](student-home-compact-20261021/protected-after.json).

Đã đọc tài liệu [Expo v57.0.0](https://docs.expo.dev/versions/v57.0.0/) theo AGENTS.md trước khi viết mã. Chưa thử trên điện thoại/iPad vật lý; không tuyên bố khớp từng pixel với ảnh chụp máy có thanh trạng thái khác nhau.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: điều chỉnh trang chủ theo bố cục ảnh được chủ sở hữu chọn.
  - Applied to: mật độ, kích thước, tỷ lệ chữ/hình, thứ tự nội dung và responsive; tìm hướng dẫn React Native về touch targets.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: màn dùng React và React Native.
  - Applied to: giữ cơ chế tải lịch sử song song, guard vòng đời/tài khoản và các callback hiện có; không thêm tải dữ liệu mới.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: ưu tiên chỉnh bố cục với phạm vi nhỏ, không tạo thêm cơ chế hay thư viện.
  - Applied to: ba file giao diện, dùng lại toàn bộ minh họa và luồng thao tác hiện có.
