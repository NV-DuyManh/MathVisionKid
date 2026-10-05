# Demo media

These assets support the repository README and documentation. They contain real app screens and a branded cover composed from those screens.

| Asset | Capture / origin |
| :--- | :--- |
| `readme-hero.jpg` | 1600 × 860 cover rendered from `showcase.html` |
| `screenshots/*-web.jpg` | Student web preview at 390 × 844 on 5 October 2026 |
| `screenshots/problem-android.png` | Original Android screenshot supplied by the project owner |

See [DEMO_GUIDE.md](../DEMO_GUIDE.md#screenshot-provenance) for individual screenshot context and limitations. Empty progress is an actual initial state. The completed lesson was reached through real UI interactions with the typed sample question.

The cover's phone frames are decorative presentation frames. App pixels inside them are real screenshots. Existing brand assets and font files are referenced from `apps/student-mobile/assets/`; they have not been replaced or altered.

## Refreshing

1. Capture the current app through its normal UI using a non-private local account.
2. Keep screenshots free of personal information and private account details.
3. Store browser captures as JPEG, with accurate source/date metadata.
4. Serve the repository and open `docs/media/showcase.html`.
5. Render its 1600 × 860 artwork and export `readme-hero.jpg`.
6. Verify README image paths, layout, alt text, and provenance.

The layout source is documentation artwork; it is not part of the student app runtime. Retain the repository and bundled font licenses when distributing media.
