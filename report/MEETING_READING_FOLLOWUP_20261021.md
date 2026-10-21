# Hoàn thiện bước hiểu đề — 21/10/2026

Tiếp nối [bốn hạng mục trong biên bản](MEETING_ACTIONS_20261021.md), đã sửa hai vấn đề trong bước đọc hiểu. Phạm vi lần này là backend, không đổi giao diện hay hợp đồng API.

## Thay đổi

1. **Tiêu đề không phải dữ kiện:** trước đây đề có dòng `Bài 6` hoặc `Câu 2 (2 điểm)` có thể khiến hệ thống lấy chính dòng ấy làm điều đã biết. Bộ trích hiện loại các tiêu đề đánh số, nhãn lớp và điểm số phổ biến khi chúng khớp trọn mệnh đề. Câu thực sự như `Lớp 5A có 36 học sinh` vẫn được giữ làm dữ kiện. Không có dữ kiện phù hợp thì dùng luồng toán đã duyệt sẵn có, không tự bịa dữ kiện.
2. **Đúng/Sai có cả hai đáp án:** không còn luôn đúng. Máy chủ chọn giữa một câu dữ kiện và câu hỏi trích nguyên văn, rồi yêu cầu phân biệt câu ấy có phải điều đã biết hay không. Khóa đáp án nằm ở máy chủ; chọn sai không tiến bước hoặc tăng phiên bản lượt trả lời. Không đổi số trong đề để tạo câu sai, không lộ kết quả tính.

Tệp thay đổi thêm: `ai/runtime/app/tutoring/lesson.py`, `ai/runtime/tests/test_source_understanding.py`.

## Bằng chứng kiểm tra

- Tái hiện lỗi cũ bằng nguồn có tiêu đề; chạy kiểm tra mới trước khi sửa: **6 thất bại, 22 qua** đúng tại các trường hợp thiếu xử lý.
- Sau sửa: **28/28 kiểm tra đọc hiểu qua**. Có kiểm tra tiêu đề, nhãn điểm, giữ dữ kiện về lớp học, thiếu dữ kiện, cả hai đáp án Đúng/Sai, trả lời sai/đúng qua phiên máy chủ và không lộ kết quả.
- Chạy bộ hồi quy bài học, phân số, tutor và OCR như lệnh Python trong báo cáo trước: **353 qua**, hai cảnh báo thư viện Starlette đã có.
- Kiểm tra web bằng fixture cục bộ được sinh từ các chuyển trạng thái phiên Python; bộ sinh kế hoạch toán được thay bằng fixture. Chạy riêng đáp án Đúng và Sai, mỗi trường hợp tại 320, 390, 820, 1440 px: **cả hai lượt qua**, không lỗi trang/tràn ngang; hoàn thành bài giải. Dòng `Bài 6` không trở thành lựa chọn dữ kiện.
- `git diff --check` qua. Không cần build lại Student hoặc chạy lại Java vì hai tầng này không thay đổi trong lượt sửa này; kết quả trước được giữ ở báo cáo gốc, không tính là phép đo mới.

Lệnh kiểm tra riêng từ `E:/MathVisionKid/ai/runtime`:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_source_understanding.py -q
```

Fixture/runner kiểm tra cục bộ nằm ở `scratch/meeting-actions-qa/`, được Git bỏ qua. `make_fixture.py 0` chọn trường hợp Đúng và `make_fixture.py 1` chọn trường hợp Sai để kiểm tra tái lập, không dùng tính ngẫu nhiên để quyết định kết quả kiểm thử.

## Giới hạn giữ nguyên

Bộ trích vẫn chỉ nhận một mệnh đề có số và một câu hỏi nêu rõ trong những dạng nguồn được hỗ trợ, mỗi đoạn tối đa 100 ký tự. Đây chưa phải kiểm tra mọi dữ kiện của mọi bài toán. Các dạng khác vẫn đi qua luồng toán hiện có. Việc chọn nhãn Đúng/Sai biến thiên không chứng minh học sinh đã hiểu bài; cần quan sát người học để đánh giá điều đó.

Chưa kiểm tra mô hình AI online hay thiết bị vật lý trong lần này. Không train, đổi model, tải dữ liệu ảnh, commit, push hoặc deploy. Các phần OCR/UI và báo cáo không liên quan trong workspace được giữ nguyên.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa hai lỗi giới hạn trong luồng backend đọc hiểu đã có.
  - Applied to: tái hiện nguyên nhân, lọc nhãn bằng thư viện chuẩn, tái sử dụng kiểm tra đáp án/phiên, kiểm tra hồi quy; không thêm phụ thuộc hoặc thay giao thức.
