# Meeting action: handwriting and mathematical-symbol OCR — 2026-10-21

## Result

Fixed a reproducible line-region defect that detached a leading minus or compact
equality mark from its neighboring numeral. The photographed-page pipeline now
keeps these supported regions in one OCR crop, preserving their expression
context. This is a targeted geometry improvement, not a measured increase in
global OCR accuracy.

## Inspection and root cause

Traced `detect_text_lines` → `run_generalized_line_detection` →
`detect_text_regions` → `merge_fragments`, including the portrait-page early
return and source-pixel crops. Reviewed shared normalization, camera EXIF
orientation, CRNN input preparation, and existing fraction/column safeguards.
The photo endpoints already apply EXIF orientation.

`merge_fragments` required neighboring region heights to differ by at most 2×.
A minus region `(80,118,94,121)` beside numeral region `(100,100,130,140)`
therefore remained a standalone 3-pixel-high line. A compact equality region
had the same failure. Before the fix the new regressions produced six failures
and five passing boundary controls, including two production-pipeline failures
at 1× and 3× image scale.

The shared function now accepts a short region only when its vertical extent
is contained in the adjacent body, its width is no greater than the body
height, the gap is at most half that height, and the larger region is not
tall and narrow. Existing overlap, center-distance, and gap checks still apply.
No character is inferred, substituted, calculated, or assigned a confidence.

## Files

- `ai/runtime/app/recognition/text_detector.py` — bounded compact-mark grouping.
- `ai/runtime/tests/test_math_symbol_regions.py` — 11 regression/control cases:
  minus/equality at two scales, both input orders; separate baselines,
  fraction/underline tiers, distant columns, long bars, tall vertical arithmetic;
  two full local pipeline checks covering original coordinates, review flags,
  unchanged source pixels, and cache behavior.
- `report/MEETING_OCR_20261021.md` — this report.

## Verification

Run from `E:\MathVisionKid\ai\runtime`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_math_symbol_regions.py tests/test_text_detector.py tests/test_generalized_segmentation.py tests/test_column_regions.py tests/test_sparse_ruled_recovery.py -q
# 152 passed in 18.99s

.\.venv\Scripts\python.exe -m pytest tests/test_math_symbol_regions.py tests/test_ocr_bridge.py tests/test_line_cap.py -q
# 31 passed in 12.63s; two existing Starlette/httpx/anyio deprecation warnings
```

There are 172 distinct passing cases across these runs (the 11 new cases run
twice). The second run includes the final synthetic-image fixture adjustment.

## Limits and scope

The new integration tests stub learned detector regions to isolate the
deterministic grouping defect; they do not measure model accuracy. No pupil
photo, Drive corpus, training set, model weights, model selection, or CRNN
recognition evaluation was changed or run. Existing local segmentation tests
may use the installed optional text detector on their synthetic fixtures.
No training, download, corpus copying, device claim, commit, push, or deployment.
No backend, mobile, tutoring, authentication, or grading-authority edits.
Other agents' working-tree changes and existing reports were preserved.

The rule deliberately leaves tall narrow bodies, distant marks, and unsupported
or ambiguous layouts on their established path. Real-photo acceptance remains
an owner-approved bounded evaluation against fixed labels, without changing
model weights or reference labels after seeing results.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: targeted OCR production fix with a minimal shared change.
  - Applied to: caller tracing, reuse of existing grouping logic, no dependency
    or model changes, regression and boundary checks before completion.
