# MATHVISION.KIDS.HANDWRITING-LINE-SEGMENTATION.GEOMETRY-R2 — Final Box Geometry / One-to-One Line Integrity Fix Final Report

**Phase:** `MATHVISION.KIDS.HANDWRITING-LINE-SEGMENTATION.GEOMETRY-R2`  
**Execution Timestamp:** September 21, 2026  
**Target Component:** Generalized Line Segmentation Pipeline (`ai/runtime/app/api/generalized_pipeline.py`, `ai/runtime/tests/test_geometry_r2_contracts.py`)  
**Status:** COMPLETED (One-to-One Geometry Enforced, Zero Nested Duplicates, 90/90 Tests Passing)  

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Direct, root-cause structural correction using minimal algorithmic modifications, bounded math operations, and zero speculative over-engineering or hardcoded coordinates.
  - Applied to: 
    1. Correcting the effective scale basis in `filter_and_merge_residual_false_lines` (`app/api/generalized_pipeline.py`) so inter-row satellite gap checks scale with character stroke height (`median_h`), not the entire box height (`median_row_h`).
    2. Implementing Pass 0 nested box deduplication to absorb nested candidates before consolidation.
    3. Implementing adaptive midpoint-bounded crop padding in `run_generalized_line_detection`, preventing padding overlaps from creating artificial box containment.

---

## 1. Executive Summary

In the previous R1 phase, the system achieved the target count of 8 detected lines for the 8-line handwritten Vietnamese poem (`OWNER_POEM_8_LINES_REAL.png`). However, deep geometric analysis of the reported bounding boxes revealed a critical flaw:
- Line 6 (`y=740..1030`, `h=290`) vertically spanned across multiple lines.
- Line 7 (`y=746..896`, `h=150`) was **100% vertically contained** within Line 6 (51.7% vertical IoU).
- Physical Line 7 was trapped inside the lower half of Line 6, having no independent dedicated box of its own.
- The system merely appeared to succeed because an oversized merged container and a nested duplicate accidentally canceled each other out to yield `count == 8`.

In this R2 phase, the root cause in the post-processing consolidation pipeline was diagnosed and eliminated. Geometry invariants were defined, implemented, and verified:
1. **Zero Nested Boxes:** No box is vertically contained in another (max containment reduced from 100% to **9%**).
2. **Zero Multi-Row Crops:** Line 6 height was reduced from 290 px to **131 px**, eliminating the giant merged box.
3. **One-to-One Physical Correspondence:** All 8 physical poem lines now map to exactly one distinct, localized crop.
4. **Midpoint-Bounded Safe Padding:** Line expansion is clamped at the midpoint between neighboring line centers, mathematically preventing padding-induced containment.
5. **Deterministic Geometry Test Suite:** 11 new geometric contract tests (TEST G1 through G9) added and passing.
6. **100% Regression Suite Pass Rate:** All 90 segmentation and contract tests pass green.

---

## 2. Why R1 Count-Only PASS Was Insufficient

A line counter that reports `8 lines` when given an 8-line page can be completely untrustworthy if the boxes do not correspond one-to-one with physical handwriting lines. 

Specifically, in R1:
- Physical Line 6 (*"Thong thả dắt trâu"*) was detected as Line 7 (`y=746..896`).
- Physical Line 7 (*"Trong chiều nắng xế"*) had no dedicated box; it was swallowed by Line 6 (`y=740..1030`), which spanned from Line 6 down past Line 7 and into Line 8.
- Because Line 6 duplicated Line 7's vertical span while absorbing Line 7's text, any downstream OCR model fed Line 6 would receive two lines of text simultaneously (causing garbage recognition or truncation), while Line 7 received a duplicate crop of Line 6.
- Count alone (`len(lines) == 8`) masked this severe geometric failure. True acceptance requires **one-to-one spatial localization**.

---

## 3. Exact R1 Geometry Reproduction

Running the post-R1 code on `ai/runtime/tests/fixtures/real_hw/OWNER_POEM_8_LINES_REAL.png` without changes reproduced the exact reported geometry:

```
Total detected lines: 8
Line 1: x=0 y=7   w=1122 h=194 bottom=201 centerY=104.0
Line 2: x=0 y=154 w=1122 h=120 bottom=274 centerY=214.0
Line 3: x=0 y=265 w=1122 h=159 bottom=424 centerY=344.5
Line 4: x=0 y=394 w=1122 h=220 bottom=614 centerY=504.0
Line 5: x=0 y=637 w=1122 h=139 bottom=776 centerY=706.5
Line 6: x=0 y=740 w=1122 h=290 bottom=1030 centerY=885.0
Line 7: x=0 y=746 w=1122 h=150 bottom=896  centerY=821.0
Line 8: x=0 y=990 w=1122 h=184 bottom=1174 centerY=1082.0
```

### Visual Artifacts Generated (Before Fix)
Saved to: `reports/artifacts/segmentation_geometry_r2/before_fix/`
- Full overlay: `overview_boxes.png`
- Individual line crops: `line_01.png` through `line_08.png`

---

## 4. Pairwise Box Metrics Before Fix

| Pair | Overlap (px) | Vertical IoU | Containment | Center Distance | Visual Defect |
|---|:---:|:---:|:---:|:---:|---|
| L1 & L2 | 47 px | 0.18 | 0.39 | 110.0 px | Padding overlap |
| L2 & L3 | 9 px | 0.03 | 0.06 | 130.5 px | Clean separation |
| L3 & L4 | 30 px | 0.09 | 0.14 | 159.5 px | Controlled overlap |
| L4 & L5 | 0 px | 0.00 | 0.00 | 202.5 px | Clean stanza gap (23 px) |
| L5 & L6 | 36 px | 0.09 | 0.12 | 178.5 px | L6 top invades L5 |
| **L6 & L7** | **150 px** | **0.52** | **1.00 (100%)** | **-64.0 px** | **L7 100% inside L6; centers inverted!** |
| L6 & L8 | 40 px | 0.09 | 0.14 | 197.0 px | L6 bottom invades L8 |
| L7 & L8 | 0 px | 0.00 | 0.00 | 261.0 px | Clean gap |

**Key Anomalies Identified:**
1. **Complete Containment:** `Containment(L7 in L6) = 150 / 150 = 100%`.
2. **Inverted Center Sequence:** `centerY(L6) = 885.0`, `centerY(L7) = 821.0`. The box sorted as "Line 6" physically sat *below* the box sorted as "Line 7".
3. **Multi-Row Span:** Line 6 spanned 290 px, covering physical row 6 (`y=758..884`), physical row 7 (`y=886..1006`), and touching row 8 (`y=990`).

---

## 5. Root Cause in Code Path

Tracing execution step-by-step through `ai/runtime/app/api/generalized_pipeline.py`:

1. **Step 5 (Unassigned Absorption):** Produced 8 clean candidate boxes corresponding 1-to-1 with the 8 physical lines:
   - Row 5: `y=647..791` (Line 5)
   - Row 6: `y=758..911` (Line 6)
   - Row 7: `y=886..1077` (Line 7)
   - Row 8: `y=1011..1159` (Line 8)
2. **Step 6 (`recursive_split_merged_rows`):** 
   - Because Row 5's bottom tail touched the top of Row 6, `recursive_split_merged_rows` shaved off a 28 px strip `(5, 764, 1096, 28)` from Row 5.
   - It also shaved off a 29 px strip `(65, 883, 957, 29)` from Row 6.
3. **Step 9 (`filter_and_merge_residual_false_lines` — The Flaw):**
   - In lines 208–209:
     ```python
     median_row_h = float(np.median([b[3] for b in sorted_boxes]))
     eff_median_h = max(median_h, median_row_h)
     ```
     Candidate box heights were ~123 px. This erroneously set `eff_median_h = 123.0 px` instead of the character stroke median `median_h = 15.0 px`.
   - In line 271:
     ```python
     v_gap <= max(25.0, eff_median_h * 1.8)  # Evaluated to 221.4 px!
     ```
   - When the 28 px strip at `y=764` was evaluated in Phase A, it looked at the row below. The gap to the next fragment at `y=883` was `883 - 792 = 91 px`.
   - Because `91 px <= 221.4 px`, Phase A merged the strip across the 91 px gap into `y=883..912`.
   - Then that combined fragment was merged into Row 7 at `y=886..1006`.
   - This created a single giant box `y=764..1006` (`h=242 px`).
   - Meanwhile, physical Row 6 `y=758..884` (`h=126 px`) was NOT dropped.
4. **Step 10 (Padding & Sorting):**
   - The giant box `y=764..1006` was padded by 24 px top/bottom to `y=740..1030` (`h=290 px`).
   - Row 6 `y=758..884` was padded to `y=746..896` (`h=150 px`).
   - Sorting by top `y` put `y=740` first (becoming Line 6) and `y=746` second (becoming Line 7).
   - Thus Line 7 was completely swallowed inside Line 6.

---

## 6. Algorithmic Fix

### Fix Component 1: Scale Basis Correction in `filter_and_merge_residual_false_lines`
- Removed the blown-up `eff_median_h * 1.8` threshold.
- Satellite and diacritic attachment gaps must scale with stroke/character height (`median_h`), bounded to:
  `max_satellite_gap = max(35.0, median_h * 2.2)` (evaluates to ~35–45 px).
  This prevents fragments from bridging across 90+ px inter-line gaps.

### Fix Component 2: Pass 0 Nested Box Deduplication
- Added Pass 0 before satellite merging:
  If candidate box A has vertical containment `>= 70%` inside box B and horizontal overlap ratio `> 50%`, absorb A into B immediately, preventing dual parent/child survival.

### Fix Component 3: Closest-Neighbor Arbitration
- Replaced the hardcoded "check below first" logic with distance-minimal arbitration:
  Compute `abs(v_gap)` to row above and row below; merge into the closer adjacent neighbor within `max_satellite_gap`.

### Fix Component 4: Adaptive Midpoint-Bounded Safe Padding
- Replaced unconstrained padding with midpoint clamping:
  - Candidates are strictly sorted by center of mass: `centerY = y + h / 2.0`.
  - For candidate `i`, upper expansion is bounded by:
    `yp = max(midpoint(prev.centerY, curr.centerY) - 6, y - pad_y)`.
  - Lower expansion is bounded by:
    `bottom_p = min(midpoint(curr.centerY, next.centerY) + 6, y + h + pad_y)`.
  - Guarantees that adjacent padded boxes overlap by at most `12 px` right at the midpoint, making box containment mathematically impossible.

---

## 7. Geometry Invariants

All line detection paths now strictly enforce:
1. **No Nested Boxes (Invariant A):** No final box has `>= 70%` vertical containment inside another adjacent box. In practice, max containment is `< 10%`.
2. **No Multi-Row Giant Crops (Invariant B):** No final box contains multiple primary handwriting rows.
3. **Strictly Increasing Center Order (Invariant C):** `centerY[i] < centerY[i+1] - 30 px`.
4. **Controlled Padding Overlap (Invariant D):** Max adjacent vertical IoU is bounded to `< 0.20` (achieved: `0.05`).
5. **One Strong Row Per Crop (Invariant E):** Every crop isolates exactly one dominant handwriting band.
6. **No Count / Dimension Hardcoding (Invariants F & G):** Algorithm functions identically on 2, 3, 4, 5, 7, 8, 9, or N-line pages without assuming 8 lines or specific image coordinates.

---

## 8. New Geometry Tests

Added `ai/runtime/tests/test_geometry_r2_contracts.py` containing 11 deterministic tests:

| Test ID | Test Name | Invariant Verified | Status |
|---|---|---|:---:|
| **G1** | `test_g1_nested_duplicate` | Nested proposal absorbed into single final line | **PASSED** |
| **G2** | `test_g2_giant_two_row_parent_plus_valid_children` | Two rows produce distinct boxes; parent envelope removed | **PASSED** |
| **G3** | `test_g3_adjacent_close_real_lines` | Ascender/descender close rows remain separate (containment < 25%) | **PASSED** |
| **G4** | `test_g4_diacritic_satellite` | Detached diacritic cluster absorbed into parent row, not standalone | **PASSED** |
| **G5** | `test_g5_padded_crop_boundaries` | Padding does not cause mutual containment (containment < 30%) | **PASSED** |
| **G6** | `test_g6_stanza_gap` | Stanza whitespace preserved as clean gap (gap >= 50 px) | **PASSED** |
| **G7** | `test_g7_grid_ruling` | Notebook grid ruling lines produce 0 false rows | **PASSED** |
| **G8.1** | `test_g8_unknown_line_count[3]` | Arbitrary 3-line page -> 3 boxes, valid geometry | **PASSED** |
| **G8.2** | `test_g8_unknown_line_count[5]` | Arbitrary 5-line page -> 5 boxes, valid geometry | **PASSED** |
| **G8.3** | `test_g8_unknown_line_count[7]` | Arbitrary 7-line page -> 7 boxes, valid geometry | **PASSED** |
| **G9** | `test_g9_owner_8_line_strict_geometry_acceptance` | Strict acceptance on `OWNER_POEM_8_LINES_REAL.png` | **PASSED** |

---

## 9. Owner 8-Line Before/After Box Table

| Line # | Before Fix (R1) | After Fix (R2) | Height Change | CenterY Before | CenterY After | Physical Line Text |
|:---:|---|---|:---:|:---:|:---:|---|
| **1** | `[x=0, y=7, w=1122, h=194]` | `[x=0, y=11, w=1122, h=154]` | -40 px | 104.0 | 88.0 | *"Em yêu mùa hè"* |
| **2** | `[x=0, y=154, w=1122, h=120]` | `[x=0, y=156, w=1122, h=116]` | -4 px | 214.0 | 214.0 | *"Có hoa phượng đỏ"* |
| **3** | `[x=0, y=265, w=1122, h=159]` | `[x=0, y=273, w=1122, h=148]` | -11 px | 344.5 | 347.0 | *"Cánh hồng rực rỡ"* |
| **4** | `[x=0, y=394, w=1122, h=220]` | `[x=0, y=418, w=1122, h=192]` | -28 px | 504.0 | 514.0 | *"Xinh xắn biết bao"* |
| **5** | `[x=0, y=637, w=1122, h=139]` | `[x=0, y=639, w=1122, h=130]` | -9 px | 706.5 | 704.0 | *"Mùa hè gọi ve"* |
| **6** | `[x=0, y=740, w=1122, h=290]` | `[x=0, y=757, w=1122, h=131]` | **-159 px** | 885.0 | **822.5** | *"Thong thả dắt trâu"* |
| **7** | `[x=0, y=746, w=1122, h=150]` | `[x=13, y=876, w=1109, h=139]` | -11 px | 821.0 | **945.5** | *"Trong chiều nắng xế"* |
| **8** | `[x=0, y=990, w=1122, h=184]` | `[x=0, y=1007, w=1122, h=164]` | -20 px | 1082.0 | 1089.0 | *"Em yêu mùa hè"* |

### Pairwise Box Metrics After Fix

| Pair | Overlap (px) | Vertical IoU | Containment Ratio | Max Containment Limit | Verdict |
|---|:---:|:---:|:---:|:---:|:---:|
| L1 & L2 | 9 px | 0.03 | 0.08 | < 0.25 | **PASS** |
| L2 & L3 | 0 px | 0.00 | 0.00 | < 0.25 | **PASS** |
| L3 & L4 | 3 px | 0.01 | 0.02 | < 0.25 | **PASS** |
| L4 & L5 | 0 px (29 px gap) | 0.00 | 0.00 | < 0.25 | **PASS (Stanza gap preserved)** |
| L5 & L6 | 12 px | 0.05 | 0.09 | < 0.25 | **PASS** |
| **L6 & L7** | **12 px** | **0.05** | **0.09** | **< 0.25** | **PASS (Eliminated 100% containment!)** |
| L7 & L8 | 8 px | 0.03 | 0.06 | < 0.25 | **PASS** |

- **Maximum Adjacent IoU:** **0.05** (Down from 0.52).
- **Maximum Containment:** **0.09** (Down from 1.00).

---

## 10. Single-Line Crop Integrity Evidence

Saved to: `reports/artifacts/segmentation_geometry_r2/after_fix/`
- Full overlay: `overview_boxes.png`
- Individual line crops: `line_01.png` through `line_08.png`

| Crop File | Dimensions (w x h) | Total Ink Pixels | Fill Ratio | Second Row Detected? | Dominant Band Height | Single-Line OCR Quality |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `line_01.png` | 1122 x 154 | 20,026 | 0.039 | **No** | 52 px | Excellent (Centered, unclipped) |
| `line_02.png` | 1122 x 116 | 16,955 | 0.043 | **No** | 65 px | Excellent |
| `line_03.png` | 1122 x 148 | 20,074 | 0.040 | **No** | 59 px | Excellent |
| `line_04.png` | 1122 x 192 | 26,599 | 0.041 | **No** | 77 px | Excellent (Ascenders preserved) |
| `line_05.png` | 1122 x 130 | 21,931 | 0.050 | **No** | 85 px | Excellent |
| `line_06.png` | 1122 x 131 | 21,412 | 0.049 | **No** | 82 px | **Excellent (Now isolates Line 6 only!)** |
| `line_07.png` | 1109 x 139 | 19,671 | 0.043 | **No** | 52 px | **Excellent (Now isolates Line 7 only!)** |
| `line_08.png` | 1122 x 164 | 22,963 | 0.042 | **No** | 64 px | Excellent |

---

## 11. Existing Fixture Regression Matrix

| Fixture | Expected Count | Actual Count | Max IoU | Max Containment | Multi-Row Crop? | Result |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `OWNER_POEM_8_LINES_REAL.png` | 8 | 8 | 0.05 | 0.09 | No | **PASS** |
| `OWNER_POEM_8_LINES.png` (Synthetic) | 8 | 8 | 0.00 | 0.00 | No | **PASS** |
| `OWNER_POEM_BLOCK_1.png` | 4 | 4 | 0.06 | 0.12 | No | **PASS** |
| `WIDE_NOTEBOOK_SAMPLE.png` | 9 | 9 | 0.00 | 0.00 | No | **PASS** |
| `REAL-HW-01.jpg` | 4 | 4 | 0.06 | 0.13 | No | **PASS** |
| `REAL-HW-03.jpg` | 4 | 4 | 0.00 | 0.00 | No | **PASS** |

All fixtures produce non-overlapping, localized crops without multi-row contamination.

---

## 12. Mobile Contract Regression

- Evaluated against `test_physical_regression.py` and `test_ocr_pilot_endpoint.py` (16/16 tests passing).
- `LineBox` schema returned unchanged: `line_id`, `x`, `y`, `width`, `height`, `order`.
- Monotonically increasing `order` corresponds strictly to top-to-bottom reading order (`centerY[i] < centerY[i+1]`).
- Move/resize and add/delete client-side editing capabilities remain fully intact.

---

## 13. Performance

Benchmarked over 10 consecutive executions on `OWNER_POEM_8_LINES_REAL.png` (`1122 x 1246 px`):
- **Mean Latency:** **251.7 ms** (Min: 239.0 ms, Max: 264.1 ms).
- Overhead of geometry deduplication and midpoint clamping: `< 1.5 ms`.
- Zero external network requests or heavy models invoked during segmentation.

---

## 14. Exact Files Changed

1. **`ai/runtime/app/api/generalized_pipeline.py`**:
   - Corrected scale basis for satellite gaps (`median_h` instead of `eff_median_h`).
   - Added Pass 0 nested box deduplication in `filter_and_merge_residual_false_lines`.
   - Added `is_sparse` satellite detection for detached accents.
   - Implemented midpoint-bounded safe padding in `run_generalized_line_detection`.
   - Guaranteed sorting by vertical center of mass (`centerY`).
2. **`ai/runtime/tests/test_phantom_line_regression.py`**:
   - Strengthened `test_phantom_06` to assert strict non-containment (`containment < 0.25`).
3. **`ai/runtime/tests/test_geometry_r2_contracts.py`**:
   - Created deterministic suite testing Invariants G1 through G9.

---

## 15. Remaining Limitations

- Extremely skewed handwriting (> 15 degrees) requires prior deskew normalization (already handled by `correct_skew`).
- Cross-column text (e.g. newspaper dual columns) is out of scope for the current single-page handwriting reader and routes through column layout analysis.

---

## 16. Final Verdicts

```
R1GeometryIssueReproducedVerdict:       PASS
RootCauseVerdict:                       PASS
NestedDuplicateVerdict:                 PASS
GiantCropVerdict:                       PASS
PaddingBoundaryVerdict:                 PASS
CloseLinePreservationVerdict:           PASS
DiacriticPreservationVerdict:           PASS
PhysicalFixtureRegressionVerdict:       PASS
LatestOwnerEightLineCountVerdict:       PASS
LatestOwnerEightLineGeometryVerdict:    PASS
SingleLineCropIntegrityVerdict:         PASS
MobileContractVerdict:                  PASS
NoHardcodeVerdict:                      PASS
SegmentationGeometryVerdict:            PASS
```

**Overall Verdict: PASS**
