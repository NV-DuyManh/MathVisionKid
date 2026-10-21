# Math Vision Kids — Jira backlog rebuild

Ngày kiểm tra: 14/10/2026, múi giờ Asia/Saigon. Project: C1SE.01 (SCRUM), board 1.

Đã cập nhật [Jira](https://duymanhdnvn20092005.atlassian.net/jira/software/projects/SCRUM/boards/1) theo sáu tài liệu và xác nhận của chủ dự án: giữ giờ chi tiết Excel, dùng ngày Project Plan. Đây là kế hoạch được dựng lại; assignment và cửa sổ task là đề xuất, không phải lịch sử thực hiện.

## Kết quả

- 193 issue hiện có: 8 Epic, 26 Story, 30 Task, 129 Subtask.
- Trong đó: 26 Story PB01–PB26; 128 Subtask SB1.1–SB4.24; 29 Task bổ sung; 2 issue quản lý kế hoạch được chuyển từ ticket mẫu SCRUM-3/SCRUM-4.
- 191 issue mới, 2 issue mẫu được chuẩn hóa. Các ticket trêu đùa trong ảnh đã không còn trên Jira ở lần kiểm tra đầu tiên; board/JQL chỉ còn SCRUM-3 và SCRUM-4. SCRUM-1 và SCRUM-17 trả 404. Không ghi nhận thao tác xóa nào do lần tái lập này.
- 25 liên kết: 23 Blocks và 2 Relates. Không tạo worklog, không tự đánh dấu Done.
- Năm tài khoản thành viên đã có quyền được giao việc; không cần mời thêm tài khoản. Phân công chính theo hồ sơ NCKH; việc chéo chuyên môn có technical owner hỗ trợ/review.

## Lịch sprint

| Sprint | Jira sprint ID | Ngày bắt đầu | Ngày kết thúc | Nhiệm vụ con | Giờ |
|---|---:|---|---|---:|---:|
| 1: MVK S1 · Perception & Rules | 1 | 2026-08-30 | 2026-09-19 | 40 | 500 |
| 2: MVK S2 · Teacher & Auth | 3 | 2026-09-20 | 2026-10-10 | 33 | 500 |
| 3: MVK S3 · Async & Tutoring | 2 | 2026-10-11 | 2026-10-31 | 31 | 500 |
| 4: MVK S4 · QA & Release | 4 | 2026-11-01 | 2026-11-21 | 24 | 500 |

Sprint 3 đang active. Sprint 1–2 giữ trạng thái planned/future với ngày quá khứ vì Excel ghi Not started và chưa có bằng chứng tiến độ. Không start/closelùi ngày hoặc tạo lịch sử hoàn thành. Sprint 4 future. Tất cả issue hiện To Do; owner cập nhật tiến độ thực tế sau khi kiểm tra evidence.

Khởi tạo 16–29/08; tích hợp/pilot 22/11–06/12; nghiệm thu/bảo vệ 07–17/12/2026. Ngày mỗi task được chia trong cửa sổ phase/sprint; Excel chỉ có Day 1–15, chưa có ngày hoàn thành thực tế. Thời gian native Original/Remaining Estimate lưu đúng giây; Jira có thể hiển thị 10 giờ thành “1d 2h” theo quy ước 8 giờ/ngày.

## Phân công và tải kế hoạch

| Thành viên | Vai trò chính theo NCKH | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Tổng giờ SB |
|---|---|---:|---:|---:|---:|---:|
| Nguyễn Văn Duy Mạnh | Kiến trúc, phân tích yêu cầu, điều phối tích hợp | 100 | 115 | 100 | 95 | 410 |
| Trần Hoài Nam | Spring Boot, API, bảo mật, tích hợp AI | 90 | 100 | 105 | 110 | 405 |
| Phan Quang Hiếu | Xử lý ảnh, OCR/AI | 105 | 75 | 100 | 95 | 375 |
| Trần Viết Lộc | Teacher Web và Student Mobile | 90 | 115 | 85 | 100 | 390 |
| Lê Minh Trường Khả | Dữ liệu, QA và đánh giá | 115 | 95 | 110 | 100 | 420 |

Tổng 2.000 giờ. Mỗi người 75–115 giờ/sprint: trung bình nhóm 6,67 giờ/người/ngày trong 15 ngày làm việc, cao hơn giả định 3 giờ/ngày của Project Plan. Đây là phân bổ kế hoạch; chưa chứng nhận availability hoặc lịch ngày khả thi. [SCRUM-4](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-4) yêu cầu PO kiểm tra capacity và pair support trước khi cam kết thực hiện.

## Quyết định baseline và chênh lệch cần review

- Chủ dự án xác nhận: estimate từng nhiệm vụ giữ theo Excel, ngày theo Project Plan. Product Backlog ban đầu 980 giờ, Sprint Backlog chi tiết 2.000 giờ; cả hai giữ provenance ở Story. Chỉ estimate các nhiệm vụ SB con để tránh tính hai lần.
- Project Plan/Excel/NCKH thống nhất lịch bốn sprint; Proposal/Architecture còn ghi lịch bảy sprint. Jira dùng bốn sprint đã chọn; không sửa các tài liệu nguồn.
- Core acceptance từ PB/Proposal: critical-token accuracy ≥90%; high-confidence first-error precision ≥85%; over-correction ≤5%; hint reviewer mean ≥4/5; p95 ≤12 giây/crop trên môi trường công bố.
- NCKH có digit accuracy 80%/95%, CER <0,10, p95 ≤2 giây/ảnh, batch 30 ảnh ≤45 giây và giảm ≥40% thời gian chấm. Đây là mục tiêu nghiên cứu riêng; metric định nghĩa khác nhau không gộp hay tuyên bố đã đạt.
- Dataset: ≥100 pilot image/guide ở PB22; NCKH nêu ≥200 ảnh Sprint 1; ≥500 gold là yêu cầu, 700 là target. Double annotation ≥20%, adjudication, writer/problem-disjoint frozen split. [SCRUM-190](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-190) quản lý mở rộng tới 31/10 (mapping W11 đề xuất, PO review).
- 29 việc bổ sung chưa có giờ chi tiết trong nguồn: estimate TBD, tách khỏi 2.000 giờ SB. Không điền giờ thực tế hay ngày nghiệm thu không có evidence.

## Kiểm tra dữ liệu sau cập nhật

- Đọc lại toàn bộ 193 issue từ Jira, có phân trang.
- Đối soát 128 nhiệm vụ SB: key tồn tại, title đúng Excel, assignee, Story cha, Start date, Due date, Original Estimate, Remaining Estimate, sprint và trạng thái. Không có sai lệch.
- Tổng giờ native: 500/500/500/500; 2.000 giờ toàn bộ SB.
- Đối soát 26 Story về Epic cha, người phụ trách, ngày và sprint; không estimate parent gây trùng giờ.
- Đối soát 29 Task bổ sung về Epic, assignee, ngày; kiểm tra 25 liên kết trên dữ liệu Jira. Không có sai lệch.
- Source Not started; không tạo lịch sử làm việc, bằng chứng thiết bị hay kết quả AI. Không sửa code, không train model, không commit/push.

## Epic và Product Backlog

| PB | Story trên Jira | Epic | Sprint | Giờ PB ban đầu | Giờ SB con | Owner |
|---|---|---|---:|---:|---:|---|
| PB01 — Assignment Setup | [SCRUM-28](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-28) | SCRUM-21 | 2 | 25 | 60 | Trần Hoài Nam |
| PB02 — Image Capture | [SCRUM-26](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-26) | SCRUM-18 | 1 | 20 | 40 | Trần Viết Lộc |
| PB03 — Image Pre-processing | [SCRUM-29](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-29) | SCRUM-18 | 2 | 25 | 55 | Trần Viết Lộc |
| PB04 — Image Quality Check | [SCRUM-30](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-30) | SCRUM-18 | 1 | 25 | 45 | Phan Quang Hiếu |
| PB05 — PII Masking (Privacy) | [SCRUM-31](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-31) | SCRUM-18 | 1 | 30 | 55 | Trần Viết Lộc |
| PB06 — Batch Upload | [SCRUM-32](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-32) | SCRUM-18 | 2 | 40 | 90 | Trần Viết Lộc |
| PB07 — Async Processing | [SCRUM-33](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-33) | SCRUM-23 | 3 | 40 | 100 | Phan Quang Hiếu |
| PB08 — AI Recognition: Layout & Tokens | [SCRUM-34](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-34) | SCRUM-19 | 1 | 40 | 80 | Phan Quang Hiếu |
| PB09 — AI Recognition: Carry/Borrow & Confidence | [SCRUM-35](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-35) | SCRUM-19 | 1 | 35 | 65 | Phan Quang Hiếu |
| PB10 — Out of Scope Handling | [SCRUM-36](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-36) | SCRUM-19 | 3 | 25 | 50 | Phan Quang Hiếu |
| PB11 — Token Confirmation | [SCRUM-37](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-37) | SCRUM-21 | 2 | 30 | 60 | Trần Viết Lộc |
| PB12 — Math Validation | [SCRUM-38](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-38) | SCRUM-20 | 1 | 35 | 65 | Nguyễn Văn Duy Mạnh |
| PB13 — Earliest Error Logic | [SCRUM-39](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-39) | SCRUM-20 | 1 | 30 | 55 | Nguyễn Văn Duy Mạnh |
| PB14 — AI Pre-grading | [SCRUM-40](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-40) | SCRUM-20 | 1 | 30 | 45 | Trần Hoài Nam |
| PB15 — Teacher Review Queue | [SCRUM-41](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-41) | SCRUM-21 | 2 | 40 | 90 | Trần Viết Lộc |
| PB16 — Teacher Final Decision | [SCRUM-42](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-42) | SCRUM-21 | 2 | 30 | 60 | Trần Hoài Nam |
| PB17 — Student Tutoring (Hint) | [SCRUM-43](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-43) | SCRUM-20 | 3 | 40 | 100 | Nguyễn Văn Duy Mạnh |
| PB18 — Student Retry | [SCRUM-44](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-44) | SCRUM-20 | 3 | 30 | 65 | Trần Hoài Nam |
| PB19 — Data & Audit Control | [SCRUM-45](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-45) | SCRUM-22 | 4 | 50 | 100 | Trần Hoài Nam |
| PB20 — Notation Diversity | [SCRUM-46](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-46) | SCRUM-19 | 3 | 35 | 75 | Nguyễn Văn Duy Mạnh |
| PB21 — Authentication & RBAC | [SCRUM-47](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-47) | SCRUM-22 | 2 | 50 | 85 | Trần Hoài Nam |
| PB22 — Dataset & Annotation | [SCRUM-48](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-48) | SCRUM-24 | 1 | 35 | 50 | Lê Minh Trường Khả |
| PB23 — AI Evaluation Harness | [SCRUM-49](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-49) | SCRUM-24 | 4 | 50 | 110 | Phan Quang Hiếu |
| PB24 — Backend-AI Integration | [SCRUM-50](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-50) | SCRUM-23 | 3 | 50 | 110 | Nguyễn Văn Duy Mạnh |
| PB25 — QA & NFR Testing | [SCRUM-51](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-51) | SCRUM-24 | 4 | 80 | 180 | Lê Minh Trường Khả |
| PB26 — Release Packaging & Docs | [SCRUM-52](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-52) | SCRUM-24 | 4 | 60 | 110 | Nguyễn Văn Duy Mạnh |

## Chi tiết 128 nhiệm vụ Sprint Backlog

| SB | PB | Jira | Owner | Giờ | Start | Due |
|---|---|---|---|---:|---|---|
| 2.1 | PB01 | [SCRUM-92](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-92) | Nguyễn Văn Duy Mạnh | 20 | 2026-09-21 | 2026-09-25 |
| 2.2 | PB01 | [SCRUM-93](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-93) | Trần Viết Lộc | 15 | 2026-09-24 | 2026-09-29 |
| 2.3 | PB01 | [SCRUM-94](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-94) | Trần Hoài Nam | 10 | 2026-10-01 | 2026-10-05 |
| 2.4 | PB01 | [SCRUM-95](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-95) | Lê Minh Trường Khả | 15 | 2026-10-06 | 2026-10-09 |
| 1.1 | PB02 | [SCRUM-27](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-27) | Trần Viết Lộc | 10 | 2026-08-31 | 2026-09-03 |
| 1.2 | PB02 | [SCRUM-53](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-53) | Trần Viết Lộc | 10 | 2026-09-04 | 2026-09-08 |
| 1.3 | PB02 | [SCRUM-54](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-54) | Trần Viết Lộc | 10 | 2026-09-10 | 2026-09-14 |
| 1.4 | PB02 | [SCRUM-55](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-55) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 2.5 | PB03 | [SCRUM-96](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-96) | Phan Quang Hiếu | 10 | 2026-09-21 | 2026-09-23 |
| 2.6 | PB03 | [SCRUM-97](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-97) | Phan Quang Hiếu | 10 | 2026-09-24 | 2026-09-28 |
| 2.7 | PB03 | [SCRUM-98](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-98) | Phan Quang Hiếu | 15 | 2026-09-28 | 2026-10-01 |
| 2.8 | PB03 | [SCRUM-99](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-99) | Trần Viết Lộc | 10 | 2026-10-02 | 2026-10-06 |
| 2.9 | PB03 | [SCRUM-100](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-100) | Lê Minh Trường Khả | 10 | 2026-10-07 | 2026-10-09 |
| 1.5 | PB04 | [SCRUM-56](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-56) | Phan Quang Hiếu | 15 | 2026-08-31 | 2026-09-03 |
| 1.6 | PB04 | [SCRUM-57](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-57) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-04 | 2026-09-08 |
| 1.7 | PB04 | [SCRUM-58](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-58) | Trần Viết Lộc | 10 | 2026-09-10 | 2026-09-14 |
| 1.8 | PB04 | [SCRUM-59](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-59) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 1.9 | PB05 | [SCRUM-60](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-60) | Trần Viết Lộc | 15 | 2026-08-31 | 2026-09-03 |
| 1.10 | PB05 | [SCRUM-61](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-61) | Trần Viết Lộc | 10 | 2026-09-03 | 2026-09-07 |
| 1.11 | PB05 | [SCRUM-62](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-62) | Trần Viết Lộc | 10 | 2026-09-08 | 2026-09-10 |
| 1.12 | PB05 | [SCRUM-63](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-63) | Trần Hoài Nam | 10 | 2026-09-11 | 2026-09-15 |
| 1.13 | PB05 | [SCRUM-64](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-64) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 2.10 | PB06 | [SCRUM-101](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-101) | Trần Viết Lộc | 25 | 2026-09-21 | 2026-09-29 |
| 2.11 | PB06 | [SCRUM-102](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-102) | Trần Hoài Nam | 30 | 2026-09-23 | 2026-10-02 |
| 2.12 | PB06 | [SCRUM-103](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-103) | Phan Quang Hiếu | 15 | 2026-09-30 | 2026-10-05 |
| 2.13 | PB06 | [SCRUM-104](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-104) | Lê Minh Trường Khả | 20 | 2026-10-05 | 2026-10-09 |
| 3.1 | PB07 | [SCRUM-125](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-125) | Phan Quang Hiếu | 20 | 2026-10-12 | 2026-10-16 |
| 3.2 | PB07 | [SCRUM-126](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-126) | Phan Quang Hiếu | 30 | 2026-10-13 | 2026-10-22 |
| 3.3 | PB07 | [SCRUM-127](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-127) | Trần Hoài Nam | 15 | 2026-10-19 | 2026-10-22 |
| 3.4 | PB07 | [SCRUM-128](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-128) | Nguyễn Văn Duy Mạnh | 15 | 2026-10-22 | 2026-10-27 |
| 3.5 | PB07 | [SCRUM-129](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-129) | Lê Minh Trường Khả | 20 | 2026-10-26 | 2026-10-30 |
| 1.14 | PB08 | [SCRUM-65](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-65) | Phan Quang Hiếu | 25 | 2026-08-31 | 2026-09-08 |
| 1.15 | PB08 | [SCRUM-66](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-66) | Phan Quang Hiếu | 20 | 2026-09-02 | 2026-09-08 |
| 1.16 | PB08 | [SCRUM-67](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-67) | Nguyễn Văn Duy Mạnh | 15 | 2026-09-07 | 2026-09-10 |
| 1.17 | PB08 | [SCRUM-68](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-68) | Trần Hoài Nam | 10 | 2026-09-11 | 2026-09-15 |
| 1.18 | PB08 | [SCRUM-69](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-69) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 1.19 | PB09 | [SCRUM-70](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-70) | Phan Quang Hiếu | 25 | 2026-08-31 | 2026-09-08 |
| 1.20 | PB09 | [SCRUM-71](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-71) | Lê Minh Trường Khả | 15 | 2026-09-03 | 2026-09-08 |
| 1.21 | PB09 | [SCRUM-72](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-72) | Trần Viết Lộc | 15 | 2026-09-09 | 2026-09-14 |
| 1.22 | PB09 | [SCRUM-73](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-73) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 3.6 | PB10 | [SCRUM-130](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-130) | Phan Quang Hiếu | 15 | 2026-10-12 | 2026-10-15 |
| 3.7 | PB10 | [SCRUM-131](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-131) | Trần Viết Lộc | 15 | 2026-10-15 | 2026-10-20 |
| 3.8 | PB10 | [SCRUM-132](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-132) | Trần Viết Lộc | 10 | 2026-10-22 | 2026-10-26 |
| 3.9 | PB10 | [SCRUM-133](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-133) | Lê Minh Trường Khả | 10 | 2026-10-28 | 2026-10-30 |
| 2.14 | PB11 | [SCRUM-105](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-105) | Phan Quang Hiếu | 10 | 2026-09-21 | 2026-09-23 |
| 2.15 | PB11 | [SCRUM-106](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-106) | Phan Quang Hiếu | 15 | 2026-09-23 | 2026-09-28 |
| 2.16 | PB11 | [SCRUM-107](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-107) | Trần Hoài Nam | 10 | 2026-09-29 | 2026-10-01 |
| 2.17 | PB11 | [SCRUM-108](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-108) | Nguyễn Văn Duy Mạnh | 15 | 2026-10-01 | 2026-10-06 |
| 2.18 | PB11 | [SCRUM-109](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-109) | Lê Minh Trường Khả | 10 | 2026-10-07 | 2026-10-09 |
| 1.23 | PB12 | [SCRUM-74](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-74) | Nguyễn Văn Duy Mạnh | 25 | 2026-08-31 | 2026-09-08 |
| 1.24 | PB12 | [SCRUM-75](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-75) | Trần Hoài Nam | 20 | 2026-09-03 | 2026-09-09 |
| 1.25 | PB12 | [SCRUM-76](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-76) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-10 | 2026-09-14 |
| 1.26 | PB12 | [SCRUM-77](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-77) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-16 | 2026-09-18 |
| 1.27 | PB13 | [SCRUM-78](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-78) | Trần Hoài Nam | 20 | 2026-08-31 | 2026-09-04 |
| 1.28 | PB13 | [SCRUM-79](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-79) | Phan Quang Hiếu | 15 | 2026-09-03 | 2026-09-08 |
| 1.29 | PB13 | [SCRUM-80](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-80) | Trần Hoài Nam | 10 | 2026-09-10 | 2026-09-14 |
| 1.30 | PB13 | [SCRUM-81](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-81) | Lê Minh Trường Khả | 10 | 2026-09-16 | 2026-09-18 |
| 1.31 | PB14 | [SCRUM-82](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-82) | Nguyễn Văn Duy Mạnh | 10 | 2026-08-31 | 2026-09-02 |
| 1.32 | PB14 | [SCRUM-83](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-83) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-03 | 2026-09-07 |
| 1.33 | PB14 | [SCRUM-84](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-84) | Trần Hoài Nam | 10 | 2026-09-08 | 2026-09-10 |
| 1.34 | PB14 | [SCRUM-85](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-85) | Trần Hoài Nam | 10 | 2026-09-11 | 2026-09-15 |
| 1.35 | PB14 | [SCRUM-86](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-86) | Lê Minh Trường Khả | 5 | 2026-09-16 | 2026-09-18 |
| 2.19 | PB15 | [SCRUM-110](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-110) | Trần Hoài Nam | 25 | 2026-09-21 | 2026-09-29 |
| 2.20 | PB15 | [SCRUM-111](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-111) | Nguyễn Văn Duy Mạnh | 15 | 2026-09-23 | 2026-09-28 |
| 2.21 | PB15 | [SCRUM-112](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-112) | Trần Viết Lộc | 20 | 2026-09-28 | 2026-10-02 |
| 2.22 | PB15 | [SCRUM-113](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-113) | Trần Viết Lộc | 15 | 2026-10-01 | 2026-10-06 |
| 2.23 | PB15 | [SCRUM-114](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-114) | Lê Minh Trường Khả | 15 | 2026-10-06 | 2026-10-09 |
| 2.24 | PB16 | [SCRUM-115](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-115) | Nguyễn Văn Duy Mạnh | 15 | 2026-09-21 | 2026-09-24 |
| 2.25 | PB16 | [SCRUM-116](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-116) | Trần Viết Lộc | 15 | 2026-09-23 | 2026-09-28 |
| 2.26 | PB16 | [SCRUM-117](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-117) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-29 | 2026-10-01 |
| 2.27 | PB16 | [SCRUM-118](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-118) | Nguyễn Văn Duy Mạnh | 10 | 2026-10-02 | 2026-10-06 |
| 2.28 | PB16 | [SCRUM-119](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-119) | Lê Minh Trường Khả | 10 | 2026-10-07 | 2026-10-09 |
| 3.10 | PB17 | [SCRUM-134](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-134) | Nguyễn Văn Duy Mạnh | 20 | 2026-10-12 | 2026-10-16 |
| 3.11 | PB17 | [SCRUM-135](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-135) | Trần Viết Lộc | 20 | 2026-10-14 | 2026-10-20 |
| 3.12 | PB17 | [SCRUM-136](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-136) | Trần Viết Lộc | 15 | 2026-10-16 | 2026-10-21 |
| 3.13 | PB17 | [SCRUM-137](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-137) | Lê Minh Trường Khả | 10 | 2026-10-21 | 2026-10-23 |
| 3.14 | PB17 | [SCRUM-138](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-138) | Phan Quang Hiếu | 20 | 2026-10-22 | 2026-10-28 |
| 3.15 | PB17 | [SCRUM-139](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-139) | Lê Minh Trường Khả | 15 | 2026-10-27 | 2026-10-30 |
| 3.16 | PB18 | [SCRUM-140](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-140) | Trần Hoài Nam | 20 | 2026-10-12 | 2026-10-16 |
| 3.17 | PB18 | [SCRUM-141](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-141) | Nguyễn Văn Duy Mạnh | 15 | 2026-10-14 | 2026-10-19 |
| 3.18 | PB18 | [SCRUM-142](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-142) | Trần Hoài Nam | 10 | 2026-10-20 | 2026-10-22 |
| 3.19 | PB18 | [SCRUM-143](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-143) | Trần Viết Lộc | 10 | 2026-10-23 | 2026-10-27 |
| 3.20 | PB18 | [SCRUM-144](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-144) | Lê Minh Trường Khả | 10 | 2026-10-28 | 2026-10-30 |
| 4.1 | PB19 | [SCRUM-156](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-156) | Trần Hoài Nam | 20 | 2026-11-02 | 2026-11-06 |
| 4.2 | PB19 | [SCRUM-157](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-157) | Trần Hoài Nam | 20 | 2026-11-04 | 2026-11-10 |
| 4.3 | PB19 | [SCRUM-158](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-158) | Nguyễn Văn Duy Mạnh | 20 | 2026-11-06 | 2026-11-12 |
| 4.4 | PB19 | [SCRUM-159](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-159) | Trần Hoài Nam | 15 | 2026-11-10 | 2026-11-13 |
| 4.5 | PB19 | [SCRUM-160](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-160) | Trần Viết Lộc | 10 | 2026-11-13 | 2026-11-17 |
| 4.6 | PB19 | [SCRUM-161](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-161) | Lê Minh Trường Khả | 15 | 2026-11-17 | 2026-11-20 |
| 3.21 | PB20 | [SCRUM-145](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-145) | Nguyễn Văn Duy Mạnh | 20 | 2026-10-12 | 2026-10-16 |
| 3.22 | PB20 | [SCRUM-146](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-146) | Trần Viết Lộc | 15 | 2026-10-14 | 2026-10-19 |
| 3.23 | PB20 | [SCRUM-147](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-147) | Lê Minh Trường Khả | 15 | 2026-10-19 | 2026-10-22 |
| 3.24 | PB20 | [SCRUM-148](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-148) | Phan Quang Hiếu | 15 | 2026-10-22 | 2026-10-27 |
| 3.25 | PB20 | [SCRUM-149](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-149) | Lê Minh Trường Khả | 10 | 2026-10-28 | 2026-10-30 |
| 2.29 | PB21 | [SCRUM-120](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-120) | Trần Hoài Nam | 25 | 2026-09-21 | 2026-09-29 |
| 2.30 | PB21 | [SCRUM-121](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-121) | Nguyễn Văn Duy Mạnh | 20 | 2026-09-23 | 2026-09-29 |
| 2.31 | PB21 | [SCRUM-122](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-122) | Trần Viết Lộc | 15 | 2026-09-28 | 2026-10-01 |
| 2.32 | PB21 | [SCRUM-123](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-123) | Nguyễn Văn Duy Mạnh | 10 | 2026-10-02 | 2026-10-06 |
| 2.33 | PB21 | [SCRUM-124](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-124) | Lê Minh Trường Khả | 15 | 2026-10-06 | 2026-10-09 |
| 1.36 | PB22 | [SCRUM-87](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-87) | Lê Minh Trường Khả | 10 | 2026-08-31 | 2026-09-02 |
| 1.37 | PB22 | [SCRUM-88](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-88) | Lê Minh Trường Khả | 10 | 2026-09-03 | 2026-09-07 |
| 1.38 | PB22 | [SCRUM-89](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-89) | Lê Minh Trường Khả | 15 | 2026-09-07 | 2026-09-10 |
| 1.39 | PB22 | [SCRUM-90](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-90) | Nguyễn Văn Duy Mạnh | 10 | 2026-09-11 | 2026-09-15 |
| 1.40 | PB22 | [SCRUM-91](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-91) | Phan Quang Hiếu | 5 | 2026-09-16 | 2026-09-18 |
| 4.7 | PB23 | [SCRUM-162](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-162) | Lê Minh Trường Khả | 20 | 2026-11-02 | 2026-11-06 |
| 4.8 | PB23 | [SCRUM-163](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-163) | Phan Quang Hiếu | 30 | 2026-11-03 | 2026-11-12 |
| 4.9 | PB23 | [SCRUM-164](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-164) | Phan Quang Hiếu | 25 | 2026-11-06 | 2026-11-16 |
| 4.10 | PB23 | [SCRUM-165](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-165) | Lê Minh Trường Khả | 20 | 2026-11-11 | 2026-11-17 |
| 4.11 | PB23 | [SCRUM-166](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-166) | Phan Quang Hiếu | 15 | 2026-11-17 | 2026-11-20 |
| 3.26 | PB24 | [SCRUM-150](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-150) | Nguyễn Văn Duy Mạnh | 15 | 2026-10-12 | 2026-10-15 |
| 3.27 | PB24 | [SCRUM-151](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-151) | Trần Hoài Nam | 25 | 2026-10-13 | 2026-10-21 |
| 3.28 | PB24 | [SCRUM-152](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-152) | Trần Hoài Nam | 20 | 2026-10-16 | 2026-10-22 |
| 3.29 | PB24 | [SCRUM-153](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-153) | Trần Hoài Nam | 15 | 2026-10-20 | 2026-10-23 |
| 3.30 | PB24 | [SCRUM-154](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-154) | Nguyễn Văn Duy Mạnh | 15 | 2026-10-22 | 2026-10-27 |
| 3.31 | PB24 | [SCRUM-155](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-155) | Lê Minh Trường Khả | 20 | 2026-10-26 | 2026-10-30 |
| 4.12 | PB25 | [SCRUM-167](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-167) | Lê Minh Trường Khả | 20 | 2026-11-02 | 2026-11-06 |
| 4.13 | PB25 | [SCRUM-168](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-168) | Trần Viết Lộc | 30 | 2026-11-03 | 2026-11-12 |
| 4.14 | PB25 | [SCRUM-169](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-169) | Trần Hoài Nam | 30 | 2026-11-04 | 2026-11-13 |
| 4.15 | PB25 | [SCRUM-170](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-170) | Phan Quang Hiếu | 25 | 2026-11-06 | 2026-11-16 |
| 4.16 | PB25 | [SCRUM-171](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-171) | Trần Hoài Nam | 25 | 2026-11-09 | 2026-11-17 |
| 4.17 | PB25 | [SCRUM-172](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-172) | Trần Viết Lộc | 20 | 2026-11-12 | 2026-11-18 |
| 4.18 | PB25 | [SCRUM-173](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-173) | Nguyễn Văn Duy Mạnh | 30 | 2026-11-11 | 2026-11-20 |
| 4.19 | PB26 | [SCRUM-174](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-174) | Nguyễn Văn Duy Mạnh | 20 | 2026-11-02 | 2026-11-06 |
| 4.20 | PB26 | [SCRUM-175](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-175) | Nguyễn Văn Duy Mạnh | 15 | 2026-11-04 | 2026-11-09 |
| 4.21 | PB26 | [SCRUM-176](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-176) | Trần Viết Lộc | 20 | 2026-11-06 | 2026-11-12 |
| 4.22 | PB26 | [SCRUM-177](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-177) | Lê Minh Trường Khả | 25 | 2026-11-06 | 2026-11-16 |
| 4.23 | PB26 | [SCRUM-178](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-178) | Trần Viết Lộc | 20 | 2026-11-12 | 2026-11-18 |
| 4.24 | PB26 | [SCRUM-179](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-179) | Nguyễn Văn Duy Mạnh | 10 | 2026-11-18 | 2026-11-20 |

## Công việc bổ sung theo vòng đời dự án

| Mã | Jira | Nội dung | Owner | Start | Due |
|---|---|---|---|---|---|
| IN01 | [SCRUM-180](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-180) | Chốt Core MVP, stakeholder và requirements baseline | Nguyễn Văn Duy Mạnh | 2026-08-16 | 2026-08-21 |
| IN02 | [SCRUM-181](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-181) | Hoàn thiện SRS, PB01–PB26 và traceability ban đầu | Lê Minh Trường Khả | 2026-08-18 | 2026-08-29 |
| IN03 | [SCRUM-182](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-182) | Baseline kiến trúc, ADR và data model | Nguyễn Văn Duy Mạnh | 2026-08-16 | 2026-08-29 |
| IN04 | [SCRUM-183](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-183) | Repository, CI và môi trường tích hợp ban đầu | Trần Hoài Nam | 2026-08-16 | 2026-08-29 |
| IN05 | [SCRUM-184](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-184) | AI skeleton và hợp đồng thin vertical slice | Phan Quang Hiếu | 2026-08-20 | 2026-08-29 |
| IN06 | [SCRUM-185](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-185) | Consent/privacy và annotation plan ban đầu | Lê Minh Trường Khả | 2026-08-18 | 2026-08-29 |
| DOC01 | [SCRUM-186](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-186) | Rà soát và bàn giao Proposal | Lê Minh Trường Khả | 2026-08-25 | 2026-09-06 |
| DOC02 | [SCRUM-187](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-187) | Rà soát và bàn giao Project Plan v1.1 | Nguyễn Văn Duy Mạnh | 2026-09-25 | 2026-10-01 |
| DOC03 | [SCRUM-188](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-188) | Baseline UI Design và provenance màn hình | Trần Viết Lộc | 2026-10-05 | 2026-10-12 |
| DOC04 | [SCRUM-189](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-189) | Baseline Architecture v1.0 và integrity review | Nguyễn Văn Duy Mạnh | 2026-10-01 | 2026-10-14 |
| DATA11 | [SCRUM-190](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-190) | Mở rộng Gold Dataset và chốt frozen split | Lê Minh Trường Khả | 2026-09-20 | 2026-10-31 |
| RES01 | [SCRUM-191](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-191) | Rà soát nghiên cứu liên quan và protocol thí nghiệm | Phan Quang Hiếu | 2026-08-16 | 2026-08-29 |
| PILOT01 | [SCRUM-192](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-192) | Tích hợp end-to-end và pilot readiness | Nguyễn Văn Duy Mạnh | 2026-11-22 | 2026-11-27 |
| PILOT02 | [SCRUM-193](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-193) | Thử nghiệm với giáo viên/lớp mẫu và khảo sát | Lê Minh Trường Khả | 2026-11-26 | 2026-12-02 |
| PILOT03 | [SCRUM-194](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-194) | Tối ưu độ trễ và benchmark sau pilot | Phan Quang Hiếu | 2026-11-27 | 2026-12-04 |
| PILOT04 | [SCRUM-195](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-195) | Khắc phục lỗi trọng yếu và regression backend | Trần Hoài Nam | 2026-11-28 | 2026-12-05 |
| PILOT05 | [SCRUM-196](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-196) | Hoàn thiện UX Web/Mobile từ phản hồi pilot | Trần Viết Lộc | 2026-11-28 | 2026-12-05 |
| PILOT06 | [SCRUM-197](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-197) | Báo cáo stabilization và chốt acceptance scope | Nguyễn Văn Duy Mạnh | 2026-12-05 | 2026-12-06 |
| FINAL01 | [SCRUM-198](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-198) | Chốt source, Gold Dataset và release bàn giao | Nguyễn Văn Duy Mạnh | 2026-12-07 | 2026-12-12 |
| FINAL02 | [SCRUM-199](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-199) | Hoàn thiện bản thảo bài báo khoa học | Phan Quang Hiếu | 2026-12-07 | 2026-12-14 |
| FINAL03 | [SCRUM-200](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-200) | Hoàn thiện báo cáo Capstone và hồ sơ nghiệm thu | Lê Minh Trường Khả | 2026-12-07 | 2026-12-15 |
| FINAL04 | [SCRUM-201](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-201) | Video demo và bộ kịch bản trình diễn | Trần Viết Lộc | 2026-12-09 | 2026-12-15 |
| FINAL05 | [SCRUM-202](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-202) | Final regression và acceptance evidence | Trần Hoài Nam | 2026-12-10 | 2026-12-16 |
| FINAL06 | [SCRUM-203](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-203) | Chuẩn bị và rehearsal bảo vệ Capstone | Nguyễn Văn Duy Mạnh | 2026-12-14 | 2026-12-17 |
| FINAL07 | [SCRUM-204](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-204) | Bàn giao và biên bản nghiệm thu cuối | Trần Hoài Nam | 2026-12-16 | 2026-12-17 |
| SCRUM1 | [SCRUM-205](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-205) | Sprint 1: planning, daily/refinement, review & retrospective | Nguyễn Văn Duy Mạnh | 2026-08-30 | 2026-09-19 |
| SCRUM2 | [SCRUM-206](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-206) | Sprint 2: planning, daily/refinement, review & retrospective | Nguyễn Văn Duy Mạnh | 2026-09-20 | 2026-10-10 |
| SCRUM3 | [SCRUM-207](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-207) | Sprint 3: planning, daily/refinement, review & retrospective | Nguyễn Văn Duy Mạnh | 2026-10-11 | 2026-10-31 |
| SCRUM4 | [SCRUM-208](https://duymanhdnvn20092005.atlassian.net/browse/SCRUM-208) | Sprint 4: planning, daily/refinement, review & retrospective | Nguyễn Văn Duy Mạnh | 2026-11-01 | 2026-11-21 |

## Tài liệu nguồn

1. [Product/Sprint Backlogs](<D:/Capstone/Tài Liệu/Product_Backlog_with_4_Sprint_Backlogs_Book1_Format.xlsx>) — 26 PB và các sheet Sprint 1–4, cột B–G.
2. [Project Plan v1.1](<D:/Capstone/Tài Liệu/3. C1SE.01_Project_Plan.pdf>) — §4.1, bảng lịch ở trang PDF 12–14; §6 deadline tài liệu. Đã kiểm tra trực quan bảng lịch.
3. [Proposal](<D:/Capstone/Tài Liệu/1. C1SE.01.Capstone_Project_Proposal.pdf>) — FR/NFR/BR, gates, Definition of Done và architecture.
4. [UI Design](<D:/Capstone/Tài Liệu/C1SE.01_UI_Design_Document.docx>) — flows, states, accessibility, privacy và provenance screenshots.
5. [Architecture](<D:/Capstone/Tài Liệu/C1SE01_Architecture_Document.pdf>) — §§4–7, processing consistency, consent và data lifecycle.
6. [Hồ sơ NCKH](<D:/Capstone/Tài Liệu/DK_NCKH_C1SE01.docx>) — §4/§8 phân công, §§14–15 schedule/deliverables và research targets.

## Skills Applied

- `xlsx`
  - SKILL.md: `.agents/skills/xlsx/SKILL.md`
  - Why selected: Đọc và đối soát Product/Sprint Backlogs.
  - Applied to: trích xuất sheet/cell, 26 PB, 128 SB và tổng giờ.
- `docx`
  - SKILL.md: `.agents/skills/docx/SKILL.md`
  - Why selected: Đọc UI Design và hồ sơ NCKH.
  - Applied to: phân công chuyên môn, UX acceptance, research deliverables.
- `pdf`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-primary-runtime/pdf/26.1013.11914/skills/pdf/SKILL.md`
  - Why selected: Workspace registry không có skill PDF; dùng skill PDF đã cài.
  - Applied to: đọc Proposal/Plan/Architecture, render và kiểm tra bảng lịch.
