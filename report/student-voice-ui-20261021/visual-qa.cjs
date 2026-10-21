const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname;
const base = process.env.STUDENT_QA_BASE || 'http://127.0.0.1:8087/study';
const problem = 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
const lesson = { sessionId: 'visual-review-session-00000001', revision: 0, topic: 'Phân số', goal: 'Hiểu và tìm số cây trong vườn', feedback: '', outline: ['Gộp phần táo và xoài', 'Tìm phần cây cam', 'Tìm số cây trong vườn'], stepIndex: 0, completed: [], status: 'READY', understandingSteps: 0, step: { kind: 'MATH', title: 'Gộp phần táo và xoài', explanation: 'Cùng tìm phần số cây táo và cây xoài trong cả vườn.', question: 'Em tính được tổng hai phân số là bao nhiêu?', choices: [], expression: '1/3 + 2/5', unit: '', workExcerpt: '' } };
const sizes = [[320,740],[360,800],[390,844],[414,896],[768,1024],[1024,768],[1280,800],[1440,1000],[1920,1080]];
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const failures = [], rows = [], consoleErrors = [];
  try {
    const context = await browser.newContext({ deviceScaleFactor: 2 });
    await context.addInitScript(() => {
      sessionStorage.setItem('portal_access_token', 'isolated-visual-qa');
      // Deterministic completion events prove the feedback flow, not acoustic voice quality.
      window.__spoken = [];
      window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
      Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
        getVoices: () => [{ voiceURI: 'vi-visual-fixture', name: 'HoaiMy Natural', lang: 'vi-VN' }],
        speak: utterance => { window.__spoken.push(utterance.text); setTimeout(() => utterance.onend?.(), 20); },
        cancel: () => {}, addEventListener: () => {}, removeEventListener: () => {},
      } });
    });
    await context.route('**/api/v1/**', route => {
      const url = route.request().url();
      let body = url.endsWith('/student/tutor/lesson') ? lesson : { id: 'visual-qa-student', name: 'Minh', grade: 4, role: 'STUDENT' };
      if (url.endsWith('/student/tutor/lesson/ask')) body = { answer: 'Các phần phải có cùng kích thước thì mới gộp được.', spokenExplanation: 'Em tưởng tượng hai hình nguyên bằng nhau. Mỗi hình được chia theo một cách khác nhau. Mình chia nhỏ lại để các phần cùng kích thước, rồi mới đếm chung. Lượng được tô vẫn giữ nguyên.', followUp: 'Em thử nói vì sao cần các phần bằng nhau nhé.', guarded: false };
      if (url.includes('/student/submissions/')) {
        const id = url.split('/').at(-1), invalid = id === 'visual-invalid';
        body = { id, status: 'FEEDBACK_READY', validation: { isValid: !invalid, diagnosisState: invalid ? 'INVALID' : 'VALID', firstInvalidIndex: 0 }, recognizedExercise: { expression: invalid ? '24 + 13 = 38' : '24 + 13 = 37' }, studentFeedback: { title: invalid ? 'Cùng xem lại hàng đơn vị' : 'Em đã kiểm tra rất cẩn thận!', hint: invalid ? 'Em đếm lại số đơn vị, rồi đối chiếu với chữ số em đã viết.' : 'Các bước tính trong bài này khớp với phép tính.', revealAnswer: false } };
      }
      return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET, POST, OPTIONS', 'access-control-allow-headers': '*' }, body: JSON.stringify(body) });
    });
    const page = await context.newPage();
    page.on('pageerror', e => consoleErrors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    const ready = async () => {
      await page.evaluate(() => document.fonts.ready);
      await page.waitForFunction(() => [...document.images].every(image => image.complete), null, { timeout: 10000 });
      await page.waitForTimeout(450);
    };
    const inspect = async (name, width, height) => {
      await ready();
      const info = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
        broken: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src),
        outside: [...document.querySelectorAll('button,[role=button],input,[role=tab]')].filter(e => {
          const r = e.getBoundingClientRect();
          return r.width && r.height && r.bottom > 0 && r.top < innerHeight && (r.left < -2 || r.right > innerWidth + 2);
        }).map(e => (e.getAttribute('aria-label') || e.textContent).slice(0, 80)),
      }));
      rows.push({ name, width, height, ...info });
      if (info.overflow || info.broken.length || info.outside.length) failures.push({ name, width, ...info });
      await page.screenshot({ path: path.join(root, 'screenshots', `${name}-${width}.png`) });
    };
    for (const [width, height] of sizes) {
      await page.setViewportSize({ width, height });
      await page.goto(`${base}/(tabs)`);
      await page.getByRole('button', { name: 'Chụp bài toán', exact: true }).waitFor();
      await inspect('home', width, height);
      // Confirm final actions remain reachable beyond the first viewport.
      await page.getByRole('button', { name: 'Bảo vệ thông tin riêng tư của em' }).scrollIntoViewIfNeeded();
      const last = await page.getByRole('button', { name: 'Bảo vệ thông tin riêng tư của em' }).boundingBox();
      assert(last && last.y + last.height < height - (width < 768 ? 72 : 0), `Final action hidden at ${width}`);
    }
    for (const [width, height] of [[320,740],[390,844],[768,1024],[1024,768],[1440,1000]]) {
      await page.setViewportSize({ width, height });
      for (const [route, name, text] of [['lessons','lessons','Bài luyện tập cho em'], ['achievements','achievements','Tuần này của em'], ['profile','profile','Bắt đầu bộ sưu tập bài học']]) {
        await page.goto(`${base}/${route}`);
        await page.getByText(text, { exact: true }).waitFor();
        await inspect(name, width, height);
      }
      await page.goto(`${base}/login`);
      await page.getByRole('button', { name: 'Đăng nhập', exact: true }).waitFor();
      await inspect('login-component', width, height);
      await page.goto(`${base}/learning/math-guide?problemText=` + encodeURIComponent(problem));
      await page.getByText('Đề bài của em', { exact: true }).waitFor();
      await inspect('confirm', width, height);
      await page.getByRole('checkbox').click();
      await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
      await page.getByText('Gộp phần táo và xoài', { exact: true }).last().waitFor();
      await inspect('learning', width, height);
      await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
      await inspect('narration', width, height);
      await page.getByRole('button', { name: 'Nghe giảng kỹ hơn', exact: true }).click();
      await page.getByRole('button', { name: 'Em chưa hiểu', exact: true }).waitFor();
      await inspect('listening-checkin', width, height);
      await page.getByRole('button', { name: 'Em chưa hiểu', exact: true }).click();
      await inspect('listening-choices', width, height);
      await page.getByRole('button', { name: 'Vì sao phải quy đồng?', exact: true }).click();
      await page.getByText('Các phần phải có cùng kích thước thì mới gộp được.', { exact: true }).waitFor();
      await inspect('listening-explanation', width, height);
      await page.getByRole('button', { name: 'Nghe giảng kỹ hơn', exact: true }).click();
      await page.getByRole('button', { name: 'Em đã hiểu', exact: true }).waitFor();
      assert((await page.evaluate(() => window.__spoken.join(' '))).includes('hai hình nguyên bằng nhau'));
      await page.getByRole('button', { name: 'Em đã hiểu', exact: true }).click();
      assert.equal(await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).count(), 0);
      await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
      await page.getByRole('button', { name: 'Xem hình phân số', exact: true }).click();
      await inspect('fraction', width, height);
      await page.getByRole('checkbox', { name: /^Phần 1 trong/ }).first().click();
      await page.getByRole('button', { name: 'Kiểm tra phần em chọn', exact: true }).click();
      await inspect('fraction-selected', width, height);
      await page.getByRole('button', { name: /Đóng/ }).last().click();
      await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
      await page.getByRole('button', { name: 'Xem video minh họa', exact: true }).click();
      await page.getByRole('button', { name: 'Phát video minh họa', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('video')?.currentTime > .5);
      await page.getByRole('button', { name: 'Tạm dừng video', exact: true }).click();
      assert(await page.locator('video').evaluate(video => video.paused));
      await inspect('video', width, height);
      await page.getByRole('button', { name: /Đóng/ }).last().click();
      await page.getByRole('button', { name: 'Hỏi bài', exact: true }).click();
      await inspect('question', width, height);
      await page.getByRole('button', { name: /Đóng/ }).last().click();
      for (const [route, name, readyText] of [
        ['results/correct?submissionId=visual-valid','result-correct','Em đã kiểm tra rất cẩn thận!'],
        ['results/error-hint?submissionId=visual-invalid','result-hint','Cùng xem lại hàng đơn vị'],
        ['results/review-required','result-review','Chưa đủ kết quả để kiểm tra bài'],
        ['results/quality-failure?issue=BLUR','result-photo','Ảnh bị rung hoặc hơi mờ'],
        ['results/out-of-scope','result-scope','Dạng bài này MathVision đang học thêm'],
        ['results/token-confirmation','result-token','Chưa có ký hiệu để xác nhận'],
        ['gallery','gallery','Bộ chọn ảnh MathVision'],
      ]) {
        await page.goto(`${base}/${route}`);
        await page.getByText(readyText, { exact: true }).waitFor();
        await inspect(name, width, height);
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/(tabs)`);
    await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
    await inspect('calculator', 390, 844);
    for (const [width, height] of [[390,844],[768,1024],[1440,1000]]) {
      await page.setViewportSize({ width, height });
      await page.goto(`${base}/camera?mode=ARITHMETIC`);
      await page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true }).waitFor();
      await inspect('camera', width, height);
      const chooser = page.waitForEvent('filechooser');
      await page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true }).click();
      await (await chooser).setFiles('C:/Users/Admin/AppData/Local/Temp/codex-clipboard-2fd24bf3-ee8e-4d43-baa5-7c4f05a65275.png');
      await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh', exact: true }).waitFor();
      await inspect('privacy-preserved', width, height);
      await page.getByRole('checkbox').click();
      await page.getByRole('button', { name: 'Tiếp tục xem lại', exact: true }).click();
      await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).waitFor();
      await page.getByRole('button', { name: 'Xoay ảnh 90 độ', exact: true }).waitFor({ state: 'visible' });
      await inspect('crop-preserved', width, height);
      await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
      await page.getByRole('button', { name: 'KIỂM TRA BÀI TOÁN', exact: true }).waitFor();
      await inspect('preview', width, height);
    }
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ fixture: 'Isolated browser API responses; actual app components; no physical-device evidence.', rows, failures, consoleErrors }, null, 2));
    console.log(JSON.stringify({ captures: rows.length, failures, consoleErrors }, null, 2));
    assert.equal(failures.length, 0);
    assert.equal(consoleErrors.length, 0);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
