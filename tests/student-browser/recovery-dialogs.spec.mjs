import { fileURLToPath } from 'node:url';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

const sample = fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url));
const photoRoute = 'POST /student/tutor/inspect';

async function scanPhoto(page, app) {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera?mode=MATH_TUTOR`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true }).click();
  await (await chooser).setFiles(sample);
  await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' }).click();
  await page.getByRole('button', { name: 'Tiếp tục xem lại', exact: true }).click();
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
}

test('scan failure opens a keyboard-accessible dialog and still offers recovery after dismissal', async ({ page, app }, info) => {
  let reads = 0;
  app.responses.set(photoRoute, ({ route }) => { reads++; return route.abort('failed'); });
  await scanPhoto(page, app);
  const dialog = page.getByRole('alertdialog', { name: 'Chưa đọc được ảnh đề' });
  await expect(dialog).toBeVisible();
  const retry = dialog.getByRole('button', { name: 'Đọc lại ảnh', exact: true });
  await expect(retry).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Nhập đề bằng chữ' })).toBeFocused();
  await page.screenshot({ path: info.outputPath('scan-failure.png'), animations: 'disabled' });
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Đọc lại ảnh', exact: true })).toBeFocused();
  await page.getByRole('button', { name: 'Đọc lại ảnh', exact: true }).click();
  await expect(dialog).toBeVisible();
  expect(reads).toBe(2);
  await dialog.getByRole('button', { name: 'Nhập đề bằng chữ' }).click();
  await expect(page.getByPlaceholder('Nhập nội dung ở đây nhé…', { exact: true })).toBeVisible();
  await expect(dialog).toHaveCount(0);
  expect(reads).toBe(2);
});

test('unreadable photo offers cropping instead of sending the same image again', async ({ page, app }) => {
  app.responses.set(photoRoute, ({ json }) => json({ kind: 'UNREADABLE', problemText: '', lines: [], needsProblem: true }));
  await scanPhoto(page, app);
  const dialog = page.getByRole('alertdialog', { name: 'Ảnh chưa đủ rõ' });
  await dialog.getByRole('button', { name: 'Chọn lại vùng bài toán' }).click();
  await expect(page).toHaveURL(/\/study\/crop/);
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh').filter({ visible: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/inspect')).toHaveLength(1);
});

test('unavailable quiz shows a recovery dialog and returns to the quiz list', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('GET /student/quizzes/unavailable-quiz', ({ reject }) => reject(503));
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/quiz/unavailable-quiz`);
  const dialog = page.getByRole('alertdialog', { name: 'Chưa mở được câu đố' });
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Về danh sách câu đố' }).click();
  await expect(page).toHaveURL(/\/study\/quiz\/?$/);
  await expect(dialog).toHaveCount(0);
});
