# Đồng bộ Git theo xác nhận chủ dự án — 2026-10-04

## Phạm vi được cho phép

Chủ dự án xác nhận: “thế là ổn rồi, cứ up git cho tôi đi, lỗi kia k đáng kể”.
Xác nhận này thay thế điều kiện giữ lại bản sửa trong báo cáo kiểm tra trước.
Đồng bộ mã nguồn và các báo cáo hiện có lên `origin/main` tại repository
`NV-DuyManh/MathVisionKid`.

Bao gồm sửa cắt/xoay ảnh, quay lại màn hình ảnh, thu gọn đề, phân vùng dòng,
điều kiện hướng dẫn đúng mục tiêu, detector có checksum/giấy phép và công cụ
kiểm tra dữ liệu. Các lỗi nhận nhầm nền và thiếu dấu hai chấm vẫn được ghi
trong `report/ANNOTATION_LINE_REFINEMENT_20261004.md`; không sửa nhãn hoặc
tuyên bố đã hết mọi lỗi để xuất bản.

## Kiểm tra trước commit

- Fetch thành công; `main` và `origin/main` cùng `91bcba5`, ahead/behind 0/0.
- 80 tệp thay đổi được rà soát trước cập nhật báo cáo xuất bản: không thấy
  khóa thật mới, ảnh riêng, dataset, ledger hoặc trọng số model. Hai chuỗi
  giống khóa trong kiểm thử là dữ liệu giả đã có.
- JUnit cuối: **995 kiểm thử AI, 0 lỗi/0 thất bại**. Không có mã nguồn hoặc
  kiểm thử thay đổi sau kết quả đó; lượt xuất bản chỉ cập nhật báo cáo.
- `git diff --check` đạt. Dữ liệu kiểm tra mới, log, môi trường và model weights
  được ignore, giữ tại máy. Không dùng ép đẩy hoặc thay lịch sử remote.
- Các kiểm tra mobile/backend/web trước đó được ghi trong báo cáo kiểm tra;
  không chạy lại các bộ không bị thay đổi chỉ để xuất bản.

Chỉ commit các thay đổi mã/tài liệu Git nhìn thấy. Các kết quả riêng từ bộ
3.279 ảnh, credential, runtime local và weights không thuộc bản đồng bộ.
Mã cài detector và manifest vẫn được đưa lên để chuẩn bị môi trường khác.
Commit và đối chiếu remote sau đẩy được báo trực tiếp cho chủ dự án.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: xuất bản phạm vi đã kiểm chứng bằng quy trình Git sẵn có.
  - Applied to: rà soát file, giữ ignore dữ liệu riêng, tái sử dụng bằng chứng
    kiểm thử hiện tại và đồng bộ không thêm thay đổi mã không được yêu cầu.
