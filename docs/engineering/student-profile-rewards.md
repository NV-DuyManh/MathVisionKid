# Student profile and verified rewards

The Student Mobile and shared Student Web profile read the same private Spring endpoints. The student JWT determines ownership. The editable fields are display name, an allowlisted avatar, visibility, and a title the student already earned. Class membership, grade, registration date, and account role are read-only. Display names appear on the private profile. The leaderboard uses a generated alias and a stock avatar, with visibility off by default. Class ranking requires current membership.

## Reward rules

| Activity | Evidence | Award |
| --- | --- | --- |
| Lesson | The owned Tutor session accepts answers, reaches COMPLETE and has a checked math step | One per confirmed content |
| Quiz | The owned server-graded Quiz reaches its first independent correct completion before seeing the solution | One per Quiz source fingerprint |
| Đường đua sao | The backend creates five questions for the student's grade, verifies answers one at a time and records at least four correct | One per level per day |
| Five themed training challenges | The student opens the challenge from a training-game card and answers at least four of five server-graded questions in that game's topic | One per game per day, subject to the shared caps |

An eligible award is one star. Defaults are six stars per day and three per source per day in the Vietnam time zone. Configure the limits with Spring properties `app.student-rewards.daily-limit` and `app.student-rewards.source-limit`. Same-content lesson/Quiz repeats do not add progress or stars. Games can record additional verified wins within the 12 daily starts, with one starred win per level/day. The ledger keeps unique event IDs, timestamps and zero-star verified activities for stats when appropriate. Lesson and Quiz histories that predate V32 are not backfilled. Existing Quiz scores retain their own scoring rules and local saved lessons retain their storage keys.

Opening, capturing, saving, incorrect answers, and starting a game do not issue stars. Streaks derive from verified activity dates. Development accounts at the seed domain and the local training-game trial have no path to an award. The packaged games keep device-local results. Each card offers a server-graded challenge themed to its game. The server receives the question index and answer, and derives the score and award. The game package's outcome never enters this reward path.

Game answers accept only question index and numerical answer. The backend determines the student, grade, game seed, current index, score and terminal result. A retry of the most recent identical answer returns the same result. An older/out-of-order index is rejected. A run expires after 20 minutes. Ledger writes use transactions and a serialized reward lock to keep caps and rank high-water marks consistent. Reassess lock contention and ranking-query cost before expanding the rollout.

The five themed challenges use the grade stored in the run. Grades 1–2 receive addition/subtraction (grade 1 operands stay within 9); grade 3 uses multiplication/division before the fraction challenges introduced at grade 4. Terrain speed questions start at grade 5; earlier grades use the foundational operations instead. The packaged boards remain separate from these adapted, server-graded challenges.

`POST /api/v1/student/game-runs` accepts the optional `mode` parameter and defaults to the original Đường đua sao. `GET /api/v1/student/game-runs/{id}` returns the owned run so the client can recover after losing a response. Completed runs can be read after the 20-minute live-play window. The result explains repeat wins, the daily total cap and the daily game cap. V34 preserves existing runs by defaulting them to the original mode. Roll back the application with the additive columns retained.

## Rank formula

Starting at Đồng III, the six pre-master tiers consume 9, 12, 16, 25, 25 and 25 stars. Cao Thủ begins at **112 total stars**. Subtract 112 to get Cao Thủ stars. The next boundaries are 10, 20, 30, 40, 50 and 100 Cao Thủ stars. Leaderboard order is total stars descending then generated alias ascending. Global positions 1–200 with at least 50 Cao Thủ stars receive Thách Đấu. Losing a qualifying position returns the student to the underlying rank. The historic Thách Đấu milestone remains. Class rank is shown for the same eligible population scoped to the class, and the Thách Đấu decision uses global position.

Rank names and master subdivisions were cross-checked against the official Garena update. Top 200 and the specified promotion thresholds are MathVision Kids product rules. [Garena update](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-phien-ban-ngay-hoi-lien-quan/)

The current ladder starts at Đồng III. The five emblems from Đồng through Kim Cương are cropped and resized from Sinestesia's **Ranks Coins and More**, released under CC0. Tinh Anh through Thách Đấu use original vector emblems. The profile and both leaderboards share the same artwork for each tier. [OpenGameArt asset and license](https://opengameart.org/content/ranks-coins-and-more)

## Release checklist

- Android app, iOS app and mobile web. Open the avatar page, edit the display name and avatar, switch leaderboard visibility, save, reopen and confirm that the changes persisted. Verify that the leaderboard displays the generated alias and a preset avatar.
- Open Thành tích at 320–390 CSS px. Verify the rank guide and Top 200 threshold, switch class and global rankings and expand the first ten rows. Test a long display name and class name with larger text.
- Open and leave all six games. Check Race in portrait and landscape, and verify that rotating back does not restart an active web race. Check the account transition after returning from a game.
- Complete the six server challenges with a fresh student, then repeat one. Verify one award per challenge and a reason for the repeat or shared daily cap. Drop a response for the final answer, resend it and inspect the ledger. Verify expired runs and account isolation on a disposable backend.

## UX evidence

The installed last30days engine ran for 14 October–13 November 2026. Reddit retrieval was unreachable and Hacker News produced one low-signal result, with no ranked evidence surviving. The design uses the existing app's palette and typography, a visible progress bar, and direct activity links. Private-by-default rankings and static, readable reward feedback follow the reviewed primary references. [Duolingo October 2026 update](https://blog.duolingo.com/october-2026-update/) · [Minecraft Education challenge](https://education.minecraft.net/en-us/challenges/minecraft-micro-models) · [ICO default settings design guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/7-default-settings/)

## Integration

V32 adds Student Profile. PR #59 reserves V30 and V31 for assignment and batch idempotency. A fresh #60 checkout can be tested by itself. For a shared environment, integrate #59 first, sync #60 with the resulting `develop`, then deploy with V30, V31 and V32 in that order. This avoids leaving older pending migrations below an already applied V32. Keep applied migrations and checksums intact. To roll back the application, use the previous build with the additive tables retained for recovery. PostgreSQL migration validation and backup/restore belong in an isolated database.
