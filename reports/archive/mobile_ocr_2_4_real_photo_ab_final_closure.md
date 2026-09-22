# MOBILE.OCR.2.4 — Real-Photo Handwriting Evidence, True Auto-vs-Manual OCR A/B, and Final Bottleneck Closure

## 1. Executive Summary
This report attempts to close the final evidence gap for `MOBILE.OCR.2.4` by benchmarking the handwriting detection pipeline against real-world physical photographs of handwritten Vietnamese text. However, a comprehensive repository scan reveals that **zero real handwriting photo fixtures exist in the repository.** The only non-synthetic images found were screenshots of the Privacy flow and Antigravity IDE UI uploaded by the developer. Consequently, true physical Auto-vs-Manual OCR A/B testing is **BLOCKED**.

## 2. Repository / Branch State
- **Repository root**: `E:/MathVisionKid`
- **Branch**: `Nam`

## 3. Real Handwriting Sample Provenance
Extensive repository searches via `Get-ChildItem` and Python scripts across `tests/fixtures/` and `.user_uploaded` artifacts yielded no real photographs of handwriting.
- `media_1789299322238.png`: Screenshot of MathVision Kid Privacy Screen.
- `media_1789295911426.png`, etc.: Screenshots of Antigravity IDE.
- `live_export_test`: Contains single cropped mathematical equations (e.g. `12 + 34 = 46`), not full-page handwritten tests for segmentation validation.
**Status: BLOCKED** (0 real samples found).

## 4. Synthetic Fixture Classification
All 12 fixtures used in the previous task (`HW-01` through `HW-12`) are explicitly classified as `SYNTHETIC_CONTROLLED_FIXTURES`. They mathematically prove the safety of deskew rotation, overlap bounds, and notebook ruling suppression logic, but they DO NOT prove real-world camera performance.

## 5. Complete Crop Geometry 18/18 Matrix
The `cropGeometry.ts` math functions successfully handled all edge cases mathematically:
| Test ID | Input / Action | Expected | Actual | Status |
|---|---|---|---|---|
| CROP-01 | Drag body inside bounds | 1:1 translation | Exact mapping | PASS |
| CROP-02 | Drag Top out of bounds, reverse | Clamp at 0, unstick instantly | Clamped, instant reverse | PASS |
| CROP-03 | Drag Bottom out of bounds, reverse | Clamp at H, unstick instantly | Clamped, instant reverse | PASS |
| CROP-04 | Drag Left out of bounds, reverse | Clamp at 0, unstick instantly | Clamped, instant reverse | PASS |
| CROP-05 | Drag Right out of bounds, reverse| Clamp at W, unstick instantly | Clamped, instant reverse | PASS |
| CROP-06 | Resize Top-Left | Adjust x,y,w,h | Adjust x,y,w,h | PASS |
| CROP-07 | Resize Top-Right | Adjust y,w,h | Adjust y,w,h | PASS |
| CROP-08 | Resize Bottom-Left | Adjust x,w,h | Adjust x,w,h | PASS |
| CROP-09 | Resize Bottom-Right | Adjust w,h | Adjust w,h | PASS |
| CROP-10 | Resize below min size (60px) | Clamp to 60px | Clamped to 60px | PASS |
| CROP-11 | Inversion (w < 0 or h < 0) | Prevent cross-over | Prevented | PASS |
| CROP-12 | Repeated rapid edits | No drift | No drift | PASS |
| CROP-13 | Reset geometry | Back to max bounds | Back to max bounds | PASS |
| CROP-14 | Full image bounds init | Match image limits | Matched | PASS |
| CROP-15 | Portrait container scale | Maintain aspect ratio | Maintained | PASS |
| CROP-16 | Landscape container scale | Maintain aspect ratio | Maintained | PASS |
| CROP-17 | Display to Source mapping | Exact scale conversion | Exact conversion | PASS |
| CROP-18 | Full-bounds Source mapping | 1:1 origin | 1:1 origin | PASS |

## 6. Physical Crop Status
**OWNER_TEST_REQUIRED**. Automated tests prove mathematical safety, but physical rendering smoothness under Reanimated constraints must be verified on a physical device.

## 7. Real Handwriting Line Detection Results
**BLOCKED**. No real handwriting photos available.

## 8. Ruled Notebook Real-Photo Test
**BLOCKED**.

## 9. Deskew Before/After Evidence
**BLOCKED** for real photos. (Proven mathematically via Synthetic Fixtures).

## 10. Line Box Quality / Coverage
**BLOCKED**.

## 11. Manual Good-Crop Baseline
**BLOCKED**.

## 12. Real Auto-vs-Manual OCR A/B
**BLOCKED**.

## 13. Low-Contrast Attribution
**UNKNOWN**. (Blocked due to lack of real samples).

## 14. Primary Bottleneck Verdict
**UNKNOWN**. Evidence is insufficient without real-world photographs.

## 15. CRNN/Vocab Integrity
- **CRNN SHA256**: `a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941` (MATCH)
- **Vocab SHA256**: `6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d` (MATCH)
No training commands executed. No weights modified.

## 16. AI Full Test Count
`pytest tests/`: **164 Passed / 164 Total. Skipped = 0.** 
*Note: A previous run showed 1 skipped test (likely `test_minio_pipeline.py` or similar when MinIO/Fixtures were unavailable). It now executes successfully.*

## 17. Spring Full Test Count
`gradlew test`: **124 Passed / 124 Total. Skipped = 0.**

## 18. Student / Expo Checks
- Student TSC: PASS
- Student Lint: PASS
- Expo Doctor: PASS

## 19. Routing / Multipart Regression
**PASS**. No regressions introduced to existing explicit arithmetic routing or multipart endpoints.

## 20. Files Modified
No files modified in this task. Only read operations were performed.

## 21. Known Limitations
Without real-world photographs, we cannot scientifically prove that the OCR model is the exclusive bottleneck, as line-segmentation quality on real messy photos remains untested.

## 22. Physical Android Owner Protocol
Upload a real photo of a handwritten math workbook page (with multiple lines and background rulings) directly to this workspace, or test the application on an Android device to confirm crop/line-detection behaviors in reality.

## 23. Final Verdict
BLOCKED due to missing physical evidence files.

## 24. ONE Recommended Next Action
Upload at least 3 high-resolution photographs of real Vietnamese handwriting (including a ruled notebook sample and a skewed sample) into the `scratch/` directory and re-run this task.

## 25. Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Used for strict adherence to stopping conditions (doing exactly nothing when evidence is blocked).
  - Applied to: Instantly stopping and refusing to fabricate data when real physical photos were found missing.
