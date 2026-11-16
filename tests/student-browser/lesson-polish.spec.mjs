import { fileURLToPath } from 'node:url';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

const problem = 'Trong vườn có 1/3 số cây là cây táo, 2/5 số cây là cây xoài. Còn lại là cây cam. Hỏi táo và xoài chiếm bao nhiêu phần số cây trong vườn?';
const firstStep = {
  kind: 'MATH', title: 'Gộp hai phần đã biết', question: 'Táo và xoài chiếm mấy phần số cây?',
  explanation: 'Cộng hai phần cùng thuộc một khu vườn.', choices: [], expression: '1/3 + 2/5',
  unit: 'phần', workExcerpt: '', solutionSentence: 'Phân số chỉ số cây táo và xoài là:',
};

function lessonFixtures(app) {
  let hints = 0;
  const lesson = { sessionId: 'lesson-fixture-polish-000001', revision: 0, topic: 'Phân số', goal: 'Cộng hai phân số khác mẫu.',
    outline: [firstStep.title], stepIndex: 0, completed: [], step: firstStep, status: 'READY', feedback: '' };
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
  app.responses.set('POST /student/tutor/lesson/media/prepare', ({ json }) => json({ phase: 'ready' }));
  app.responses.set('POST /student/tutor/lesson/narration/prepare', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson/narration/status', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson/narration', ({ reject }) => reject(422));
  app.responses.set('POST /student/tutor/lesson', ({ json }) => json(lesson));
  app.responses.set('POST /student/tutor/lesson/answer', ({ body, json }) => {
    if (body.hint) return json({ ...lesson, status: 'HINT', feedback: ++hints === 1
      ? 'Quy đồng hai phân số về cùng mẫu số.' : 'Đưa hai phân số về mẫu số 15, rồi cộng hai tử số.' });
    expect(body.answer).toBe('11/15');
    return json({ ...lesson, revision: 1, status: 'COMPLETE', stepIndex: 1, step: null,
      completed: [{ ...firstStep, answer: '11/15', calculationDetails: ['5/15 + 6/15 = 11/15'] }],
      feedback: 'Đúng bước này rồi! Mình cùng tiếp tục nhé.', conclusion: 'Đáp số: 11/15 số cây.' });
  });
  app.responses.set('POST /student/quizzes/from-learning', ({ json }) => json({ offered: false, quiz: null }));
}

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

for (const width of [375, 768, 1440]) {
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
    await page.getByRole('radio', { name: 'Nhập số thường', exact: true }).click();
    await expect(page.getByRole('radio', { name: 'Nhập số thường', exact: true })).toHaveAttribute('aria-checked', 'true');
    await page.getByRole('textbox', { name: 'Câu trả lời của em', exact: true }).fill('2');
    await page.getByRole('radio', { name: 'Nhập kết quả phân số', exact: true }).click();
    await expect(page.getByRole('radio', { name: 'Nhập kết quả phân số', exact: true })).toHaveAttribute('aria-checked', 'true');
    await expect(numerator).toHaveValue('2');
    await expect(denominator).toHaveValue('1');
    await numerator.fill('11');
    await denominator.fill('15');
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
    await stableDock(page, dock, area);
    await testInfo.attach(`guided-hint-polish-${width}`, { body: await page.screenshot(), contentType: 'image/png' });

    await dock.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
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
  await page.getByRole('button', { name: 'Xem ảnh đề bài', exact: true }).click();
  await expect(body.getByRole('img', { name: 'Ảnh đề bài đã che thông tin', exact: true })).toBeVisible();
  await expect(body).not.toContainText('Trong vườn');
  await page.getByRole('button', { name: 'Xem đề bài bằng chữ', exact: true }).click();
  await expect(body).toContainText('Trong vườn');
  await expect(body.getByRole('img')).toHaveCount(0);
});
