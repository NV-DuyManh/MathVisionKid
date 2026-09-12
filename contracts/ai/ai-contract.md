# MathVision AI Internal Contract

## Overview
This document defines the strict, authoritative internal contract between the Spring Boot Business Backend and the FastAPI AI Service / Celery Worker.

All internal endpoints require authentication via the `X-Internal-API-Key` header (development default: `secret-key-default`). Requests lacking or presenting an invalid key are rejected with `401 Unauthorized`.

---

## 1. Asynchronous Arithmetic Grading Pipeline

### Step 1.1: Job Enqueue (Spring Boot -> FastAPI)
`POST /internal/v1/jobs`

#### Request Headers
- `Content-Type: application/json`
- `X-Internal-API-Key: <key>`

#### Request Payload
```json
{
  "jobId": "30cb088f-48a0-42a5-8201-fcd07161437a",
  "submissionId": "bbd6f49c-7b4a-4ec2-b5c4-3071a0a4c3d9",
  "imageReference": "submissions/bbd6f49c-7b4a-4ec2-b5c4-3071a0a4c3d9_exercise.jpg",
  "allowedOperations": ["VERTICAL_ADDITION", "VERTICAL_SUBTRACTION"],
  "policyMode": "STUDENT",
  "callbackUrl": "http://localhost:8080/internal/v1/ai/jobs/30cb088f-48a0-42a5-8201-fcd07161437a/callback"
}
```

#### Response (202 Accepted)
```json
{
  "jobId": "30cb088f-48a0-42a5-8201-fcd07161437a",
  "status": "PENDING"
}
```

### Step 1.2: Asynchronous Worker Execution (Celery -> MinIO -> AI Models)
- Worker: Celery task `app.jobs.tasks.process_submission`
- Transport: Redis (`redis://localhost:6379/0`)
- Storage: MinIO bucket `mathvision`
- Execution:
  1. Image bytes fetched from MinIO object key.
  2. YOLOv8n inference detects digit and operator bounding boxes.
  3. Expression parser clusters rows and reconstructs arithmetic operation.
  4. Deterministic arithmetic validator computes expected result and error localization.

### Step 1.3: Asynchronous Callback (Celery Worker -> Spring Boot)
`POST {callbackUrl}` (e.g. `/internal/v1/ai/jobs/{jobId}/callback`)

#### Request Headers
- `Content-Type: application/json`
- `X-Internal-API-Key: <key>`

#### Request Payload
```json
{
  "status": "FEEDBACK_READY",
  "gradeProposal": {
    "suggestedScore": 10,
    "maxScore": 10,
    "confidence": 0.95,
    "isOfficial": false
  },
  "studentFeedback": {
    "title": "Bài làm chính xác!",
    "message": "Em đã thực hiện phép cộng rất tốt.",
    "subtext": "Giữ vững phong độ nhé!"
  },
  "evidence": [
    {
      "type": "CORRECT_STEP",
      "detail": "45 + 27 = 72"
    }
  ],
  "confidenceBundle": {
    "recognition": 0.92,
    "parsing": 0.95
  },
  "recognizedExercise": "45 + 27 = 72"
}
```

#### Terminal Status Routing in Spring Boot
- `FEEDBACK_READY` -> Submission status `FEEDBACK_READY` (Student immediate feedback)
- `PROPOSED_GRADE` -> Submission status `PROPOSED_GRADE` (Teacher batch review)
- `REVIEW_REQUIRED` / `OUT_OF_SCOPE` / `MODEL_NOT_AVAILABLE` -> Submission status `REVIEW_REQUIRED`
- `NEEDS_RETAKE` / `CROP_REQUIRED` -> Submission status `NEEDS_RETAKE`
- `NEEDS_CONFIRMATION` -> Submission status `NEEDS_CONFIRMATION`

*Note: AI output never sets `isOfficial: true`. Official grade finalization is reserved for teachers.*

---

## 2. Vietnamese Handwriting OCR Pilot Endpoints

### 2.1 Single-Line OCR Recognition
`POST /internal/v1/ocr/recognize-line`

Synchronously recognizes a single cropped line of Vietnamese handwriting using the frozen CRNN model (`best_cer.pth` + `vocab.json`).

#### Request Headers
- `Content-Type: image/jpeg` or `image/png` (Raw binary image bytes)
- `X-Internal-API-Key: <key>`

#### Response (200 OK)
```json
{
  "recognized_text": "Em tập viết chữ đẹp",
  "confidence": null
}
```
*Rule: `confidence` is strictly `null` (no fabricated heuristics).*

### 2.2 Multi-Line Line Segmentation Detection
`POST /internal/v1/ocr/detect-lines`

Synchronously detects horizontal text line bounding boxes on a page image using morphology and horizontal projection profiles.

#### Request Headers
- `Content-Type: image/jpeg` or `image/png` (Raw binary image bytes)
- `X-Internal-API-Key: <key>`

#### Response (200 OK)
```json
{
  "lines": [
    { "order": 1, "y": 22, "height": 42, "width": 320, "x": 30 },
    { "order": 2, "y": 72, "height": 42, "width": 320, "x": 30 },
    { "order": 3, "y": 127, "height": 42, "width": 320, "x": 30 }
  ],
  "count": 3
}
```
*Rule: Lines are ordered strictly top-to-bottom (`order` starting at 1).*
