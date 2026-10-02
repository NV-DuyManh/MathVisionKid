# MathVision Kids

MathVision Kids hỗ trợ học sinh tiểu học nhận dạng chữ viết tay trong bài giải, đọc phép tính, kiểm tra từng bước và tự sửa bài.

## Cấu trúc dự án

```text
apps/
  student-mobile/src/
    app/recognition/           # Các màn nhận dạng của MathVision
    features/recognition/     # API, ảnh, bản nháp, gợi ý AI, lịch sử, đo lường
  teacher-web/
  admin-web/                  # Phân tích nhận dạng nằm trong khu vực quản trị
  portal-web/
backend/business-api/        # Tài khoản, quyền, bài làm và phản hồi OCR
ai/runtime/
  app/ocr/                   # Nhận chữ viết tay
  app/api/                   # Phân dòng, nhận dạng, gợi ý và xử lý toán
  app/schemas/ocr.py          # Hợp đồng OCR nội bộ
  models/                    # Checkpoint OCR và mô hình toán
packages/                    # Các phần dùng chung
contracts/                   # Hợp đồng giữa các dịch vụ
infra/                       # Hạ tầng phát triển
scripts/                     # Khởi chạy và kiểm thử
docs/                        # Hướng dẫn dự án
report/                      # Báo cáo kiểm chứng; tài liệu cũ tại archive/
reports/                     # Các kết quả nghiên cứu và bằng chứng trước đây
```

Nhận chữ và nhận phép tính là hai chức năng trong cùng sản phẩm. OCR sử dụng `/api/v1/ocr/**` của backend và `/internal/v1/ocr/**` của AI runtime. Backend kiểm tra đăng nhập, vai trò và chủ sở hữu bài nhận dạng.

Xem [mô-đun nhận dạng](apps/student-mobile/src/features/recognition/README.md) và [báo cáo tái cấu trúc](report/RECOGNITION_UNIFICATION_20261002.md).

## Chạy trên máy phát triển

Tại thư mục gốc:

```powershell
./RUN_MATHVISION.bat
```

Các lệnh điều khiển môi trường sẵn có:

```powershell
./scripts/start-all.bat
./scripts/health-check.bat
./scripts/stop-all.bat
```

Frontend dùng workspace npm của dự án. Cấu hình nhận dạng thương hiệu mobile có một nguồn ở `apps/student-mobile/app.json`; các cờ chuyển chế độ ứng dụng cũ không còn tác dụng.

Không mặc định coi dữ liệu mô phỏng hoặc benchmark mẫu là chất lượng mô hình thật. Dashboard học sinh chỉ tính tỷ lệ trên dữ liệu có bản chuẩn độc lập.

## Kiểm thử

```powershell
npm run --workspace student-mobile test -- --runInBand
./node_modules/.bin/tsc.cmd --noEmit -p apps/student-mobile/tsconfig.json
npm run build:admin
```

Kiểm thử backend dùng profile `test` để chạy cơ sở dữ liệu kiểm thử:

```powershell
cd backend/business-api
$env:SPRING_PROFILES_ACTIVE='test'
./gradlew.bat test --console=plain
```

Các hướng dẫn môi trường: [thiết lập](docs/LOCAL_SETUP.md), [kiến trúc](docs/ARCHITECTURE_LOCAL_RUNTIME.md), [xử lý lỗi](docs/TROUBLESHOOTING.md), [bảo trì](docs/MAINTENANCE_GUIDE.md).

Migration đã áp dụng và bằng chứng lịch sử được giữ nguyên để bảo toàn checksum cơ sở dữ liệu và nguồn gốc kết quả. Không dùng tài liệu lịch sử để bật lại chế độ hoặc API riêng.
