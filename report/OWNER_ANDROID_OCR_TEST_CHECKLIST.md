# MathVision Kids — Hướng dẫn Kiểm thử OCR Viết tay trên Thiết bị Android Thật
**Giai đoạn:** `AI.HWTEXT.PHYSICAL.1` / `AI.HWTEXT.PHYSICAL.1A`  
**Mục tiêu:** Xác thực quy trình nhận diện chữ viết tay thực tế (OCR-First: CRNN + Hỗ trợ Groq) trên camera điện thoại Android thật.

---

## 1. Yêu cầu & Nguyên tắc An toàn
- **Tuyệt đối không chia sẻ / không hiển thị Groq API Keys** trong ảnh chụp màn hình, logs hoặc báo cáo.
- **Không tự ý huấn luyện lại CRNN / không đổi checkpoint / không đổi vocab**.
- Toàn bộ kết quả nhận diện gốc của CRNN (`rawOcrText`) phải luôn được hiển thị trong bảng chẩn đoán kỹ thuật (DEV).

---

## 2. Quy trình Kiểm thử Chuẩn bị & Thực thi (A–J)

### A. Start services
Khởi động đầy đủ các dịch vụ backend và AI:
- **FastAPI AI Service:** cổng `8000` (`http://127.0.0.1:8000`)
- **Spring Boot Business API:** cổng `8080` (`http://127.0.0.1:8080`)
- **MinIO / PostgreSQL / Redis:** đang hoạt động

### B. Confirm Spring :8080 reachable from Android
Đảm bảo thiết bị Android kết nối được với Spring Boot qua Wi-Fi LAN hoặc USB adb reverse:
```bash
adb reverse tcp:8080 tcp:8080
adb reverse tcp:8000 tcp:8000
```
Kiểm tra mở trình duyệt trên Android truy cập `http://localhost:8080/actuator/health` trả về `{"status":"UP"}`.

### C. Confirm FastAPI :8000 healthy from Spring
Kiểm tra endpoint AI nội bộ trả về HTTP 200:
```bash
curl http://127.0.0.1:8000/internal/v1/ocr/health -H "X-Internal-API-Key: secret-key-default"
```

### D. Confirm Metro / Expo app connected
Chạy ứng dụng Expo trên Android:
```bash
npx expo start
```
Mở app MathVision Kids trên Android, đăng nhập thành công vào trang chủ.

### E. Confirm OCR_PHYSICAL_TRACE_ENABLED=true only for dev test
Xác nhận rằng cờ `OCR_PHYSICAL_TRACE_ENABLED=true` chỉ được bật trong môi trường phát triển/kiểm thử cục bộ (mặc định luôn an toàn `false` trong production).

### F. Confirm diagnostic panel visible
Vào màn hình **Nhận diện chữ viết tay (OCR Pilot)** -> Chọn **Nhiều dòng (Multiline)**. Sau khi nhận diện thử, cuộn xuống dưới xác nhận nhìn thấy thẻ **"Bảng chẩn đoán kỹ thuật (DEV)"** với các thông số:
- `OCR Engine` (CRNN)
- `Segmentation` (LOCAL_CV / LOCAL_CV_GROQ_ASSIST)
- `AI Correction` (NONE / GROQ_POST_CORRECTION)
- `Final Text Source` (CRNN_RAW / CRNN_PLUS_GROQ_CORRECTION)
- `Lines`, `Groq calls`, `Latency`
- `Request ID` và chi tiết từng dòng.

### G. Run Block 1
Chụp ảnh khổ thơ số 1 chuẩn (`OWNER_POEM_BLOCK_1.png`):
```
Em yêu mùa hè
Có hoa sim tím
Mọc trên đồi quê
Rung rinh bướm lượn.
```
Căn chỉnh khung cắt bao quanh vừa vặn 4 dòng và nhấn **Nhận diện**.

### H. Copy requestId
Mở bảng chẩn đoán hoặc kiểm tra terminal dev log để sao chép mã `requestId` (ví dụ: `req-xxxx-xxxx`).

### I. Capture screenshot
Chụp ảnh màn hình kết quả hiển thị văn bản và bảng chẩn đoán kỹ thuật. Lưu tên ảnh theo định dạng chuẩn (ví dụ: `BLOCK1_ANDROID.png`).

### J. Record raw/final OCR
Mở file `report/OWNER_ANDROID_OCR_RESULTS_TEMPLATE.md`, dán `requestId`, kết quả `rawOcrText`, `finalText`, quyết định AI (`AUTO_APPLY`, `SUGGEST_ONLY`, `KEEP_RAW`) và trạng thái đánh giá.

---

## 3. Các kịch bản Kiểm thử Bổ sung

### Kịch bản B: Khảo sát Khả năng Cắt ảnh (Recrop Variations)
Sử dụng cùng khổ thơ Block 1 nhưng chụp với các góc độ và điều kiện khác nhau:
1. `P-B1`: Cắt khung thật sát lề chữ (Tight crop).
2. `P-B2`: Cắt chừa khoảng trống rộng ở mép trên và dưới (Loose margins).
3. `P-B3`: Đặt camera hơi lệch góc sang trái hoặc sang phải (Shifted).
4. `P-B4`: Đặt điện thoại chụp nghiêng một góc nhỏ khoảng 5-10 độ (Rotated).
5. `P-B5`: Chụp trong điều kiện ánh sáng yếu / thiếu sáng (Low light).
6. `P-B6`: Chụp trong điều kiện ánh sáng mạnh hoặc bị bóng đèn phản chiếu (Glare/Bright).

### Kịch bản C: Nhận diện Chữ viết tay Mới (Unknown Handwriting)
Chụp các mẫu chữ viết tay tự do chưa từng có trong tập mẫu:
1. `C1`: 1 dòng chữ viết tay tự do.
2. `C2`: Đoạn văn 3 dòng chữ viết tay tự do.
3. `C3`: Đoạn văn 5 dòng trở lên.
4. `C4`: Dòng chữ có từ vựng tiếng Việt đặc thù hoặc có nhiều dấu thanh phức tạp.
5. `C5`: Chữ viết bằng loại bút khác (bút mực nước, bút chì) hoặc trên loại giấy khác (giấy trắng không kẻ ô).

### Kịch bản D: Tương tác UX Gợi ý Sửa lỗi (SUGGEST_ONLY)
Tìm hoặc viết một từ hơi khó đọc để kích hoạt cơ chế `SUGGEST_ONLY`:
- Kiểm tra văn bản mặc định giữ nguyên bản nhận diện của CRNN.
- Kiểm tra giao diện hiển thị rõ hai nút:
  - Nhấn **[Chấp nhận gợi ý]**: Văn bản cập nhật theo từ sửa đổi của AI.
  - Nhấn **[Giữ nguyên OCR]**: Văn bản giữ nguyên bản gốc CRNN nhận diện.

### Kịch bản E: Kiểm thử Độc lập khi Ngắt Mạng Cloud (Groq Offline)
- Tắt kết nối Internet của máy chủ AI hoặc đặt `GROQ_ENABLED=false` trong `services/ai-service/.env`.
- Chụp và nhận diện lại một bức ảnh trên điện thoại.
- **Yêu cầu:** Ứng dụng vẫn hoạt động bình thường bằng CRNN cục bộ (`finalTextSource=CRNN_RAW`), không bị crash hay báo lỗi kết nối.

### Kịch bản F: An toàn Phép tính Số học (Arithmetic Safety)
- Chụp một dòng chữ viết tay chứa phép tính toán học (Ví dụ: `12 + 25 = 38` hoặc `45 - 17 = 28`).
- **Yêu cầu:** Pipeline tự động phân loại miền là `ARITHMETIC`. Groq tuyệt đối không tự sửa số hoặc dấu phép tính của học sinh.
