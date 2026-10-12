# Sparse writing on ruled pages — 2026-10-12

Status: shared detection fix, regression checks and full page screening completed.

The owner requested continued work on unresolved OCR failures and requires original images to stay on Drive. This phase addresses a missed small coloured glyph on a ruled portrait; it does not change model weights, authentication, Student Mobile or deploy the application.

## Problem and change

On Drive `NEW2/IMG/828.jpeg`, the learned detector returned no text. The classical fallback then produced six large lower-grid regions while missing the actual small red `t` near the top. CRNN rerecognition of these boxes could produce phantom characters even though the relevant ink was outside them.

The portrait pipeline now attempts a bounded recovery only after an explicitly empty learned detection. It requires several distinct long horizontal and vertical rules, light paper, sparse curved pen components, and no supported competing neutral writing. Dense writing, ordinary unruled pages, missing optional detector weights and fractions keep the established path. The recovered region remains explicitly unverified and needs review. The detector cache version changed so older cached grid boxes cannot mask the new result.

On the observed failure page, six false grid regions are replaced by one box `[324, 420, 363, 502]` containing the visible small glyph in the original 2160×2880 source. The image is not rewritten or copied. The experimental CRNN still reads this crop as `1`, so **geometry recovery does not certify correct character recognition**.

## Evidence and limits

Twelve source-hash-checked real pages were read directly from Drive. The changed page recovered one source region. The other eleven pages, including prose, repeated writing, unit conversion and fractions, retained their region counts and established profiles. This is a focused check, not a general accuracy result or independent writer-disjoint evaluation.

The source-ink eligibility guard was screened on **all 1,581 page photographs** in the recorded corpus, with source SHA-256 verification. Of these, 1,569 were read through the mounted Drive and 12 initial source-read failures were recovered using authenticated Drive references in RAM. Only `828.jpeg` triggered the sparse guard. This screening tests the guard's eligibility, not every photo's OCR or manually verified detection accuracy. Exact source coordinates on the other eleven focused pages matched the historical detector JSON, including the fractional and unit-conversion pages.

**250 tests passed**, covering the new sparse cases, existing text detection, handwriting rows, general segmentation, true-redetection/cache safety and offline data/model/recognition safeguards. There is no fabricated phone evidence. Model weights, the vocabulary, 29 protected historical/model files and the global Drive index remain unchanged; two runtime source files and one new test file implement the fix. No new dependency, model fitting, deployment, commit or push occurred in this phase. All phase jobs finished.

The sparse guard has a known limit around faint neutral writing and page borders; it does not classify a page as blank or provide training labels. Synthetic tests cover red/blue glyphs at two scales, unchanged source pixels, blank/unruled inputs, neutral-word veto, fraction preservation, existing nonempty model detections, missing weights and the API cache path.

A separate repeated-gutter experiment on the column-layout page `1007.jpeg` found potential exercise-column gaps but also gaps within a multi-word name. That splitter was rejected and not applied in runtime. Column structure remains unresolved; no heuristic guesses were converted into labels or solutions.

Private evidence: `ai-training/datasets/drive_math/layout_20261012/`. Only metadata, diagnostic outputs and experiment code are stored locally. Original photographs remain on Drive and are read into RAM; no source image/ZIP/Parquet copy is created in this phase. The owner reported deleting the previously generated temporary folders; they were not recreated.

The final reconciliation is `final_layout_summary.json`, with source/code hashes, focused geometry comparison, full page-screen membership, limits and the rejected column-splitting decision. The previous temporary `containers` and `pages_originals` directories were confirmed absent.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Fix the shared detection path with existing OpenCV utilities and no added dependencies.
  - Applied to: Bounded empty-detection recovery, cache invalidation, conservative fraction/neutral-ink guards and targeted regression checks.
- `google-drive`
  - SKILL.md: `C:/Users/Admin/.codex/plugins/cache/openai-curated-remote/google-drive/0.1.20/skills/google-drive/SKILL.md`
  - Why selected: Preserve the user's Drive-only original-image policy.
  - Applied to: Observed source IDs, direct mounted Drive reads, authenticated RAM-only retries and source SHA-256 checks.
