const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname, base = 'http://127.0.0.1:8092/study';
const problem = 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn có tất cả bao nhiêu cây?';
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
    await context.addInitScript(() => sessionStorage.setItem('portal_access_token', 'reading-layout-fixture'));
    let finishReading;
    const reading = new Promise(resolve => { finishReading = resolve; });
    const preparing = new Promise(() => {});
    await context.route('**/api/v1/**', async route => {
      const url = route.request().url();
      if (url.endsWith('/tutor/inspect')) await reading;
      if (url.endsWith('/tutor/lesson')) await preparing;
      const data = url.endsWith('/tutor/inspect') ? { kind: 'PROBLEM', problemText: problem, needsProblem: false, lines: [] }
        : { id: 'reading-layout-pupil', name: 'Minh', grade: 4, role: 'STUDENT' };
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const page = await context.newPage(), errors = [], rows = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/camera?mode=MATH_TUTOR');
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true }).click();
    await (await chooser).setFiles('C:/Users/Admin/AppData/Local/Temp/codex-clipboard-2fd24bf3-ee8e-4d43-baa5-7c4f05a65275.png');
    await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh', exact: true }).click();
    await page.getByRole('button', { name: 'Tiếp tục xem lại', exact: true }).click();
    await page.waitForFunction(() => [...document.images].every(image => image.complete && image.naturalWidth));
    await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
    const sizes = [[320, 568], [390, 844], [768, 1024], [1440, 1000], [844, 390]];
    async function capture(state) {
      const screen = page.getByTestId(state === 'reading' ? 'lesson-reading-screen' : 'lesson-preparation-screen');
      await screen.waitFor();
      assert.equal(await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).count(), 0);
      assert.equal(await page.getByRole('button', { name: 'Chụp bài khác', exact: true }).count(), 0);
      for (const [width, height] of sizes) {
        await page.setViewportSize({ width, height });
        await page.evaluate(() => document.fonts.ready);
        await page.waitForFunction(() => [...document.images].every(image => image.complete && image.naturalWidth));
        await page.waitForTimeout(120);
        const metrics = await screen.evaluate(element => {
          const bounds = element.getBoundingClientRect(), content = element.firstElementChild.getBoundingClientRect();
          return { x: content.x, y: content.y, width: content.width, height: content.height,
            centerX: Math.abs(content.x + content.width / 2 - innerWidth / 2),
            centerY: Math.abs(content.y + content.height / 2 - (bounds.y + bounds.height / 2)),
            overflow: document.documentElement.scrollWidth > innerWidth + 1 };
        });
        assert(metrics.centerX < 2 && metrics.centerY < 2 && !metrics.overflow, JSON.stringify(metrics));
        const cancel = page.getByRole('button', { name: state === 'reading' ? 'Dừng chờ, giữ ảnh' : 'Dừng chờ', exact: true });
        await cancel.scrollIntoViewIfNeeded();
        const cancelBounds = await cancel.boundingBox();
        assert(cancelBounds && cancelBounds.y >= 0 && cancelBounds.y + cancelBounds.height <= height + 1);
        await page.screenshot({ path: path.join(root, 'screenshots', `${state}-${width}x${height}.png`) });
        rows.push({ state, viewport: { width, height }, ...metrics });
      }
    }
    await capture('reading');
    finishReading();
    await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số', exact: true }).click();
    await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
    await capture('preparing');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ evidence: 'Actual exported Student web UI with isolated delayed API fixtures and real photo upload; browser viewports, not physical devices.', rows, errors }, null, 2));
    console.log(JSON.stringify({ captures: rows.length, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
