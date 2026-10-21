# Personal lesson video with Vietnamese audio

Goal: build a voiced MP4 from the authenticated pupil's actual, published lesson steps, with zero additional model calls for video creation.

Architecture: Student requests a private video job through business-api. AI runtime snapshots `lesson.present` after owner/revision checks, composes numbered scenes, synthesizes local Vietnamese speech and renders H.264/AAC with FFmpeg. Current steps contain hints only; completed steps may include their verified calculation. Each revision has its own cached job. Playback is click-to-play with captions.

Constraints: free local rendering/TTS; no paid provider, training, model switch, commit, push or deployment. Preserve privacy/crop and existing unrelated work. Use existing feature branch/workspace because the authorized Student implementation is already uncommitted there; do not move or reset it.

Implementation tasks:

- [x] Add failing Python tests for storyboards, no future answers, owner/stale access and bounded reusable private jobs; implement renderer/job service and internal endpoints.
- [x] Add business-api DTO/controller/service routes and tests proving owner comes from authentication, private status/content, bounded MP4 and no cache headers.
- [x] Replace the fixed example picker with automatic per-lesson video preparation, authenticated binary download and local playback; test cancellation, retries, audio enforcement and cleanup.
- [x] Render and inspect two different math problems with real Vietnamese audio; measure generation time and audio/video streams. Run relevant regression, export and responsive UI checks.
- [x] Request fresh-context review, resolve important findings and write Vietnamese report with skill traceability and explicit deployment/device limitations.

Decisions: synthesize speech offline using installed Vietnamese Windows WinRT Speech (Microsoft An) on this PC; Linux image includes eSpeak NG Vietnamese, FFmpeg and fonts. The older SAPI enumerator does not expose An, so the implementation uses WinRT from standard Windows PowerShell. Fail visibly when a Vietnamese engine is unavailable; never return a supposedly voiced silent video. The two engines have different voice quality. Video creation runs on demand when the video sheet is opened, rather than wasting CPU for unused uploads. No autoplay.

Review focus: native player release order; cross-account/stale video access; concurrent job/memory/disk limits; spoken math and caption accuracy; unsupported notation falls back to exact published text, never a fabricated diagram.

Verification ledger: 860 Student tests/65 suites; 123 Python lesson/video/conversation tests; 120 Java tutoring controller/service tests; TS/ESLint pass; web 32 routes and Android/iOS exports pass; 16 browser states pass. ASGI smoke runs actual encoder/audio, checks ownership/revision/no-store and asserts zero extra model calls. Three actual voiced MP4s verified AAC, nonzero decoded audio RMS, nonblack opening frame. Reviewer P1 font-path/P2 grouping/P2 expiry findings fixed with failing-then-passing tests and reviewer recheck. Added submission-failure cleanup regression. No commit/push/deploy/training. See report/STUDENT_PERSONAL_VIDEO_20261021.md.
