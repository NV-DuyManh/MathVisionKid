# AI.HWTEXT.RUNTIME.8 — General Satellite Filtering & Handwriting Row Consolidation Fix

**Project**: MathVision Kids  
**Task**: AI.HWTEXT.RUNTIME.8 — General Satellite Filtering & Handwriting Row Consolidation  
**Date**: 2026-09-14  
**Status**: COMPLETE / VERIFIED  
**Constraints**: NO training, NO fine-tuning, NO LLM/Cloud OCR, NO dataset changes, NO model/vocab changes, NO commit, NO push  

---

## 1. Root Cause

Three distinct root causes produced over-segmentation where real handwritten rows were split into multiple boxes:

### 1.1 Missing Primary Body Evidence Gate
The original `consolidate_line_boxes` emitted every contour that survived a minimal noise threshold (`ink < 20 AND w < 20`) as a standalone line. Vietnamese diacritics (sắc, huyền, hỏi, ngã, nặng), vowel marks (â, ă, ê, ô, ơ, ư), dots over i/j, punctuation, and detached pen strokes all exceeded that threshold and became false standalone line boxes.

### 1.2 No Explicit Satellite-to-Primary Attachment Phase
Without a dedicated attachment pass, a satellite component (accent mark, tone mark, graph fragment) positioned away from its parent text row — but too large for the noise filter — was emitted as an independent line box. This was the direct cause of 4 real rows → 5–8 detected boxes.

### 1.3 Destructive 3×3 Morphological Open in Chromatic Path
In `run_grid_handwriting_detection`, a `cv2.morphologyEx(binary, MORPH_OPEN, (3,3))` applied to the chromatic ink mask was eroding thin 1–2px pen strokes to zero ink mass, causing single characters to fragment into multiple disconnected pieces. This was restricted to the grayscale fallback path only.

---

## 2. Algorithm Changes

### 2.1 `has_primary_body_evidence(w, h, ink, median_h) → bool`
A new function that determines whether a bounding box has sufficient evidence to anchor a text line. Uses three adaptive criteria based on `median_h` (the median component height for the current image):

| Criterion | Condition |
| :--- | :--- |
| **Wide-span text** | $w \ge \max(60, median\_h \times 2.8)$ AND $ink \ge \max(90, median\_h \times 4.5)$ |
| **Dense ink mass** | $ink \ge \max(160, median\_h \times 8.0)$ |
| **Normal body row** | $h \ge \max(13, median\_h \times 0.65)$ AND $ink \ge \max(45, median\_h \times 2.2)$ AND $w \ge \max(20, median\_h \times 0.9)$ |

All thresholds are **relative to `median_h`**, adapting to different image scales, paper types, and handwriting sizes. Nothing is hardcoded to a specific image.

### 2.2 `is_component_satellite(w, h, ink, median_h) → bool`
Simplified to: `return not has_primary_body_evidence(w, h, ink, median_h)`. A box is a satellite if and only if it lacks primary body evidence.

### 2.3 Updated `consolidate_line_boxes` — Three-Stage Pipeline

**Stage 1: Contained Fragment Absorption** (unchanged)  
Small specks horizontally inside a larger parent's span are absorbed into the parent, preventing them from acting as bridge mergers between rows.

**Stage 2: Multi-Pass Row Consolidation** (unchanged)  
Four merge cases run iteratively:
1. **Collinear word merge**: y-center proximity and vertical overlap
2. **Touching vertical splits**: graph-line-severed characters with v_gap ≤ 5px
3. **Satellite attachment**: accent/diacritic within v_gap ≤ max(25, median_h × 2.5) attaches to nearest primary row
4. **Contained fragment/accent band absorption**: strong horizontal overlap + height asymmetry

**Stage 3: Primary/Satellite Partition & Attachment** (NEW in RUNTIME.8)  
After consolidation, every remaining box is classified:
- **Primary**: has primary body evidence → becomes a final line box
- **Satellite**: lacks primary body evidence → attempts attachment to the nearest primary row within plausible reach (v_gap ≤ max(35, median_h × 3.5), h_overlap > 0 or h_gap ≤ max(25, median_h × 2.0))
  - If attachment succeeds: primary row bounds expand to preserve the satellite's accent/diacritic pixels
  - If no primary row is reachable: **satellite is discarded as non-text noise**

Only primary rows survive to the final output. Satellites never become standalone lines.

---

## 3. Classification Examples

| Component | w | h | ink | Primary? | Satellite? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Full text row | 200 | 22 | 800 | ✅ | — |
| Short row "Bài giải" | 90 | 20 | 400 | ✅ | — |
| "Đáp số: 17" | 130 | 22 | 550 | ✅ | — |
| Small number "5" | 22 | 18 | 60 | ✅ | — |
| Vietnamese accent (sắc/huyền) | 12 | 7 | 20 | — | ✅ → attaches |
| Dot over i | 5 | 5 | 12 | — | ✅ → attaches |
| Punctuation | 4 | 4 | 8 | — | ✅ → attaches |
| Noise speck | 3 | 3 | 5 | — | ✅ → discarded |
| Detached stroke | 15 | 6 | 25 | — | ✅ → attaches |
| Graph fragment | 30 | 3 | 15 | — | ✅ → discarded |

---

## 4. Regression Cases — Before/After

### 4.1 Physical 4-Row Graph-Paper Handwriting Fixture

| Metric | Before (RUNTIME.6) | After (RUNTIME.8) |
| :--- | :--- | :--- |
| Detected boxes | 7–8 | **4** |
| Accent-only standalone | 2–3 | **0** |
| Duplicate same-row | 1–2 | **0** |
| Real rows preserved | 4 | **4** |

Final boxes:
- Line 1: `[x=0, y=47, w=329, h=32]`
- Line 2: `[x=0, y=78, w=400, h=50]`
- Line 3: `[x=14, y=171, w=76, h=26]`
- Line 4: `[x=15, y=221, w=340, h=80]`

### 4.2 Fixture + Isolated Satellite at Top Margin (y=15)

| Metric | Before (RUNTIME.7) | After (RUNTIME.8) |
| :--- | :--- | :--- |
| Detected boxes | 5 | **4** |
| Extra satellite box | 1 | **0** |

### 4.3 Fixture + Isolated Noise at Bottom Margin (y=310)

| Metric | Before (RUNTIME.7) | After (RUNTIME.8) |
| :--- | :--- | :--- |
| Detected boxes | 5 | **4** |
| Extra noise box | 1 | **0** |

---

## 5. Accent Preservation

Vietnamese diacritics are **never deleted or masked**. The satellite attachment mechanism expands the parent row's bounding box to fully enclose the satellite:

$$y_{new} = \min(y_{row}, y_{sat}), \quad h_{new} = \max(y_{row} + h_{row}, y_{sat} + h_{sat}) - y_{new}$$

This guarantees that every accent pixel is inside the final crop sent to the CRNN recognizer.

Verified in test `SEG-16` (`test_seg_16_final_crop_preserves_accent_pixels`): Row 4's crop extends from y ≤ 228 to y + h ≥ 290, fully enclosing both upper accents and lower descenders.

---

## 6. Full-Page Result

Synthetic 8-row full-page text (800×500px, 8 rows with accent dots):
- **Expected**: 8 rows
- **Detected**: **8 rows**
- **False satellite boxes**: 0
- **Duplicate rows**: 0

---

## 7. General Validation Matrix

| Scenario | Expected | Result |
| :--- | :--- | :--- |
| Physical 4-row fixture | 4 lines | **4 ✅** |
| Fixture + isolated satellite | 4 lines | **4 ✅** |
| Fixture + margin noise | 4 lines | **4 ✅** |
| Synthetic 3-row Vietnamese | 3 lines | **3 ✅** |
| Single long row | 1 line | **1 ✅** |
| Blank page | 0 lines | **0 ✅** |
| Graph grid only (no text) | 0 lines | **0 ✅** |
| Full page 8 rows + accent dots | 8 lines | **8 ✅** |
| Two rows with ascender/descender overlap | 2 lines | **2 ✅** |
| Short legitimate row ("Bài giải") retained | 3 lines | **3 ✅** |

---

## 8. Test Suite Results

### 8.1 Segmentation Contracts (19/19 PASSED)

| Test | Description | Result |
| :--- | :--- | :--- |
| SEG-01 | Physical 4-row → exactly 4 boxes | **PASSED** |
| SEG-02 | Acute/grave/hook/tilde not standalone | **PASSED** |
| SEG-03 | Dot over i attaches to row | **PASSED** |
| SEG-04 | Punctuation attaches to row | **PASSED** |
| SEG-05 | Circumflex/breve/horn retained | **PASSED** |
| SEG-06 | Tiny noise does not become line | **PASSED** |
| SEG-07 | Nested fragment absorbed | **PASSED** |
| SEG-08 | Overlapping same-row consolidated | **PASSED** |
| SEG-09 | Adjacent real rows remain separate | **PASSED** |
| SEG-10 | Ascender/descender overlap doesn't merge | **PASSED** |
| SEG-11 | Short legitimate row retained | **PASSED** |
| SEG-12 | Long cursive row = one line | **PASSED** |
| SEG-13 | Graph grid = 0 rows | **PASSED** |
| SEG-14 | Full-page duplicate reduction | **PASSED** |
| SEG-15 | Top-to-bottom order | **PASSED** |
| SEG-16 | Final crop preserves accent pixels | **PASSED** |
| SEG-17 | Strong-band/final-count consistency | **PASSED** |
| SEG-18 | Blank page = 0 lines | **PASSED** |
| SEG-19 | Isolated satellite discarded (RUNTIME.8) | **PASSED** |

### 8.2 Full AI Service Suite
- **196 passed, 1 skipped, 0 failed** (18.22s)

### 8.3 Mobile Verification
- TypeScript (`npx tsc --noEmit`): **PASSED**
- ESLint (`npm run lint`): **PASSED**
- Expo Doctor: **21/21 CHECKS PASSED**

### 8.4 Business API
- `com.mathvisionkids.api.ocr.*`: **BUILD SUCCESSFUL, ALL PASSED** (35 tests)

---

## 9. Files Modified

| File | Change |
| :--- | :--- |
| `services/ai-service/app/api/ocr.py` | Added `has_primary_body_evidence()`. Rewrote `is_component_satellite()` to use it. Replaced Step 3 noise filter with primary/satellite partition + attachment + noise discard. Widened satellite Case 3/4 v_gap to max(25, median_h × 2.5). Restricted 3×3 morph open to grayscale fallback. |
| `services/ai-service/tests/test_segmentation_contracts.py` | Added `test_seg_19_isolated_satellite_away_from_rows_discarded`. |

---

## 10. Limitations

1. **Severely overlapping handwriting**: If two consecutive rows have extreme physical overlap (descenders extending completely across the next row's baseline), bounding boxes may overlap vertically.
2. **Skewed documents > 15°**: Handwriting tilted beyond the 10° deskew range may require additional preprocessing.
3. **CRNN accuracy**: The segmentation pipeline delivers correct line crops, but final OCR accuracy depends on the CRNN model's training coverage for the specific handwriting style.
4. **Camera blur/motion**: Extreme camera blur may reduce ink mass below primary body thresholds for faint text.

---

## 11. Design Principles

- **No hardcoded coordinates**: All thresholds are relative to `median_h`, which is computed fresh for each image.
- **Generalizes across paper types**: Works for graph paper (vở ô ly), ruled paper (vở kẻ ngang), and plain paper (giấy trắng) because the chromatic/grayscale pipeline adapts to the ink color and grid structure.
- **Classify first, then act**: Small components are classified as primary or satellite before any decision is made. Small Vietnamese accents are attached; small noise is discarded. No blind deletion.
- **Weak evidence alone never creates rows**: Only boxes with primary body evidence anchor new lines. Satellites extend existing rows or are discarded.
