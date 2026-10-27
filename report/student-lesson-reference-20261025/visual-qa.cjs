const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname;
const problem = 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
const lesson = { sessionId: 'reference-lesson-session-12345', revision: 0, topic: 'Phân số', goal: 'Tìm tổng số cây', feedback: '', understandingSteps: 3,
  outline: ['Dữ kiện', 'Câu hỏi', 'Tóm tắt', 'Tính phần cây cam', 'Tìm số cây'], stepIndex: 0, completed: [], status: 'READY',
  step: { kind: 'UNDERSTAND', title: 'Nhận biết dữ kiện', explanation: 'Đọc lại nguyên đề. Tách điều đã biết và điều cần tìm trước khi tính.',
    question: 'Câu nào là điều đề đã cho biết?', choices: ['1/3 số cây là cây táo', 'Hỏi trong vườn có tất cả bao nhiêu cây?'], expression: '', unit: '', workExcerpt: '' } };
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const rows = [], errors = [];
  try {
    for (const [width, height] of [[320, 568], [390, 844], [844, 390], [768, 1024], [1440, 900]]) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
      await context.addInitScript(() => sessionStorage.setItem('portal_access_token', 'reference-fixture'));
      let lessonRequests = 0;
      await context.route('**/api/v1/**', route => {
        const url = route.request().url();
        if (url.endsWith('/tutor/lesson')) lessonRequests++;
        const data = url.endsWith('/tutor/lesson') ? lesson : { id: 'reference-pupil', name: 'Minh', role: 'STUDENT', grade: 4 };
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      const openLesson = async text => {
        await page.goto('http://127.0.0.1:8097/study/learning/math-guide?problemText=' + encodeURIComponent(text));
        await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
        await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
        await page.getByRole('button', { name: 'Thu gọn đề bài', exact: true }).waitFor();
        await page.evaluate(() => document.fonts.ready);
      };
      const shot = async name => {
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        assert.equal(overflow, false, `Horizontal overflow at ${width}: ${name}`);
        await page.screenshot({ path: path.join(root, 'screenshots', `${name}-${width}.png`) });
      };
      await openLesson(problem);
      const reference = page.getByTestId('lesson-problem-reference'), body = page.getByTestId('lesson-problem-content'), working = page.getByTestId('lesson-working-area');
      const before = await reference.boundingBox();
      assert.equal(await page.getByRole('button', { name: 'Thu gọn đề bài', exact: true }).getAttribute('aria-expanded'), 'true');
      assert(before.y + before.height < height - 90, `Question leaves too little working space at ${width}`);
      await shot('expanded');
      const scrolled = await working.evaluate(element => { element.scrollTop = element.scrollHeight; element.dispatchEvent(new Event('scroll')); return element.scrollTop; });
      await page.waitForTimeout(100);
      const after = await reference.boundingBox();
      assert(Math.abs(before.y - after.y) < 1, `Reference moved while working at ${width}`);
      if (width < 600) assert(scrolled > 0, 'Phone working area must scroll independently');
      await page.getByRole('button', { name: 'Thu gọn đề bài', exact: true }).click();
      assert.equal(await body.count(), 0);
      await shot('collapsed');
      const toggle = page.getByRole('button', { name: 'Mở đề bài', exact: true });
      await toggle.focus(); await page.keyboard.press('Enter');
      assert.equal(await body.count(), 1);
      await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
      assert.equal(await page.getByRole('button', { name: 'Xem lại đề bài', exact: true }).count(), 0);
      assert.equal(await page.getByRole('button', { name: 'Máy tính', exact: true }).count(), 0);
      await shot('more');
      await page.getByRole('button', { name: 'Đóng Em cần gì thêm?', exact: true }).click();
      assert.equal(await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).count(), 1);
      if (width === 390) {
        await openLesson(Array(8).fill(problem).join('\n\n'));
        const overflow = await body.evaluate(element => ({ client: element.clientHeight, scroll: element.scrollHeight }));
        assert(overflow.scroll > overflow.client && overflow.client <= 169);
        const innerScroll = await body.evaluate(element => { element.scrollTop = element.scrollHeight; return element.scrollTop; });
        assert(innerScroll > 0);
        await shot('long-question');
        await body.focus(); await page.keyboard.press('Home'); await page.keyboard.press('ArrowDown'); await page.waitForTimeout(150);
        assert(await body.evaluate(element => element.scrollTop > 0), 'Long question supports keyboard scrolling');
        await page.evaluate(() => document.querySelectorAll('[dir="auto"]').forEach(element => {
          const style = getComputedStyle(element);
          element.style.fontSize = `${parseFloat(style.fontSize) * 1.6}px`;
          element.style.lineHeight = `${parseFloat(style.lineHeight) * 1.6}px`;
        }));
        await shot('large-text');
      }
      rows.push({ width, height, pinnedY: before.y, referenceHeight: before.height, workingScroll: scrolled, lessonRequests });
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ evidence: 'Actual Student web export; isolated authentication and lesson API fixtures. Browser viewport checks, not physical Android evidence.', rows, errors }, null, 2));
    console.log(JSON.stringify({ viewports: rows.length, screenshots: 17, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
