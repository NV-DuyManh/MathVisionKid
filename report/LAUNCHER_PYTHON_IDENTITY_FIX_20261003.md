# Sửa launcher nhận nhầm dịch vụ Python đang chạy

Ngày: 03/10/2026. Phạm vi: launcher local và kiểm tra hồi quy nhận diện tiến trình. Không đổi Student Mobile, AI model, auth/RBAC hoặc dữ liệu. Không commit/push.

## Nguyên nhân

FastAPI đang chạy hợp lệ ở cổng 8000 với PID 26420. Trên máy này, Python virtualenv chạy qua tiến trình chuyển tiếp của Windows:

- Tiến trình cha 22972: `E:\MathVisionKid\ai\runtime\.venv\Scripts\python.exe -m uvicorn app.main:app ...`.
- Tiến trình con 26420 giữ cổng: Python nền do uv cài đặt ở thư mục người dùng, `-m uvicorn app.main:app ...`.

Kiểm tra cũ đòi đường dẫn dự án xuất hiện ngay trong command line của tiến trình giữ cổng. Tiến trình con không chứa đường dẫn đó nên bị báo PORT_CONFLICT dù đúng là runtime đã chạy cho dự án.

## Sửa đổi

Thêm `Test-ServiceProcessIdentity` trong `scripts/dev/start-all.ps1`, dùng cho FastAPI đang giữ cổng và nhận diện Celery worker. Vẫn giữ kiểm tra command line trực tiếp hiện có.

Nếu Python con không chứa đường dẫn dự án, chỉ chấp nhận khi đồng thời:

- Tiến trình con chạy đúng mô-đun dịch vụ và là Python.
- Tiến trình cha trực tiếp còn tồn tại; thời điểm tạo không sau tiến trình con, tránh nhầm khi PID được tái sử dụng.
- Executable của cha nằm đúng trong `.venv/Scripts` thuộc runtime dự án.
- Command line của cha cũng chạy đúng dịch vụ thuộc đường dẫn dự án.

Không tin PID file đơn thuần, không duyệt tổ tiên bất kỳ để tìm chuỗi tên dự án, không tắt tiến trình chiếm cổng. Dịch vụ dự án khác vẫn bị từ chối.

## Kiểm tra

`powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/test/test_service_runtime_identity.ps1`:

- 8 trường hợp command identity hiện có: PASS.
- 8 trường hợp chuyển tiếp Python Windows: PASS, gồm đúng dự án, dự án khác, thư mục tên gần giống, cha là shell, mô-đun sai, PID cha được tái sử dụng, thiếu cha và mô-đun con không liên quan.
- Listener TCP thật không phải Spring: bị chặn đúng và vẫn chạy; không khởi động chương trình thay thế.

Chạy `scripts/dev/start-all.ps1` trên hệ thống thật: exit 0, FastAPI PID 26420 được dùng lại, các dịch vụ còn thiếu được khởi động, diagnostic báo `READY_FOR_FULL_DEMO`.

Chạy lại lần thứ hai: các dịch vụ được nhận ra là đang chạy, Celery được dùng lại, không khởi động thêm bản trùng. `scripts/start-student-metro.ps1` cũng exit 0 và dùng lại tiến trình 37308. Kiểm tra này không phải bằng chứng test điện thoại thật.

Đã đọc tài liệu [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/) theo yêu cầu repository; lượt sửa không thay mã Expo.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Sửa nguyên nhân trong bộ nhận diện chung của launcher với thay đổi nhỏ.
  - Applied to: Dùng lại kiểm tra command identity hiện có, kiểm tra cha trực tiếp cho Python Windows, bổ sung hồi quy trong script test hiện có; không thêm dependency hoặc cơ chế quản lý tiến trình mới.
