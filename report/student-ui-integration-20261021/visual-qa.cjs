const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname;
const base = process.env.STUDENT_QA_BASE || 'http://localhost:8081';
const problem = 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
const lesson = { sessionId: 'visual-review-session-00000001', revision: 0, topic: 'Phân số', goal: 'Hiểu và tìm số cây trong vườn', feedback: '', outline: ['Gộp phần táo và xoài', 'Tìm phần cây cam', 'Tìm số cây trong vườn'], stepIndex: 0, completed: [], status: 'READY', understandingSteps: 0, step: { kind: 'MATH', title: 'Gộp phần táo và xoài', explanation: 'Cùng tìm phần số cây táo và cây xoài trong cả vườn.', question: 'Em tính được tổng hai phân số là bao nhiêu?', choices: [], expression: '1/3 + 2/5', unit: '', workExcerpt: '' } };
const sizes = [[320,740],[360,800],[390,844],[414,896],[768,1024],[1024,768],[1280,800],[1440,1000],[1920,1080]];
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const failures = [], rows = [], consoleErrors = [];
  try {
    const context = await browser.newContext({ deviceScaleFactor: 2 });
    await context.addInitScript(() => { sessionStorage.setItem('portal_access_token', 'isolated-visual-qa'); });
    await context.route('**/api/v1/**', route => {
      const url = route.request().url();
      const body = url.endsWith('/student/tutor/lesson') ? lesson : { id: 'visual-qa-student', name: 'Minh', grade: 4, role: 'STUDENT' };
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
    for (const [width, height] of [[390,844],[768,1024],[1440,1000]]) {
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
      await page.getByRole('button', { name: /Đóng/ }).last().click();
      await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
      await page.getByRole('button', { name: 'Xem hình phân số', exact: true }).click();
      await inspect('fraction', width, height);
      await page.getByRole('checkbox', { name: /^Phần 1 trong/ }).first().click();
      await page.getByRole('button', { name: 'Kiểm tra phần em chọn', exact: true }).click();
      await inspect('fraction-selected', width, height);
      await page.getByRole('button', { name: /Đóng/ }).last().click();
      await page.getByRole('button', { name: 'Hỏi bài', exact: true }).click();
      await inspect('question', width, height);
      await page.getByRole('button', { name: /Đóng/ }).last().click();
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${base}/(tabs)`);
    await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
    await inspect('calculator', 390, 844);
    for (const [width, height] of [[390,844],[768,1024],[1440,1000]]) {
      await page.setViewportSize({ width, height });
      await page.goto(`${base}/camera?mode=MATH_TUTOR`);
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
    }
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ fixture: 'Isolated browser API responses; actual app components; no physical-device evidence.', rows, failures, consoleErrors }, null, 2));
    console.log(JSON.stringify({ captures: rows.length, failures, consoleErrors }, null, 2));
    assert.equal(failures.length, 0);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
