# Loc/Web PR #12 review

Date: 2026-11-02
Repository: `MathVisionKid`
PR: [#12](https://github.com/NV-DuyManh/MathVisionKid/pull/12)
Merge commit: `1f5543b`

## Kết quả

PR #12 đã được merge vào `main` trước lượt review này. Review phát hiện hai vấn đề ngữ nghĩa dù Git không báo xung đột:

1. `StudentLandingPage.tsx` đã bị thay bằng một trang học Toán demo với dữ liệu và tương tác giả. Trang đó không dùng luồng học thật và làm mất cổng chuyển học sinh đã xác thực sang `/study/`. Đã khôi phục cổng xác thực/chuyển trang từ commit cha `a60f5fc`; tệp hiện tại khớp với phiên bản đó.
2. Theme Admin và Teacher áp màu chung lên mọi nút `contained`/`outlined`, có thể ghi đè màu cảnh báo, lỗi và thành công. Đã giới hạn màu thương hiệu vào nút `primary`, giữ hiệu ứng chung và để các màu ngữ nghĩa theo palette của MUI.

Ghi nhận Lộc/Four-L và PR #12 trong `CONTRIBUTORS.md`; lịch sử Git của commit nguồn và merge vẫn nguyên vẹn. Không phát hiện xung đột văn bản cần xử lý thêm.

## Kiểm chứng

- Portal config: 21/21 qua.
- Teacher config: 21/21 qua.
- Admin config: 34/34 qua.
- Portal production smoke: 2/2 qua sau khi build lại bundle từ source đã khôi phục.
- Teacher production smoke: 2/2 qua.
- Admin production smoke: 5/5 qua.
- Build Portal, Teacher và Admin đều thành công.
- `git diff --check` thành công.

Các bài production là smoke test cục bộ với fixture HTTP; đây không phải kiểm thử trên môi trường production đang chạy hay trên thiết bị thật. Ba lần build có cảnh báo bundle entry vượt 500 kB; đây là cảnh báo kích thước, không làm build thất bại và chưa được xử lý trong phạm vi review này.

## Phạm vi Git

Không tạo commit hoặc push. Workspace còn nhiều thay đổi chưa commit thuộc các phần mobile, AI, backend và báo cáo khác; các thay đổi đó được giữ nguyên và không thuộc phần review Loc/Web này.

## Skills Applied

- `ponytail-review`
  - SKILL.md: `.agents/skills/ponytail-review/SKILL.md`
  - Why selected: review nhánh tích hợp để nhận diện code demo/thừa và các vấn đề ngữ nghĩa.
  - Applied to: rà soát thay thế trang Student và các style theme dùng chung.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: chọn cách sửa nhỏ, không mở rộng phạm vi ngoài các lỗi đã xác nhận.
  - Applied to: khôi phục cổng Student và giới hạn style nút theo màu primary.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: phần sửa liên quan ứng dụng React/Vite và luồng điều hướng.
  - Applied to: kiểm tra luồng chuyển trang Student và build/smoke test ba web app.
