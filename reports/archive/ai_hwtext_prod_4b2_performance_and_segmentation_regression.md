# AI.HWTEXT.PROD.4B.2 — PERFORMANCE + SEGMENTATION REGRESSION CLOSURE

## SKILL ROUTING
Task domains: Computer Vision, Handwriting Pipeline, AI integration, Backend Arbitration
Skills matched: none
Skills loaded: none

## 0. PHYSICAL EVIDENCE TRUTHFULNESS
- **Physical 12-line fixture:** `FIXTURE_UNAVAILABLE` in automated test suite.
- **Physical 2-line regression:** Root cause verified in code (`is_mobile_ui`).
- **Owner Retest:** REQUIRED. We cannot simulate the physical photo crop locally.

## 1. SEGMENTATION REGRESSION FIX (10/12 Lines Dropped)
**Root Cause:**
In `app/api/generalized_pipeline.py`, the `is_mobile_ui` heuristic (triggered when aspect ratio $\ge 1.8$) dropped all bounding boxes below `img_h * 0.17`. A physical phone photo of an A4 page typically exceeds a 1.8 aspect ratio, causing valid lower text lines to be wrongly classified as mobile UI clutter and discarded.

**Fix:**
Removed the `is_mobile_ui` layout drop condition entirely. 

## 2. LLM BATCH OPTIMIZATION (1 Request Per Document)
**Root Cause:**
The pipeline looped 11 times for 11 lines, triggering sequential/concurrent crop-based LLM requests. The instruction explicitly required maximum 1 request to Groq and 1 to Gemini for the entire image.

**Fix:**
- Added `app/integrations/groq/document_corrector.py` and `app/integrations/gemini/document_corrector.py`.
- Built `request_document_groq_correction` and `request_document_gemini_correction`.
- These correctors draw an overlay of all triggered bounding boxes (with Line IDs) onto the full-page image.
- A single API call per provider asks the LLM to return a structured JSON dictionary mapping each `line_id` to its correction.
- Refactored `ocr.py` (Pass 2) to await exactly one Groq and one Gemini task, then distribute the parsed JSON map back to the individual `LineBox` models.

## 3. ARBITRATION BADGE MISMATCH ("Bó hoa sim tímm")
**Root Cause:**
The user reported: *Current result vẫn = OCR gốc "Bó hoa sim tímm" nhưng có Đề xuất tin cậy cao...*
In `app/api/ocr.py`, even if the AI suggestion achieved high confidence and was marked `AUTO_APPLY_SAFE` or `AUTO_APPLY`, the code aggressively hardcoded `line.correctionApplied = False` and `line.finalText = line.rawOcrText`. The frontend correctly rendered the AI suggestion badge in the suggestions array, but the main line text payload was wrongly blocked by the backend.

**Fix:**
Corrected the assignment block in `ocr.py`:
```python
if canonical_groq_dec in ("AUTO_APPLY_SAFE", "AUTO_APPLY"):
    line.correctionApplied = True
    line.finalText = line.correctedText
    any_correction_applied = True
else:
    line.correctionApplied = False
    line.finalText = line.rawOcrText
```

## 4. ACCEPTANCE CRITERIA CHECKLIST
- [x] Restore 12-line detection (removed `is_mobile_ui` crop trap).
- [x] Tối đa 1 request Groq, 1 request Gemini (Batch processing implemented).
- [x] Sửa lỗi Arbitration (AUTO_APPLY giờ đã được ghi đè text).
- [x] TypeScript Green (`ExitCode 0`).
- [x] Python Compile Green (`ExitCode 0`).
- [x] Không sửa codebase đoán mò (chỉ sửa các config/logic sai rõ ràng).
- [x] Không commit/push.

**BLOCKER FOR FINAL ACCEPTANCE:**
- This phase requires the Owner to run a physical end-to-end device test to confirm the 12 lines map perfectly to the Batch AI Correctors on the physical device.

## Skills Applied
`Skills Applied: None — no installed skill under .agents/skills/ matched this task.`
