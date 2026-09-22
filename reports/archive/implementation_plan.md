# Goal Description
Refactor and generalize the handwriting line segmentation algorithm in `services/ai-service/app/api/ocr.py`. Replace the current fixture-specific dual-path logic (Path A / Path B) with a single, robust, generalized pipeline designed for unseen images.

## Open Questions
- Do we need to retain `run_classical_line_detection` and `run_grid_handwriting_detection` for backward compatibility, or can we entirely replace the body of `detect_text_lines` with the generalized algorithm? (Assuming complete replacement as per instructions).

## Proposed Changes

### AI Service (OCR)
#### [MODIFY] ocr.py
- **Retain** `run_classical_line_detection` and `run_grid_handwriting_detection` for now. Do not delete them in this phase.
- **Implement** `detect_text_lines` to route through a new generalized algorithm (bypassing legacy functions in the active path):
  1. **Preprocessing**: Deskew, contrast normalization, and adaptive ink extraction (combining chromatic clustering with adaptive thresholding).
  2. **Global Row Proposal**: Compute horizontal text-density profile to identify candidate primary body bands.
  3. **Local Component Analysis**: Extract and classify components (PRIMARY, SATELLITE, NOISE, AMBIGUOUS).
  4. **Row Assignment**: Score and assign components to row bands.
  5. **Merged-Row Splitting**: Recursively split assigned rows if multiple strong bands are detected within them.
  6. **Same-Row Consolidation**: Intelligently merge fragments that belong to the same logical row based on baseline and y-center.
  7. **Primary-Body Requirement**: Filter final standalone rows without sufficient text-body evidence.
  8. **Coverage Check & Missing-Row Recovery**: Compare global bands to final boxes and recover dropped middle rows.
  9. **Confidence**: Calculate structural detection confidence and flag `needs_review`.

#### [MODIFY] tests/test_segmentation_contracts.py
- **Add** generalized tests (GEN-01 through GEN-25) to cover paper types, ink modes, layouts, image quality variations (skew, resize, brightness, contrast, JPEG compression), and edge cases (isolated satellites, grid fragments, merged rows).

#### [MODIFY] tests/test_physical_regression.py
- Ensure known physical fixtures pass without relying on exact pixel coordinates or hardcoded constraints.

## Verification Plan
### Automated Tests
- Full `pytest tests/ -v` for all AI tests, including new GEN-01 to GEN-25 tests.
- Physical regression tests for all observed failure modes (0-line, 8-line over-segmentation, 5-line satellite false positive, 2-line under-segmentation, correct 4-row case, full-page over-segmentation).
- Business API OCR tests.
- Mobile frontend tests: TypeScript `tsc`, `eslint`, and `expo-doctor`.

### Manual Verification
- None required before reporting; the prompt explicitly states to stop after the report and wait for owner physical retest.
