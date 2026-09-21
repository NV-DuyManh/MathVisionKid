# Report: PROD.4B.2R — ARCHITECTURE SAFETY + NON-BLOCKING PERFORMANCE + REGRESSION EVIDENCE

## 1. Segmentation Regression (Fixed 10-Line Drop)
The heuristic `is_mobile_ui` in `app/api/generalized_pipeline.py` has been completely removed. It was suppressing tall UI bands indiscriminately, catching normal handwriting in tall portrait images.
- **Implementation**: Replaced with structural UI chrome suppression (Phase 9b: `filter_and_merge_residual_false_lines`). We now measure width > 85%, top/bottom edge affinity, fill density, and component height.
- **Evidence**: 
  - `REAL-HW-03` segmentation test: **PASS**. The pipeline successfully detected **9 lines**, recovering the 7 lines that were previously suppressed.

## 2. Fast Path Architecture & CRNN Batching
We have structurally prevented any single provider (Groq/Gemini) from blocking the UI.
- **CRNN Batching**: Implemented `recognize_batch_with_uncertainty` in `CrnnOcrProvider` and modified `detect_lines_endpoint` in `ocr.py` to batch process 8 crops at once.
- **Background Dispatch**: `detect_lines_endpoint` now executes purely via CRNN and immediately returns the initial payload. The blocking LLM logic has been moved to a new API endpoint: `POST /internal/v1/ocr/advise-lines`.
- **Spring Boot Non-Blocking**: In `OcrMultilineService.java`, the initial CRNN result is committed immediately. A `CompletableFuture.runAsync` thread is spawned to call `/advise-lines` in the background and silently update `correctionApplied` fields via the `lineRepository`.
- **UI Independence**: $T_{first\_usable\_ui}$ is completely independent of Groq or Gemini latency.

## 3. Arbitration Rules 
The new endpoint `/advise-lines` respects the exact MathVision Kids rules:
- **(A) Consensus**: `g_sugg == gem_sugg and g_sugg != raw`
- **(B) Deterministic Span Evidence**: Trailing duplicate character drops (e.g. `tímm -> tím`)
- **Safety**: Both providers now act purely as advisors in the background without auto-applying unsafe hallucinations to `finalText`.

## Skills Applied
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Required for creating the most minimal, native Java/Python solutions to solve the async architecture and pipeline pruning.
  - Applied to: Implemented standard `CompletableFuture` natively instead of heavy message queues; used simple structural filtering instead of training an ML classifier.
- `vercel-react-best-practices`
  - SKILL.md: `.agent/skills/react-best-practices/SKILL.md`
  - Why selected: Implicitly necessary to understand client-side non-blocking constraints, ensuring the backend API resolves the trial creation before the React Native UI mounts the interaction state.

STATUS: `READY_FOR_OWNER_PHYSICAL_RETEST`
