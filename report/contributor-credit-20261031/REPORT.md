# Ghi nhận tác giả và đối chiếu PR Kha — 31/10/2026

## Kết quả đối chiếu

Đã kiểm kê lịch sử tác giả của toàn bộ main, các remote branch đã fetch và **3.475 tệp** của cây main trước sửa `dd3b324ed1d59c8916db0489f014c55e80bf574f`. PR [#7](https://github.com/NV-DuyManh/MathVisionKid/pull/7) dùng head Kha `bf29939b4c47be180581f951c1e7483011227b17`; merge base là `20d6780f3a77b0ac2db96edc575e62481788ccad`.

Vấn đề là phần Kha đã được mang vào working tree, review và commit trong `d68cce8`, nhưng năm commit gốc của PR chưa là tổ tiên của main. Không phải thiếu toàn bộ tính năng Kha: trước lượt này main đã có bốn commit Kha về trò chơi; còn phần Quiz/Admin/auth và chuẩn bị bài có trong nội dung mã nhưng thiếu liên kết lịch sử của PR #7.

Kiểm kê **đủ 256 tệp PR**, so sánh Git blob theo từng đường dẫn:

| Trạng thái | Số tệp | Quyết định |
|---|---:|---|
| Trùng nguyên blob Kha/main | 176 | Giữ bản đang có; nối lại commit gốc để có bằng chứng tác giả. |
| Đã sửa hoặc phát triển tiếp trên main | 29 | Giữ bản main đã kiểm thử. Bao gồm guard bộ giải, phục hồi bài, UI Quiz/nhận xét, xác thực của Hiếu, bản vá dependency và launcher/volume. |
| Báo cáo/ảnh kiểm tra cũ đã bị dọn khỏi main | 51 | Tiếp tục không khôi phục vào cây hiện tại. Commit lịch sử vẫn giữ chúng như Git vốn hoạt động. |
| Mã chạy còn thiếu, chưa giải thích | **0** | Không có mã mới cần chép thêm. |

Danh sách đầy đủ cùng SHA blob ở [provenance-20261031.json](../../docs/contributions/provenance-20261031.json). So sánh blob chứng minh nội dung tệp trùng/khác, không tự chứng minh một người đã viết mọi dòng. Đối chiếu tác giả dùng metadata commit và nguồn đã review, không đoán từ tên nhánh hoặc tỷ lệ dòng giống nhau.

## Cách hợp nhất lịch sử

Dùng merge hai parent với chiến lược `ours` để **nối lịch sử Kha, giữ nguyên cây ứng dụng main đã kiểm thử**. Đây là bước hoàn tất lịch sử sau tích hợp chọn lọc trước đó, không phải lấy mã nhánh Kha nguyên trạng và bỏ các sửa lỗi trên main. Trước khi thêm tài liệu, `git write-tree` và `HEAD^{tree}` cùng hash:

```text
ff220def61c7617aef22f014d051ed7fdc18be05
```

Chỉ các tệp tài liệu/quy tắc/kiểm kê được thêm hoặc sửa trong lượt này. Không sửa code Student/AI/backend, không thay dữ liệu, migration, dependency hay runtime. Không force-push, amend, giả tên tác giả hoặc tạo vòng sửa/hoàn tác code để làm tăng bộ đếm đóng góp. Lịch sử cũ và các sửa lỗi đã push được bảo toàn.

Năm commit Kha được giữ nguyên SHA/author/committer:

- `6766fdc1505d793e86dbcb0ed2371d19b44c379f` — Admin/auth/ảnh Student.
- `31e6a2e172b04a7b0df69b05555dd5742b795a94` — merge các guard khởi động/quyền Student.
- `651f4bf53aac8f797ef532d0ef278d10e135e748` — merge guard truy cập phiên.
- `3121c1993b5f7f73cfc737b991c54ae41b473eb5` — Smart Quiz và tutor runtime.
- `bf29939b4c47be180581f951c1e7483011227b17` — merge main và tích hợp Quiz/phục hồi bài.

Cả năm mang author Git `deptraivodich`; tài khoản GitHub của commit nguồn được xác nhận là `deptraivodich`. Kha có chín commit tác giả trong đồ thị main sau nối lịch sử, **tính cả merge commits**. Đây không phải số đóng góp hiển thị trên biểu đồ GitHub; không hứa biểu đồ tăng đúng năm ô/điểm.

## Kiểm tra các tác giả khác

| Tác giả | Bằng chứng đang có trên main | Xử lý |
|---|---|---|
| Nam / `tranhoainam298` | Bốn commit OCR/mobile; trailer `Co-authored-by` trong `3b80e41` cho phần tích hợp hai giọng từ nguồn `705faab`. | Giữ nguyên; bổ sung mô tả rõ trong CONTRIBUTORS. Không cần giả thêm đồng tác giả vào commit tài liệu hiện tại. |
| Lộc / `Four-L` | Hai commit gốc từ Loc/Web, gồm `5907090`; đã nối qua `9c713cf`. | Giữ nguyên metadata. |
| Hiếu / `AnBaToBun22` | Ba commit từ nhánh Hieu, đã nối qua `dd3b324`. | Giữ nguyên metadata. |
| Chủ dự án / `NV-DuyManh` | Các commit nền, phát triển và tích hợp; hai địa chỉ author có sẵn của cùng chủ repository được liệt kê riêng trong kiểm kê. | Không gán lại code người khác cho chủ repository; không coi người merge là tác giả duy nhất. |

Nhánh Nam còn sáu commit chưa nằm nguyên trong main: nguồn TTS đã được tích hợp chọn lọc và có đồng tác giả; năm commit còn lại là phần nghiên cứu/lowdose khác. Không tự merge những thay đổi chưa review hoặc tuyên bố toàn nhánh Nam đã merge. Các remote khác trong lượt fetch đều đã là tổ tiên main, ngoài Kha trước bước nối lịch sử này. Các branch kiểm tra local/stash không được coi là một tác giả mới.

Đã thêm [CONTRIBUTORS.md](../../CONTRIBUTORS.md), liên kết từ README, và quy tắc ở CONTRIBUTING/AGENTS: giữ commit gốc khi merge; `cherry-pick -x` khi chọn commit; code thích nghi phải dẫn nguồn và ghi đồng tác giả đúng danh tính đã xác minh. Không sửa các giấy phép/notice bên thứ ba.

Giới hạn: không thể chứng minh người viết từng dòng trong các lần sao chép ngoài Git hoặc công việc chưa có provenance. `git blame` ở một số tệp vẫn có thể chỉ vào commit tích hợp `d68cce8`; giữ lịch sử công khai an toàn hơn việc viết lại main để đổi blame. Commit nguồn và bản kiểm kê cho phép truy nguyên phần Kha mà không tạo thông tin giả.

## Kiểm chứng

- Cây index sau merge lịch sử và main trước merge giống nhau toàn bộ, hash ghi ở trên.
- Kiểm tra 176 blob trùng, 29 blob thích nghi và 51 mục loại bỏ; không có mục chưa phân loại.
- Student: **3 bộ Quiz / 17 test đạt**, 21,11 giây.
- AI: **121 test đạt**, 8,99 giây, gồm bộ giải chữ số/phân số, phục hồi bước 3 và giọng Quiz; 2 cảnh báo deprecation đã biết.
- Backend: **51/51 test đạt**, chạy lại `QuizMathTest` và `QuizIntegrationTest`, build thành công trong 33 giây; kết quả tổng hợp lưu ở `verification.json` cạnh báo cáo.
- Kiểm tra Git trước push: giữ SHA/author gốc, không có file code ứng dụng thay đổi, không có conflict, không stage `demoUI`/khóa/model/local artifacts.

Đây là các kiểm tra tập trung của lượt sửa ghi nhận tác giả. Bộ kiểm thử toàn dự án của lượt trước xem [báo cáo release](../release-audit-hieu-20261031/REPORT.md); không báo đã chạy lại toàn bộ khi không cần cho một thay đổi lịch sử/tài liệu.

GitHub chỉ ghi nhận được commit theo tài khoản khi danh tính email liên kết phù hợp; biểu đồ/contributor statistics có thể cập nhật sau. Xem [hướng dẫn đồng tác giả chính thức](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors). Trạng thái cuối của PR #7 phải được kiểm tra lại trên GitHub sau push; không suy ra đã đóng chỉ từ merge local.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: khắc phục provenance bằng thao tác Git và tài liệu nhỏ, tránh thay hoặc viết lại mã đã ổn định.
  - Applied to: đối chiếu toàn bộ tệp PR, merge bảo toàn cây hiện tại, giữ tác giả và các kiểm tra tập trung.
