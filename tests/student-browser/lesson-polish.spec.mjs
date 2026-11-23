import { fileURLToPath } from 'node:url';
import { readFileSync } from 'node:fs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

const problem = 'Trong vườn có 1/3 số cây là cây táo, 2/5 số cây là cây xoài. Còn lại là cây cam. Hỏi táo và xoài chiếm bao nhiêu phần số cây trong vườn?';
const curriculum = JSON.parse(readFileSync(new URL('../../apps/student-mobile/src/data/primaryMathCurriculumData.json', import.meta.url), 'utf8'));
const firstStep = {
  kind: 'MATH', title: 'Gộp hai phần đã biết', question: 'Táo và xoài chiếm mấy phần số cây?',
  explanation: 'Cộng hai phần cùng thuộc một khu vườn.', choices: [], expression: '1/3 + 2/5',
  unit: 'phần', workExcerpt: '', solutionSentence: 'Phân số chỉ số cây táo và xoài là:',
};

test('orchard lesson opens each calculation on hint two and checks an exact retry on a short phone', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  const source = 'Bài 6\nVườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
  const given = 'Vườn cây nhà bác Nam có (1)/(3) số cây là cây táo';
  const asked = 'Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
  const reading = (title, question, choices) => ({ kind: 'UNDERSTAND', title, question, choices, expression: '', unit: '',
    explanation: 'Em đối chiếu với đề bài.', workExcerpt: '' });
  const steps = [reading('Nhận biết dữ kiện', 'Điều nào đề đã cho biết?', [given, asked]),
    reading('Tìm yêu cầu', 'Đề muốn em tìm gì?', [given, asked]), reading('Đối chiếu với đề', `«${asked}» là dữ kiện đã cho?`, ['Đúng', 'Sai']),
    { ...firstStep, title: 'Tìm phần cây cam', question: 'Phần cây cam là bao nhiêu?', expression: '1 − (1/3 + 2/5)', answerFormat: 'FRACTION' },
    { ...firstStep, title: 'Tìm tổng số cây', question: 'Cả vườn có bao nhiêu cây?', expression: '16 ÷ 4/15', unit: 'cây', answerFormat: 'INTEGER' }];
  const completed = [];
  let hintLevel = 0;
  const hints = () => completed.length === 3
    ? ['Coi cả vườn là một đơn vị.', 'Em quy đồng rồi tự tính các tử số.']
    : ['Nghĩ cách tìm cả vườn từ phần đã biết.', 'Em chia số cây cam cho phân số biểu thị phần cây cam.'];
  const state = (status = 'READY', feedback = '') => {
    const step = steps[completed.length];
    return { sessionId: 'lesson-orchard-fixture-0001', topic: 'Phân số', goal: 'Tự tính phần còn lại.',
      outline: steps.map(item => item.title), understandingSteps: 3, revision: completed.length, stepIndex: completed.length,
      step: step ? { ...step, explanation: 'Em xác định đại lượng cần tìm rồi nhập kết quả.', expression: hintLevel === 2 ? step.expression : '' } : null,
      completed, status, feedback, hintLevel, hintCount: step ? 2 : 0, revealedHints: hints().slice(0, hintLevel),
      summary: completed.length >= 2 ? { givens: ['1/3 số cây là cây táo', '2/5 số cây là cây xoài', 'Còn lại là cây cam', 'Có 16 cây cam'], question: asked } : null,
      conclusion: status === 'COMPLETE' ? 'Đáp số: 60 cây.' : '' };
  };
  app.realStudent = true;
  lessonFixtures(app);
  app.responses.set('POST /student/tutor/lesson', ({ json }) => json(state()));
  app.responses.set('POST /student/tutor/lesson/resume', ({ json }) => json(state(completed.length === steps.length ? 'COMPLETE' : 'READY')));
  app.responses.set('POST /student/tutor/lesson/answer', ({ body, json }) => {
    expect(body.revision).toBe(completed.length);
    const index = completed.length;
    if (body.hint) {
      const feedback = hints()[hintLevel++];
      return json(state('HINT', feedback));
    }
    const accepted = [given, asked, 'Sai', '8/30', '60'][index];
    if (body.answer !== accepted) return json(state('TRY_AGAIN', index === 0
      ? 'Câu em chọn yêu cầu tìm tổng số cây. Đề chưa cho biết tổng.' : 'Em quy đồng các phân số về cùng mẫu số rồi kiểm tra phép trừ.'));
    completed.push({ ...steps[index], answer: index === 3 ? '4/15' : accepted,
      ...(index === 3 ? { calculationDetails: ['15/15 − 11/15 = 4/15'] } : {}) });
    hintLevel = 0;
    return json(state(index === 4 ? 'COMPLETE' : 'CORRECT', index === 0
      ? `«${given}» là thông tin đề cho trực tiếp.` : index === 2 ? 'Đây là điều cần tìm, chưa phải dữ kiện đã biết.' : 'Em đã kiểm tra đúng bước này.'));
  });
  await page.setViewportSize({ width: 360, height: 640 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: source })}`);
  const problemText = page.locator('#confirmed-problem-body').getByText('Vườn', { exact: true });
  await expect(problemText).toHaveCSS('font-family', /NunitoBold/);
  await expect(problemText).toHaveCSS('font-size', '16px');
  const confirmationHelp = page.getByText(/^Bố mẹ và con có thể cùng đọc đề/);
  await expect(confirmationHelp).toHaveCSS('font-family', /NunitoRegular/);
  await expect(confirmationHelp).toHaveCSS('font-size', '14px');
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
  await page.getByRole('button', { name: asked, exact: true }).click();
  await expect(page.getByTestId('incorrect-answer-feedback')).toContainText('Đề chưa cho biết tổng');
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await page.getByRole('button', { name: given, exact: true }).click();
  await expect(page.getByLabel(/là thông tin đề cho trực tiếp/)).toBeVisible();
  await page.getByRole('button', { name: 'Tiếp tục bước tiếp theo', exact: true }).click();
  await page.getByRole('button', { name: asked, exact: true }).click();
  await page.getByRole('button', { name: 'Tiếp tục bước tiếp theo', exact: true }).click();
  await page.getByRole('button', { name: 'Sai', exact: true }).click();
  await expect(page.getByText('Đây là điều cần tìm, chưa phải dữ kiện đã biết.', { exact: true })).toBeVisible();
  await expect(page.getByTestId('lesson-summary-screen')).toHaveCount(0);
  await page.getByRole('button', { name: 'Tiếp tục', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Tóm tắt bài toán', exact: true })).toBeVisible();
  await expect(page.getByText('Có 16 cây cam', { exact: true })).toBeVisible();
  await expect(page.getByTestId('lesson-fixed-tools')).toBeVisible();
  await expect(page.getByRole('progressbar', { name: 'Tiến trình bài học' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Mở máy tính bỏ túi' })).toBeVisible();
  await page.getByRole('button', { name: 'Thu gọn đề bài' }).click();
  await expect(page.getByTestId('lesson-problem-content')).toHaveCount(0);
  await page.getByRole('button', { name: 'Mở đề bài' }).click();
  await expect(page.getByTestId('lesson-problem-content')).toBeVisible();
  await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
  await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).click();
  await page.getByRole('button', { name: 'Hỏi bài', exact: true }).click();
  await page.getByRole('button', { name: 'Đóng Hỏi bài', exact: true }).click();
  await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Lưu bài để học tiếp' })).toBeVisible();
  await page.getByRole('button', { name: 'Đóng Em cần gì thêm?' }).click();
  await expect(page.getByRole('button', { name: 'Sai', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Bước trước', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Sai', exact: true })).toBeVisible();
  const submittedCount = app.requests.filter(request => request.path === '/student/tutor/lesson/answer').length;
  await page.reload();
  await expect(page.getByRole('button', { name: 'Sai', exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson/answer')).toHaveLength(submittedCount);
  await page.getByRole('button', { name: 'Tiếp tục', exact: true }).click();
  // Saving is debounced by the real progress store.
  await expect.poll(() => page.evaluate(() => Object.keys(localStorage).filter(key => key.startsWith('mathvision_progress_'))
    .some(key => JSON.parse(localStorage.getItem(key)).summaryStage === 'summary'))).toBe(true);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Tóm tắt bài toán', exact: true })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('orchard-summary.png') });
  await page.getByRole('button', { name: 'Bắt đầu giải', exact: true }).click();
  const formula = page.getByLabel('1 − (1 phần 3 + 2 phần 5) = ?', { exact: true });
  await expect(formula).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true }).fill('1');
  await page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true }).fill('2');
  await page.reload();
  await expect(page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true })).toHaveValue('2');
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson/answer')).toHaveLength(submittedCount);
  await page.getByRole('button', { name: 'Bước trước', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Tóm tắt bài toán', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Bắt đầu giải', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true })).toHaveValue('2');
  await page.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
  const hint = page.getByTestId('lesson-hint-panel');
  for (let level = 1; level <= 2; level++) {
    await expect(hint).toContainText(`CẤP ${level}/2`);
    await expect(hint).not.toContainText(/4\s*\/\s*15|\b60\b/);
    if (level === 1) {
      await expect(formula).toHaveCount(0);
      await page.getByRole('button', { name: 'Gợi ý sau', exact: true }).click();
    } else await expect(formula).toBeInViewport({ ratio: 0.95 });
  }
  await expect(page.getByRole('button', { name: 'Gợi ý sau', exact: true })).toHaveCount(0);
  await testInfo.attach('orchard-progressive-hint', { body: await page.screenshot({ path: testInfo.outputPath('orchard-progressive-hint.png') }), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Em muốn hiểu gợi ý rõ hơn', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Cùng hiểu gợi ý', exact: true })).toBeVisible();
  const figures = page.getByTestId('given-fraction-visuals');
  const part = figures.getByRole('checkbox', { name: 'Phần 1 trong 3 phần bằng nhau của hình nguyên 1', exact: true });
  await expect(figures.getByText('Tô màu 1 phần', { exact: true })).toBeVisible();
  await expect(part).toBeInViewport();
  await expect(figures.getByRole('checkbox')).toHaveCount(3);
  await part.focus();
  await part.press('Space');
  await expect(part).toBeChecked();
  await page.screenshot({ path: testInfo.outputPath('orchard-fraction-explorer.png') });
  await figures.getByRole('button', { name: 'Kiểm tra phần em chọn' }).click();
  await expect(figures.getByText(/Đúng rồi, số phần em chọn/)).toBeVisible();
  await figures.getByRole('button', { name: 'Xem phân số 2 phần 5', exact: true }).click();
  await expect(figures.getByRole('checkbox')).toHaveCount(5);
  await expect(figures.getByRole('checkbox', { checked: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Xem hai phân số cùng mẫu', exact: true }).click();
  await expect(page.getByLabel('2 phần 5 bằng 6 phần 15', { exact: true })).toBeVisible();
  await expect(page.getByLabel(/4 phần 15/)).toHaveCount(0);
  await page.getByRole('button', { name: 'Thu gọn hình phân số', exact: true }).click();
  await expect(figures).toHaveCount(0);
  await page.getByRole('button', { name: 'Nhìn phân số trong đề', exact: true }).click();
  await expect(figures.getByRole('checkbox')).toHaveCount(3);
  await page.keyboard.press('Escape');
  await expect(figures).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true })).toHaveValue('1');
  await expect(page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true })).toHaveValue('2');
  await page.getByRole('button', { name: 'Thu gọn gợi ý', exact: true }).click();
  const numerator = page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true });
  const denominator = page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true });
  const check = page.getByRole('button', { name: 'Kiểm tra bước này', exact: true });
  await numerator.fill('1');
  await denominator.fill('0');
  await expect(check).toBeDisabled();
  await denominator.fill('2');
  await check.click();
  await expect(page.getByTestId('incorrect-answer-feedback')).toContainText('cùng mẫu số');
  await numerator.fill('8');
  await denominator.fill('30');
  await check.click();
  await expect(page.getByTestId('checked-student-answer')).toContainText('30');
  await page.getByRole('button', { name: 'Tiếp tục bước tiếp theo', exact: true }).click();
  const finalFormula = page.getByLabel('16 ÷ 4 phần 15 = ?', { exact: true });
  await expect(finalFormula).toHaveCount(0);
  await page.getByRole('button', { name: 'Bước trước', exact: true }).click();
  await expect(page.getByText('Bước này đã được kiểm tra đúng', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Về bước đang học', exact: true }).click();
  await page.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
  await expect(hint).toContainText('CẤP 1/2');
  await expect(finalFormula).toHaveCount(0);
  await page.getByRole('button', { name: 'Gợi ý sau', exact: true }).click();
  await expect(finalFormula).toBeInViewport();
  await expect(hint).not.toContainText(/\b60\b|sáu mươi/);
  await expect(page.getByText('16 ÷ (4 ÷ 15) = ?', { exact: true })).toHaveCount(0);
  await page.screenshot({ path: testInfo.outputPath('orchard-division-fraction.png') });
  await page.reload();
  await expect(page.getByText('Đã khôi phục bước đang học của em.', { exact: true })).toBeVisible();
  await expect(hint).toContainText('CẤP 2/2');
  await expect(finalFormula).toBeVisible();
  await expect(hint).not.toContainText(/\b60\b|sáu mươi/);
  expect(app.requests.filter(item => item.path === '/student/tutor/lesson/answer' && item.body.hint)).toHaveLength(4);
  await page.getByRole('textbox', { name: 'Câu trả lời của em', exact: true }).fill('60');
  await check.click();
  await page.getByRole('button', { name: 'Xem bài giải', exact: true }).click();
  await expect(page.getByText('Đáp số: 60 cây.', { exact: true })).toBeVisible();
  const finalSubmissionCount = app.requests.filter(request => request.path === '/student/tutor/lesson/answer').length;
  await page.reload();
  await expect(page.getByText('Đáp số: 60 cây.', { exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson/answer')).toHaveLength(finalSubmissionCount);
});

test('centers a short hint, constrains long hints and preserves the other lesson sheets', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  app.realStudent = true;
  lessonFixtures(app);
  const cases = [
    { name: 'fraction', problem: 'Tính 3/4 − 2/5', expression: '3/4 − 2/5', title: 'Tô màu 3 phần' },
    { name: 'multiply', problem: 'Tính 5 × 6', expression: '5*6', title: 'Xếp thành các hàng' },
    { name: 'divide', problem: 'Tính 12 ÷ 3', expression: '12 ÷ 3', title: 'Chia đều vào các nhóm' },
    { name: 'text-only', problem: 'Tính 10 ÷ 3', expression: '10 ÷ 3' },
  ];
  async function captureCenter(name, screenshot = false) {
    const safe = page.getByTestId('hint-sheet-safe-viewport');
    const panel = page.getByTestId('hint-sheet-panel');
    const viewport = await safe.boundingBox();
    const box = await panel.boundingBox();
    expect(viewport).toBeTruthy();
    expect(box).toBeTruthy();
    const top = box.y - viewport.y;
    const bottom = viewport.y + viewport.height - box.y - box.height;
    expect(Math.abs(top - bottom)).toBeLessThanOrEqual(2);
    expect(Math.abs(box.x + box.width / 2 - viewport.x - viewport.width / 2)).toBeLessThanOrEqual(2);
    expect(Math.min(top, bottom)).toBeGreaterThanOrEqual(-1);
    const metrics = { name, safeTop: viewport.y, safeBottom: viewport.y + viewport.height, modalTop: box.y,
      modalBottom: box.y + box.height, topGap: top, bottomGap: bottom, delta: Math.abs(top - bottom) };
    await testInfo.attach(name + '-geometry', { body: JSON.stringify(metrics), contentType: 'application/json' });
    if (screenshot) {
      await page.evaluate(({ safeTop, safeBottom, modalTop, modalBottom, topGap, bottomGap }) => {
        const overlay = document.createElement('div');
        overlay.id = 'hint-measurement-overlay';
        overlay.style.cssText = 'position:fixed;inset:0;z-index:2147483647;pointer-events:none';
        const guides = [
          [safeTop, 'safe top', '#157457'], [safeBottom - 1, 'safe bottom', '#157457'],
          [modalTop, 'modal top · ' + topGap.toFixed(1) + ' px', '#6534bc'],
          [modalBottom - 1, 'modal bottom · ' + bottomGap.toFixed(1) + ' px', '#6534bc'],
        ];
        guides.forEach(([y, name, color], index) => {
          const line = document.createElement('div');
          line.style.cssText = 'position:absolute;left:0;right:0;top:' + y + 'px;border-top:1px dashed ' + color;
          const label = document.createElement('span');
          label.style.cssText = 'position:absolute;right:' + (index < 2 ? '0' : '98px') + ';' +
            (index % 2 === 0 ? 'top:0' : 'bottom:0') + ';font:11px monospace;background:white;color:' + color;
          label.textContent = name;
          line.append(label);
          overlay.append(line);
        });
        document.body.append(overlay);
      }, metrics);
      await page.screenshot({ path: testInfo.outputPath(name + '.png') });
      await page.locator('#hint-measurement-overlay').evaluate(node => node.remove());
    }
    return box;
  }
  await page.setViewportSize({ width: 390, height: 884 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  for (const entry of cases) {
    let hintLevel = 0;
    const step = { ...firstStep, answerFormat: 'INTEGER', title: 'Tính kết quả', expression: '' };
    const lesson = { sessionId: 'lesson-center-' + entry.name + '-00001', revision: 0, topic: 'Tính toán',
      goal: 'Tính từng bước.', outline: [step.title], stepIndex: 0, completed: [], step,
      status: 'READY', hintCount: 2, hintLevel: 0, revealedHints: [], feedback: '' };
    app.responses.set('POST /student/tutor/lesson', ({ json }) => json(lesson));
    app.responses.set('POST /student/tutor/lesson/answer', ({ json }) => {
      const hints = ['Em tìm cách làm trước.', 'Dựa vào dữ kiện để tự tính.'];
      return json({ ...lesson, hintLevel: ++hintLevel, status: 'HINT',
        step: hintLevel === 2 ? { ...step, expression: entry.expression } : step,
        revealedHints: hints.slice(0, hintLevel), feedback: hints[hintLevel - 1] });
    });
    await page.goto(sites.portal.origin + '/study/learning/math-guide?' + new URLSearchParams({ problemText: entry.problem }));
    await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
    await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
    await page.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
    await page.getByRole('button', { name: 'Gợi ý sau', exact: true }).click();
    await page.getByRole('button', { name: 'Em muốn hiểu gợi ý rõ hơn', exact: true }).click();
    if (entry.title) await expect(page.getByText(entry.title, { exact: true })).toBeVisible();
    const expanded = await captureCenter(entry.name + '-390', true);
    if (entry.title) {
      await page.getByRole('button', { name: /Thu gọn hình/ }).click();
      const collapsed = await captureCenter(entry.name + '-collapsed', true);
      expect(collapsed.height).toBeLessThan(expanded.height);
      await page.getByRole('button', { name: /Nhìn phân số trong đề|Xem hình minh họa/ }).click();
    } else {
      expect(expanded.height).toBeLessThan(500);
      const cta = await page.getByRole('button', { name: 'Em đã hiểu, để em thử' }).boundingBox();
      expect(expanded.y + expanded.height - cta.y - cta.height).toBeLessThan(28);
    }
    if (entry.name === 'multiply') {
      const add = page.getByRole('button', { name: 'Thêm một hàng' });
      for (let i = 0; i < 5; i++) await add.click();
      await expect(add).toBeDisabled();
      await page.getByRole('button', { name: 'Kiểm tra cách xếp' }).click();
      await expect(page.getByText(/Đúng số hàng rồi/)).toBeVisible();
      await captureCenter('multiply-completed', true);
    }
    if (entry.name === 'divide') {
      await expect(page.getByText('Còn 12 chấm chưa chia')).toBeVisible();
      await page.getByRole('button', { name: 'Nhóm 1, có 0 chấm' }).click();
      await expect(page.getByText('Còn 11 chấm chưa chia')).toBeVisible();
      await page.getByRole('button', { name: 'Bỏ lượt cuối' }).click();
      await expect(page.getByText('Còn 12 chấm chưa chia')).toBeVisible();
    }
    if (entry.name === 'fraction') {
      for (const width of [320, 360, 412]) {
        await page.setViewportSize({ width, height: 540 });
        await captureCenter('fraction-' + width, true);
      }
      await page.setViewportSize({ width: 320, height: 380 });
      await captureCenter('fraction-reduced-viewport', true);
      await expect(page.getByRole('button', { name: 'Đóng Cùng hiểu gợi ý' })).toBeInViewport();
      await page.setViewportSize({ width: 390, height: 884 });
    }
    await page.keyboard.press('Escape');
    await expect(page.getByTestId('hint-sheet-panel')).toHaveCount(0);
  }
  for (const [button, title] of [['Nghe giảng', 'Nghe giảng'], ['Hỏi bài', 'Hỏi bài'], ['Xem thêm', 'Em cần gì thêm?']]) {
    await page.getByRole('button', { name: button, exact: true }).click();
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
    await expect(page.getByTestId('hint-sheet-panel')).toHaveCount(0);
    await page.getByRole('button', { name: 'Đóng ' + title, exact: true }).click();
  }
});

function lessonFixtures(app) {
  let hints = 0;
  const lesson = { sessionId: 'lesson-fixture-polish-000001', revision: 0, topic: 'Phân số', goal: 'Cộng hai phân số khác mẫu.',
    outline: [firstStep.title], stepIndex: 0, completed: [], step: { ...firstStep, expression: '' }, status: 'READY', feedback: '',
    hintCount: 2, hintLevel: 0, revealedHints: [] };
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
  app.responses.set('POST /student/tutor/lesson/media/prepare', ({ json }) => json({ phase: 'ready' }));
  app.responses.set('POST /student/tutor/lesson/narration/prepare', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson/narration/status', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson/narration', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson', ({ json }) => json(lesson));
  app.responses.set('POST /student/tutor/lesson/answer', ({ body, json }) => {
    if (body.hint) {
      const available = ['Quy đồng hai phân số về cùng mẫu số.', 'Đưa hai phân số về mẫu số 15, rồi cộng hai tử số.'];
      return json({ ...lesson, status: 'HINT', feedback: available[hints++], hintLevel: hints,
        revealedHints: available.slice(0, hints), step: hints === 2 ? firstStep : lesson.step });
    }
    expect(body.answer).toBe('11/15');
    return json({ ...lesson, revision: 1, status: 'COMPLETE', stepIndex: 1, step: null, hintCount: 0,
      completed: [{ ...firstStep, answer: '11/15', calculationDetails: ['5/15 + 6/15 = 11/15'] }],
      feedback: 'Đúng bước này rồi! Mình cùng tiếp tục nhé.', conclusion: 'Đáp số: 11/15 số cây.' });
  });
  app.responses.set('POST /student/quizzes/from-learning', ({ json }) => json({ offered: false, quiz: null }));
}

test('lesson preparation recovers two temporary service failures without a manual retry', async ({ page, app }) => {
  app.realStudent = true;
  lessonFixtures(app);
  const readingTitles = ['Dữ kiện', 'Câu hỏi', 'Đối chiếu'];
  const completed = readingTitles.map(title => ({ kind: 'UNDERSTAND', title, expression: '', unit: '', answer: 'Đã kiểm tra', explanation: 'Em đọc đề.' }));
  const ready = { sessionId: 'lesson-poll-recovery-000001', revision: 3, topic: 'Phân số', goal: 'Tự tính.', understandingSteps: 3,
    outline: [...readingTitles, firstStep.title], stepIndex: 3, completed, step: { ...firstStep, expression: '' }, status: 'READY', feedback: '',
    hintCount: 2, hintLevel: 0, revealedHints: [], preparingMath: false };
  app.responses.set('POST /student/tutor/lesson', ({ json }) => json({ ...ready, outline: readingTitles, status: 'PREPARING', preparingMath: true, step: null }));
  let checks = 0;
  app.responses.set('POST /student/tutor/lesson/preparation', ({ body, json, reject }) => {
    expect(body.retry).toBe(false);
    return ++checks <= 2 ? reject(503) : json(ready);
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
  await expect(page.getByText(firstStep.question, { exact: true })).toBeVisible();
  expect(checks).toBe(3);
  await expect(page.getByRole('button', { name: 'Thử chuẩn bị lại', exact: true })).toHaveCount(0);
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson')).toHaveLength(1);
});

test('preparation retry waits for the server cooldown and starts with one tap', async ({ page, app }) => {
  app.realStudent = true;
  lessonFixtures(app);
  const titles = ['Dữ kiện', 'Câu hỏi', 'Đối chiếu'];
  const ready = { sessionId: 'lesson-cooldown-fixture-0001', revision: 3, topic: 'Phân số', goal: 'Tự tính.', understandingSteps: 3,
    outline: [...titles, firstStep.title], stepIndex: 3, completed: titles.map(title => ({ kind: 'UNDERSTAND', title, expression: '', unit: '', answer: 'Đã kiểm tra', explanation: 'Em đọc đề.' })),
    step: { ...firstStep, expression: '' }, status: 'READY', feedback: '', preparingMath: false, retryAfterSeconds: 0, hintCount: 2, hintLevel: 0, revealedHints: [] };
  app.responses.set('POST /student/tutor/lesson', ({ json }) => json({ ...ready, outline: titles, status: 'RETRYABLE', preparingMath: true, retryAfterSeconds: 3, step: null }));
  app.responses.set('POST /student/tutor/lesson/preparation', ({ body, json }) => {
    expect(body).toEqual({ sessionId: ready.sessionId, revision: 3, retry: true });
    return json(ready);
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
  const retry = page.getByRole('button', { name: 'Thử chuẩn bị lại', exact: true });
  await expect(retry).toBeDisabled();
  await expect(page.getByText(/Em có thể thử chuẩn bị lại sau \d giây\./)).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson/preparation')).toHaveLength(0);
  await expect(retry).toBeEnabled();
  await retry.click();
  await expect(page.getByText(firstStep.question, { exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/lesson/preparation')).toHaveLength(1);
});

test('voice preparation recovers repeated brief outages while preserving the selected male voice', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  lessonFixtures(app);
  await page.addInitScript(() => localStorage.setItem('mathvision.lesson-voice', JSON.stringify({ voiceId: 'device' })));
  const ready = { phase: 'ready', mode: 'online', percent: 100, elapsedMs: 1, completedChunks: 1, totalChunks: 1 };
  let prepares = 0;
  app.responses.set('POST /student/tutor/lesson/narration/prepare', ({ body, json, reject }) =>
    body.voice === 'vi-VN-NamMinhNeural' && ++prepares <= 4 ? reject(503) : json(ready));
  app.responses.set('POST /student/tutor/lesson/narration/status', ({ json }) => json(ready));
  // Deterministic one-second PCM fixture verifies download/player UI, not a live voice provider.
  const wav = Buffer.alloc(44 + 32000);
  wav.write('RIFF', 0); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(16000, 24); wav.writeUInt32LE(32000, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
  wav.write('data', 36); wav.writeUInt32LE(32000, 40);
  app.responses.set('POST /student/tutor/lesson/narration', ({ route }) => route.fulfill({ body: wav, contentType: 'audio/wav' }));
  await page.setViewportSize({ width: 360, height: 800 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
  await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
  await page.getByRole('radio', { name: 'Giọng nam', exact: true }).click();
  await expect(page.getByTestId('narration-player')).toBeVisible({ timeout: 20000 });
  await expect(page.getByRole('radio', { name: 'Giọng nam', exact: true })).toHaveAttribute('aria-checked', 'true');
  await expect(page.getByRole('button', { name: 'Tải lại lời giảng', exact: true })).toHaveCount(0);
  expect(prepares).toBeGreaterThanOrEqual(5);
  await page.screenshot({ path: testInfo.outputPath('voice-device-first-recovered.png') });
});

async function stableDock(page, dock, area) {
  await expect(dock).toBeVisible();
  const before = await dock.boundingBox();
  const viewport = page.viewportSize();
  expect(before.y).toBeGreaterThan(0);
  expect(before.y + before.height).toBeLessThanOrEqual(viewport.height + 1);
  await area.evaluate(node => { node.scrollTop = node.scrollHeight; });
  const after = await dock.boundingBox();
  expect(Math.abs(after.y - before.y)).toBeLessThan(2);
}

test('parent guidance stays on the current step and preserves the child’s draft', async ({ page, app }) => {
  app.realStudent = true;
  lessonFixtures(app);
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await expect(page.getByText(/Bố mẹ và con có thể cùng đọc đề/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Bắt đầu từng bước' })).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước' }).click();

  const numerator = page.getByRole('textbox', { name: 'Tử số câu trả lời' });
  await numerator.fill('11');
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    await page.getByRole('button', { name: 'Xem thêm', exact: true }).click();
    await page.getByRole('button', { name: 'Gợi ý cho bố mẹ', exact: true }).click();
    await expect(page.getByRole('heading', { name: `Bước 1/1 · ${firstStep.title}` })).toBeVisible();
    await expect(page.getByText(/Cho con giải thích cách nghĩ và thử lại/)).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Bài giải', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Đóng Gợi ý cho bố mẹ', exact: true }).click();
    await expect(numerator).toHaveValue('11');
  }
  expect(app.requests.filter(item => item.path === '/student/tutor/lesson/answer')).toHaveLength(0);
});

for (const width of [360, 390, 430, 768, 1024, 1280, 1440]) {
  test(`guided lesson keeps current tools fixed and pages hints at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    lessonFixtures(app);
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
    await expect(page.getByRole('button', { name: 'Lưu bài để học tiếp', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Chụp bài khác', exact: true })).toHaveCount(0);
    await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
    await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
    await expect(page.getByTestId('lesson-problem-content')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Thu gọn đề bài', exact: true })).toBeVisible();
    const dock = page.getByTestId('lesson-fixed-tools');
    const area = page.getByTestId('lesson-working-area');
    await stableDock(page, dock, area);
    for (const name of ['Nghe giảng', 'Hỏi bài', 'Xem thêm']) await expect(dock.getByRole('button', { name, exact: true })).toBeVisible();

    const numerator = page.getByRole('textbox', { name: 'Tử số câu trả lời', exact: true });
    const denominator = page.getByRole('textbox', { name: 'Mẫu số câu trả lời', exact: true });
    await expect(page.getByTestId('lesson-calculation')).toHaveCount(0);
    await page.getByRole('button', { name: 'Nhập số thường', exact: true }).click();
    await page.getByRole('textbox', { name: 'Câu trả lời của em', exact: true }).fill('2');
    await page.getByRole('button', { name: 'Nhập kết quả phân số', exact: true }).click();
    await expect(numerator).toHaveValue('2');
    await expect(denominator).toHaveValue('1');
    await numerator.fill('11');
    await denominator.fill('0');
    await expect(page.getByRole('button', { name: 'Kiểm tra bước này', exact: true })).toBeDisabled();
    await denominator.fill('15');
    await page.getByRole('button', { name: 'Nhập số thường', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Câu trả lời của em', exact: true })).toHaveValue('2');
    await expect(page.getByText(/Mỗi kiểu nhập giữ bản nháp riêng/)).toBeVisible();
    await page.getByRole('button', { name: 'Nhập kết quả phân số', exact: true }).click();
    await expect(numerator).toHaveValue('11');
    await expect(denominator).toHaveValue('15');
    await page.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
    const hint = page.getByTestId('lesson-hint-panel');
    await expect(hint).toContainText('Quy đồng hai phân số về cùng mẫu số.');
    await page.getByRole('button', { name: 'Gợi ý sau', exact: true }).click();
    await expect(hint).toContainText('Đưa hai phân số về mẫu số 15');
    await page.getByRole('button', { name: 'Gợi ý trước', exact: true }).click();
    await expect(hint).toContainText('Quy đồng hai phân số về cùng mẫu số.');
    await expect(numerator).toHaveValue('11');
    await expect(denominator).toHaveValue('15');
    expect(app.requests.filter(item => item.path === '/student/tutor/lesson/answer' && item.body.hint)).toHaveLength(2);
    await page.getByRole('button', { name: 'Thu gọn gợi ý', exact: true }).click();
    await expect(hint).toHaveCount(0);
    await expect(page.getByTestId('lesson-calculation')).toHaveCount(0);
    await page.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
    await expect(hint).toContainText('Quy đồng hai phân số về cùng mẫu số.');
    await page.getByRole('button', { name: 'Gợi ý sau', exact: true }).click();
    await expect(hint).toContainText('Đưa hai phân số về mẫu số 15');
    await expect(page.getByLabel('1 phần 3 + 2 phần 5 = ?', { exact: true })).toBeVisible();
    expect(app.requests.filter(item => item.path === '/student/tutor/lesson/answer' && item.body.hint)).toHaveLength(2);
    await expect(numerator).toHaveValue('11');
    await expect(denominator).toHaveValue('15');
    await stableDock(page, dock, area);
    await testInfo.attach(`guided-hint-polish-${width}`, { body: await page.screenshot(), contentType: 'image/png' });

    await dock.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
    const voices = page.getByRole('radiogroup', { name: 'Chọn giọng đọc', exact: true });
    await expect(voices.getByRole('radio')).toHaveText([/Giọng thiết bị/, /Giọng nam/, /Giọng nữ/]);
    await expect(voices.getByText(width < 768 ? 'Chờ 5–15 giây' : '5–15 giây', { exact: true })).toHaveCount(2);
    await expect(voices.getByRole('radio', { name: 'Giọng thiết bị', exact: true })).toHaveAttribute('aria-checked', 'true');
    const deviceBox = await voices.getByRole('radio', { name: 'Giọng thiết bị', exact: true }).boundingBox();
    const maleBox = await voices.getByRole('radio', { name: 'Giọng nam', exact: true }).boundingBox();
    expect(deviceBox.y + deviceBox.height).toBeLessThanOrEqual(maleBox.y);
    await expect(page.getByRole('button', { name: 'Đọc lời giảng chi tiết', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đọc lời giảng chi tiết', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Em đã đọc lời giảng', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).click();
    await dock.getByRole('button', { name: 'Hỏi bài', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Ghi âm câu hỏi', exact: true })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Câu hỏi của em', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng Hỏi bài', exact: true }).click();
    await expect(numerator).toHaveValue('11');
    await expect(denominator).toHaveValue('15');

    await page.getByRole('button', { name: 'Kiểm tra bước này', exact: true }).click();
    await expect(page.getByText('Đúng rồi!', { exact: true })).toBeVisible();
    await expect(page.getByText('Đúng bước này rồi! Mình cùng tiếp tục nhé.', { exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Về trang chủ', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Làm bài khác', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Xem bài giải', exact: true }).click();
    await expect(page.getByLabel('Đáp số: 11 phần 15 số cây.', { exact: true })).toBeVisible();
    const detail = page.getByRole('button', { name: 'Xem chi tiết: Gộp hai phần đã biết', exact: true });
    await expect(page.getByLabel('5 phần 15 + 6 phần 15 = 11 phần 15', { exact: true })).toHaveCount(0);
    await detail.click();
    await expect(page.getByRole('button', { name: 'Thu gọn: Gộp hai phần đã biết', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByLabel('5 phần 15 + 6 phần 15 = 11 phần 15', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Thu gọn: Gộp hai phần đã biết', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Về trang chủ', exact: true })).toBeVisible();
    await testInfo.attach(`guided-lesson-polish-${width}`, { body: await page.screenshot(), contentType: 'image/png' });
  });

  test(`Quiz keeps existing tool controls fixed at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: 900 });
    lessonFixtures(app);
    const id = 'quiz-polish-fixture';
    const now = '2026-11-16T08:00:00Z';
    const path = `/student/quizzes/${id}`;
    const quiz = { quizId: id, sourceType: 'LESSON', sourceId: 'fixture', topicCode: 'ADD', topicName: 'Phép cộng', skillCode: 'ADD',
      gradeLevel: 5, taxonomyVersion: '1', verificationStatus: 'VERIFIED', confidencePercent: 100,
      questionText: 'Tính 17 + 25. Em có thể nhẩm bằng cách cộng hàng chục rồi cộng hàng đơn vị.', unit: '', answerFormat: 'INTEGER',
      status: 'IN_PROGRESS', createdAt: now, startedAt: now, completedAt: null, serverNow: now, elapsedMillis: 0,
      stars: 0, wrongAttempts: 0, solutionViewed: false, completedWithSolution: false, canRevealSolution: false,
      attempts: [], explanationText: null, correctAnswer: null, timerRunning: false };
    app.responses.set(`GET ${path}`, ({ json }) => json(quiz));
    app.responses.set(`POST ${path}/activity`, ({ json }) => json(quiz));
    app.responses.set(`POST ${path}/help`, ({ json }) => json({ ...quiz, solutionViewed: true }));
    app.responses.set(`POST ${path}/narration`, ({ reject }) => reject(422));
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/quiz/${id}`);
    const dock = page.getByTestId('quiz-fixed-tools');
    await expect(dock).toBeVisible();
    const before = await dock.boundingBox();
    await page.getByRole('button', { name: 'Trở về danh sách', exact: true }).scrollIntoViewIfNeeded();
    const after = await dock.boundingBox();
    expect(Math.abs(before.y - after.y)).toBeLessThan(2);
    expect(after.y + after.height).toBeLessThanOrEqual(901);
    await dock.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Đọc lời giảng chi tiết', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).click();
    await dock.getByRole('button', { name: 'Hỏi bài', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Đóng Hỏi bài', exact: true })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Câu hỏi của em', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng Hỏi bài', exact: true }).click();
    await testInfo.attach(`quiz-polish-${width}`, { body: await page.screenshot(), contentType: 'image/png' });
  });
}

test('lesson reference switches exclusively between text and the reviewed photo', async ({ page, app }) => {
  app.realStudent = true;
  lessonFixtures(app);
  app.responses.set('POST /student/tutor/inspect', ({ json }) => json({ kind: 'PROBLEM', problemText: problem, lines: [], needsProblem: false }));
  await page.setViewportSize({ width: 375, height: 900 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera?mode=MATH_TUTOR`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thư viện' }).click();
  await (await chooser).setFiles(fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url)));
  await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' }).click();
  await page.getByRole('button', { name: 'Tiếp tục xem lại' }).click();
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh' }).click();
  await expect(page).toHaveURL(/\/study\/learning\/math-guide/);
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
  const body = page.getByTestId('lesson-problem-content');
  await expect(body).toContainText('Trong vườn');
  await expect(body.getByRole('img')).toHaveCount(0);
  await page.getByRole('radio', { name: 'Xem ảnh đề bài', exact: true }).click();
  await expect(page.getByRole('radio', { name: 'Xem ảnh đề bài', exact: true })).toHaveAttribute('aria-checked', 'true');
  await expect(body.getByRole('img', { name: 'Ảnh đề bài đã che thông tin', exact: true })).toBeVisible();
  await expect(body).not.toContainText('Trong vườn');
  await page.getByRole('radio', { name: 'Xem đề bài bằng chữ', exact: true }).click();
  await expect(body).toContainText('Trong vườn');
  await expect(body.getByRole('img')).toHaveCount(0);
});

test('web work recovery offers capture and typing while retaining the original problem', async ({ page, app }) => {
  app.realStudent = true;
  lessonFixtures(app);
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
  await page.getByRole('button', { name: 'Chụp thêm bài làm', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/camera\?mode=MATH_TUTOR/);
  await expect(page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem })}`);
  await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Chụp thêm bài làm', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Nhập bài làm bằng chữ', exact: true }).click();
  await page.getByRole('textbox', { name: 'Nội dung bài làm', exact: true }).fill('1/3 + 2/5 = 11/15');
  await page.getByRole('button', { name: 'Dùng nội dung này', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Đối chiếu đề bài', exact: true })).toBeVisible();
  expect(app.requests.filter(item => item.path === '/student/tutor/lesson')).toHaveLength(0);
});

test('grade library topic links and keyboard accordions preserve search and grade boundaries', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  const section = 'Số và phép tính';
  const matching = curriculum.filter(item => item.grade === 5 && item.section === section);
  await page.goto(`${sites.portal.origin}/study/lessons?${new URLSearchParams({ section })}`);
  await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(matching.length);
  const topic = page.getByRole('button', { name: `Chủ đề ${section}`, exact: true });
  await topic.focus();
  await page.keyboard.press('Enter');
  await expect(topic).toHaveAttribute('aria-expanded', 'false');
  await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Tìm bài học', exact: true }).fill('cong so thap phan');
  await expect(page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true })).toBeVisible();
  await expect(topic).toHaveAttribute('aria-expanded', 'true');
  await page.goto(`${sites.portal.origin}/study/lessons?section=unknown-topic`);
  await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /^Chọn Lớp / })).toHaveCount(0);
});

test('grade library explains unavailable saved-work storage', async ({ page, app }) => {
  app.realStudent = true;
  await page.addInitScript(() => {
    const read = Storage.prototype.getItem;
    Storage.prototype.getItem = function (key) {
      if (key.startsWith('mathvision_lessons_')) throw new DOMException('Storage unavailable', 'SecurityError');
      return read.call(this, key);
    };
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/lessons`);
  await expect(page.getByText('Chưa tải được bài đã lưu. Em mở lại trang để thử nhé.', { exact: true })).toBeVisible();
  await expect(page.getByText('—', { exact: true })).toBeVisible();
  await expect(page.getByRole('progressbar', { name: 'Bài trong chương trình đã lưu trên thiết bị này', exact: true })).toHaveAttribute('aria-busy', 'false');
  await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
});
