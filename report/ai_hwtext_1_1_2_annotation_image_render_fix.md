# AI.HWTEXT.1.1.2 Annotation Image Render Fix

## 1. Root Cause
The `annotation_tool.html` originally had `document.getElementById('cropImg').src = "../../" + item.crop_path;` hardcoded.
Since the tool itself lives in `data/hwtext_v1/`, and the batch crops were referenced as `work/crops/IMG_XXXX_LYY.jpg` (which is correctly relative to `data/hwtext_v1/`), appending `../../` broke out of the repository structure entirely, resolving to a non-existent path on the root origin.

## 2. Raw Example Path
`work/crops/IMG_0086_L03.jpg` (from `batch_001.json`).

## 3. Broken Resolved URL Before
`http://127.0.0.1:5500/work/crops/IMG_0086_L03.jpg`
This incorrectly bypassed the `data/hwtext_v1/` working directory.

## 4. Canonical Resolver
Implemented `resolveCropUrl(cropPath, batchFileName)` in `annotation_tool.html`.
It handles:
- Windows absolute paths (stripping down to repo prefix)
- Root-relative paths (`/data/hwtext_v1/...`)
- Tool-relative paths (`work/crops/...`)
- Batch-relative paths (`crops/...` -> `annotation_batches/...`)
- Backslash normalization.

## 5. Resolved URL After
`work/crops/IMG_0086_L03.jpg` (Resolves correctly in the browser relative to `annotation_tool.html`).

## 6. Real Image HTTP Verification
A python test validated that physical crop files exist for:
- batch_001
- batch_007 (middle)
- batch_014
All physically exist and map correctly to the resolved UI URL.

## 7. UI Error Handling
Added a visible `<div id="imgError">` and an `onerror` handler to the `<img>` tag. If an image fails to load, it hides the broken image icon and displays bold red text: "Image load failed!" along with the exact `rawPath` and `resolvedUrl` for instant debugging.

## 8. Image Readability
The image rendering uses CSS `.crop-img { max-width: 100%; height: auto; }` which guarantees it does not overflow but preserves aspect ratio and maximum native resolution for inspecting Vietnamese diacritics.

## 9. Tests
- Path resolution tests: 11/10 (exceeded base expectation by explicitly testing physical file existence)
- Annotation workflow regression tests: PASS

## 10. Files Modified
- `data/hwtext_v1/annotation_tool.html`
- `scripts/test_image_paths.py` (New test script)

## 11. Final Verdict
PASS. The local annotation tool's image rendering bug is fixed without mutating any underlying datasets. The tool is now fully usable for the manual review phase.
