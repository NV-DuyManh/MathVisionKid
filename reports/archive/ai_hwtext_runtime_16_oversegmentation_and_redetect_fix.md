# AI.HWTEXT.RUNTIME.16 — Fix Graph-Paper Over-Segmentation AND Make Re-Detect Actually Re-Analyze

## 1. Issue Addressed
The AI detector was exhibiting severe over-segmentation on graph-paper backgrounds: 4 physical handwriting rows were producing 11 bounding boxes. This happened because large morphology kernels used to subtract grids were missing imperfect, skewed, or broken grid lines. The remaining grid lines formed artificial components which split legitimate candidate boxes (thin strips) and falsely inflated the candidate count.
Additionally, the "Re-Detect" button merely hit a cache-busted endpoint that deterministically returned the exact same 11 boxes because the detection pipeline had only one path.

## 2. Changes Made
- **Introduced Profiles**: Modified `app/api/generalized.py` to support variable morphological kernels and grid-suppression thresholds (`PROFILE_A`, `PROFILE_B`, `PROFILE_C`).
- **Structural Quality Scoring**: Added `compute_structural_quality` in `app/api/generalized_pipeline.py`. It aggressively penalizes outputs that contain thin-strip boxes (height < 50% median) and heavily checks box-to-band consistency.
- **Deterministic Multi-Profile Fallback**: The main `run_generalized_line_detection` orchestrator now runs `PROFILE_A` (Default). If the output scores `< 90.0` or flags `needs_review`, the image is automatically re-analyzed using `PROFILE_B` (Strong Grid Suppression) and `PROFILE_C` (Strong Horizontal Continuity). The detector compares scores and deterministically outputs the highest-quality candidate set.
- **Cache-Busting Validation**: The frontend's "Re-Detect" semantics (`_t` timestamp) remain intact. When a user taps Re-Detect, it invokes this newly hardened pipeline. The pipeline automatically evaluates the image and correctly outputs 4 boxes if `PROFILE_B` handles the graph lines better, providing meaningful, accurate re-analysis.

## 3. Test Coverage (OVER-Matrix)
Added explicit test case `GEN-26/OVER-01` to `tests/test_generalized_segmentation.py`. The test explicitly generates random handwriting noise and horizontal line fragments (simulating broken graph lines) which trick `PROFILE_A` into returning a terrible quality score (0.0). The test proves that `PROFILE_B` activates and achieves 100.0 quality, extracting the correct 4 rows.
All 26 pipeline regression tests pass locally.

## Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: We explicitly focused on minimal code changes, augmenting existing functions rather than building an entirely new secondary OpenCV pipeline.
  - Applied to: Adding `fallback_profile` iteration inside `generalized_pipeline.py` without reinventing component classification.
