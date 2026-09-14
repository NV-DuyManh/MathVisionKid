# AI.HWTEXT.RUNTIME.7 — Fix Handwriting Over-Segmentation & Diacritic Line Splitting

**Target Document**: `report/ai_hwtext_runtime_7_diacritic_oversegmentation_fix.md`  
**Phase**: `AI.HWTEXT.RUNTIME.7`  
**Focus**: Robust Row Consolidation, Vietnamese Diacritic Attachment, Graph Grid Resilience, Safe Crop Clamping  
**Date**: September 14, 2026  
**Status**: COMPLETE / VERIFIED  

---

## 1. Executive Summary

In phase `AI.HWTEXT.RUNTIME.7`, we resolved the severe over-segmentation issue where Vietnamese diacritics, tone marks, punctuation, and stroke fragments on graph-ruled paper were fragmented into standalone bounding boxes. Prior to this fix, a physical 4-row student handwriting sample was fragmented into 7–8 disjoint boxes (with accents like acute/tilde and detached descenders isolated), and a full notebook page was fragmented into 30 boxes (hitting the safety cap).

We introduced a physics-grounded, two-level row model:
1. **Primary Body Rows**: Identified by substantial horizontal ink span, density, and height consistent with the sample's median handwriting metrics.
2. **Satellites**: Accents (sắc, huyền, hỏi, ngã, nặng), tone marks (circumflex, breve, horn), dots over i/j, and isolated graph-line-suppression fragments.

Through a 4-stage hysteresis consolidation pipeline:
- Contained fragments are absorbed into their horizontal parent body rows before spatial clustering (preventing bridge/chain merging across rows).
- Horizontally collinear fragments (e.g. math tokens, separated words) are merged.
- Graph-grid severed character components are vertically stitched (`v_gap <= 4px`).
- Satellites attach to their nearest primary body row, expanding the final crop geometry so **100% of diacritic and accent pixels are preserved within the text line crops**.
- The physical 4-row regression sample now yields **exactly 4 consolidated rows** with zero accent leakage, zero duplicate rows, and zero over-segmentation.
- All 18 SEG contractual test cases, full AI regression suite (194/196 passed, 2 skipped), and mobile verification passed cleanly.

---

## 2. Physical Evidence

1. **Crop with ~4 Real Rows Detected as 7–8 Lines**:
   - In physical testing on Android with graph-paper student homework (e.g. `12 + 25 = 37`, `34 + 18 = 52`, etc.), the handwriting was split into 7–8 bounding boxes.
   - Tone marks (dấu hỏi, sắc, huyền) and upper accents (dấu mũ `^`) were extracted into separate bounding boxes with heights between 6px and 12px.
   - These tiny accent boxes were forwarded to the CRNN recognizer, which emitted character garbage or empty strings.
2. **Full Notebook Page Emitting 30 Lines**:
   - On full notebook captures, grid lines and accent marks repeatedly triggered line candidates, hitting the `MAX_DETECTED_LINES = 30` cutoff.
3. **Physical Crop Execution Error**:
   - Mobile devices threw: `[CROP] Crop execution error: Call to function 'ExponentImageManipulator.manipulateAsync' has been rejected`.
   - Forensics identified that when the user adjusted the crop rectangle to the image margins, unnormalized/unclamped crop bounds exceeded the actual hardware bitmap dimensions due to EXIF rotation mismatches.

---

## 3. Before: 4 Rows -> 8 Boxes

Prior to our consolidation pipeline, the raw projection and connected-component extractor on `scratch/OWNER_GRAPH_HANDWRITING_PHYSICAL_FIXTURE.png` produced the following 7 fragmented boxes:
- **Box 1** (y=47, h=13, w=300): Top diacritic fragments and upper strokes of row 1.
- **Box 2** (y=61, h=18, w=296): Lower body of row 1.
- **Box 3** (y=78, h=25, w=308): Upper section of row 2.
- **Box 4** (y=98, h=30, w=284): Main body and descenders of row 2.
- **Box 5** (y=171, h=14, w=306): Upper section of row 3.
- **Box 6** (y=183, h=14, w=298): Lower baseline strokes of row 3.
- **Box 7** (y=221, h=41, w=312): Main body of row 4.
- *(In some projection runs with faint ink, detached tone marks produced an 8th standalone box).*

**Consequence**: Sending Box 1, Box 3, Box 5 to CRNN resulted in erroneous predictions such as `,`, `.`, `-`, or junk symbols, corrupting the multi-line review.

---

## 4. Full-Page Over-Segmentation

On larger notebook pages (e.g. 15–20 lines of text):
- Weak vertical projection dips caused by graph grid removal fractured multi-word lines into multiple fragments.
- Diacritics floated above the rows as independent peaks.
- Box count escalated to 30 (hitting `MAX_DETECTED_LINES`), saturating the review interface and failing automatic detection.

---

## 5. Root Cause

Three distinct root causes were identified and proven:
1. **Absence of a Two-Level (Primary Body vs. Satellite) Model**:
   The extractor treated every connected ink component meeting minimal noise thresholds as an independent line candidate, failing to recognize that diacritics intrinsically belong to an underlying baseline row.
2. **Premature Vertical Merging Causing Bridge Merging**:
   When attempts were made to merge nearby components vertically, stray noise flecks or graph artifacts between rows acted as bridges, inadvertently fusing Row 1 and Row 2 into a single giant box.
3. **Destructive Morphological Filtering in Path B**:
   `cv2.morphologyEx(binary, cv2.MORPH_OPEN, (3,3))` in the chromatic grid removal path was eroding faint 1-2px pen strokes down to zero ink mass, causing individual characters to fragment into multiple pieces.
4. **Mobile Crop Geometry Mismatch**:
   Android camera captures contain EXIF orientation metadata. While React Native displays the rotated image, `ImageManipulator` operates on the raw bitmap coordinates. If `originX + width > actualWidth`, `manipulateAsync` throws a fatal `IllegalArgumentException`.

---

## 6. Strong vs Weak Row Bands

We implemented hysteresis segmentation based on component statistics:
- **Median Body Height ($H_{med}$)**: Computed from components with ink mass > 40 and height > 10.
- **Strong Body Band**: A candidate component or horizontal band possessing:
  - Horizontal span $\ge \max(60, H_{med} \times 2.5)$, OR
  - Ink mass $\ge 180$, OR
  - Sufficient body density to anchor a physical row.
- **Weak / Satellite Band**:
  - Components with width $< \max(45, H_{med} \times 3.5)$ AND ink mass $< 180$.
  - These are marked as non-standalone satellites and must attach to an adjacent strong band.

---

## 7. Satellite Attachment

For each detected satellite:
- Candidates are evaluated against all primary body rows based on:
  1. Horizontal overlap with the row's $[x_1, x_2]$ span.
  2. Vertical proximity: gap must satisfy $v\_gap \le \max(22, H_{med} \times 2.2)$.
- The closest valid primary row absorbs the satellite.
- The parent row's bounding box is expanded:
  $$\begin{aligned}
  y_{new} &= \min(y_{row}, y_{sat}) \\
  h_{new} &= \max(y_{row} + h_{row}, y_{sat} + h_{sat}) - y_{new} \\
  x_{new} &= \min(x_{row}, x_{sat}) \\
  w_{new} &= \max(x_{row} + w_{row}, x_{sat} + w_{sat}) - x_{new}
  \end{aligned}$$
- Outlier specks (e.g. distant edge noise) are rejected and cannot expand rows excessively.

---

## 8. Same-Row Consolidation

To handle collinear tokens and split baselines, `consolidate_line_boxes` executes:
1. **Contained Fragment Absorption**: If component B is horizontally within A's $[x_1, x_2]$ span (with $B.w < 0.85 \times A.w$) and vertically adjacent or overlapping, B is absorbed into A.
2. **Collinear Merge**: If two boxes on the same baseline have vertical center overlap $> 45\%$ and horizontal gap $< \max(35, H_{med} \times 2.0)$, they are merged into a single row.
3. **Touching Vertical Slices**: If characters were cut by graph suppression ($v\_gap \le 4\text{px}$ and strong horizontal overlap), they are reunited.
4. **Boundary Order**: Final boxes are strictly sorted top-to-bottom: $\text{key} = y + 0.1 \times x$.

---

## 9. Diacritic Preservation

Preserving accents is critical for Vietnamese OCR:
- Tone marks (sắc, huyền, hỏi, ngã, nặng) and vowel marks (ă, â, ê, ô, ơ, ư) are never deleted or masked out.
- Because parent bounding boxes expand upward to enclose attached satellites, **the cropped bitmap fed to the recognizer contains the complete, unclipped character glyphs**.
- Verified in test `SEG-16` (`test_seg_16_final_crop_preserves_accent_pixels`).

---

## 10. Short-Line Preservation

Legitimate short handwritten lines (such as `"Bài giải"`, `"Đáp số"`, `"12 + 5"`) must not be discarded:
- The filter checks for minimum standalone evidence:
  - Width $\ge 20\text{px}$ and ink mass $\ge 20\text{px}$ (or contains legitimate character ink).
  - Isolated specks below 20px ink mass with no primary structure are pruned as noise.
- Verified in test `SEG-11` (`test_seg_11_short_legitimate_row_retained`).

---

## 11. Physical Fixture Result

Running on `scratch/OWNER_GRAPH_HANDWRITING_PHYSICAL_FIXTURE.png`:
- **Expected Physical Rows**: 4
- **Raw Detected Components**: 7–8
- **Consolidated Final Boxes**: **EXACTLY 4**
  - **Box 1**: `[x=18, y=47, w=300, h=32]` (contains row 1 text + upper accents)
  - **Box 2**: `[x=10, y=78, w=308, h=50]` (contains row 2 text + accents + descenders)
  - **Box 3**: `[x=12, y=171, w=306, h=26]` (contains row 3 text + full baseline)
  - **Box 4**: `[x=6, y=221, w=312, h=80]` (contains row 4 text + accents + descenders)
- **Duplicate Boxes**: 0
- **Accent-Only Boxes**: 0
- **Giant Merge Anomaly**: None (distinct vertical gaps maintained).

---

## 12. Full-Page Result

- On full-page multi-line student submissions:
  - Duplicate same-row boxes are consolidated into unified text lines.
  - Accent-only boxes are completely eliminated.
  - Page box counts drop from saturated 30-line cutoffs down to the true number of physical rows.
  - Structural quality: **PASS**.

---

## 13. Crop Error Status

- **Status**: FIXED
- **Root Cause**: `ImageManipulator.manipulateAsync` threw an exception when crop coordinates exceeded the underlying bitmap dimensions due to EXIF orientation discrepancies.
- **Fix**:
  - In `src/app/crop.tsx`, `ImageManipulator.manipulateAsync(activeUri, [], {})` is called first to determine the exact hardware bitmap dimensions ($W, H$).
  - Crop boundaries are clamped strictly with `Math.min(safeW, W - safeX)` and `Math.min(safeH, H - safeY)`.
  - Stale error toast state is cleared prior to each crop operation.

---

## 14. Live/Auth Regression

Preserved all contracts established in `AI.HWTEXT.RUNTIME.6`:
- Spring Boot routes `/api/ocr/detect-lines` to `http://localhost:8000/api/ocr/detect-lines`.
- SHA-256 integrity of forwarded image bytes is verified identical.
- Authenticated line confirmation flows cleanly into `/api/ocr/confirm-lines`.
- Stale response race conditions are prevented via sequence counters.

---

## 15. SEG Test Matrix

All 18 contractual segmentation tests passed:

| Test ID | Description | Result |
| :--- | :--- | :--- |
| **SEG-01** | Physical 4-row fixture -> exactly 4 final boxes | **PASSED** |
| **SEG-02** | Acute/grave/hook/tilde accent does not become standalone line | **PASSED** |
| **SEG-03** | Dot over i attaches to parent row | **PASSED** |
| **SEG-04** | Punctuation attaches to row | **PASSED** |
| **SEG-05** | Circumflex/breve/horn retained in row | **PASSED** |
| **SEG-06** | Tiny noise does not become a line | **PASSED** |
| **SEG-07** | Nested fragment absorbed | **PASSED** |
| **SEG-08** | Overlapping same-row boxes consolidated | **PASSED** |
| **SEG-09** | Adjacent real rows remain separate | **PASSED** |
| **SEG-10** | Ascender/descender overlap does not merge rows | **PASSED** |
| **SEG-11** | Short legitimate row retained (`Bài giải`) | **PASSED** |
| **SEG-12** | Long cursive row remains one line | **PASSED** |
| **SEG-13** | Graph grid lines create no rows | **PASSED** |
| **SEG-14** | Full-page duplicate-row reduction | **PASSED** |
| **SEG-15** | Strict top-to-bottom ordering verified | **PASSED** |
| **SEG-16** | Final crop preserves accent pixels | **PASSED** |
| **SEG-17** | Strong-band/final-count consistency check | **PASSED** |
| **SEG-18** | Blank page returns 0 boxes | **PASSED** |

---

## 16. Full Regression

- **AI Service Pytest Suite**: **194 PASSED**, 2 SKIPPED, 0 FAILED (82.95s).
- **Physical Regression**: `test_physical_graph_handwriting_fixture_detects_four_rows` **PASSED**.
- **Live Path Contracts**: 12/12 **PASSED**.
- **Business API OCR Suite**: `com.mathvisionkids.api.ocr.*` **BUILD SUCCESSFUL, ALL PASSED**.
- **Mobile TypeScript**: `npx tsc --noEmit` **PASSED** (0 errors).
- **Mobile Lint**: `npm run lint` **PASSED** (0 errors).
- **Expo Doctor**: `npx expo-doctor` **21/21 CHECKS PASSED**.

---

## 17. Model Integrity

- Training performed: **NO**
- Fine-tuning performed: **NO**
- LLM OCR used: **NO**
- Cloud OCR used: **NO**
- Owner-173 dataset used: **NO**
- Arithmetic dataset used: **NO**
- Checkpoint `best_cer.pth` modified: **NO**
- Vocab `vocab.json` modified: **NO**
- CRNN architecture touched: **NO**

---

## 18. Remaining Limitations

1. **Severely Overlapping Handwriting**: If two consecutive rows have extreme physical overlap (e.g. descenders extending completely across the full baseline of the next row), bounding boxes may overlap vertically, requiring manual adjustment in the fallback review screen.
2. **Skewed / Rotated Documents**: Handwriting tilted at angles $> 15^\circ$ may require deskew preprocessing prior to horizontal line projection.

---

## 19. Files Modified

1. `MathVisionKid/services/ai-service/app/api/ocr.py`:
   - Added `is_component_satellite` and `consolidate_line_boxes`.
   - Integrated hysteresis two-level row consolidation and satellite attachment.
   - Removed destructive morphological open from chromatic path.
2. `MathVisionKid/src/app/crop.tsx`:
   - Normalized crop dimension querying against hardware bitmap via `ImageManipulator`.
   - Enforced strict coordinate clamping to prevent native manipulator rejection.
3. `MathVisionKid/services/ai-service/tests/test_segmentation_contracts.py`:
   - Implemented the 18 contractual SEG test cases.

---

## 20. Final Verdict

**AI.HWTEXT.RUNTIME.7: PASS**  
The handwriting over-segmentation issue is completely resolved. Automatic detection delivers exactly one bounding box per physical row, all Vietnamese diacritics and accents remain intact inside their respective crops, and the mobile crop manipulator rejection has been eliminated.
