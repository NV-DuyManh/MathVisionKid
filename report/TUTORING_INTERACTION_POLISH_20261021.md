# Cải thiện gợi ý học toán và tương tác hình phân số

Ngày kiểm tra: 21/10/2026. Nhánh: `codex/meeting-actions-20261021`.

Yêu cầu: làm rõ gợi ý giải và thao tác học sinh với hình học, tiếp tục sửa trên phần hình phân số/tóm tắt đề đã có. Đợt này tập trung vào các lỗi tái hiện được; không khẳng định mọi bài toán hoặc thiết bị đều hoàn hảo.

## Thay đổi cho học sinh

### Gợi ý phù hợp với bước đang học

- Bước hiểu đề yêu cầu đọc dữ kiện và câu hỏi, chọn một ý; không bảo học sinh tự tính ở bước chỉ có lựa chọn.
- Câu kiểm tra nhỏ sau gợi ý phân biệt đọc hiểu, tử số, mẫu số và phép tính. Gợi ý phân số sâu hơn dùng câu về tử số thay vì lặp nguyên câu về mẫu số. Đây là kiểm tra khái niệm cục bộ; không thay phần chấm bài của máy chủ.
- Giữ gợi ý mới nhất khi học sinh trả lời sai; phản hồi sai hiện riêng để em đọc lại cả hai. Lựa chọn trong câu kiểm tra nhỏ cũng không tự đặt lại chỉ vì trả lời sai bài chính.
- Nút **Em đã hiểu, để em thử** đưa học sinh về ô trả lời hoặc lựa chọn đầu tiên của câu hỏi. Không điền đáp án, không tự chọn, không gửi câu trả lời.
- Giữ các gợi ý khác nhau, kể cả gợi ý thứ ba nếu có. Khi máy chủ chỉ trả lại cùng gợi ý đã mở, ngừng yêu cầu lặp và giữ nội dung để đọc lại. Hết gợi ý không khóa việc tự trả lời.
- Sửa thanh tiến độ: bước đầu chưa được tính là đã hoàn tất.

### Hình phân số giúp hiểu lỗi thao tác

- Hình tròn, hình vuông và thanh phân số dùng các phần bằng nhau. Chạm vùng hình hoặc nút số để chọn/bỏ chọn; đổi hình vẫn giữ lựa chọn.
- Khi kiểm tra, nêu số phần đã chọn, số phần cần có theo tử số và hành động cụ thể: ví dụ **Em chọn thêm 1 phần nhé** hoặc **Em bỏ chọn 1 phần nhé**. Không tự sửa lựa chọn.
- Giải thích vì sao thay số phần được chọn không thay mẫu số: mỗi hình nguyên vẫn chia theo cách ban đầu.
- Nút **Vì sao mỗi phần bằng nhau?** mở thêm lời giải thích về chia đều/diện tích bằng nhau; không bắt buộc đọc trước khi thao tác. Có lời phù hợp riêng cho tử số 0, mẫu số 1 và nhiều hình nguyên.
- Nút phần có kích thước tối thiểu 48, cho phép chữ lớn và nút tăng kích thước. Có dấu chọn, tiêu điểm, nhãn và thao tác Space/Enter trên web; không chỉ dựa vào màu.
- Giữ hướng dẫn tóm tắt **Đã biết / Cần tìm** theo tiến độ kiểm tra nguồn, cùng bài giải có câu lời giải và các phép biến đổi sau khi hoàn tất.

### Sửa nội dung gợi ý từ máy chủ

- Một số gợi ý chứa tham chiếu bước trước như `{s0}`, `{s0_numerator}`, `{s0_denominator}` chưa được thay bằng giá trị đã kiểm tra. Dùng chung bộ thay tham chiếu an toàn cho lời hướng dẫn, gợi ý gửi học sinh và dữ liệu gửi bộ duyệt.
- Chỉ cho tham chiếu phép tính trước đó; từ chối tham chiếu bước hiện tại, tương lai hoặc lựa chọn đọc hiểu. Giữ giới hạn độ dài và các bảo vệ không lộ đáp án chưa học.
- Giữ đúng tham chiếu khi thêm ba bước hiểu đề ở đầu bài học.
- Sửa câu hướng dẫn kiểm tra Đúng/Sai: đối chiếu vai trò câu trích với đề, không yêu cầu tìm số/đơn vị trong chính chữ Đúng/Sai.

## Bằng chứng kiểm tra

| Kiểm tra bản cuối | Kết quả |
|---|---|
| Toàn bộ Student: `npm test -- --runInBand --silent` | **743/743**, 53 suites |
| Python hướng dẫn toán, đọc hiểu, phân số và notebook | **393/393**, 2 cảnh báo deprecation thư viện Starlette/anyio |
| TypeScript: `npx tsc --noEmit` | Qua |
| ESLint các component và màn hình triển khai liên quan | Qua, không chẩn đoán lỗi/cảnh báo |
| Export web, Android, iOS bản cuối | Qua; 32 route web |
| Trình duyệt tại 320×740, 390×844, 820×1180, 1440×1000 | Qua, không lỗi trang hoặc tràn ngang |
| Rà soát độc lập tích hợp | Không có phát hiện cần sửa trong phạm vi gợi ý, tiêu điểm, tham chiếu, pha và hình phân số |
| `git diff --check` | Qua; Git chỉ thông báo quy đổi LF/CRLF của working copy |

Các hồi quy mới được chạy thất bại trước khi sửa và chạy lại thành công: gợi ý dùng kết quả bước trước; hướng dẫn bước đọc hiểu; giữ gợi ý sau câu sai; gợi ý thứ ba; phản hồi chọn thừa/thiếu phần và lời giải thích chia đều.

Lệnh Python từ `ai/runtime`:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_source_understanding.py tests/test_guided_lesson.py tests/test_fraction_lesson_support.py tests/test_primary_lessons.py tests/test_math_tutor.py tests/test_notebook_tutor.py tests/test_notebook_math_layout.py -q
```

Trình duyệt thực hiện lựa chọn đọc hiểu sai rồi sửa; đọc gợi ý và trở về tiêu điểm đúng; chọn vùng hình; đổi cả ba dạng; dùng Space/Enter; kiểm tra thiếu/thừa phần không tự sửa; giữ lựa chọn qua pha; mở/thu gọn tóm tắt; nhập câu sai vẫn giữ gợi ý và dữ liệu đang gõ; dừng gợi ý lặp; hoàn tất bài giải. Các thao tác khám phá hình, tóm tắt và kiểm tra khái niệm không gửi câu trả lời lên máy chủ.

Đầu ra kiểm tra cục bộ, được Git bỏ qua:

- Bundle: `scratch/tutoring-polish-web/`.
- Fixture/runner/kết quả: `scratch/tutoring-polish-qa/make_fixture.py`, `check.cjs`, `results.json`.
- Đã xem ảnh thực tế: `shape-Hình tròn-390.png`, `shape-Hình vuông-820.png`, `hint-1440.png`, `hint-320.png`, `summary-820.png`, `solution-390.png` trong cùng thư mục QA.

## Phạm vi và giới hạn

Web QA dùng HTTP fixture phát lại chuyển trạng thái Python thật, thay bộ lập kế hoạch phép tính bằng dữ liệu kiểm thử. Chưa xác minh thiết bị vật lý hoặc chất lượng model trực tuyến. Export Android/iOS không phải bằng chứng đã cài/chạy trên điện thoại. Không có thay đổi hợp đồng Java trong đợt polish này; không chạy lại bộ Java của đợt trước.

Hình tương tác biểu diễn tối đa hai phân số viết rõ trong đề, mẫu 1–20, tử không âm và tối đa ba hình nguyên theo giới hạn hiện có. Phạm vi này là học phân số qua hình học, không phải bộ giải toàn bộ các dạng hình học. Bài không trích được nguồn an toàn vẫn dùng luồng toán đã duyệt hiện có.

Chưa commit, push hoặc deploy. Không huấn luyện, đổi model, sao chép dữ liệu Drive hoặc gọi AI trực tuyến có thông tin xác thực. Giữ các thay đổi và báo cáo trước đó.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: hướng dẫn và phản hồi thao tác cho học sinh.
  - Applied to: chia nhỏ nội dung, phản hồi thiếu/thừa phần, giải thích chia đều và hướng quay lại bài.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React Native dùng chung web và native.
  - Applied to: giữ/đặt lại state gợi ý theo bước, lượt yêu cầu, nút tương tác và hồi quy màn hình.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: lựa chọn, hình tương tác, nội dung mở rộng và tiêu điểm.
  - Applied to: aria-pressed/expanded, thông báo sai, nút 48, chữ co giãn, bàn phím và trả tiêu điểm.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa backend bằng luồng có sẵn.
  - Applied to: dùng chung bộ thay tham chiếu, kiểm tra phụ thuộc, không thêm model hoặc tầng xử lý mới.
