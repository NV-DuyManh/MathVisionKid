# Student profile and verified rewards

The Student Mobile and shared Student Web profile read the same private Spring endpoints. The student JWT determines ownership. The editable fields are display name, an allowlisted avatar, visibility, and a title the student already earned. Class membership, grade, registration date, and account role are read-only. Display names appear on the private profile. The leaderboard uses a generated alias and a stock avatar, with visibility off by default. Class ranking requires current membership.

## Reward rules

| Activity | Evidence | Award |
| --- | --- | --- |
| Lesson | The owned Tutor session accepts answers, reaches COMPLETE and has a checked math step | One per confirmed content |
| Quiz | The owned server-graded Quiz reaches its first independent correct completion before seeing the solution | One per Quiz source fingerprint |
| Đường đua sao | The backend creates five questions for the student's grade, verifies answers one at a time and records at least four correct | One per level per day |

An eligible award is one star. Defaults are six stars per day and three per source per day in the Vietnam time zone. Configure the limits with Spring properties `app.student-rewards.daily-limit` and `app.student-rewards.source-limit`. Same-content lesson/Quiz repeats do not add progress or stars. Games can record additional verified wins within the 12 daily starts, with one starred win per level/day. The ledger keeps unique event IDs, timestamps and zero-star verified activities for stats when appropriate. Lesson and Quiz histories that predate V30 are not backfilled. Existing Quiz scores retain their own scoring rules and local saved lessons retain their storage keys.

Opening, capturing, saving, incorrect answers, and starting a game do not issue stars. Streaks derive from verified activity dates. Development accounts at the seed domain and the local training-game trial have no path to an award. The five existing game packages still produce local outcomes. Their canonical sources need a server-authoritative gameplay integration before those games can add server rewards. The new Đường đua sao is a separate mode in Training Games. It verifies arithmetic answers, without claiming to prove a human solved them without assistance.

Game answers accept only question index and numerical answer. The backend determines the student, grade, game seed, current index, score and terminal result. A retry of the most recent identical answer returns the same result. An older/out-of-order index is rejected. A run expires after 20 minutes. Ledger writes use transactions and a serialized reward lock to keep caps and rank high-water marks consistent. Reassess lock contention and ranking-query cost before expanding the rollout.

## Rank formula

Starting at Đồng III, the six pre-master tiers consume 9, 12, 16, 25, 25 and 25 stars. Cao Thủ begins at **112 total stars**. Subtract 112 to get Cao Thủ stars. The next boundaries are 10, 20, 30, 40, 50 and 100 Cao Thủ stars. Leaderboard order is total stars descending then generated alias ascending. Global positions 1–200 with at least 50 Cao Thủ stars receive Thách Đấu. Losing a qualifying position returns the student to the underlying rank. The historic Thách Đấu milestone remains. Class rank is shown for the same eligible population scoped to the class, and the Thách Đấu decision uses global position.

Rank names and master subdivisions were cross-checked against the official Garena update. Top 200 and the specified promotion thresholds are MathVision Kids product rules. [Garena update](https://lienquan.garena.vn/chi-tiet-ban-cap-nhat-phien-ban-ngay-hoi-lien-quan/)

## UX evidence

The installed last30days engine ran for 14 October–13 November 2026. Reddit retrieval was unreachable and Hacker News produced one low-signal result, with no ranked evidence surviving. The design uses the existing app's palette and typography, a visible progress bar, and direct activity links. Private-by-default rankings and static, readable reward feedback follow the reviewed primary references. [Duolingo October 2026 update](https://blog.duolingo.com/october-2026-update/) · [Minecraft Education challenge](https://education.minecraft.net/en-us/challenges/minecraft-micro-models) · [ICO default settings design guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/7-default-settings/)

## Integration

Run Flyway V30 before serving the new build. To roll back the application, use the previous build with the additive tables retained for recovery. PostgreSQL migration validation and backup/restore belong in an isolated database. Do not reset or delete a shared database. Source-only branch checkout for this change uses `develop` as its base.
