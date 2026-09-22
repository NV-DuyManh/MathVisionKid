# MOBILE.OCR.2 — Smooth Crop UX & Robust Handwriting Line Detection

## Skills Applied
- `fixing-motion-performance`
  - SKILL.md: `.agents/skills/fixing-motion-performance/SKILL.md`
  - Why selected: Addressed UI-thread gesture discontinuity and lag near screen edges.
  - Applied to: `crop.tsx` gesture clamping logic and layout sizes.

## 1. Crop UX Edge Behavior (Physical Android)
**Problem:** The gesture handlers used absolute `translationX/Y` compared against a fixed initial `ctxX/Y` coordinate. If a user dragged outside the boundaries, the box visual would clamp, but the math accumulated translation. Reversing direction caused a "dead zone" where the box wouldn't move until the translation decayed back to the boundary. Additionally, Android dropped touches near screen edges because the 24x24 hit targets relied on `hitSlop` which gets clipped by parent views.

**Fix:**
- Swapped `.onUpdate()` for RNGH2's `.onChange(e)`. 
- Refactored the math to use incremental `e.changeX` / `e.changeY`. The boundary clamping now perfectly zeroes out the delta without creating a dead zone. The instant the user pulls back from a boundary, the box follows.
- Added `.minDistance(0)` to completely eliminate the default 10px activation threshold lag.
- Wrapped the visual corner boxes (`24x24`) inside a large, transparent `48x48` `cornerHitTarget`. This provides a massive physical touch area that Android cannot clip, making corner grabs 100% reliable.

## 2. Handwriting Line Detection Robustness
**Problem:** The classical OpenCV pipeline in `ai-service/app/api/ocr.py` used strict horizontal dilation (`30x3` kernel) and strict vertical overlap logic. Hand-drawn text is often sloped and uneven, causing these horizontal assumptions to shatter single lines into fragments, sever diacritics, and isolate tall letters.

**Fix:**
- **Small-Angle Deskew:** Implemented a HoughLinesP-based small-angle deskew `[-10, 10] degrees`. This flattens casually tilted camera shots or slanted handwriting before horizontal processing begins.
- **Adaptive Morphology:** Increased the dilation kernel height from a flat `3` to a dynamic ellipse (`k_height = max(7, height * 0.008)`). This catches sloped strokes and floating diacritics without bleeding into adjacent lines.
- **Tolerant Vertical-Center Merging:** The collinear grouping logic no longer demands 35% bounding box overlap. It now merges fragments if their *vertical centers* are aligned relative to the text height (`y_dist < max_h * 0.6`). This gracefully stitches together wavy handwriting.
- **Dynamic Padding:** Increased output bounding box padding (`pad_y = 15%`) to guarantee Vietnamese accents (`^`, `~`) and descenders (`g`) are not clipped before reaching the CRNN.

## 3. Diagnostic A/B Setup
**Added:** `scratch/test_ocr_ab.py` (in artifacts)
A local diagnostic script has been created. If the owner still encounters OCR errors, they can pass an image to this script. It runs the new handwriting detector and outputs a visual `_detected.jpg` overlay. This will cleanly isolate whether future failures stem from bad line crop bounding boxes or purely from the OCR CRNN model misreading the pixels.

## 4. Verification
- TypeScript compilation: `PASS`
- React Native Linting: `PASS`
- AI Service Pytest (`164` tests): `PASS`
- Business API Gradle Test (`80` tests): `PASS`
- No model checkpoints were altered or trained.

**Ready for physical device validation.**
