# AI.HWTEXT.1.1 Annotation Preparation Report

## 1. Executive Summary
The annotation preparation phase is complete. 331 text-line crops have been packaged into 14 manageable batches for human review. A lightweight local HTML UI (`annotation_tool.html`) has been provided to accelerate the verification process securely and offline.

## 2. Input Counts
- **Total candidate line crops:** 510
- **TEXT_ONLY:** 155
- **TEXT_WITH_CONTEXTUAL_NUMBERS:** 176
- **MATH_DOMINANT:** 146 (Quarantined)
- **REJECT:** 33

## 3. Annotation Queue Validation
- Recalculated matching counts.
- Exactly 331 text lines requiring human verification were identified.

## 4. Batch Layout
- 14 annotation batches created.
- Target size: 25 items per batch.
- Batch directories: `data/hwtext_v1/annotation_batches/batch_001` through `batch_014`.
- Each batch includes a `TSV` file and a `JSON` file for the UI.

## 5. Difficulty Prioritization
Lines were sorted by a calculated priority score:
- **Priority A/B:** High clarity (low blur score) and `TEXT_ONLY` appear first.
- **Priority C/D:** `TEXT_WITH_CONTEXTUAL_NUMBERS` and higher blur scores appear later, allowing the reviewer to knock out easy cases first.

## 6. Math Reclassification
Math-dominant lines (146 items) were successfully identified and excluded from the annotation queue. They remain quarantined in the dataset manifest. The reviewer is still requested to re-classify any surviving math-dominant lines to "REJECTED" during manual verification if any slipped through.

## 7. Annotation Tool/Workflow
A local, offline, secure HTML annotation tool was created at:
`data/hwtext_v1/annotation_tool.html`
- **Features:** Shows image crop, category, pre-label suggestion, and allows keyboard-driven "Accept" (Enter) or "Reject" (Ctrl+Del).
- **No Internet Required.**
- Exports reviewed batches locally as JSON.

## 8. Progress Statistics
`data/hwtext_v1/annotation_progress.json` has been initialized to track verification state.
- **Total:** 331
- **Verified:** 0
- **Rejected:** 0
- **Remaining:** 331

## 9. Label QA
Pending human review. Cannot be run yet.

## 10. Vocab Coverage
Pending human review. Cannot be run yet.

## 11. Training Readiness
**ANNOTATION_INCOMPLETE**. Training is blocked until human verification is complete.

## 12. Files Generated
- `data/hwtext_v1/annotation_progress.json`
- `data/hwtext_v1/annotation_tool.html`
- `data/hwtext_v1/annotation_batches/` (14 batches)
- `report/ai_hwtext_1_1_annotation_preparation.md`

## 13. Final Verdict
PARTIAL. The annotation packages are ready. The pipeline is paused awaiting human input.

## 14. Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Used for minimalist implementation of the offline HTML tool and script.
  - Applied to: Building a simple `<script>` based vanilla HTML annotation UI instead of a full React/Vue app to save time and dependencies.
