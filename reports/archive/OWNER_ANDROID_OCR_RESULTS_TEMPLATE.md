# MathVision Kids — Mẫu Nhật ký Kết quả Kiểm thử Android Thực tế
**Giai đoạn:** `AI.HWTEXT.PHYSICAL.1` / `AI.HWTEXT.PHYSICAL.1A`  
**Người thực hiện:** Project Owner  
**Thiết bị thử nghiệm:** [Ví dụ: Samsung Galaxy A54 / Xiaomi Redmi Note 12 / Thiết bị Android thật]  
**Phiên bản Android:** [Ví dụ: Android 14]  

---

## 1. Bảng Tổng hợp Kết quả Kiểm thử Thực tế

| Test Case | Screenshot Filename | Request ID | Physical Lines | Final Lines | Segmentation | CRNN Engine | Raw OCR | Final Text | AI Decision | Đánh giá (PASS/FAIL) |
|---|---|---|---|---|---|---|---|---|---|---|
| **BLOCK1** | `BLOCK1_ANDROID.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | Em yêu mùa hè... | Em yêu mùa hè... | AUTO_APPLY / KEEP_RAW | [Chờ test] |
| **BLOCK1_RECROP_1** (Tight) | `BLOCK1_RECROP_1.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **BLOCK1_RECROP_2** (Loose) | `BLOCK1_RECROP_2.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **BLOCK1_RECROP_3** (Shift) | `BLOCK1_RECROP_3.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **BLOCK1_RECROP_4** (Rotated) | `BLOCK1_RECROP_4.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **BLOCK1_RECROP_5** (Dim) | `BLOCK1_RECROP_5.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **BLOCK1_RECROP_6** (Bright) | `BLOCK1_RECROP_6.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **UNKNOWN_1** (1 dòng) | `UNKNOWN_1.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **UNKNOWN_2** (3 dòng) | `UNKNOWN_2.png` | `req_...` | 3 | 3 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **UNKNOWN_3** (5+ dòng) | `UNKNOWN_3.png` | `req_...` | 5 | 5 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **UNKNOWN_4** (Từ vựng khó) | `UNKNOWN_4.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **UNKNOWN_5** (Bút/Giấy khác) | `UNKNOWN_5.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | ... | [Chờ test] |
| **SUGGEST_ONLY** | `SUGGEST_ONLY.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | SUGGEST_ONLY | [Chờ test] |
| **AUTO_APPLY** | `AUTO_APPLY.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | AUTO_APPLY | [Chờ test] |
| **KEEP_RAW** | `KEEP_RAW.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | ... | ... | KEEP_RAW | [Chờ test] |
| **GROQ_OFFLINE** | `GROQ_OFFLINE.png` | `req_...` | 4 | 4 | LOCAL_CV | CRNN | ... | ... | NONE | [Chờ test] |
| **ARITHMETIC** | `ARITHMETIC.png` | `req_...` | 1 | 1 | LOCAL_CV | CRNN | 12 + 25 = 38 | 12 + 25 = 38 | KEEP_RAW | [Chờ test] |

---

## 2. Chi tiết từng Trường hợp Kiểm thử

### Case: BLOCK1
- **Screenshot filename:** `BLOCK1_ANDROID.png`
- **Request ID:** `req_...`
- **Expected text:**
  1. `Em yêu mùa hè`
  2. `Có hoa sim tím`
  3. `Mọc trên đồi quê`
  4. `Rung rinh bướm lượn.`
- **Actual raw OCR:**
  1. `...`
  2. `...`
  3. `...`
  4. `...`
- **Actual final text:**
  1. `...`
  2. `...`
  3. `...`
  4. `...`
- **Pass/Fail notes:** [Ghi nhận đánh giá đạt/chưa đạt]

---

### Case: BLOCK1_RECROP_1..N (P-B1 đến P-B6)
- **P-B1 (Tight):**
  - Screenshot filename: `BLOCK1_RECROP_1.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **P-B2 (Loose):**
  - Screenshot filename: `BLOCK1_RECROP_2.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **P-B3 (Shift):**
  - Screenshot filename: `BLOCK1_RECROP_3.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **P-B4 (Rotated):**
  - Screenshot filename: `BLOCK1_RECROP_4.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **P-B5 (Dim):**
  - Screenshot filename: `BLOCK1_RECROP_5.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **P-B6 (Bright):**
  - Screenshot filename: `BLOCK1_RECROP_6.png`
  - Request ID: `req_...`
  - Expected text: Khổ thơ 1 (4 dòng)
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`

---

### Case: UNKNOWN_1..N (C1 đến C5)
- **C1 (1 dòng tự do):**
  - Screenshot filename: `UNKNOWN_1.png`
  - Request ID: `req_...`
  - Expected text: `...`
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **C2 (3 dòng tự do):**
  - Screenshot filename: `UNKNOWN_2.png`
  - Request ID: `req_...`
  - Expected text: `...`
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **C3 (5+ dòng tự do):**
  - Screenshot filename: `UNKNOWN_3.png`
  - Request ID: `req_...`
  - Expected text: `...`
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **C4 (Từ vựng tiếng Việt phức tạp):**
  - Screenshot filename: `UNKNOWN_4.png`
  - Request ID: `req_...`
  - Expected text: `...`
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`
- **C5 (Bút/Giấy khác):**
  - Screenshot filename: `UNKNOWN_5.png`
  - Request ID: `req_...`
  - Expected text: `...`
  - Actual raw: `...`
  - Actual final: `...`
  - Pass/Fail notes: `...`

---

### Case: SUGGEST_ONLY
- **Screenshot filename:** `SUGGEST_ONLY.png`
- **Request ID:** `req_...`
- **Expected text:** `...`
- **Actual raw OCR:** `...`
- **Actual final text (trước khi duyệt):** Giữ nguyên raw OCR
- **Gợi ý AI:** `...`
- **Hành vi khi bấm [Chấp nhận gợi ý]:** Cập nhật theo gợi ý
- **Hành vi khi bấm [Giữ nguyên OCR]:** Giữ nguyên bản gốc
- **Pass/Fail notes:** `...`

---

### Case: AUTO_APPLY
- **Screenshot filename:** `AUTO_APPLY.png`
- **Request ID:** `req_...`
- **Expected text:** `...`
- **Actual raw OCR:** `...`
- **Actual final text:** Tự động sửa lỗi rõ ràng (ví dụ dấu thanh)
- **Pass/Fail notes:** `...`

---

### Case: KEEP_RAW
- **Screenshot filename:** `KEEP_RAW.png`
- **Request ID:** `req_...`
- **Expected text:** `...`
- **Actual raw OCR:** `...`
- **Actual final text:** Giữ nguyên raw OCR do độ tin cậy AI thấp / ảnh mờ
- **Pass/Fail notes:** `...`

---

### Case: GROQ_OFFLINE
- **Screenshot filename:** `GROQ_OFFLINE.png`
- **Request ID:** `req_...`
- **Trạng thái Groq:** Disabled (`GROQ_ENABLED=false` hoặc ngắt Internet)
- **Expected text:** Khổ thơ 1 hoặc câu chữ viết tay
- **Actual raw OCR:** `...`
- **Actual final text:** `...`
- **Pass/Fail notes:** Ứng dụng không crash, CRNN chạy trọn vẹn độc lập

---

### Case: ARITHMETIC
- **Screenshot filename:** `ARITHMETIC.png`
- **Request ID:** `req_...`
- **Expected text:** `12 + 25 = 38` (hoặc phép tính học sinh viết)
- **Actual raw OCR:** `...`
- **Actual final text:** `...` (không bị sửa số/dấu)
- **Pass/Fail notes:** Phép toán được bảo toàn tuyệt đối, phân loại ARITHMETIC
