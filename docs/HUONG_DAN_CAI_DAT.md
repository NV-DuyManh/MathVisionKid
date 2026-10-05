# Cài đặt MathVision Kids

[README](../README.md) · [English setup](LOCAL_SETUP.md) · [Cách dùng app](USER_GUIDE.md)

Hướng dẫn này dành cho Windows. Thực hiện các lệnh trong PowerShell tại thư mục gốc của dự án. Có hai việc riêng: chạy hệ thống và cấu hình khả năng nhận diện thật.

## Chuẩn bị

| Công cụ | Yêu cầu |
| :--- | :--- |
| Node.js | Nhánh 22, từ 22.13 trở lên |
| Python | 3.12 |
| Java | JDK 21 |
| Docker Desktop | Đã mở, engine chạy, có Docker Compose |
| Git | Có thể gọi trong terminal |
| Điện thoại, nếu test | Expo Go tương thích SDK 57, cùng Wi-Fi với máy tính |

Không cần cài Gradle riêng. Lần cài đầu cần mạng để tải thư viện và Docker images.

## 1. Tải code và cài thư viện

```powershell
git clone https://github.com/NV-DuyManh/MathVisionKid.git
cd MathVisionKid
npm ci
py -3.12 -m venv ai\runtime\.venv
.\ai\runtime\.venv\Scripts\python.exe -m pip install --upgrade pip
.\ai\runtime\.venv\Scripts\python.exe -m pip install -r ai\runtime\requirements.txt
```

`npm ci` ở thư mục gốc cài cho toàn bộ JavaScript workspaces. Nếu máy không có lệnh `py`, dùng đường dẫn tới Python 3.12 đã cài để tạo môi trường.

## 2. Bật nhận diện thật

Code trên Git có cấu hình và manifest, **không chứa model weights hoặc API key riêng**.

| Muốn dùng | Cần chuẩn bị |
| :--- | :--- |
| Đọc từng dòng chữ viết tay bằng OCR của dự án | Checkpoint CRNN `best_cer.pth` do chủ dự án cung cấp |
| Đọc ảnh đề trong màn hình hướng dẫn toán | Groq hoặc Gemini được cấu hình bằng key hợp lệ |
| Hướng dẫn từng bước | Backend và AI runtime; một số dạng đã có kế hoạch sẵn, các dạng khác phụ thuộc AI |
| Chấm phép tính bằng YOLO | Model YOLO và `RUNTIME_MODE=MODEL` |

Đặt checkpoint chữ viết tay tại:

```text
ai/runtime/models/ocr/crnn_vi_handwriting_v1/best_cer.pth
```

`vocab.json` và `model_manifest.json` trong cùng thư mục đã có trên Git. [Hướng dẫn tiếng Anh](LOCAL_SETUP.md#enable-real-recognition-and-guidance) có hash để đối chiếu, cách cài detector và cấu hình YOLO.

Để bật đọc ảnh đề, tạo file `ai/runtime/.env.local` bằng trình soạn thảo, ví dụ:

```dotenv
GROQ_ENABLED=true
GROQ_API_KEYS="THAY_BANG_KEY_HOP_LE_CUA_BAN"
GEMINI_ENABLED=false
GEMINI_API_KEYS=""
```

Nếu dùng Gemini, tắt Groq rồi bật Gemini với key hợp lệ. Có thể bật cả hai để dùng fallback. Kiểm tra model được cấu hình có được tài khoản nhà cung cấp hỗ trợ hay không. Không copy nguyên `.env.example` rồi chạy: file mẫu có placeholder và không phải cấu hình hoàn chỉnh.

Giữ file key ngoài Git. Khởi động lại dịch vụ sau khi chỉnh cấu hình. Mặc định `RUNTIME_MODE=FIXTURE` chỉ dùng kết quả giả lập cho luồng chấm phép tính bất đồng bộ; nó không biến OCR hoặc đọc ảnh đề thành tính năng offline.

## 3. Khởi chạy

Mở Docker Desktop rồi chạy:

```powershell
.\RUN_MATHVISION.bat
```

Launcher bật hệ thống, mở web portal và hiện QR cho app học sinh. **Giữ terminal để quét QR.** Terminal của student server mở riêng; cửa sổ launcher cũng dừng chờ ở cuối để không mất mã.

Không bật thêm toàn bộ Compose cùng lúc với launcher vì có thể trùng cổng AI.

| Trang | Địa chỉ trên máy tính |
| :--- | :--- |
| Portal | `http://localhost:5172` |
| Giáo viên | `http://localhost:5173` |
| Quản trị | `http://localhost:5174` |
| App học sinh trên web | `http://localhost:8081` |

Tài khoản **chỉ dành cho môi trường dev cục bộ**:

| Vai trò | Tài khoản | Mật khẩu |
| :--- | :--- | :--- |
| Học sinh | `minh.student@mathvision.local` | `MathVision123!` |
| Giáo viên | `lan.teacher@mathvision.local` | `MathVision123!` |
| Quản trị | `admin.demo@mathvision.local` | `MathVision123!` |

## 4. Test trên điện thoại

1. Nối điện thoại và máy tính cùng Wi-Fi.
2. Mở Expo Go tương thích SDK 57 và quét QR launcher hiện.
3. Đăng nhập bằng tài khoản được cấp hoặc tài khoản dev ở trên.
4. Chạm **Chụp bài toán**, cấp quyền camera khi hệ điều hành hỏi, rồi thử một ảnh rõ.

Điện thoại kết nối bằng IP LAN của máy tính; `localhost` trên điện thoại không trỏ về máy tính. Nếu cần đặt API thủ công, dùng `EXPO_PUBLIC_API_OVERRIDE=http://IP_LAN_MAY_TINH:8080/api/v1` trong `apps/student-mobile/.env.local`, rồi khởi động lại student server. Giữ phần `/api/v1` ở cuối. `EXPO_PUBLIC_API_BASE_URL` chỉ là cấu hình dự phòng, không ưu tiên hơn host phát hiện từ student server. Không đưa key AI vào biến `EXPO_PUBLIC_`.

## 5. Kiểm tra và tắt

```powershell
.\scripts\health-check.bat
```

Khi dùng xong:

```powershell
.\scripts\stop-all.bat
```

Đóng terminal launcher không tự tắt các dịch vụ nền. Lệnh stop thông thường giữ dữ liệu database và ảnh. Log nằm ở `infra/local-runtime/logs/`.

Health check xanh chưa chứng minh model OCR có đầy đủ weights, key AI còn quota hoặc ảnh được đọc đúng. Kiểm tra bằng ảnh thật, đối chiếu chữ, số và dấu toán. Nếu lỗi, xem [Troubleshooting](TROUBLESHOOTING.md).
