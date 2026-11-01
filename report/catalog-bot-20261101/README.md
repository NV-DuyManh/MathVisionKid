# Catalog Bot — 01/11/2026

Bot đã tồn tại trên GitHub dưới tên `Lesson catalog guard`. Trước khi xuất bản bản nâng cấp, API GitHub công khai xác nhận workflow đang active; lượt gần nhất khi kiểm tra là [run 41210073128](https://github.com/NV-DuyManh/MathVisionKid/actions/runs/41210073128), kết quả success, commit `b738ef1cc8affb1e1b642b9f2010e41b0f1f7f05`. Đây là **bản cũ**. Trạng thái của bản mới cần đối chiếu [GitHub Actions](https://github.com/NV-DuyManh/MathVisionKid/actions/workflows/lesson-catalog.yml) theo SHA commit, không suy ra từ các lượt kiểm thử tại máy.

## Phần bổ sung

- Tên dễ tìm `MathVision Catalog Bot`, badge trên README và liên kết vào Actions.
- Báo cáo tiếng Việt ở Summary và artifact `mathvision-catalog-bot`: HTML, Markdown, JSON; giữ 14 ngày.
- `RUN_CATALOG_BOT.bat` tạo bảng kiểm kê trên máy. `--no-open` chạy kiểm tra mà không mở cửa sổ trình duyệt.
- Báo cáo ghi thời điểm và phạm vi dữ liệu; kho không có/không đọc được báo chưa có số liệu. Kho hỏng hoặc kiểm thử CI thất bại không được báo đạt.
- Giữ nguyên collector hiện có trong ứng dụng. Không thêm model call, không ảnh hưởng hàng đợi giọng và không đọc kho này mỗi lần Student mở màn hình.
- GitHub chỉ kiểm tra dữ liệu công khai. Đối số đọc kho riêng bị chặn trong GitHub Actions; artifact chỉ chứa trường tổng hợp cho phép. Không tự đẩy đề, ảnh, âm thanh hoặc mã tài khoản lên GitHub.

## Số liệu thực tế

Lần kiểm kê chỉ đọc ngày 01/11/2026 tại máy này: **16 kế hoạch**, **210 tệp âm thanh**, **49 lượt dùng lại** trên các bản ghi còn giữ. Hết hạn: 0; sai checksum: 0. Các số này không phải số liệu toàn bộ triển khai hay tổng lịch sử trọn đời. Kiểm tra checksum không chứng minh mọi lời giải đúng.

Bảng hiện tại: `.local-artifacts/catalog-bot/index.html`; bản tóm tắt: `.local-artifacts/catalog-bot/summary.md`. Cả hai được tạo từ số liệu thật, không phải mô hình UI có số giả. Browser automation từ chối mở URL file theo chính sách; chỉ mở Markdown bằng panel tài liệu, **chưa kiểm tra hình ảnh HTML trong trình duyệt**.

## Kiểm thử

| Kiểm tra | Kết quả |
| :--- | :--- |
| `python -S ai/runtime/scripts/test_catalog_store.py -v` | 5/5 qua, chỉ standard library |
| `python -S ai/runtime/scripts/test_catalog_bot.py -v` | 8/8 qua, chỉ standard library |
| `python -m pytest tests/test_lesson_catalog.py tests/test_catalog_solver_integration.py -q` từ `ai/runtime/` | 14/14 qua; kho tạm và mock provider |
| Chạy mô phỏng `GITHUB_ACTIONS=true` và báo cáo public | Qua; không truy cập kho riêng |
| `RUN_CATALOG_BOT.bat --no-open` | Exit 0, báo cáo thực tế được tạo |
| Workflow YAML, trigger, token chỉ đọc, SHA action, không có `--database` | Qua kiểm tra cấu trúc bằng parser; chưa phải lượt chạy GitHub mới |
| `git diff --check` trên các file đã sửa trong tác vụ | Qua |

Tổng **27 kiểm thử riêng biệt** qua, không cộng các lượt chạy lặp thành số test mới. Lệnh pytest đầu tiên từ thư mục repo thiếu import path và không thu thập được test; chạy lại từ `ai/runtime/` theo cấu trúc dự án đã qua 14 test.

Chủ dự án đã đồng ý xuất bản riêng phần bot lên `main`. Những sửa UI/Quiz có sẵn trước tác vụ được giữ lại trên máy, không đưa vào commit bot. Các file riêng, kho SQLite, `.local-artifacts/` và `demoUI/` vẫn bị Git bỏ qua. Sau khi push phải kiểm tra lượt chạy mới theo SHA để xác nhận trạng thái và artifact; kiểm thử local không thay thế bằng chứng đó.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: bot và kiểm kê cần ít phụ thuộc, dễ chạy lại.
  - Applied to: tái sử dụng collector/CatalogStore hiện có, runner standard library, kiểm thử quyền riêng tư và lỗi; không thêm dịch vụ hay model.
- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: cần bảng catalog dễ tìm, dễ đọc và biết dữ liệu thuộc thời điểm nào.
  - Applied to: HTML responsive, các số liệu có nhãn và timestamp, trạng thái đạt/lỗi có chữ, focus rõ, font hệ thống và không tải tài nguyên ngoài.
