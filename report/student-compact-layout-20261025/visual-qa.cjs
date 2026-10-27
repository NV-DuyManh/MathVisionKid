const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname, base = 'http://127.0.0.1:8098/study';
const wav = fs.readFileSync(path.join(root, '../student-media-timeline-20261022/samples/lesson.wav'));
const problem = 'Bài 6: Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)';
const lesson = { sessionId: 'compact-lesson-session-12345', revision: 0, topic: 'Phân số', goal: 'Tìm tổng số cây', feedback: '', understandingSteps: 3,
  outline: ['Dữ kiện', 'Câu hỏi', 'Tóm tắt', 'Tính phần cây cam', 'Tìm số cây'], stepIndex: 0, completed: [], status: 'READY',
  step: { kind: 'UNDERSTAND', title: 'Nhận biết dữ kiện', explanation: 'Đọc lại nguyên đề. Tách điều đã biết và điều cần tìm trước khi tính.',
    question: 'Câu nào là điều đề đã cho biết?', choices: ['Bài 6: Vườn cây nhà bác Nam có 1/3 số cây là cây táo', 'Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)'], expression: '', unit: '', workExcerpt: '' } };
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true }), rows = [], errors = [];
  let shots = 0;
  try {
    for (const [width, height] of [[320, 568], [360, 800], [390, 844], [768, 1024], [844, 390], [1440, 900]]) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2, reducedMotion: 'reduce' });
      await context.addInitScript(() => sessionStorage.setItem('portal_access_token', 'compact-fixture'));
      await context.route('**/api/v1/**', route => {
        const url = route.request().url();
        if (url.endsWith('/tutor/lesson/narration')) return route.fulfill({ status: 200, contentType: 'audio/wav', body: wav });
        const data = url.endsWith('/tutor/lesson') ? lesson : { id: 'compact-pupil', name: 'Minh', role: 'STUDENT', grade: 4 };
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      const shot = async (name, target = page) => {
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false, `${name}: overflow at ${width}`);
        await target.screenshot({ path: path.join(root, 'screenshots', `${name}-${width}.png`) }); shots++;
      };
      await page.goto(base + '/');
      const firstCard = page.getByRole('button', { name: 'Luyện phép cộng và trừ trong phạm vi 100, lớp 1', exact: true });
      const secondCard = page.getByRole('button', { name: 'Đọc phép tính. Kiểm tra phép cộng và trừ đặt dọc', exact: true });
      await firstCard.waitFor(); await page.evaluate(() => document.fonts.ready);
      await firstCard.evaluate(element => element.scrollIntoView({ block: 'center', behavior: 'instant' }));
      await page.waitForTimeout(120);
      const title = firstCard.getByText('Phép cộng đến 100', { exact: true });
      const titleBox = await title.boundingBox(), cardBox = await firstCard.boundingBox(), otherBox = await secondCard.boundingBox();
      assert(titleBox.height <= 19, `Recommendation title wrapped at ${width}: ${titleBox.height}`);
      assert(cardBox.height <= 90 && Math.abs(cardBox.height - otherBox.height) <= 1, 'Recommendation cards stay compact and balanced');
      const clearCard = await firstCard.evaluate(element => {
        const box = element.getBoundingClientRect();
        return element.contains(document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2));
      });
      assert(clearCard, `Bottom navigation obscures recommendations at ${width}`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
      await page.screenshot({ path: path.join(root, 'screenshots', `home-cards-${width}.png`), clip: await firstCard.locator('xpath=..').boundingBox() }); shots++;
      await page.goto(base + '/learning/math-guide?problemText=' + encodeURIComponent(problem));
      await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
      await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
      const collapse = page.getByRole('button', { name: 'Thu gọn đề bài', exact: true });
      await collapse.waitFor(); await page.evaluate(() => document.fonts.ready);
      const reference = page.getByTestId('lesson-problem-reference'), working = page.getByTestId('lesson-working-area');
      const referenceBox = await reference.boundingBox();
      assert(referenceBox.height <= 160, `Question panel remains oversized at ${width}`);
      assert((await collapse.boundingBox()).height >= 48, 'Collapsing keeps a 48px touch target');
      await shot('lesson-expanded');
      await working.evaluate(element => { element.scrollTop = element.scrollHeight; });
      assert(Math.abs((await reference.boundingBox()).y - referenceBox.y) < 1, 'Question remains pinned');
      await collapse.click(); await shot('lesson-collapsed');
      await page.getByRole('button', { name: 'Mở đề bài', exact: true }).click();
      let transcriptFont;
      if (width === 390) {
        await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
        await page.getByRole('button', { name: 'Đọc lời giảng chi tiết', exact: true }).click();
        await page.waitForFunction(() => {
          const play = document.querySelector('[aria-label="Phát lời giảng"]');
          return play && !play.hasAttribute('disabled') && play.getAttribute('aria-disabled') !== 'true';
        });
        transcriptFont = await page.getByText(lesson.step.explanation, { exact: true }).last().evaluate(element => parseFloat(getComputedStyle(element).fontSize));
        assert(transcriptFont <= 14.5); await shot('narration');
        await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).click();
        await working.evaluate(element => { element.scrollTop = 0; });
        await page.evaluate(() => document.querySelectorAll('[dir="auto"]').forEach(element => {
          const style = getComputedStyle(element); element.style.fontSize = `${parseFloat(style.fontSize) * 1.6}px`; element.style.lineHeight = `${parseFloat(style.lineHeight) * 1.6}px`;
        }));
        await shot('large-text');
      }
      rows.push({ width, height, recommendationTitleHeight: titleBox.height, recommendationHeight: cardBox.height, referenceHeight: referenceBox.height, transcriptFont });
      await context.close();
    }
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ evidence: 'Actual Student web export; authentication and lesson replies isolated with fixtures. Browser/CSS size checks only, not physical Android evidence.', rows, screenshots: shots, errors }, null, 2));
    console.log(JSON.stringify({ viewports: rows.length, screenshots: shots, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
