# Owner Physical Retest Checklist: Vietnamese Handwriting OCR Pipeline

**Phase:** `AI.HWTEXT.PROD.4B.2R4-FINAL`  
**Evaluation Scope:** Final Pre-Physical Engineering Gate Closure  
**Target:** Owner On-Device Physical Execution (iPhone / Android Physical Hardware)  
**Status:** `OWNER_RETEST_REQUIRED` (Automated pre-physical gate PASSED; physical testing required)

---

> [!IMPORTANT]
> **PHYSICAL VERDICT POLICY**  
> Physical verification CANNOT be automated or fabricated. Every check below requires manual execution on an actual physical mobile device under natural lighting.

---

## Retest Matrix & Execution Steps

| Step # | Test Item | Action / Procedure | Expected Verification Criteria | Physical Result |
|:---:|---|---|---|:---:|
| **1** | **App Boot & Initialization** | Launch MathVision Kids from home screen. | Splash screen dismisses cleanly; Home dashboard loads within 1.5s; 0 red screens or unhandled exceptions. | `[ ] PASS / [ ] FAIL` |
| **2** | **Direct System Picker** | On Home dashboard, tap **"Chọn từ thư viện"** button. | **Direct System Image Picker opens immediately.** NO intermediate `/gallery` screen or "Ảnh gần đây" navigation appears. Selected photo proceeds directly to `/privacy`. | `[ ] PASS / [ ] FAIL` |
| **3** | **Privacy Masking (4 Consecutive Masks)** | On `/privacy`, draw Mask 1, tap Commit. Draw Mask 2, tap Commit. Draw Mask 3, tap Commit. Draw Mask 4, tap Commit. | Live preview active during drawing. Previous committed masks remain visible and persistent. Snapshot output includes all 4 black privacy rectangles. | `[ ] PASS / [ ] FAIL` |
| **4** | **Crop Session Reset (Image A $\to$ Image B)** | On crop screen, select Image A and drag crop box narrowly. Return to Home and select Image B. | **Image B opens with clean, full-page crop default.** The narrow crop rectangle from Image A is completely discarded (`cropTouchedByUser=false`). | `[ ] PASS / [ ] FAIL` |
| **5** | **12-Line Poem Document** | Photograph a physical handwritten 12-line poem. Proceed to segmentation. | **All 12 legitimate handwriting lines are segmented.** Zero lines collapsed, zero false-positive phantom lines from margins. | `[ ] PASS / [ ] FAIL` |
| **6** | **New Handwriting Page (Unseen Notebook)** | Capture a completely new notebook page with ruling lines and handwriting. | Ruling lines are cleanly suppressed. Handwriting crossing printed lines remains fully detected. Exactly $N$ lines detected. | `[ ] PASS / [ ] FAIL` |
| **7** | **OCR Quality Inspection** | Inspect raw local OCR output across all lines. | Local CRNN renders immediately (< 800ms) without waiting for network advisors. Text is legible Vietnamese with proper diacritics. | `[ ] PASS / [ ] FAIL` |
| **8** | **Ambiguity Case ("Bó" vs "Có" / Duplicated Final)** | Inspect Line 2 or ambiguous cursive capital letters. | If visual evidence has narrow margin ($<0.05$), status is `NEEDS_REVIEW`. No silent hallucination of ungrounded tokens. Stutter error (e.g. `tímm`) is resolved to `tím`. | `[ ] PASS / [ ] FAIL` |
| **9** | **Async Suggestions (Mounted Screen)** | Keep the review screen open without navigating away while AI advisors finish. | Initial OCR is immediately editable. AI suggestions appear dynamically within 3–8s on the mounted screen without requiring a reload. | `[ ] PASS / [ ] FAIL` |
| **10** | **Manual Edit Precedence** | Manually edit Line 1 text BEFORE cloud advisors return. | When advisor suggestions arrive, the student's manual edit is **NOT overwritten**. `selectedSource` remains `'MANUAL_EDIT'`. | `[ ] PASS / [ ] FAIL` |
| **11** | **High-Confidence Badge Semantics** | Observe badge icons and labels next to suggestions. | Single-provider suggestion displays *"Gợi ý AI"*. Exact independent consensus with strong support displays *"Đề xuất tin cậy cao"*. | `[ ] PASS / [ ] FAIL` |
| **12** | **True Re-detect Safety** | Tap "Nhận diện lại" (True Re-detect) on the line editor screen. | `requestId` and `detectionRunId` refresh. If the re-detect yields a lower quality score, the superior standard segmentation is preserved. | `[ ] PASS / [ ] FAIL` |
| **13** | **Provider Outage Resilience** | Enable Airplane mode or block external network while running OCR. | Local OCR continues to work instantly. Advisors gracefully show network offline warning. No app freeze or unhandled promise rejection. | `[ ] PASS / [ ] FAIL` |
| **14** | **Whole-Document Text Consistency** | Tap "Xác nhận toàn bộ bài làm" and proceed to Submission Summary. | Full document text matches line-by-line confirmed state. No synthetic third strings or interpolated words. | `[ ] PASS / [ ] FAIL` |
| **15** | **Zero Debug UI / Student Privacy** | Review all student-facing screens for technical leaks. | **ZERO developer strings visible.** No ports, localhost, FastAPI, MinIO, Redis, Spring Boot, Groq, Gemini, model weights, or tokens. | `[ ] PASS / [ ] FAIL` |

---

## Final Owner Retest Sign-off

- **Tester Name:** ___________________________  
- **Device Model & OS:** ___________________________  
- **Test Date:** ___________________________  
- **Physical Test Verdict:** `[ ] PASS  /  [ ] FAIL  /  [X] OWNER_RETEST_REQUIRED`  
- **Notes / Observations:**
