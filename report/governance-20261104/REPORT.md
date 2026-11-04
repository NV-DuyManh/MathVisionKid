# Quy trình GitHub/CI và luật dự án — 04/11/2026

## Phạm vi

Triển khai ở nhánh `Manh`, nền `ac7aa8e`. Không đổi mã nghiệp vụ Student/web/backend/AI hoặc huấn luyện model. Dọn báo cáo/tệp được giao cho chat riêng; commit governance không gộp thay đổi cleanup.

## Đã triển khai

- Quy ước naming, workflow nhóm, API/database, chất lượng/bảo mật, bảo trì và bàn giao trong `docs/engineering/` và `docs/templates/`.
- `.editorconfig`, Node 22.19.0, CODEOWNERS, mẫu PR/issue, Dependabot có giới hạn; không đổi tên/reformat hàng loạt code cũ hoặc biên nhận nghiên cứu.
- Registry 23 skill và 20 route; bốn skill riêng MathVision bao phủ workflow/requirements/release, review correctness, quality và backend/database. Giữ skill hiện có, không nhập duplicate hay nghiệp vụ café.
- CI PR có quyền đọc, action SHA cố định, không giữ credential checkout, không dùng pull_request_target hoặc live TTS/model. Bot tổng hợp phạm vi/kết quả trong Job Summary; không giả làm AI semantic review và không auto-approve/merge/comment.
- Các nhóm Web, Student, Backend/migration PostgreSQL, AI offline, Windows launcher. `Quality gate` là check tổng hợp ổn định; lỗi/cancel hoặc skip bất ngờ không được tính là đạt.
- JSON chính sách ở `.github/rulesets/`: chỉ owner quyết định merge qua PR; resolve discussions, chống force-push/xóa main, required Quality gate gắn app GitHub Actions. Theo chỉ đạo mới của owner, bỏ yêu cầu một approval khác tác giả; số approval bắt buộc là 0 như CODEGYM.

## Kiểm chứng local

| Kiểm tra | Kết quả |
| --- | --- |
| Governance policy/routing tests | 7/7 đạt; registry 23 skill, 20 route |
| Skill Creator quick_validate | 4/4 skill mới hợp lệ |
| actionlint 1.7.12 | Hai workflow hợp lệ; binary kiểm tra checksum theo release chính thức |
| Portal / Teacher / Admin config tests | 33/31/34 đạt |
| Production build + bundle tests ba web | Build đạt; 2/2/5 kiểm thử bundle đạt |
| Lint web | Không lỗi; Teacher còn một cảnh báo Fast Refresh đã có |
| Student | Typecheck và 15 contracts đạt; không đổi source Student |
| Backend Gradle | 487 ca được liệt kê, 0 lỗi; 1 MinIO opt-in skip; H2 profile test |
| SQL PostgreSQL 16 | 28 migration chạy trong container dùng một lần, không cổng/volume dự án; container đã dừng |
| Migration runner guards | 3/3 đạt; từ chối DB không phải test, ngoài CI hoặc DB không rỗng |
| AI môi trường Python 3.12 sạch | 123/123 toán/phát âm đạt; dependencies riêng, không torch/trọng số |
| Catalog | Store và bot checks đạt, không đọc DB học sinh thật |
| Windows launcher | Environment/identity regressions đạt; 6 batch launcher tests đạt |

AI lần đầu thiếu Celery do fixture chung import worker, sau đó thiếu plugin pytest-asyncio; đã bổ sung dependencies vào manifest CI và chạy lại môi trường sạch đạt 123/123. Không bỏ fixture hoặc assertion để làm xanh. Không bật/dừng SmartCafe hay chiếm cổng 8080.

Các build vẫn cảnh báo bundle lớn; task này không đổi bundling hoặc tuyên bố tối ưu runtime mới. Migration check kiểm SQL PostgreSQL fresh DB, không chứng minh Flyway history/checksum hoặc upgrade từ DB production. Không tạo bằng chứng thiết bị thật/latency live.

Log local: `C:\Users\Admin\.codex\tmp\web-audit-20261103\governance-*.log`. Snapshot cấu hình GitHub trước thay đổi: `C:\Users\Admin\.codex\tmp\mathvision-governance-20261104\`.

## GitHub — trạng thái rollout

PR kiểm chứng: https://github.com/NV-DuyManh/MathVisionKid/pull/15. Lượt CI đầu `41849390422` đạt Web, Student, Backend/migrations, AI và governance; launcher Windows thất bại vì fixture Python parent dùng cứng ổ E không tồn tại trên runner. `Quality gate` chặn đúng lỗi đó. Đã sửa riêng test theo đường dẫn checkout và chạy lại cả checkout E lẫn fixture C; không thay launcher nghiệp vụ hoặc bỏ assertion.

Đã đọc lại qua API: auto-delete head sau merge bật; auto-merge vẫn tắt. Dependabot security updates, secret scanning và secret push protection đã bật. Các cấu hình này không nằm trong git diff.

CI thật https://github.com/NV-DuyManh/MathVisionKid/actions/runs/41850845448 tại commit `17932d6` đã đạt toàn bộ 7 jobs, gồm `Quality gate` của GitHub Actions app ID 15368. Sau bằng chứng này mới bật ruleset `24461306` (PR/lịch sử/required Quality gate, không bypass) và `26539651` (owner-only update, bypass chỉ qua PR). Đọc lại API xác nhận cả hai active và `branches/main.protected=true`; main vẫn ở `f1c4bb2`, chưa merge PR này.

Đã bổ sung hồi quy chọn phạm vi cho root batch launcher, wrapper PowerShell/batch, scripts/deploy và infra: thay đổi triển khai chạy web/launcher; hạ tầng chạy mọi nhóm. Mỗi push còn phải qua check mới trên đúng head PR. File CI/Dependabot trong nhánh chưa merge không đồng nghĩa đã áp dụng làm cấu hình mặc định của main.

Chỉ owner `NV-DuyManh` quyết định merge sau required checks/discussions. Approval của người khác không cấp quyền merge. Không tự approve hoặc dùng token để tự thực hiện quyết định thay owner. Auto-delete không xóa lịch sử đóng góp, nhánh local hoặc nhánh còn PR mở. Quy tắc review cũ đã được thay bằng yêu cầu owner-only trong cả tài liệu và JSON chính sách.

Đã PUT lại ruleset `24461306` và GET xác nhận `required_approving_review_count=0`, `require_extra_approval_for_unattributed_changes=false`; ruleset `26539651` vẫn chỉ cho user ID 154242112 (`NV-DuyManh`) bypass update ở chế độ pull_request. Không tồn tại thêm ruleset cũ bị bỏ quên; main vẫn protected và không bypass required Quality gate.

## Cảnh báo dependency hiện hữu

Sau khi bật security alerts, API GitHub trả đủ 167 cảnh báo mở trên default branch main: 17 critical, 84 high, 57 medium, 9 low. Có 84 mã advisory khác nhau; một advisory có thể xuất hiện ở nhiều manifest. Phân bố: 63 ở handoff OCR `requirements-verified.txt`, 58 ở runtime `requirements-lock.txt`, 41 ở runtime `requirements.txt`, 1 ở runtime `uv.lock`, 4 ở `package-lock.json`.

Đây là cảnh báo từ manifest trên main, không phải bằng chứng 167 lỗi đều có thể khai thác trong tiến trình đang chạy. Cũng không được kết luận an toàn chỉ vì một số manifest thuộc handoff cũ. Cần triage phiên bản/phạm vi sử dụng, cập nhật dependency theo từng PR và chạy hồi quy OCR/ảnh/giọng trước khi thay major hoặc khóa môi trường nghiên cứu. Governance này không nâng hàng loạt thư viện để che cảnh báo; không tuyên bố dự án sạch bảo mật. Snapshot đầy đủ lưu local trong `dependency-alerts-all.ndjson` bên cạnh backup cấu hình.

## Sửa launcher chờ xác nhận PowerShell

Probe `/internal/v1/tutor/runtime` trong `scripts/dev/start-all.ps1` thiếu `-UseBasicParsing`, khác các probe web còn lại. Windows PowerShell 5.1 sau cập nhật bảo mật có thể hỏi xác nhận trước khi phân tích response, chặn khởi động tự động. Đã thêm đúng switch vào probe, giữ nguyên header xác thực, timeout và kiểm tra readiness; không hạ policy bảo mật hệ thống.

Regression trong `local-env.test.ps1` kiểm tra đủ 4 Invoke-WebRequest của launcher phải dùng basic parsing; CI chạy cả pwsh và Windows PowerShell 5.1. Local cả hai đạt. Thử chính câu lệnh probe qua HTTP loopback tạm với khóa tổng hợp ở chế độ NonInteractive đạt trên 5.1.26100.9711 và 7.6.5, không gọi dịch vụ thật hoặc in khóa. Không chạy lại toàn bộ hệ thống đang dùng để kiểm tra việc này. Skills applied cho bản sửa: ponytail, mathvision-quality (đường dẫn và lý do trong mục Skills Applied bên dưới).

Nguồn hành vi PowerShell: [Microsoft Support](https://support.microsoft.com/en-us/servicing/os/windows/2025/12/powershell-5-1-invoke-webrequest-preventing-script-execution-from-web-content).

## Sửa race khi khởi động lại worker Windows

Danh sách Celery có thể chứa cả tiến trình cha và con. `taskkill /T` dừng cây cha trước, làm PID con trong snapshot cũ không còn tồn tại; Windows PowerShell 5.1 với ErrorActionPreference Stop biến stderr native thành NativeCommandError dù có `2>$null`. Đã dùng helper capture stdout/stderr và timeout hiện có, đọc lại PID/CreationDate và định danh checkout trước khi dừng; bỏ qua tiến trình đã thoát hoặc PID đã được tái sử dụng. Sau lệnh dừng, nếu worker cũ vẫn còn sống thì báo WORKER_STOP_FAILED và không tạo worker thay thế. Đọc lại danh sách worker sau vòng dừng để tránh tạo trùng.

Kiểm thử local `scripts/test/test_service_runtime_identity.ps1` trên Windows PowerShell 5.1 và pwsh 7 đạt: các ca định danh sẵn có, 9 tình huống dừng worker/race/timeout, lỗi process-not-found từ taskkill thật với PID không tồn tại và listener TCP ngoài dự án vẫn được giữ nguyên. `local-env.test.ps1` cũng đạt trên cả hai shell; actionlint và git diff --check của các file sửa đạt. `npm run check:governance` đạt 8 tests trong working tree hiện tại, gồm thay đổi artifact policy của chat dọn dẹp chưa được đưa vào commit bản sửa này. CI bổ sung suite định danh vào step PowerShell 5.1; kết quả local không thay thế kết quả CI của commit mới.

Chạy thật `scripts/start-all.bat` trên máy trả exit code 0 và READY_FOR_CORE_DEMO: Docker, PostgreSQL, MinIO, Redis, Spring, FastAPI, xác thực tutor nội bộ, Celery, Portal/Teacher/Admin đều PASS. Lượt quan sát đầy đủ xác nhận các dịch vụ hiện hành được tái sử dụng; không tuyên bố đây là bằng chứng tất cả tình huống race đều xảy ra trong lần chạy thật. Student Metro chưa chạy; không có bằng chứng Expo Go/thiết bị thật trong bản sửa này. Skills applied: ponytail, mathvision-quality, mathvision-review.

## Nguồn và phần không lấy

Tham chiếu governance CODEGYM ở revision `667b580f89d63c7caf176d26869a2b2dbb5e25c8`; chi tiết trong `docs/engineering/skill-provenance.md`. Không nhập Maven/MySQL, mã CF/QA, luật hóa đơn/đơn hàng, skill trùng, prototype daemon, bot AI trả phí hoặc auto-merge. Giữ Catalog Bot hiện có.

## Bổ sung kiểm thử trình duyệt

Thêm Playwright 1.64.1 khóa phiên bản, 13 tình huống trên hai viewport Chromium (26 lượt). Build Portal/Teacher/Admin production riêng trong `.local-artifacts/browser/`, API fixture offline; không ghi đè dist đang dùng hoặc gọi dịch vụ thật. `Web checks` chạy browser sau lint/contracts/build và upload report/trace/ảnh tổng hợp khi lỗi, retention 7 ngày. Routing CI nhận diện cả `tests/browser/` và `playwright.config.mjs`.

Lượt đầu phát hiện lỗi thật Teacher logout: `clearTokens` phát event dẫn tới `/login`, effect trang login có thể chuyển về Portal root và thắng điều hướng `/logout`, bỏ sót xóa phiên Portal. Sửa bằng ref đánh dấu explicit logout trước khi clearTokens để chỉ luồng logout quyết định chuyển trang. Ca browser giữ kiểm tra xóa token Portal và không vào lại dashboard sau logout. `npm run test:browser` sau sửa đạt 26/26 local Windows trong 39,1 giây, gồm build cả ba web; Unit/contracts Teacher 31/31 và lint không lỗi; cảnh báo Fast Refresh đã có vẫn còn. CI cần chạy lại trên commit mới, không tính các lượt đang phát triển thất bại là đạt.

Giới hạn: production frontend thật, API giả lập; Student chỉ kiểm entry `/study/`, không test toàn bộ nội dung Student. Không thay backend authority, không có bằng chứng thiết bị thật hoặc kiểm thử OCR/giọng từ bộ browser này. Hướng dẫn và chi tiết phạm vi: `docs/engineering/browser-testing.md`.

## Kiểm tra trước merge được owner cho phép

Owner đã yêu cầu merge sau khi nghiệm thu local. CI `41866441567` trên `9e31a5d` chặn đúng vì browser đạt 25/26: test Teacher hết phiên đếm gộp refresh của Teacher và Portal thành hai yêu cầu. Trace mạng chứng minh một POST từ `https://teacher.mathvision.test` lúc 16:24:39.654Z và một POST từ `https://portal.mathvision.test` lúc 16:24:40.058Z, đều 401; không phải hai lần refresh của cùng ứng dụng. Phiên Portal được khởi tạo lại khi Teacher chuyển về trang chủ, nên thời điểm assertion cũ khiến kết quả chập chờn.

Sửa fixture ghi origin của request; assertion mới đợi Portal xóa token, kiểm đúng một refresh cho mỗi origin, tổng số đúng theo luồng và mở lại dashboard không phát sinh refresh nữa. Không sửa production auth, tăng timeout hoặc bật retry để làm xanh. Local `npx playwright test --grep "expired credentials" --repeat-each=3` đạt 12/12 trong 37,7 giây; `npm run test:browser` đạt 26/26 trong 40,3 giây. CI phải chạy lại trên head chứa bản sửa; không dùng kết quả head cũ để merge. Artifact CI tổng hợp lưu local ở `.local-artifacts/merge-review-20261104/`; không commit trace/log.

Skills applied cho kiểm tra tích hợp: mathvision-workflow, mathvision-review, mathvision-quality.

## Tích hợp dọn kho theo yêu cầu owner

Owner yêu cầu commit phần dọn và đưa vào main. Nhánh cleanup mới tách từ `399a7b7f604b8057a2ecf24391f0309e5d490a77`; không tiếp tục ghi vào nhánh task đã merge. Rà lại 921 tệp đã loại: 866 báo cáo/hiện vật cũ, 55 script kiểm chứng một lần và preview. Đối chiếu đủ 921 bản sao với SHA-256 và byte count của hai manifest; tổng 60.501.325 byte. Kho khôi phục vẫn tồn tại trong Recycle Bin của owner; không làm rỗng thùng rác. Git history tại revision gốc cũng giữ bản tracked cho máy clone khác. Đây là số nội dung loại khỏi cây hiện tại, không phải số byte ổ đĩa hay Git history đã được giải phóng.

Giữ 17 tệp báo cáo/biên nhận đang dùng, provenance tác giả và model/dataset. Rà các source/config còn giữ không thấy tham chiếu tới báo cáo bị xóa; tham chiếu script cũ chỉ còn trong inventory attribution và ghi chép lịch sử được giữ lại. Các link Markdown của tài liệu sửa và CONTRIBUTORS không hỏng. Bổ sung đường đọc báo cáo cũ từ Git vào report/README.md để người clone không phụ thuộc đường E hay Recycle Bin. Dọn thêm 77 thư mục report/reports rỗng bằng thao tác không đệ quy; không xóa tệp mới trong lần dọn thư mục này.

Giữ thay đổi `.gitignore`, tài liệu và guard CI do chat cleanup chuẩn bị: từ chối tệp tracked nhưng bị ignore bởi chính repo, kể cả git add -f; không dùng ignore cá nhân làm policy. Kiểm thử guard gồm path có khoảng trắng/ký tự shell, local-only, ngoại lệ biên nhận, tệp bị ép add và checkout CLI thật. Không đổi mã runtime, dependency/lockfile, launcher, model, database, secrets hoặc demoUI.

Local PASS: `npm run check:governance` (8), Metro/QR node tests (2), launcher/migration-runner unittest (9), Student typecheck, 3 pytest đọc checklist/biên nhận giữ lại, git diff --check; pytest còn 4 cảnh báo deprecation có sẵn. Audit manifest, tham chiếu và danh sách thư mục rỗng ở `.local-artifacts/cleanup-review-20261104/`, không commit log/trace/ảnh/manifest local. CI PR sẽ kiểm lại cây commit sạch trước merge; không tuyên bố subset local đã test toàn bộ app hay thiết bị thật.

Skills applied cho cleanup: ponytail, mathvision-review, mathvision-quality; đường dẫn/lý do/phạm vi trong mục Skills Applied dưới đây. Không viết lại lịch sử để giảm số thống kê đóng góp.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Quy trình tập trung, không thêm framework/SDK hoặc wrapper trùng.
  - Applied to: Registry, bot Job Summary, CI, dừng worker và cleanup dùng helper/công cụ sẵn có, không thêm framework dọn tệp.
- `skill-creator`
  - SKILL.md: `C:/Users/Admin/.codex/skills/.system/skill-creator/SKILL.md`
  - Why selected: Tạo skill dự án phù hợp và không mở rộng quyền ngoài yêu cầu.
  - Applied to: Bốn SKILL.md ngắn, mô tả chọn đúng phase, quick_validate.
- `mathvision-review`
  - SKILL.md: `.agents/skills/mathvision-review/SKILL.md`
  - Why selected: Review chính sách, an toàn dữ liệu và tính đúng của bằng chứng trước tích hợp.
  - Applied to: Quyền workflow, ruleset không bypass chất lượng, bảo vệ PID/checkout khi dừng worker, giữ provenance/biên nhận khi cleanup, phân biệt local/CI và mock/live.
- `mathvision-quality`
  - SKILL.md: `.agents/skills/mathvision-quality/SKILL.md`
  - Why selected: Kiểm thử hành vi web bằng trình duyệt, giữ bằng chứng và giới hạn chính xác.
  - Applied to: Fixture offline, 401/403/503, SSO/phiên/đăng xuất, form/filter, CI failure artifacts, hồi quy launcher trên PowerShell 5.1/7, guard artifact và test phụ thuộc biên nhận sau cleanup.
- `mathvision-workflow`
  - SKILL.md: `.agents/skills/mathvision-workflow/SKILL.md`
  - Why selected: Owner đã cho phép tích hợp qua PR sau kiểm tra đúng revision.
  - Applied to: Kiểm tra head/base/checks/discussions, giữ attribution và tách thay đổi dọn dẹp chưa commit.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: Browser test phát hiện race điều hướng trong React Teacher AuthProvider.
  - Applied to: Ref trạng thái logout, tránh effect chuyển trang cạnh tranh; giữ cache/session cleanup.
