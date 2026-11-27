import { test, expect, sites, login } from '../browser/fixtures.mjs';

// The Student bundle, storage, editing and navigation are real; semantic HTTP
// verdicts below are synthetic. These tests do not measure live model accuracy.
const problem = 'Lớp có 40 học sinh, nữ chiếm 3/5. Hỏi số học sinh nam trong lớp?';
const partial = 'Số học sinh nữ là:\n40 × 3/5 = 24 (học sinh)';
const finished = partial + '\nSố học sinh nam là:\n40 - 24 = 16 (học sinh)';
const severalQuestions = 'Lớp có 40 học sinh, nữ chiếm 3/5. a) Hỏi số học sinh nam trong lớp? b) Tính số học sinh nữ nhiều hơn nam.';
const description = 'Tính số học sinh nam trong lớp.';
const hint = 'Em đã tìm được số học sinh nữ.\nEm lấy tổng số học sinh trong lớp trừ đi số học sinh nữ. Kết quả cho biết số học sinh nam trong lớp.';

function reviews(app, { unknown = false, multiple = false } = {}) {
  app.realStudent = true;
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/quizzes/from-learning', ({ json }) => json({ offered: false, quiz: null }));
  app.responses.set('POST /student/tutor/work-review', ({ body, json }) => {
    const correct = body.workText === finished;
    const gap = { type: 'MISSING_CALCULATION', target: 'số học sinh nam trong lớp', description,
      hint, requirementIndex: 0, relatedLineIndices: [1], evidence: 'DUAL_REVIEW' };
    const gaps = unknown || correct ? [] : multiple ? [gap, { ...gap, target: 'số học sinh nữ nhiều hơn nam',
      description: 'Tính số học sinh nữ nhiều hơn nam.',
      hint: 'Trước hết, em tìm số học sinh nam trong lớp ở phần trên. Sau đó, em lấy số học sinh nữ trừ đi số học sinh nam trong lớp. Kết quả cho biết số học sinh nữ nhiều hơn nam.', requirementIndex: 1 }] : [gap];
    return json({ sourceId: body.sourceId, completionVersion: 2, status: correct ? 'CORRECT' : 'NEEDS_REVIEW',
      complete: correct ? true : unknown ? null : false, missingParts: gaps, missingPart: gaps[0]?.description || '',
      arithmeticVerified: true, summary: correct ? 'Em đã trả lời đủ câu hỏi.' : 'Các phép tính em đã viết đều đúng.',
      praise: correct ? 'Em đã làm đúng bài toán.' : '', nextAction: gaps[0]?.hint || 'Em có thể thử nhận xét lại trên bài này.', alternative: '',
      rows: body.workText.split('\n').map((sourceText, lineIndex) => ({ sourceText, lineIndex,
        rowKind: lineIndex % 2 ? 'CALCULATION' : 'EXPLANATION', status: 'OK', errorKind: 'NONE',
        arithmeticCorrect: lineIndex % 2 ? true : null, feedback: 'Dòng này phù hợp.', hints: [] })) });
  });
}

async function openReview(page, work = partial, question = problem) {
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: question, workText: work })}`);
  await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
}

test('Incomplete work names the unmet quantity and clears feedback after completion', async ({ page, app, isMobile }, testInfo) => {
  reviews(app);
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await openReview(page);
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  await expect(page.getByText('Gợi ý cho em:', { exact: true })).toBeVisible();
  await expect(page.getByText(hint, { exact: true })).toBeVisible();
  await expect(page.getByText('Cần đối chiếu', { exact: true })).toHaveCount(0);
  const missingImage = testInfo.outputPath('missing-quantity.png');
  await page.screenshot({ path: missingImage, fullPage: true });
  await testInfo.attach('Specific missing quantity and hint — synthetic API', { path: missingImage, contentType: 'image/png' });
  const save = page.getByRole('button', { name: 'Lưu bài để học tiếp', exact: true });
  if (isMobile) {
    await save.click();
    await expect(page.getByRole('button', { name: 'Đã lưu bài của em', exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/profile`);
    await page.getByRole('button', { name: 'Học tiếp: ' + problem.slice(0, 60), exact: true }).click();
    await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
    await expect(page.getByText(description, { exact: true })).toBeVisible();
    const opened = app.requests.filter(request => request.path === '/student/tutor/work-review');
    expect(opened).toHaveLength(2);
    expect(opened[1].body.workText).toBe(partial);
    expect(opened[1].body.sourceId).not.toBe(opened[0].body.sourceId);
  } else {
    await expect(save).toHaveCount(0);
  }
  await page.getByRole('button', { name: 'Xem lại đề và bài làm', exact: true }).click();
  await page.getByRole('button', { name: 'Chỉnh chỗ chưa đọc đúng', exact: true }).click();
  await page.getByRole('textbox', { name: 'Nội dung bài làm', exact: true }).fill(finished);
  await page.getByRole('button', { name: 'Dùng nội dung này', exact: true }).click();
  await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
  await expect(page.getByText('Em làm đúng rồi!', { exact: true })).toBeVisible();
  await expect(page.getByText(description, { exact: true })).toHaveCount(0);
  const completedImage = testInfo.outputPath('completed-work.png');
  await page.screenshot({ path: completedImage, fullPage: true });
  await testInfo.attach('Updated source receives a correct result — synthetic API', { path: completedImage, contentType: 'image/png' });
});

test('Several unmet requirements stay in one numbered missing-work panel', async ({ page, app }, testInfo) => {
  reviews(app, { multiple: true });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await openReview(page, partial, severalQuestions);
  await expect(page.getByText('1. ' + description, { exact: true })).toBeVisible();
  await expect(page.getByText('2. Tính số học sinh nữ nhiều hơn nam.', { exact: true })).toBeVisible();
  await expect(page.getByText('Trước hết, em tìm số học sinh nam trong lớp ở phần trên.', { exact: false })).toBeVisible();
  await expect(page.getByText('Gợi ý cho em:', { exact: true })).toHaveCount(2);
  const multipleImage = testInfo.outputPath('multiple-missing.png');
  await page.screenshot({ path: multipleImage, fullPage: true });
  await testInfo.attach('Numbered missing requirements — synthetic API', { path: multipleImage, contentType: 'image/png' });
});

test('Unverified completion preserves correct calculations and offers retry without a new photo', async ({ page, app, isMobile }) => {
  reviews(app, { unknown: true });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await openReview(page);
  await expect(page.getByRole('button', { name: 'Thử lại nhận xét', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Thử nhận xét lại', exact: true })).toHaveCount(0);
  await expect(page.getByText('Em đang thiếu phần này:', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Cần đối chiếu', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Chụp lại bài em đã sửa', exact: true })).toHaveCount(0);
  const retry = page.getByRole('button', { name: 'Thử lại nhận xét', exact: true });
  const save = page.getByRole('button', { name: 'Lưu bài để học tiếp', exact: true });
  await expect(save).toHaveCount(isMobile ? 1 : 0);
  if (!isMobile && page.viewportSize().width >= 1100) {
    const [button, column] = await Promise.all([
      retry.boundingBox(), page.getByTestId('work-review-result-column').boundingBox(),
    ]);
    expect(button.x).toBeCloseTo(column.x, 0);
    expect(button.width).toBeCloseTo(column.width, 0);
  }
  await retry.click();
  await expect.poll(() => app.requests.filter(request => request.path === '/student/tutor/work-review').length).toBe(2);
});
