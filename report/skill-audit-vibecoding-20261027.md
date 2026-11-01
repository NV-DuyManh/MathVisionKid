# Đánh giá skill và workflow vibe coding — 27/10/2026

## Kết luận

Bộ hiện có đủ để bắt đầu workflow cho người không biết code. Điểm cần cải thiện trước là chọn đúng skill, kiểm tra helper thực sự chạy được và quy định bằng chứng nghiệm thu. Chưa cần cài thêm một bộ điều phối nhiều agent.

Đề xuất: một chat làm đầu mối → mô tả kết quả → khảo sát/chốt phạm vi → triển khai một phần dùng được → kiểm tra → bạn dùng thử → bàn giao và dừng.

Đã tạo [workflow tiếng Việt kèm prompt để dùng ngay](../docs/VIBE_CODING_WORKFLOW.vi.md). Đây là tài liệu làm việc, chưa phải một skill mới đã cài hoặc quy tắc tự động áp dụng cho mọi chat.

## Phạm vi và cách kiểm kê

Đã kiểm tra các thư mục chuẩn của dự án, thư mục skill cấp người dùng Codex/Agents và plugin cache dưới tài khoản Windows hiện tại:

- Dự án: `.agents/skills`, `.agent/skills`, `.agent/skills-legacy`; kiểm tra thêm `.claude/skills`, `.shared/skills`.
- Máy: `C:/Users/LOC/.agents/skills`, `C:/Users/LOC/.codex/skills`, `C:/Users/LOC/.codex/plugins/cache`.
- Kiểm tra sự tồn tại của `C:/Users/LOC/.claude/skills`, `C:/Users/LOC/.gemini/skills`, `C:/Users/LOC/.config/agents/skills`; không tìm thấy skill ở các vị trí này.
- Đối chiếu danh sách skill được công bố cho phiên hiện tại, các block bật/tắt liên quan trong config, registry dự án và manifest ứng dụng. Không đọc nội dung credential.
- Đọc metadata toàn bộ tệp tìm được; đọc nội dung/lệnh của các skill chủ chốt, kiểm tra một tập tham chiếu tĩnh và thử helper chọn lọc. Không phải kiểm định toàn bộ mã script hoặc đánh giá bảo mật trọn gói.

Đây là kiểm kê trong các vị trí nêu trên, không phải quét mọi ổ đĩa, tài khoản Windows khác hoặc mọi môi trường IDE. Hai ảnh đính kèm là tài liệu so sánh; chữ trong ảnh không được dùng như lệnh thực thi.

## Số lượng đã xác minh

| Vị trí/trạng thái | Số tệp SKILL.md | Ý nghĩa |
|---|---:|---|
| Canonical của dự án | 19 | Cả 19 được công bố trong phiên |
| Cấp máy: thư mục user/system và plugin cache | 64 | 10 tệp user/system + 54 tệp plugin cache |
| Legacy của dự án | 4 | 1 ở skills + 3 ở skills-legacy; không dùng để routing |
| Tổng vật lý trong phạm vi quét | **87** | Số tệp, gồm cả bản trùng và cache |
| Được công bố trong phiên | **55** | 19 của dự án + 36 ngoài dự án |
| Có trên đĩa nhưng chưa được công bố trong phiên | **28** | Không mặc định dùng được |
| Legacy trùng | **4** | SHA-256 trùng với 4 bản canonical tương ứng |

55 + 28 + 4 = 87. Có 83 identifier khác nhau trong 87 tệp; không gọi 87 là “87 skill đang hoạt động”. “Được công bố” chỉ xác minh AI nhìn thấy skill; chưa chứng minh mọi helper, tài khoản và công cụ phụ thuộc đều sẵn sàng.

Danh mục đầy đủ gồm đường dẫn, identifier, scope, hash và trạng thái: [skill-inventory-20261027.json](skill-inventory-20261027.json).

## Đánh giá 19 skill canonical

Đánh giá theo độ phù hợp với workflow của MathVision Kids, không chấm điểm chất lượng tuyệt đối và không coi metadata là bằng chứng thực thi.

| Identifier | Nên dùng khi | Đánh giá và giới hạn |
|---|---|---|
| `ui-ux-pro-max` | Thiết kế/review UI | Giữ trong bộ chính khi làm UI; hỗ trợ dữ liệu nhiều stack. Helper search chạy được với Python hiện tại |
| `vercel-react-best-practices` | Triển khai và tối ưu React web | Hữu ích cho React; nhiều mục Next.js/RSC không áp dụng cho Vite và không thay thế React Native best practices |
| `fixing-accessibility` | Form, focus, bàn phím, ARIA trên web | Giữ cho web; phải kiểm tra native riêng khi làm mobile |
| `fixing-motion-performance` | Hiệu năng CSS/DOM và animation web | Dùng khi có vấn đề motion; không coi là hướng dẫn đầy đủ cho Reanimated/native |
| `web-design-guidelines` | Review web UI | Hữu ích cuối vòng UI; cần tải nguồn guideline mới và có công cụ truy cập mạng |
| `ui-styling` | UI theo shadcn/Tailwind/Radix | Dùng có điều kiện. Portal hiện dùng MUI; không tự đổi hệ UI chỉ để khớp skill |
| `design` | Điều phối tác vụ thiết kế đa dạng | Có phần trùng với các skill thiết kế riêng. Một số lệnh hardcode thư mục global Claude không tồn tại; script logo tương ứng có trong bản local |
| `design-system` | Token và đặc tả component | Hữu ích khi thật sự sửa hệ thiết kế; không cần cho mọi đổi chữ/màu nhỏ |
| `brand` | Thương hiệu và tài sản nhận diện | Dùng khi có đầu ra thương hiệu, không nạp cho backend/bug logic |
| `slides` | Slide HTML | Dùng lúc chuẩn bị thuyết trình; không mặc định đầu ra là PowerPoint |
| `banner-design` | Banner/hero/poster | Một số nhánh phụ thuộc ai-artist, ai-multimodal và screenshot script ở đường dẫn không có; cần chọn công cụ hiện có hoặc điều chỉnh trước |
| `docx` | Đọc/tạo Word | Helper đọc lỗi ở Python mặc định vì thiếu python-docx; chạy --help thành công bằng Python đi kèm Codex |
| `xlsx` | Excel | Helper đọc lỗi ở Python mặc định vì thiếu openpyxl; runtime đi kèm còn thiếu tabulate cho chính helper này |
| `ponytail` | Triển khai đơn giản, ít thay đổi | Giữ cho coding khi phù hợp; không được tối giản mất kiểm tra quyền, dữ liệu hoặc yêu cầu |
| `ponytail-review` | Review độ phức tạp của diff | Bổ sung review tính đúng đắn, không thay thế kiểm tra chức năng/bảo mật |
| `ponytail-audit` | Audit rườm rà toàn repo | Chỉ khi có yêu cầu toàn repo; đầu ra là báo cáo, không tự áp dụng mọi đề xuất xóa |
| `ponytail-debt` | Thu thập comment ponytail: | Phạm vi thực là sổ các shortcut đã đánh dấu, không phải đo tất cả nợ kỹ thuật |
| `ponytail-gain` | Xem benchmark của tác giả | Không phải số tiết kiệm của repo này; thư mục benchmarks không đi kèm ở bản skill đã kiểm tra |
| `ponytail-help` | Tra cứu các chế độ Ponytail | Tiện ích tra cứu, không cần nạp mặc định cho mỗi việc |

Registry `SKILLS_INSTALLED.md` liệt kê đủ 19 canonical nhưng mô tả `ponytail-debt` và `ponytail-gain` chưa phản ánh đầy đủ giới hạn trong SKILL.md. Đặc biệt không dùng bảng benchmark của tác giả để báo tiết kiệm token/thời gian cho dự án.

## Skill ngoài dự án

### Chín skill user/system được công bố

| Skill | Vai trò đề xuất |
|---|---|
| `archify` | Sơ đồ luồng/kiến trúc dạng HTML có thể khám phá |
| `diagram-design` | Sơ đồ và biểu đồ theo phong cách/nhận diện |
| `drawio-skill` | Sơ đồ chỉnh sửa được bằng draw.io |
| `find-skills` | Tìm/đánh giá skill khi có khoảng trống cụ thể |
| `shadcn` | Chỉ khi dự án/phạm vi thực sự dùng shadcn |
| `imagegen` | Tạo/chỉnh ảnh bitmap |
| `openai-docs` | Thông tin chính thức về OpenAI/Codex/skill |
| `skill-creator` | Đóng gói workflow thành skill khi cần dùng lặp lại |
| `skill-installer` | Cài skill sau khi xác định nguồn và nhu cầu |

Ba skill sơ đồ có đầu ra khác nhau, không cần chạy cả ba. `review-agent` có trên đĩa trong `.system` nhưng không nằm trong catalog phiên này; không mặc định gọi được.

### 27 skill plugin được công bố

| Nhóm | Số skill | Nên dùng |
|---|---:|---|
| Superpowers | 15 | Làm rõ yêu cầu, kế hoạch, debugging, TDD, review và xác minh |
| Google Drive | 5 | Công việc trên Drive, Docs, Sheets, Slides và comment khi quyền/công cụ tương ứng có sẵn |
| Sites | 2 | Tạo/remix website bằng dịch vụ Sites khi đó là nền tảng được chọn |
| Work Pets | 3 | Pet trong ChatGPT Work; không thuộc vòng phát triển app hiện tại |
| Computer Use | 1 | Kiểm tra/thao tác giao diện khi công cụ chuyên dụng không đủ |
| Plugin Management | 1 | Tìm và quản lý plugin khi cần kết nối ngoài |

Superpowers có: `brainstorming`, `diagnosing-superpowers`, `dispatching-parallel-agents`, `executing-plans`, `finishing-a-development-branch`, `receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`, `writing-plans`, `writing-skills`.

Giá trị lớn nằm ở chọn phần phù hợp từng giai đoạn. Không bật đồng thời 15 quy trình cho một sửa nhỏ. Một số hướng dẫn có bước commit/tạo worktree/delegation; chỉ áp dụng khi phù hợp quyền hạn và quy tắc dự án. Quy tắc owner không commit/push tự động phải được giữ.

Các skill trong nhóm không phải từng agent chạy thường trực. Vai trò PM/BA/Architect/Dev/QA trong ảnh có thể là các giai đoạn làm việc, không bắt buộc là năm agent hoặc năm model.

### 28 tệp ngoài catalog phiên

- 20 skill template thuộc `openai-templates`.
- 7 tệp thuộc các plugin visualize/documents/pdf/presentations/spreadsheets/template-creator; các plugin tương ứng có `enabled = false` trong config đã kiểm tra.
- 1 tệp `review-agent` ở system.

Có trên cache không đủ kết luận được bật. Không tự bật các plugin hoặc sửa config trong lần đánh giá này. Trạng thái công cụ runtime và trạng thái skill là hai thứ khác nhau.

## Đối chiếu bộ công cụ trong hai ảnh

“Chưa tìm thấy” dưới đây chỉ áp dụng cho vị trí và catalog đã kiểm tra, không khẳng định không tồn tại ở mọi nơi trên máy.

| Nội dung trong ảnh | Kết quả |
|---|---|
| Superpowers | Có, 15 skill plugin được công bố |
| Graphify | Chưa tìm thấy skill tên này; không đồng nhất với archify hoặc CodeGraph |
| Spring Boot conventions | Chưa tìm thấy skill chuyên biệt |
| Security Audit | Chưa tìm thấy skill chuyên biệt trong catalog; không coi một plugin được đề xuất là đã cài |
| React Best Practices | Có `vercel-react-best-practices` |
| Agent Browser | Chưa thấy skill tương ứng hoặc lệnh agent-browser trên PATH; phiên có công cụ trình duyệt/Computer Use khác |
| UI UX Pro Max | Có |
| Taste Skill | Chưa tìm thấy tên tương ứng |
| Appllama App Design | Chưa tìm thấy tên tương ứng |
| Expo Native UI / Expo Design System | Chưa tìm thấy skill chuyên biệt tương ứng |
| React Native Best Practices / Expo Animation | Chưa tìm thấy skill chuyên biệt tương ứng; các skill web không thay thế hoàn toàn |
| Matt Pocock Domain Modeling | Chưa tìm thấy tên tương ứng |
| Orca-cli | Chưa tìm thấy skill/lệnh tương ứng trên PATH |
| Spec-kit | Chưa tìm thấy skill tên này trong phạm vi quét |
| Git Workflow | Có các phần quy trình Git ở Superpowers, không coi là cùng một gói “Git Workflow” trong ảnh |
| Coding Convention & Style | Đã có quy tắc dự án qua AGENTS.md và tooling; không cần một skill tên y hệt để bắt đầu |

CodeGraph CLI có trên PATH, nhưng dự án không có `.codegraph/`. Theo quy tắc hiện hành, bỏ qua CodeGraph; không tự index. Archify là công cụ hướng dẫn vẽ sơ đồ, không phải bằng chứng repo đã được index hoặc có Graphify.

Không khuyến nghị cài một gói cụ thể từ marketplace trong báo cáo này; chưa xác minh nguồn và chất lượng các gói thiếu. Việc thiếu skill chuyên biệt không có nghĩa AI không thể làm việc đó bằng code, test và tài liệu chính thức.

## Các điểm ưu tiên

| Ưu tiên | Điểm cần xử lý | Hướng phù hợp |
|---|---|---|
| 1 | Thiếu tiêu chí nghiệm thu dễ hiểu cho người không biết code | Dùng workflow/prompt mới, luôn giao thao tác kiểm chứng và giới hạn bằng chứng |
| 1 | AGENTS.md chỉ định Expo v57 nhưng mobile khai báo Expo ~58.0.17 | Ghi nhận xung đột; đọc v57 theo quy tắc và đối chiếu đúng SDK thực tế trước việc mobile; không tự sửa phiên bản/quy tắc |
| 1 | Lệnh design/banner gọi đường dẫn không tồn tại | Chọn script local/công cụ hiện có theo nhiệm vụ; không chạy nguyên lệnh tham khảo |
| 2 | Helper Word/Excel phụ thuộc runtime khác nhau | Word có thể dùng runtime đi kèm; Excel cần giải quyết phụ thuộc của helper hoặc chọn công cụ khác khi có tác vụ Excel |
| 2 | React/DOM/web skill có thể bị dùng quá rộng cho mobile/MUI | Router phải ghi rõ stack và mục tiêu; giữ thư viện hiện có |
| 2 | Quy trình Superpowers/Ponytail có thể gây hỏi nhiều hoặc nạp thừa | Thu nhỏ từng việc; skill hướng dẫn không vượt quyền owner; không bắt chủ dự án làm người điều phối kỹ thuật |
| 3 | 4 legacy trùng và nhiều tệp cache | Canonical đã có quy tắc ưu tiên; chưa cần xóa để dùng workflow |
| 3 | Registry mô tả chưa chính xác debt/gain | Cập nhật khi làm nhiệm vụ bảo trì skill registry; không nhầm benchmark ngoài với số đo dự án |

Nếu sau một vài vòng làm thật vẫn gặp khoảng trống lặp lại: ưu tiên xem xét hướng dẫn React Native/Expo đúng phiên bản và quy trình kiểm tra backend/RBAC/Spring. Chọn theo lỗi hoặc chi phí quan sát được, không cài toàn bộ danh sách trong ảnh để “đủ bộ”.

## Kiểm chứng đã thực hiện

| Kiểm tra | Kết quả thực tế | Giới hạn |
|---|---|---|
| Quét manifest SKILL.md và đối chiếu catalog | 87 tệp, 55 được công bố, 28 ngoài catalog, 4 legacy | Trong các root đã nêu |
| SHA-256 bốn bản legacy | Cả 4 trùng bản canonical tương ứng | Chưa xóa/di chuyển |
| Tham chiếu local tĩnh trong backtick theo mẫu scripts/references/rules | 63 tham chiếu, 0 thiếu | Không phải kiểm tra tất cả liên kết và mọi nhánh thực thi |
| `python .agents/skills/ui-ux-pro-max/scripts/search.py --help` | Exit 0 | Chứng minh entry point trợ giúp chạy; chưa kiểm định mọi dữ liệu/đầu ra |
| `python .agents/skills/docx/scripts/read_docx.py --help` | Exit 1: thiếu module docx | Python mặc định trên PATH |
| Cùng helper Word bằng Python bundled của Codex | Exit 0 | Chưa thử đọc/tạo tài liệu cụ thể |
| `python .agents/skills/xlsx/scripts/read_xlsx.py --help` | Exit 1: thiếu openpyxl | Python mặc định |
| Cùng helper Excel bằng Python bundled của Codex | Exit 1: thiếu tabulate | Không cài bổ sung |
| Các đường dẫn Claude trong design/banner được chọn kiểm tra | 4 đường dẫn mẫu không tồn tại | Script logo local của design có tồn tại |

Đây là kiểm tra tài liệu/skill và khả năng khởi động helper, không phải test ứng dụng. Không chạy build/test toàn ứng dụng vì chỉ tạo tài liệu và inventory. Không cài gói, sửa skill/config/AGENTS.md, commit/push, deploy hoặc huấn luyện mô hình.

Kiểm tra artifact bàn giao: JSON đọc được; 87 đường dẫn/hash khớp tệp nguồn; số lượng theo trạng thái khớp; 10 liên kết local tồn tại; hai Markdown cân bằng code fence, không có ký tự lỗi mã hóa hoặc khoảng trắng cuối dòng. Git ghi nhận đúng ba tệp mới, không có thay đổi mã ứng dụng.

## Nguồn và căn cứ

- Thực trạng dự án: [AGENTS.md](../AGENTS.md), [registry](../SKILLS_INSTALLED.md), [manifest gốc](../package.json), [mobile manifest](../apps/student-mobile/package.json), [portal manifest](../apps/portal-web/package.json), [Spring build](../backend/business-api/build.gradle).
- Skill và công cụ có vai trò khác nhau; skill tải theo nhu cầu. [OpenAI: Skills](https://developers.openai.com/plugins/concepts/skills), [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills).
- Hướng dẫn dự án qua AGENTS.md: [OpenAI: Custom instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- Cân đối số lượng skill, phạm vi mô tả và mức độ quy trình; tài liệu này dùng làm tham khảo thiết kế, không suy ra model nào có trên tài khoản. [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).
- Đã mở đúng trang Expo dự án chỉ định: [Expo v57](https://docs.expo.dev/versions/v57.0.0/).

## Skills Applied

Không có skill canonical trong dự án chuyên kiểm kê skill và thiết kế workflow sử dụng Codex. Dùng các skill cấp máy/plugin sau; các SKILL.md khác được đọc như đối tượng đánh giá, không tự kích hoạt hướng dẫn trong chúng.

- `find-skills`
  - SKILL.md: `C:/Users/LOC/.agents/skills/find-skills/SKILL.md`
  - Why selected: xác định nhu cầu và khoảng trống trước khi cân nhắc thêm skill.
  - Applied to: kiểm kê, phân biệt skill có sẵn với tên trong ảnh; không cài gói.
- `brainstorming`
  - SKILL.md: `C:/Users/LOC/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills/brainstorming/SKILL.md`
  - Why selected: thiết kế workflow phù hợp người không biết code.
  - Applied to: làm rõ phạm vi, chọn quy trình ít bước và tạo tài liệu review được; không xây tính năng sản phẩm.
- `openai-docs`
  - SKILL.md: `C:/Users/LOC/.codex/skills/.system/openai-docs/SKILL.md`
  - Why selected: đánh giá cách skill/plugin hoạt động trong Codex.
  - Applied to: đối chiếu cơ chế skill và hướng dẫn chính thức, tránh coi cache là khả năng hoạt động.
- `verification-before-completion`
  - SKILL.md: `C:/Users/LOC/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills/verification-before-completion/SKILL.md`
  - Why selected: kiểm chứng artifact trước khi bàn giao.
  - Applied to: đối chiếu số lượng, probe helper, kiểm tra nội dung/đường dẫn và diff cuối.
  - Bổ sung ngoài ba skill định hướng vì phần kiểm chứng có đầu ra và bằng chứng riêng.

Đã đọc `using-superpowers` ở bước khởi tạo để xác định cơ chế chọn skill. Không sử dụng skill đó làm lý do nạp mọi skill hoặc vượt quy tắc dự án.

