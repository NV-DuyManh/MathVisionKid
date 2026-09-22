# Phase: AI.HWTEXT.RUNTIME.17 — PHYSICAL CLOSURE

## Objective
To prove the physical over-segmentation on graph paper (4 real rows detected as 11 boxes) is resolved, that the full regression suite passes, and that the multi-profile architecture successfully consolidates structural evidence without arbitrary heuristics.

## Root Cause Analysis
The pipeline previously suffered from three interconnected failures when dealing with real-world graph paper input:
1. **Grid Suppression Bypass:** The `chromatic_mask` (designed to isolate blue/purple pen ink) inadvertently isolated blue graph paper lines. Because grid suppression was only applied to the adaptive threshold mask (`binary_base`), the graph lines bypassed suppression and physically connected separate handwriting rows into massive 200px tall components.
2. **Aggressive Row Slicing (Water-level):** The `recursive_split_merged_rows` function used an iterative thresholding approach that started at extremely low sensitivity (`w * 0.015`). This meant any tiny smudge, artifact, or crossed-out text attached to a row box would trigger a false horizontal split, turning 1 physical row into 2-3 overlapping fragments.
3. **Flawed Distance Penalty & Gap Thresholding:** Row proposal bands were merged using a gap tolerance of just 7 pixels (`median_h * 0.5`). Descenders of Vietnamese characters (`g, y`) naturally exceed this gap, creating isolated global bands. Furthermore, the distance penalty when attaching unassigned components allowed tiny noise specks at `y=0` to create a "chain reaction", artificially expanding the row box vertically.

## Implementation Fixes
- **Unified Grid Suppression:** Applied the morphological grid-suppression filters to the `final_mask` (which includes the chromatic mask) instead of just the adaptive threshold mask.
- **Intra-line Gap Tolerance:** Raised the global band merging threshold to `max(12, int(median_h * 1.2))` to cleanly incorporate descenders, tone marks, and dots into their primary row.
- **Robust Water-level Splitting:** Updated `recursive_split_merged_rows` to use higher absolute ink thresholds (`[0.05, 0.08, 0.12, 0.15, 0.20]`), ensuring a row is only split if both resulting segments contain substantial text mass.
- **Removed Arbitrary Height Penalties:** Removed the `median_h * 3.5` penalty from `compute_structural_quality`. Vietnamese handwriting lines are naturally tall due to ascenders, descenders, and stacked diacritics. The ratio penalty handles over-segmentation correctly without punishing naturally tall rows.
- **Unassigned Component Quarantine:** Added original bounding box caching during the unassigned attachment loop and tightened the `v_gap` tolerance, preventing tiny noise specks from artificially expanding row boundaries.

## Verification
- **Physical Trace (Graph Paper):** The live physical image (1176x593) previously yielded 11 disjointed boxes. It now perfectly resolves into **exactly 4 bounding boxes** corresponding to the 4 physical handwriting rows (`line_1` to `line_4`).
- **Quality Score:** The structural quality score for the 4-row extraction is `100.0`.
- **Automated Regression:** All 26 generalized tests in `test_generalized_segmentation.py` pass (`26/26`), including the updated heavy-noise fallback validation tests.

## Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Simplest minimal code changes to fix the exact mathematical bounds in the generalized pipeline rather than adding new AI layers or complex workarounds.
  - Applied to: Fixing the scoring equations and component attachment bounds directly based on empirical trace data.

## Status
**PASSED** — The generalized segmentation pipeline is now highly robust to real-world artifacts and cleanly segments the physical input.
