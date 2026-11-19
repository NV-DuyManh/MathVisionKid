import { fileURLToPath } from 'node:url';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

const route = (path) => `${sites.portal.origin}/study/${path}`;
const title = 'Diện tích tam giác có đáy và chiều cao thập phân';
const step = {
  kind: 'MATH', title: 'Tính diện tích hình tam giác', question: 'Diện tích của hình tam giác là bao nhiêu?',
  expression: '', choices: [], answerFormat: 'DECIMAL', unit: 'cm²', workExcerpt: '',
  explanation: 'Em dùng độ dài đáy và chiều cao tương ứng.',
};
const lesson = {
  sessionId: 'lesson-web-design-fixture-001', revision: 0, step, stepIndex: 0, completed: [], outline: [step.title],
  topic: 'Diện tích tam giác', goal: 'Tính diện tích hình tam giác.', status: 'READY', feedback: '',
  hintCount: 2, hintLevel: 0, revealedHints: [],
};

async function capture(page, testInfo, name) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  await testInfo.attach(name, {
    body: await page.screenshot({ path: testInfo.outputPath(`${name}.png`) }),
    contentType: 'image/png',
  });
}

for (const width of [1672, 390]) {
  test(`library, lesson, practice, calculator and camera remain usable at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
    app.responses.set('POST /student/tutor/lesson/narration/prepare', ({ reject }) => reject(422));
    app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
    app.responses.set('POST /student/tutor/lesson/media/prepare', ({ json }) => json({ phase: 'ready' }));
    app.responses.set('POST /student/tutor/lesson', ({ json }) => json(lesson));
    app.responses.set('POST /student/tutor/lesson/answer', ({ body, json }) => {
      expect(body.hint).toBe(true);
      const hint = 'Em nhân độ dài đáy với chiều cao tương ứng, rồi chia cho 2.';
      return json({ ...lesson, revision: 1, status: 'HINT', feedback: hint, hintLevel: 1, revealedHints: [hint] });
    });
    await page.setViewportSize({ width, height: width === 1672 ? 941 : 844 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(route('lessons'));
    await expect(page.getByRole('heading', { name: 'Chương trình học của em', exact: true })).toBeVisible();
    const plan = page.getByRole('heading', { name: 'Hành động nhanh', exact: true });
    if (width === 1672) await expect(plan).toBeVisible();
    else await expect(plan).toHaveCount(0);
    await capture(page, testInfo, 'lessons');

    await page.goto(route(`lessons?${new URLSearchParams({ q: 'dien tich tam giac' })}`));
    const search = page.getByRole('textbox', { name: 'Tìm bài học', exact: true });
    await expect(search).toHaveValue('dien tich tam giac');
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(1);
    await search.fill('dien tich');
    await expect(page.getByRole('button', { name: /^Mở bài: / }).nth(1)).toBeVisible();
    await page.getByRole('button', { name: `Mở bài: ${title}`, exact: true }).click();
    await page.getByRole('button', { name: `Học từng bước: ${title}`, exact: true }).click();
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
    if (width === 1672) await expect(page.getByRole('heading', { name: 'Cách học bài này', exact: true })).toBeVisible();
    await capture(page, testInfo, 'lesson_detail');
    await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
    await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
    const working = page.getByTestId('lesson-working-area');
    await expect(working.getByRole('textbox', { name: 'Câu trả lời của em', exact: true })).toBeVisible();
    await expect(working.getByText('63 cm²', { exact: true })).toHaveCount(0);
    await expect(page.getByTestId('lesson-fixed-tools')).toBeVisible();
    await capture(page, testInfo, 'practice');
    await working.getByRole('button', { name: 'Gợi ý cách làm bước này', exact: true }).click();
    await expect(page.getByTestId('lesson-hint-panel')).toContainText('chiều cao tương ứng');

    await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
    const calculator = page.getByTestId('calculator-popup');
    const expression = calculator.getByRole('textbox', { name: 'Phép tính', exact: true });
    await expression.fill('15×8,4÷2');
    await calculator.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
    await expect(calculator.locator('[aria-live="polite"]').filter({ hasText: '63' }).first()).toBeVisible();
    if (width === 1672) await expect(calculator.getByRole('heading', { name: 'Lịch sử', exact: true })).toBeVisible();
    await capture(page, testInfo, 'calculator');
    await calculator.getByRole('button', { name: 'Đóng máy tính', exact: true }).click();

    await page.goto(route('camera?mode=MATH_TUTOR'));
    const upload = page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true });
    await expect(upload).toBeVisible();
    if (width === 1672) {
      await expect(page.getByRole('heading', { name: 'Giữ thông tin riêng tư', exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Mẹo chụp ảnh rõ', exact: true })).toBeVisible();
    }
    await capture(page, testInfo, 'ai_capture');
    const chooser = page.waitForEvent('filechooser');
    await upload.click();
    await (await chooser).setFiles(fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url)));
    await expect(page).toHaveURL(/\/study\/privacy/);
    await expect(page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' })).toBeVisible();
    expect(app.requests.some(request => request.path === '/student/tutor/inspect')).toBe(false);
  });
}
