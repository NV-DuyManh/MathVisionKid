# HƯỚNG DẪN TEST APP MATHVISION KIDS TRÊN ĐIỆN THOẠI ANDROID THẬT
**Mã tác vụ:** `MOBILE.PHYSICAL.1`  
**Phương thức thử nghiệm xác nhận:** `EXPO GO` (Hỗ trợ đầy đủ Expo SDK 57)  
**Địa chỉ IP LAN Laptop:** `192.168.1.12`  
**Cổng Spring Boot API:** `8080`  
**Cổng Expo Metro Server:** `8081`  

---

## A. CHUẨN BỊ TRÊN LAPTOP (WINDOWS)

1. **Kết nối mạng Wi-Fi:**
   - Laptop phải đang kết nối vào Wi-Fi: **`Kim Chung 4`** (hoặc mạng Wi-Fi dùng chung với điện thoại).
   - *Lưu ý quan trọng:* Đảm bảo chế độ mạng trên Windows là **Private network** để Windows Firewall không chặn kết nối từ điện thoại.
     *(Vào Settings → Network & internet → Wi-Fi → Bấm vào mạng đang kết nối → Chọn **Private network**)*.

2. **Khởi động hệ thống Backend MathVision:**
   - Mở terminal tại thư mục gốc `E:\MathVisionKid`.
   - Nếu hệ thống chưa chạy, chạy lệnh:
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
     ```
   - Chờ terminal thông báo `READY_FOR_DEMO` (tất cả Docker, Spring Boot, FastAPI, Celery đều PASS).

3. **Khởi động Student Mobile Server (chế độ LAN):**
   - Mở một cửa sổ PowerShell mới tại `E:\MathVisionKid`.
   - Chạy lệnh:
     ```bash
     npm run start:device
     ```
     *(hoặc lệnh tương đương: `npx expo start --lan`)*.
   - Metro Bundler sẽ khởi động và hiển thị mã **QR Code** trực tiếp trên màn hình terminal.

---

## B. KẾT NỐI VÀ MỞ APP TRÊN ĐIỆN THOẠI ANDROID

1. **Kết nối cùng mạng Wi-Fi:**
   - Trên điện thoại Android, vào Cài đặt Wi-Fi và kết nối vào cùng mạng Wi-Fi **`Kim Chung 4`** giống laptop.

2. **Mở ứng dụng Expo Go:**
   - Mở ứng dụng **Expo Go** trên điện thoại (như giao diện trên màn hình hiện tại của bạn).

3. **Mở ứng dụng MathVision Kids:**
   - **Cách 1 (Quét mã QR):**
     - Bấm vào nút **`Scan QR`** trên màn hình Expo Go.
     - Cấp quyền máy ảnh cho Expo Go nếu được hỏi.
     - Hướng camera điện thoại quét mã QR hiển thị ở terminal laptop.
   - **Cách 2 (Nhập URL trực tiếp nếu không quét được QR):**
     - Tại ô **`Enter URL`** (đã có sẵn chữ `exp://`), nhập chính xác:
       ```
       192.168.1.12:8081
       ```
       *(URL đầy đủ sẽ là: `exp://192.168.1.12:8081`)*.
     - Bấm nút **`Connect`**.

4. **Chờ tải ứng dụng (JavaScript Bundle):**
   - Điện thoại sẽ tải bundle (0% -> 100%).
   - Màn hình Splash và màn hình Đăng nhập của **MathVision Kids** sẽ xuất hiện!

---

## C. KIỂM TRA ĐƯỜNG TRUYỀN (CONNECTIVITY CHECK)

1. **Kiểm tra trực tiếp trên trình duyệt Chrome điện thoại:**
   - Mở Google Chrome trên điện thoại, truy cập địa chỉ sau:
     ```
     http://192.168.1.12:8080/actuator/health
     ```
   - **Kết quả mong đợi:** Màn hình hiển thị JSON: `{"status":"UP",...}`.
   - Nếu Chrome trên điện thoại mở được trang này, nghĩa là điện thoại và backend laptop đã thông mạng 100%!

2. **Kiểm tra qua công cụ Chẩn đoán (Dev Diagnostic) trong app:**
   - Tại màn hình Đăng nhập của app MathVision Kids, kéo xuống dưới cùng.
   - Bấm vào dòng: **`🛠️ Chẩn đoán kết nối API (Dev)`**.
   - Màn hình sẽ hiển thị:
     - Môi trường: `ANDROID (Development)`
     - API Base URL: `http://192.168.1.12:8080/api/v1`
     - Bấm nút: **`Kiểm tra kết nối Backend`**.
     - Kết quả báo xanh: `Kết nối thành công! {"status":"UP",...}`.

---

## D. ĐĂNG NHẬP VÀ THỰC HIỆN BÀI TEST CHỤP ẢNH ĐẦU TIÊN

### 1. Đăng nhập tài khoản học sinh thử nghiệm:
- **Tài khoản (Email):** `minh.student@mathvision.local`
- **Mật khẩu:** `MathVision123!`
- Bấm nút **`Đăng nhập`**.
- Màn hình chính của học sinh xuất hiện với lời chào *"Xin chào Nguyễn Bình Minh!"*.

### 2. Chuẩn bị phép tính trên giấy:
Viết ra giấy một phép tính đặt dọc đơn giản (cộng hoặc trừ 2 số tự nhiên 2 chữ số):
```text
    45
  + 27
  ----
    72
```
*Lưu ý:*
- Mỗi ảnh chỉ chứa duy nhất 1 phép tính đặt dọc.
- Viết rõ ràng, đủ ánh sáng, không để bóng tay che chữ số.
- Không thử phân số, hình học hay toán có lời văn (nằm ngoài phạm vi MVP).

### 3. Thực hiện chụp và gửi bài:
1. Trên màn hình chính của app, bấm nút lớn: **`CHỤP BÀI CỦA EM`**.
2. **Cấp quyền máy ảnh:** App sẽ hiển thị hộp thoại xin quyền camera, bấm **`Cho phép mở máy ảnh`** (hoặc *"Trong khi dùng ứng dụng"*).
3. Đưa phép tính vào giữa khung ngắm **ScanFrame**.
4. Bấm nút chụp ảnh hình tròn màu trắng.
5. **Màn hình Bảo vệ quyền riêng tư (Privacy Gate):**
   - Dùng ngón tay kiểm tra xem trong ảnh có khuôn mặt hay tên học sinh/trường học không (vẽ hộp che đen nếu có).
   - Tích chọn: **`Em đã kiểm tra và che hết thông tin riêng tư trong ảnh.`**
   - Bấm **`Tiếp tục xem lại`**.
6. **Màn hình Xem lại (Preview):**
   - Kiểm tra các huy hiệu chất lượng (Ảnh đủ sáng, Nằm trong khung, Một bài toán).
   - Có thể bấm **`Xoay ảnh`** hoặc **`Chỉnh vùng bài`** nếu cần.
   - Bấm nút: **`KIỂM TRA BÀI TOÁN`**.
7. **Màn hình Xử lý (Processing):**
   - App sẽ hiển thị 3 bước: *1. Đọc bài -> 2. Kiểm tra -> 3. Gợi ý*.
   - Ảnh được gửi lên Spring Boot (`/api/v1/student/submissions`) → lưu MinIO → gửi Celery/FastAPI → YOLO nhận diện chữ số → Spatial RowGrouper → Parser & Validator kiểm tra toán học → lưu kết quả.
8. **Màn hình Kết quả (Results):**
   - Kết quả xuất hiện: Thông báo phép tính chính xác hoặc chỉ ra hàng tính bị sai kèm lời giải thích thân thiện cho học sinh tiểu học.

---

## E. XỬ LÝ SỰ CỐ KHI GẶP LỖI (TROUBLESHOOTING)

Nếu điện thoại báo lỗi không kết nối được hoặc không tải được bundle, hãy kiểm tra theo thứ tự sau:

1. **Điện thoại và Laptop không cùng Wi-Fi:**
   - Kiểm tra lại xem cả hai có cùng kết nối vào mạng Wi-Fi **`Kim Chung 4`** không.
   - Nếu một bên dùng 4G/5G hoặc Wi-Fi khác, kết nối sẽ không hoạt động.

2. **Wi-Fi bật tính năng cách ly (AP Isolation / Guest Network):**
   - Một số modem Wi-Fi công cộng hoặc chế độ Khách (Guest Wi-Fi) chặn các thiết bị kết nối trực tiếp với nhau. Hãy dùng mạng Wi-Fi gia đình/nội bộ bình thường.

3. **Windows Firewall chặn kết nối cổng 8080 hoặc 8081:**
   - Kiểm tra xem mạng Wi-Fi trên Windows đã chuyển sang **Private** chưa.
   - Nếu vẫn bị chặn, mở **PowerShell với quyền Administrator** trên laptop và chạy 2 lệnh mở cổng tạm thời:
     ```powershell
     New-NetFirewallRule -DisplayName "MathVision Spring Boot (8080)" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
     New-NetFirewallRule -DisplayName "MathVision Expo Metro (8081)" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow
     ```

4. **Tắt các phần mềm VPN trên laptop:**
   - Nếu đang bật VPN (Radmin VPN, Tailscale, Cloudflare WARP...), hãy tạm tắt để tránh xung đột định tuyến IP LAN `192.168.1.12`.

---

## F. CẢNH BÁO VỀ DỮ LIỆU RIÊNG TƯ (PRIVACY LIMITATION)
> ⚠️ **LƯU Ý:** Đợt thử nghiệm trên thiết bị thật này chỉ dành cho các hình ảnh bài tập toán có kiểm soát. Tuyệt đối không chụp hoặc tải lên khuôn mặt thật, tên thật của trẻ em hoặc tên trường học cho đến khi toàn bộ quy trình che PII tự động/thủ công được kiểm định độc lập hoàn tất.
