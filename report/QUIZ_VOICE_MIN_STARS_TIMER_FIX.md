# Smart Quiz: Voice, tối thiểu 1 sao và timer

Ngày kiểm tra: 31/10/2026. Checkout `C:\MathVisonKid`, branch `main`, HEAD
`ca6629e`. Không commit, push, merge, deploy, reset hoặc clean Git trong tác vụ này.

## 1. Kết quả và giới hạn bằng chứng

- HTTP thật qua Spring → FastAPI → TTS Edge tạo được WAV cho **cả giọng nam và
  nữ**, trên **Digit Append và Fraction**. Đã giải mã, kiểm tra PCM16 mono
  16 kHz, độ dài, số frame và tín hiệu không im lặng; cache trả bytes giống hệt.
- Giao diện Student Web thực chạy ở kích thước 412×915 đã tải và phát cả bốn
  trường hợp qua audio player thật: `currentTime` tăng, player không pause/error.
  Đây là giải mã/phát trong Chrome headless, **không phải bằng chứng nghe qua loa
  Android/iPhone**. Không có thiết bị vật lý kết nối để xác nhận phần đó.
- Backend chấm lượt đúng độc lập 15/45/90 giây thành 3/2/1 sao. Có hướng dẫn
  nhận đúng 1 sao; PRACTICE không thưởng; CHALLENGE giữ quy tắc max và không
  cộng lặp. Migration V27 đã thử trên PostgreSQL QA rồi áp dụng thành công local.
- Runtime local cuối cùng: `READY_FOR_FULL_DEMO`, LAN PASS; Spring, FastAPI,
  Celery, MinIO, PostgreSQL, Redis và Metro PASS. AI diagnostics vẫn là FIXTURE;
  bằng chứng TTS ở đây dùng nhà cung cấp thật, không dùng âm thanh giả.

## 2. Voice: nguyên nhân và truy vết

Luồng hiện có là:

`QuizVoice → quizApi.audio → POST /api/v1/student/quizzes/{id}/narration`
`→ QuizNarration → POST /internal/v1/tutor/quiz/narration → render_audio`
`→ Edge TTS/ffmpeg → WAV bytes → saveNarration → Expo AudioPlayback`.

Đây là HTTP đồng bộ trả WAV, **không có job ID hoặc vòng polling Quiz Voice**.
Spring xác minh chủ sở hữu và quyền mở lời giải trước mọi lần gọi, kể cả khi
FastAPI đã cache audio. Không có URL audio công khai chứa token; native dùng
file `.wav` trong cache app, web dùng Blob URL có dispose.

### Bằng chứng từ đúng lượt trên điện thoại

`infra/local-runtime/logs/spring.log` ghi:

```text
14:43:09  POST .../7de51338-493b-426c-95b6-bc828a443e9e/submit
          status=200 durationMs=715 platform=ios
14:44:00  POST .../7de51338-493b-426c-95b6-bc828a443e9e/narration
          status=503 durationMs=40860 platform=ios
```

`infra/local-runtime/logs/fastapi.err.log` cùng khoảng thời gian:

```text
14:43:23  first_audio_ms=-1 bytes=0 outcome=NoAudioReceived
14:43:26  first_audio_ms=-1 bytes=0 outcome=NoAudioReceived
14:43:29  category=NoAudioReceived
14:44:00  total_ms=30016 outcome=cancelled; category=TimeoutError
```

Vì vậy nút bấm **có gửi request**, đi đúng Spring/FastAPI, nhưng lần này provider
không trả đủ audio trong deadline. Không có bằng chứng thiếu key/quota TTS hoặc
Android không hỗ trợ định dạng ở lần thất bại này: nó kết thúc bằng 503 trước
khi có file để player mở. Ảnh cũng là iPhone, khớp `platform=ios` trong log.

### Vì sao trải nghiệm trông như loading vô hạn

UI cũ chỉ có `busy` quanh Promise HTTP và thông báo chung “Đang xử lý…”. Nó dựa
vào timeout Axios 45 giây, không có deadline riêng bao trùm async interceptor,
refresh/xử lý native transport. Không đổi giọng được trong khi busy. Audio player
chưa báo ngược lỗi tải về QuizVoice để lấy lại file. Những Promise không kết
thúc được tái hiện bằng regression test; UI mới thoát sau deadline và thử lại được.

**Không kết luận ảnh tĩnh chứng minh Promise trên chính điện thoại đã treo vĩnh
viễn**: log đo được request kết thúc 503 sau 40,86 giây. Phần đã xác minh là TTS
thất bại/chậm và thiếu bảo đảm lifecycle ở UI; không đổ lỗi cho provider thay cho
việc sửa lifecycle.

### Sửa

- Deadline tổng 45 giây bằng Promise race + AbortController, bao trùm cả client
  pipeline; luôn thu hồi timer, listener và trạng thái request hiện hành.
- Hủy khi đổi giọng, đổi Quiz, blur/unmount hoặc background. Kết quả cũ chỉ được
  nhận nếu vẫn là đúng controller hiện hành; không ghi đè audio giọng/bài mới.
- Chặn nhiều lượt bấm cho cùng request. Đổi giọng trong khi tạo vẫn được; sau khi
  đổi, bấm “Nghe cách giải” để tạo đúng giọng mới.
- Phân biệt chưa phát, đang tạo, đang mở, sẵn sàng, đang phát và lỗi. Player thật
  hiển thị trạng thái đang phát; lỗi/timeout có nút tải lại, phần chữ luôn còn.
- Player có giới hạn mở file 12 giây và watchdog phát 6 giây; QuizVoice nay nhận
  callback lỗi để bỏ asset hỏng và tải lại. Không thay player bằng mock trong app.
- FastAPI giữ tối đa hai render khác nhau, cho phép chuyển giữa hai giọng; cùng
  owner/Quiz/voice/hash lời giải dùng single flight và cache TTL 15 phút. Giới hạn
  8 entries/24 MiB được giữ. Nội dung hoặc challenge khác không dùng lẫn cache.
- Khi provider có empty turn, giữ các chunk đã tạo và thử lại tối đa một lần trong
  deadline gốc 32 giây. Retry transport vốn có vẫn bị deadline đó giới hạn.
- Log mới chỉ ghi Quiz ID, voice, cache hit/miss, category, bytes và thời lượng;
  không thêm token, key, nội dung lời giải hoặc URL provider vào log.

Log mới `fastapi-runtime.err.log` và QA Spring xác nhận cả bốn WAV HTTP 200.
Ví dụ Fraction: nam 150.608 bytes/4.358 ms, nữ 145.232 bytes/12.327 ms.
Provider vẫn có thể gián đoạn; khi đó hệ thống trả lỗi có giới hạn và cho thử lại,
không tự đổi giới tính giọng, không phát âm thanh giả.

## 3. Sao: nguyên nhân, chính sách và dữ liệu cũ

Nguyên nhân trực tiếp là `QuizService.stars(..., viewed)` cũ trả `0` khi đã xem
lời giải. Cả UI và các test cũ phản ánh chính sách đó. Đã sửa hàm chấm điểm
backend: đúng có hướng dẫn = 1; đúng độc lập ≤30s = 3, ≤60s = 2, sau đó = 1.
PRACTICE được kiểm tra riêng trước hàm chấm điểm và vẫn ghi attempt 0 sao vì
đây là lượt không thưởng; UI không hiển thị khung 0/3 sao cho PRACTICE.

`quiz_attempts.stars` là thưởng của lượt đó, `student_quizzes.stars` là kỷ lục.
DTO trả hai giá trị qua `attempt.stars` và `quiz.stars`; UI dùng lượt đúng gần
nhất để hiển thị kết quả, kèm kỷ lục riêng. Không ép 0 thành 1 ở frontend.
`bestStars=max(bestStars, earnedStars)` và tổng sao vẫn là tổng kỷ lục các Quiz
không INVALIDATED. Duplicate request giữ nguyên attempt/reward, không cộng lặp.
Chỉ trả lời sai/chưa hoàn thành không được thưởng.

### Flyway V27

Không sửa V21/V22/V23 hay migration đã áp dụng. V27:

1. Chọn đúng attempt **correct**, 0 sao, mode NONE/CHALLENGE, có bằng chứng đã
   xem lời giải. Trường hợp snapshot thiếu chỉ suy ra khi mốc run/completion và
   cờ hoàn thành có hướng dẫn khớp; không cập nhật toàn bộ `stars=0`.
2. Lưu thưởng gốc vào `quiz_star_policy_adjustments` theo attempt ID, kèm policy,
   thưởng mới và thời điểm; sau đó cập nhật **giá trị thưởng** thành 1. Không
   xóa/tạo lại attempt; không đổi đáp án, câu hỏi, mode hay timestamp lịch sử.
   Điểm lịch sử gốc vẫn truy vết được trong ledger điều chỉnh, không bị mất.
3. Nâng kỷ lục bằng MAX các lượt đúng có thưởng, giữ kỷ lục cao hơn đã có.
4. Thêm CHECK: COMPLETED ở mode có thưởng phải có ít nhất 1 sao. Dữ liệu mơ hồ
   không suy đoán được sẽ khiến migration rollback để kiểm tra, không sửa mù.

Đã backup database local vào thư mục runtime bị Git ignore, clone riêng
`mathvision_voice_stars_timer_20261031`, chạy Flyway bằng JAR thật rồi so sánh.
Chỉ sau khi QA pass mới restart đúng Spring local và để Flyway áp dụng V27.

Kết quả local: **6 Quiz, 26 attempts giữ nguyên số lượng; 1 attempt điều chỉnh;
tổng sao 14 → 15; 0 Quiz COMPLETED có thưởng còn 0 sao**. Mọi trường lịch sử
ngoài thưởng giữ nguyên byte/giá trị khi đối chiếu JSON; V21/V22/V23 checksum
không đổi. Bản backup chứa dữ liệu riêng tư nên không đưa vào report/Git.

## 4. Timer `2407:52`: nguyên nhân chính xác

Quiz trong ảnh có mốc PostgreSQL UTC:

```text
started_at   = 2026-10-29T15:35:16.642040Z
completed_at = 2026-10-31T07:43:09.360516Z
elapsed_millis của attempt đúng = 144472719
```

Đó là **40 giờ 7 phút 52 giây**, không phải nhầm milliseconds/seconds. Hàm cũ
luôn định dạng `floor(seconds/60):ss` nên thành **2407:52**. Lượt này là NONE,
không phải replay kế thừa nhầm timer. Quy tắc đã có tính liên tục sau Start,
kể cả offline/background/lưu làm sau, để không giải ngoài giờ rồi nhận 3 sao.

Giữ chính sách và thời gian thật, không sửa timestamp cũ, không cắt 60 giây,
không reset về 0. Hàm mới hiển thị `h:mm:ss` từ một giờ và giải thích đó là tổng
thời gian kể cả rời bài; dưới một giờ dùng `m:ss`.

Display clock dùng `performance.now()` thay `Date.now()` sau baseline server,
tránh người dùng đổi đồng hồ máy làm timer nhảy. Foreground vẫn tải lại baseline
server. Server tính sao từ timestamp của mình; payload thời gian/sao tự thêm
không có quyền chấm điểm. Completed dùng duration server cố định, không tiếp
tục tăng. PRACTICE và CHALLENGE đều tạo mốc Start riêng; retry cùng replay giữ
đúng run hiện hành, không reset để gian lận. Đã kiểm tra HTTP và Spring tests.

## 5. Các file của bản sửa

Sản phẩm:

- `ai/runtime/app/tutoring/quiz_narration.py`
- `backend/business-api/src/main/java/com/mathvisionkids/api/quiz/QuizService.java`
- `backend/business-api/src/main/resources/db/migration/V27__quiz_assisted_completion_minimum_star.sql`
- `apps/student-mobile/src/features/quiz/QuizVoice.tsx`
- `apps/student-mobile/src/features/quiz/quizInput.ts`
- `apps/student-mobile/src/app/quiz/[quizId].tsx`
- `apps/student-mobile/src/app/quiz/index.tsx`

Tests và harness:

- `ai/runtime/tests/test_quiz_narration.py`
- `backend/business-api/src/test/java/com/mathvisionkids/api/quiz/QuizIntegrationTest.java`
- `backend/business-api/src/test/java/com/mathvisionkids/api/quiz/QuizMathTest.java`
- `apps/student-mobile/src/__tests__/quizVoice.test.tsx`
- `apps/student-mobile/src/__tests__/quizAudioLifecycle.test.tsx` (mới)
- `apps/student-mobile/src/__tests__/quizInput.test.ts`
- `apps/student-mobile/src/__tests__/quizStudent.test.tsx`
- `scripts/test/quiz_voice_min_stars_timer_qa.py` (mới)
- `scripts/test/quiz_voice_browser_qa.mjs` (mới)

Không thay dependency/secrets, không sửa các script/báo cáo PR review cũ. Ba WIP
có từ đầu tác vụ vẫn được giữ: Compose MinIO, test MinIO guard và diagnostics
Celery timeout. Các report untracked sẵn có cũng được giữ.

## 6. Kiểm thử và bằng chứng

| Nhóm | Kết quả |
|---|---|
| Spring QuizIntegrationTest + QuizMathTest | 52 tests PASS, 0 fail |
| FastAPI Quiz/Neural/lesson narration/pronunciation | 95 tests PASS |
| Mobile Quiz/Voice/timer/library/lesson narration + Audio lifecycle | 51 tests PASS, 6 suites, 0 fail |
| TypeScript `tsc --noEmit --incremental false` | PASS |
| PostgreSQL/Flyway + HTTP thật trên QA riêng | 43 checks PASS |
| Chrome thật → QA API/TTS → player thật | 4 trường hợp PASS: hai giọng × hai dạng |
| Main migration pre/post, backup và ledger | PASS; 26 attempts giữ nguyên |
| Local diagnostics sau restart | READY_FOR_FULL_DEMO, LAN PASS |
| `git diff --check` | PASS |

Regression bao phủ deadline Promise không kết thúc, taps trùng, chuyển giọng khi
render cũ chưa xong, đổi Quiz, unmount, retry sau lỗi, file 404/expired/native
loader timeout, blur/background, cache expiry và nội dung/challenge khác. Những
lỗi có điều khiển như mạng hỏng/provider lỗi/native loader được kiểm tra bằng
test doubles; bốn thành công HTTP/browser dùng TTS và audio thật. Không gọi
test doubles là kiểm thử vật lý.

Chạy unit/regression:

```powershell
# backend/business-api
.\gradlew.bat test --tests '*QuizIntegrationTest' --tests '*QuizMathTest' bootJar --console=plain
# ai/runtime
.\.venv\Scripts\python.exe -m pytest tests/test_quiz_narration.py tests/test_neural_speech.py tests/test_lesson_narration.py tests/test_speech_pronunciation.py -q
# apps/student-mobile
npx jest --runInBand --watch=false src/__tests__/quizStudent.test.tsx src/__tests__/quizVoice.test.tsx src/__tests__/quizAudioLifecycle.test.tsx src/__tests__/quizInput.test.ts src/__tests__/quizLibrary.test.tsx src/__tests__/lessonNarration.test.tsx
```

Harness HTTP là quy trình snapshot một lần: `setup`, `launch`, `run`, rồi
`verify-main`. `setup` từ chối ghi đè QA database đã có. Không chạy lại harness
legacy có tài khoản cố định trên database chính. Fixture nguồn bài học và thay
đổi timestamp để đo 15/45/90s chỉ xảy ra trong QA DB; các lượt submit đi qua API
thật. Không tạo attempt hoặc Quiz giả để bù sao ở database chính.

Bằng chứng riêng tư/local trong `runtime/quiz-voice-min-stars-timer-20261031/`:
`acceptance.json`, `browser-acceptance.json`, `main-migration-verification.json`,
`jest-final.json`, `qa-spring.log`, các WAV và ảnh browser. QA login để trong
`qa-login.json`, không đưa token/password vào báo cáo. Runtime JAR có hash
`e3a5cb0dc45e9d3f…`, khớp JAR đã build/test và process Spring local mới.

## 7. Nghiệm thu Android/iPhone

1. Điện thoại cùng Wi-Fi với máy tính. Reload Expo Go để nhận JS mới; mở lại Quiz
   để tải dữ liệu mới. Địa chỉ local hiện tại: `exp://192.168.2.2:8081`.
2. Dùng tài khoản QA/dữ liệu thử riêng. Chưa mở lời giải thì không có Voice hoặc
   endpoint từ chối. Sai hai lần, mở Cách giải, chọn nam và bấm Nghe cách giải.
   Sau “Đang tạo”/“Đang mở”, phải có player sẵn sàng; bấm phát và nghe đúng đề.
3. Làm lại với nữ, trên Digit Append và Fraction. Đang tạo thì đổi giọng và bấm
   nghe giọng mới: không được phát giọng/lời giải cũ. Bấm liên tiếp không tạo
   nhiều render giống nhau. Chuyển challenge khác phải đọc đúng challenge đó.
4. Tắt mạng trước khi tải: phải ra lỗi/Thử lại, chậm nhất khoảng 45 giây khi app
   ở foreground. Bật mạng và thử lại. Rời bài/đưa app ra nền khi đang tải/phát:
   tác vụ cũ không chiếm trạng thái hoặc tự phát khi quay lại. Lỗi mở file ra
   nút tải lại sau tối đa 12 giây, không quay mãi ở “Đang xử lý”.
5. Hoàn thành có hướng dẫn: 1 sao cho lượt này. PRACTICE: không chấm điểm, giữ
   kỷ lục. CHALLENGE mới: timer riêng, ≤30s nâng lên 3; lượt sau chậm chỉ được 1
   nhưng kỷ lục vẫn 3. Tổng sao phải khớp library/profile sau khi mở lại.
6. Quiz cũ trong ảnh hiển thị **40:07:52** và lời giải thích thời gian liên tục,
   thay vì 2407:52. Lượt mới không kế thừa 40 giờ. Sau hoàn thành, chờ hoặc đổi
   giờ điện thoại không làm duration/kết quả thưởng đổi.

Chưa xác nhận âm lượng/loa Bluetooth, audio session sau cuộc gọi, silent switch
iPhone, hoặc decoder/file URI trên Android Expo Go thật. Không báo đã PASS các
mục đó; chủ dự án cần nghe nghiệm thu trên thiết bị.

## 8. Ảnh đầu vào và Git bàn giao

Đã đọc `anh_test/Anh1.jpg`, `Anh2.jpg` và đối chiếu log/database. Theo yêu cầu,
thư mục `anh_test` được xóa sau khi hoàn tất; không đưa bản sao ảnh điện thoại
vào Git. SHA-256 trước khi xóa:

- Anh1: `761b3b2a8ee3ab3b86f4905ce79dabac6099a46b5af432d55669a0c7561f01fc`
- Anh2: `45a9d2eef8bdf5dfb2e2b5bf239d5030f079e8c597f5452ebf2b5150162b062a`

Toàn bộ thay đổi tác vụ vẫn **chưa commit**. Các file sản phẩm/test sửa ở mục 5
và migration/harness/report mới cần review trước khi đưa lên Git. Không có PR
mới hoặc thao tác publish/deploy. Dịch vụ local được giữ chạy để nghiệm thu.

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa đúng nhánh chấm điểm và tái sử dụng renderer/player hiện có.
  - Applied to: lifecycle, retry bounded, migration và regression tối thiểu cần thiết.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: React state và async lifecycle.
  - Applied to: controller identity, cleanup, tránh request/kết quả cũ ghi đè.
- `vercel-react-native-skills`
  - SKILL.md: `C:/Users/khatr/.agents/skills/vercel-react-native-skills/SKILL.md`
  - Why selected: Expo Audio, app foreground/background và native UI.
  - Applied to: audio lifecycle và phân biệt bằng chứng web với thiết bị thật.
