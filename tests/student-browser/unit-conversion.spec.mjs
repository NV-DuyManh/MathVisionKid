import { readFileSync } from 'node:fs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

// Actual ASGI responses with providers mocked unavailable, verified by the Python
// API regression. Auth and the Spring gateway are fixtures. Set both environment
// variables below to exercise the running AI API as well as the real Student app.
const verdicts = JSON.parse(readFileSync(new URL('../../ai/runtime/tests/fixtures/work_review_unit_conversion.json', import.meta.url)));
const runtime = process.env.WORK_REVIEW_API_ORIGIN;
const apiKey = process.env.WORK_REVIEW_API_KEY;
const cases = [['Đổi: 300 yến = 30 tạ.', 'OK'], ['10 m = 1000 cm', 'OK'], ['300 yến = 3 tạ', 'FIX']];

test('confirmed unit conversion verdicts reach Student Work Review', async ({ page, app }, info) => {
  app.realStudent = true;
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/quizzes/from-learning', ({ json }) => json({ offered: false, quiz: null }));
  app.responses.set('POST /student/tutor/work-review', async ({ body, json }) => {
    expect(body.problemConfirmed).toBe(true);
    expect(body.workConfirmed).toBe(true);
    const captured = verdicts[body.workText];
    expect(captured).toBeTruthy();
    const expected = { ...captured, sourceId: body.sourceId };
    if (!runtime) return json(expected);
    expect(apiKey, 'The local AI API requires its test key').toBeTruthy();
    const response = await fetch(`${runtime}/internal/v1/tutor/work-review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Internal-API-Key': apiKey },
      body: JSON.stringify(body),
    });
    expect(response.status).toBe(200);
    const actual = await response.json();
    expect(actual).toEqual(expected);
    return json(actual);
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  for (const [index, [workText, status]] of cases.entries()) {
    expect(verdicts[workText].rows[0]).toMatchObject({ sourceText: workText, status,
      rowKind: 'CALCULATION', arithmeticCorrect: status === 'OK', errorKind: status === 'OK' ? 'NONE' : 'CALCULATION' });
    const query = new URLSearchParams({ problemText: 'Đổi khối lượng hoặc độ dài và viết kết luận.', workText });
    await page.goto(`${sites.portal.origin}/study/learning/math-guide?${query}`);
    await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
    if (status === 'OK') {
      await expect(page.getByText('Các phép tính em viết đều đúng', { exact: true })).toBeVisible();
      await expect(page.getByText('Các phép tính em cần sửa', { exact: true })).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Thử lại nhận xét', exact: true })).toBeVisible();
    } else {
      await expect(page.getByText('Sai tính toán', { exact: true }).first()).toBeVisible();
      await expect(page.getByText(verdicts[workText].rows[0].feedback, { exact: true }).first()).toBeVisible();
      await expect(page.getByRole('button', { name: 'Gợi ý sửa dòng này', exact: true })).toBeVisible();
    }
    await expect(page.getByText('Chưa đọc được dòng này thành phép tính đầy đủ.', { exact: false })).toHaveCount(0);
    await expect(page.getByText('Cần đối chiếu', { exact: true })).toHaveCount(0);
    await expect(page.getByText('Em làm đúng rồi!', { exact: true })).toHaveCount(0);
    const screenshot = info.outputPath(`conversion-${index + 1}.png`);
    await page.screenshot({ path: screenshot, fullPage: true });
    await info.attach(workText, { path: screenshot, contentType: 'image/png' });
  }
  expect(app.requests.filter(request => request.path === '/student/tutor/work-review').map(request => request.body.workText))
    .toEqual(cases.map(([workText]) => workText));
});
