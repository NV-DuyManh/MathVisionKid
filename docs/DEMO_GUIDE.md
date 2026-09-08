# MathVision Kids -- Local Demonstration Guide

This guide describes how to run a complete end-to-end local demonstration of the MathVision Kids platform using deterministic fixture evaluation.

---

## 1. Demo Mode Architecture

In local demonstration mode:
- **Spring Boot API** executes real database transactions, batch orchestration, JWT authentication, and privacy gates.
- **MinIO Object Storage** persists real image binaries in private S3 buckets.
- **FastAPI AI Runtime** ingests async job requests, validates payloads, and enqueues tasks.
- **Redis & Celery Worker** execute async background processing and dispatch authenticated HTTP callbacks back to Spring Boot.
- **Fixture Recognition Engine** provides deterministic, reproducible math recognition without requiring trained deep learning weights (`RUNTIME_MODE=FIXTURE`, `MODEL_ARTIFACT=NOT_PROVIDED`).
- **Deterministic Validators** calculate real column-by-column arithmetic proofs (addition carries, subtraction borrows).

---

## 2. Seeded Demo Accounts & Data

When running with `--spring.profiles.active=dev`, Spring Boot automatically seeds:

### Teacher Account
- **Email:** `lan.teacher@mathvision.local`
- **Password:** `MathVision123!`
- **Display Name:** `Ms. Lan`

### Demo Classroom ("Lớp 3A")
A Grade 3 classroom with 11 synthetic students ready for batch assignment demonstration:
1. `minh.student@mathvision.local` -- Nguyễn Bình Minh
2. `an.student@mathvision.local` -- Trần Văn An
3. `binh.student@mathvision.local` -- Lê Thanh Bình
4. `cuong.student@mathvision.local` -- Phạm Quốc Cường
5. `dung.student@mathvision.local` -- Hoàng Ngọc Dũng
6. `giang.student@mathvision.local` -- Vũ Hương Giang
7. `ha.student@mathvision.local` -- Đỗ Thu Hà
8. `khoa.student@mathvision.local` -- Bùi Anh Khoa
9. `linh.student@mathvision.local` -- Ngô Phương Linh
10. `mai.student@mathvision.local` -- Đặng Tuyết Mai
11. `nam.student@mathvision.local` -- Dương Nhật Nam

### Supported Demo Assignments
- **Bài tập Phép Cộng Dọc** (`VERTICAL_ADDITION`, Max Score: 10)
- **Bài tập Phép Trừ Dọc** (`VERTICAL_SUBTRACTION`, Max Score: 10)

---

## 3. Deterministic Fixture Scenarios

The AI pipeline reacts deterministically based on image references or file naming:

| Scenario | Trigger Keyword in File / Reference | Pipeline Result | Teacher Decision Status | Student Feedback |
| :--- | :--- | :--- | :--- | :--- |
| **Valid Addition** | Default / `clean-addition` | `12 + 34 = 46` | `PROPOSED_GRADE` (10/10) | Correct |
| **Addition Carry Mistake** | `addition-carry-error` | `45 + 27 = 62` (missed carry) | `PROPOSED_GRADE` (0/10 + evidence) | Hint on column carry |
| **Subtraction Borrow Mistake** | `subtraction-borrow-error` | `52 - 18 = 44` (missed borrow) | `PROPOSED_GRADE` (0/10 + evidence) | Hint on column borrow |
| **Ambiguous Handwriting** | `ambiguous` | Digit confidence `< 0.5` | `REVIEW_REQUIRED` | Confirmation requested |
| **Blurry / Dark Image** | `quality-blur` or `quality-dark` | Quality gate trigger | `NEEDS_RETAKE` | Prompt to retake photo |
| **Incomplete Crop** | `quality-incomplete-crop` | Quality gate trigger | `CROP_REQUIRED` | Prompt to re-crop |
| **Out-of-Scope Content** | `out-of-scope` | Fractions / Geometry | `OUT_OF_SCOPE` | Unsupported operation message |

---

## 4. Complete Step-by-Step Demonstration Flow

### Step 1: Start the Local Stack
Open Command Prompt or PowerShell:
```cmd
scripts\start-all.bat
```
Wait until the output concludes with `READY_FOR_DEMO`.

### Step 2: Verify Diagnostics
Confirm all services are healthy:
```cmd
scripts\health-check.bat
```

### Step 3: Open Teacher Web Portal
Navigate to [http://localhost:5173](http://localhost:5173) in your browser.

### Step 4: Log In as Teacher
- Email: `lan.teacher@mathvision.local`
- Password: `MathVision123!`
- Click **Sign In**.

### Step 5: Explore the Teacher Dashboard
- Observe active classes (including **Lớp 3A**).
- Observe assignments (**Bài tập Phép Cộng Dọc**).

### Step 6: Create a Batch
1. Click **Batches** in the navigation bar.
2. Click **Create New Batch**.
3. Select **Lớp 3A** and assignment **Bài tập Phép Cộng Dọc**.
4. Click **Create Batch**.

### Step 7: Upload Submissions & Map Students
1. Drag & drop or select images to upload (sample images from root: `test_image.jpg`, `retry_image.jpg`).
2. Map each uploaded submission to a student in Lớp 3A from the dropdown list.

### Step 8: Batch Privacy Gate
1. Inspect the uploaded items.
2. Confirm the privacy editor allows verifying that student PII (names, personal information outside math problem bounds) is masked or cropped before analysis.
3. Click **Submit Batch for AI Analysis**.

### Step 9: Observe Async AI Processing
1. In the batch overview, watch the status transition:
   `QUEUED` -> `PROCESSING` -> `COMPLETED`.
2. Spring Boot sent asynchronous jobs to FastAPI.
3. Celery executed the validation pipelines.
4. Celery posted signed callbacks to Spring Boot, which persisted `AnalysisResult` entities.

### Step 10: Review-by-Exception
1. Navigate to the **Review Queue**.
2. Notice the intelligent classification:
   - Confident submissions receive `PROPOSED_GRADE` (advisory score 10/10 for correct; advisory score 0/10 with detailed carry error diagnosis for mistakes).
   - Ambiguous or low-confidence submissions are routed to `REVIEW_REQUIRED`.
3. Click into a submission:
   - View the recognized tokens.
   - View arithmetic validation proofs.
   - Accept the proposed grade or enter an overridden final score and feedback note.
   - Click **Submit Teacher Decision**.

### Step 11: Optional Student Mobile Flow
1. In another terminal, run: `npm start`.
2. Open the app via Expo Go or web preview.
3. In the Home Screen, tap **"Demo Mocks (For Testing)"** to view how students receive interactive step-by-step hints and token confirmations.

### Step 12: Clean Shutdown
When finished with the demo, stop all services cleanly:
```cmd
scripts\stop-all.bat
```
