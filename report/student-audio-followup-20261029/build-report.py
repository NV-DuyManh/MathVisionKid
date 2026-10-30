"""Build the follow-up evidence gallery from measured local results."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
qa = json.loads((root / 'visual-qa.json').read_text(encoding='utf-8'))
tests = json.loads((root / 'all-student-tests.json').read_text(encoding='utf-8-sig'))
assert tests['success'] and tests['numFailedTests'] == 0
gallery_qa = json.loads((root / 'gallery-qa.json').read_text(encoding='utf-8'))
assert gallery_qa['realStudentLogin'] and gallery_qa['sessionSurvivesReload'] and not gallery_qa['errors']
rows = qa['rows']
timings = [row['cachedReopenMs'] for row in rows]
table = '\n'.join(f"| {r['width']} × {r['height']} | {r['cachedReopenMs']} ms | {r['replyPlayerHeight']} px | {r['recoveryHeight']} px | Đạt |" for r in rows)
report = f'''# Cải thiện giọng đọc và giao diện Student — 29/10/2026

Đã sửa trực tiếp tại `E:/MathVisionKid`, nhánh `codex/student-learning-voice-polish-20261029`. Chưa commit hoặc push.

## Những gì sửa trong vòng này

1. **Bỏ công việc chuẩn bị dư trong hỏi đáp.** Trước đây khi làm nóng hai giọng cho câu trả lời, hook còn gửi yêu cầu chuẩn bị cả bài học. Giờ câu trả lời chỉ làm nóng hai bản giọng của nội dung vừa được trả về. Luồng học chính vẫn chuẩn bị các phần tiếp theo như trước.
2. **Giảm khởi động lại công việc nền.** Thông báo foreground trùng lặp không còn hủy rồi tạo lại lượt tải đang chạy. Chỉ chuyển trạng thái thật sự mới dừng hoặc tiếp tục. Khi đổi giọng, giữ hai lượt tải hiện có và cập nhật ưu tiên của bài học.
3. **Giữ nguyên câu hỏi khi chỉ đang đọc/gõ.** Rời ứng dụng lúc không ghi âm hoặc gửi yêu cầu sẽ không gọi dừng máy ghi và không chèn thông báo “Đã dừng”. Việc ghi âm/yêu cầu đang hoạt động vẫn có quy tắc hủy và chặn phản hồi đến muộn.
4. **Bỏ nháy giao diện chờ.** Chỉ hiện phần chuẩn bị nếu việc mở âm thanh kéo dài hơn 180 ms. Tệp đã lưu sẵn mở thẳng bộ phát sau khi bộ giải mã xác nhận tải xong. Khi thật sự phải chờ, giao diện hoàn tất tiến độ trước khi chuyển sang bộ phát, tránh hiện hai khung cùng lúc.
5. **Thu gọn bộ phát trong hỏi đáp.** Chuyển tùy chọn gọn xuống đúng thành phần phát. Khung giảm từ 342 xuống 264 px trong các ảnh kiểm tra, khoảng 23%; vẫn giữ thanh tua tự do, lùi/tiến 10 giây, nghe lại và đổi tốc độ. Bản ghi câu hỏi vẫn giữ điều khiển riêng của nó.

Không đổi hai giọng hiện tại, không tự chuyển âm sắc và không thay timeout giọng 60 giây. Không bổ sung video hay thư viện. Các thông báo lỗi vẫn dùng khung gọn với “Thử lại” và “Giọng thiết bị”, có thể mở lời giảng dạng chữ.

## Kết quả kiểm chứng

- **{tests['numPassedTests']} kiểm thử / {tests['numPassedTestSuites']} bộ kiểm thử Student đạt**, không có kiểm thử thất bại. Xem `all-student-tests.json`.
- TypeScript đạt. Lint không có lỗi; còn hai cảnh báo đã có từ trước trong `cropRotation.web.ts`.
- Xuất Android thành công; bằng chứng `android-export/metadata.json`. Đây là kiểm tra đóng gói, **không phải thử trên điện thoại thật**.
- Đăng nhập Student qua giao diện thật và backend thật đạt; tải lại trang vẫn giữ phiên và mở được trang chủ. Trang phát triển vẫn hoạt động sau khi xuất Android. Xem `gallery-qa.json`.
- Kiểm tra ảnh và thao tác trên 5 kích thước, gồm điện thoại dọc/ngang, tablet và desktop. Không tràn ngang. Các nút bộ phát cao ít nhất 44 px. Tab được giữ trong hộp thoại, Escape đóng và tiêu điểm trở lại nút mở.
- Mô phỏng dịch vụ báo thất bại rồi phục hồi: hiển thị hai thao tác gọn, tải lại phát được, giữ nội dung bài. Không lộ chi tiết nhà cung cấp.
- Kiểm tra âm thanh đã lưu sẵn: không gửi lại lượt tải tệp; không thấy khung chuẩn bị lóe lên; không chồng khung chuẩn bị và bộ phát.
- Kiểm tra hỏi đáp: không phát sinh thêm yêu cầu `/lesson/media/prepare` khi câu trả lời xuất hiện.

| Khung nhìn | Mở lại bộ phát đã lưu | Bộ phát hỏi đáp | Khung lỗi | Thao tác/bố cục |
|---|---:|---:|---:|---|
{table}

Đơn vị px trong bảng là CSS pixel. Mỗi thời gian là một lượt đo, tính từ thao tác mở đến khi bộ phát thực sự sẵn sàng trong Chromium chạy ở máy này; chưa phải phân vị thống kê hay thời gian trên Android.

## Phạm vi bằng chứng và giới hạn

Ảnh chụp là **thành phần Student thực đang chạy**, không phải ảnh thiết kế dựng lại. Đăng nhập dùng máy chủ thật; phản hồi bài học và trạng thái giọng được chủ động mô phỏng để kiểm tra chờ/lỗi/phục hồi có thể lặp lại. Tệp WAV dùng cho kiểm tra bộ phát là âm thanh tiếng Việt đã tạo thật ở vòng trước. Vì vậy số {min(timings)}–{max(timings)} ms ở đây chỉ chứng minh đường mở tệp đã lưu và UI, **không chứng minh tốc độ tạo mới của dịch vụ bên ngoài**.

Vòng này không đo lại chất lượng bằng nghe trực tiếp và không có thử nghiệm Android vật lý. Kết quả cold synthesis ở vòng trước vẫn được ghi riêng tại `../student-audio-refinement-20261029/REPORT.md`; không gộp nó với thời gian cache. Chưa có cơ sở cam kết mọi lượt tạo giọng mới đều đạt 1–3 giây, hoặc dịch vụ bên ngoài không bao giờ lỗi. Chuẩn bị sớm và tái dùng tệp giúp giảm thời gian người học phải đợi, nhưng bài mới/nội dung mới vẫn cần tạo âm thanh.

## Tệp liên quan

- `apps/student-mobile/src/features/tutoring/NarrationPreparation.tsx`
- `apps/student-mobile/src/features/tutoring/LessonQuestion.tsx`
- `apps/student-mobile/src/features/tutoring/LessonNarration.tsx`
- `apps/student-mobile/src/features/tutoring/AudioPlayback.tsx`
- Các kiểm thử `narrationPreparation`, `lessonQuestion`, `lessonNarration`; kịch bản trình duyệt `capture.cjs`.

Không đụng vào các thay đổi OCR có sẵn của tác vụ khác. Không thay backend hoặc dữ liệu huấn luyện trong vòng này.

## Skills Applied

- `ui-ux-pro-max`
  - SKILL.md: `.agents/skills/ui-ux-pro-max/SKILL.md`
  - Why selected: giao diện chờ, phản hồi và bố cục trên màn hình nhỏ.
  - Applied to: trì hoãn khung chờ ngắn, chuyển sang bộ phát, khung hỏi đáp gọn.
- `vercel-react-best-practices`
  - SKILL.md: `.agents/skills/react-best-practices/SKILL.md`
  - Why selected: hook React và công việc mạng nền.
  - Applied to: bỏ yêu cầu chuẩn bị dư, xử lý foreground và giữ lượt tải đang có.
- `fixing-accessibility`
  - SKILL.md: `.agents/skills/fixing-accessibility/SKILL.md`
  - Why selected: bộ phát và hộp thoại tương tác.
  - Applied to: ẩn phần chưa sẵn sàng khỏi trình đọc màn hình; kiểm tra Tab/Escape/trả tiêu điểm, nhãn và kích thước nút.
- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: sửa gọn theo nguyên nhân đã kiểm chứng.
  - Applied to: tái dùng cache, RecoveryNotice và MediaTimeline; không thêm dependency hoặc cơ chế focus tùy biến trùng nền tảng.
'''
(root / 'REPORT.md').write_text(report, encoding='utf-8')
html='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Student • Giọng đọc & UI</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f7f5fd;color:#211746;font:16px/1.6 system-ui,sans-serif}main{max-width:1240px;padding:38px 22px 70px;margin:auto}header{max-width:850px}small{font-weight:800;letter-spacing:.12em;color:#7651be}h1{font-size:clamp(29px,4vw,46px);line-height:1.17;margin:12px 0}p{color:#655b78}a{color:#653ab7}nav{display:flex;flex-wrap:wrap;gap:8px;margin:25px 0}button{cursor:pointer;font:inherit;color:#60429b;border:1px solid #dfd3f3;background:white;min-height:44px;padding:8px 15px;border-radius:12px}button[aria-pressed=true]{background:#7145d2;color:white;border-color:#7145d2}button:focus-visible,a:focus-visible{outline:3px solid #9a72f0;outline-offset:3px}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:26px 0}.fact{background:white;border:1px solid #e7dff3;border-radius:18px;padding:19px}.fact strong{font-size:26px;display:block;color:#6943c5}.fact span{font-size:14px;color:#655b78}section{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;align-items:start}article{border:1px solid #e6dff0;border-radius:20px;background:#fff;overflow:hidden}article h2{font-size:17px;line-height:1.3;margin:20px 18px 4px}article p{font-size:13px;margin:0 18px 18px}article .picture{padding:0;border:0;display:block;width:100%;background:#ede8f7;min-height:0;border-radius:0}article img{display:block;width:100%;height:auto}footer{font-size:13px;border-top:1px solid #e3d9ef;margin-top:30px;padding-top:20px;color:#6e607e}dialog{max-width:min(96vw,1160px);max-height:96vh;border:0;border-radius:18px;padding:13px;background:#f7f5fd}dialog::backdrop{background:#211746b8}dialog img{display:block;max-width:100%;max-height:83vh;object-fit:contain;margin:auto}dialog button{display:block;margin:0 0 12px auto}@media(max-width:850px){section{grid-template-columns:repeat(2,minmax(0,1fr))}.facts{gap:8px}.fact{padding:14px}.fact strong{font-size:21px}}@media(max-width:540px){main{padding:24px 16px}.facts{grid-template-columns:1fr}.fact strong{display:inline;margin-right:10px}section{grid-template-columns:1fr}article{max-width:420px;margin:auto;width:100%}}</style>
<main><header><small>STUDENT · 29 / 10 / 2026</small><h1>Giọng đọc mở mượt hơn.<br>Hỏi đáp gọn, dễ theo dõi.</h1><p>Ảnh chụp giao diện dự án đang chạy: nghe giảng, hỏi bài, trạng thái chờ và thử lại. Chọn kích thước để xem từng bố cục.</p><a href="REPORT.md">Báo cáo & bằng chứng kiểm tra ↗</a></header>
<div class="facts"><div class="fact"><strong>TEST_COUNT</strong><span>kiểm thử Student đạt</span></div><div class="fact"><strong>TIME_RANGE ms</strong><span>mở lại bộ phát đã lưu</span></div><div class="fact"><strong>−23%</strong><span>chiều cao bộ phát hỏi đáp</span></div></div>
<nav aria-label="Chọn khung nhìn"></nav><section id="gallery" aria-live="polite"></section>
<footer>Ảnh thật của thành phần Student. Trạng thái máy chủ trong kịch bản được mô phỏng để kiểm tra UI; dùng WAV đã tạo thật. Thời gian trên là mở âm thanh đã lưu trong Chromium, không phải thời gian tạo giọng mới hoặc đo trên Android. Chưa commit/push.<br><a href="visual-qa.json">Kết quả trình duyệt</a> · <a href="all-student-tests.json">Kết quả kiểm thử</a></footer></main>
<dialog aria-label="Ảnh giao diện phóng lớn"><button type="button" autofocus>Đóng ảnh</button><img alt=""></dialog>
<script>const sizes=[[390,'Điện thoại 390'],[320,'Điện thoại nhỏ 320'],[768,'Tablet 768'],[1440,'Desktop 1440'],[844,'Điện thoại ngang']],states=[['player','Nghe giảng','Hai giọng quen thuộc, thanh tua tự do và nghe lại.'],['answer','Lời giải thích gọn','Giữ câu hỏi và gợi mở; bộ phát chiếm ít chỗ hơn.'],['recovery','Lỗi có cách tiếp tục','Hai thao tác rõ ràng: thử lại hoặc dùng giọng thiết bị.'],['preparing','Khi thực sự cần chờ','Theo dõi giai đoạn đang làm và số đoạn đã tạo.'],['question','Nói hoặc viết câu hỏi','Một việc chính mỗi lần, có thể sửa trước khi gửi.'],['lesson','Vừa đọc đề, vừa làm','Đề vẫn ở trên, phân số trình bày theo chiều đứng.']];let selected=390;
const nav=document.querySelector('nav'),gallery=document.querySelector('#gallery'),dialog=document.querySelector('dialog'),full=dialog.querySelector('img');
function render(){nav.replaceChildren(...sizes.map(([w,label])=>{const b=document.createElement('button');b.textContent=label;b.setAttribute('aria-pressed',w===selected);b.onclick=()=>{selected=w;render()};return b}));gallery.replaceChildren(...states.map(([file,title,description])=>{const card=document.createElement('article'),h=document.createElement('h2'),p=document.createElement('p'),b=document.createElement('button'),img=document.createElement('img');h.textContent=title;p.textContent=description;b.className='picture';b.setAttribute('aria-label','Phóng lớn '+title);img.src='screenshots/'+file+'-'+selected+'.png';img.alt=title+' – khung nhìn '+selected;img.loading='lazy';b.append(img);b.onclick=()=>{full.src=img.src;full.alt=img.alt;dialog.showModal()};card.append(h,p,b);return card}))}dialog.querySelector('button').onclick=()=>dialog.close();render();</script></html>'''
html=html.replace('TEST_COUNT',str(tests['numPassedTests'])).replace('TIME_RANGE',f'{min(timings)}–{max(timings)}')
(root / 'index.html').write_text(html, encoding='utf-8')
print(json.dumps({'studentTestsPassed':tests['numPassedTests'],'suitesPassed':tests['numPassedTestSuites'],'cachedReopenRangeMs':[min(timings),max(timings)],'viewportCount':len(rows)},ensure_ascii=False))
