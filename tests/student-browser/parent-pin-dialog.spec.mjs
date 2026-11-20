import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('Parent Mode web PIN opens over the profile, rejects a wrong code, then navigates after a valid code', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('GET /student/parent-control/status', ({ json }) =>
    json({ pinConfigured: true, dailyLimitConfigured: true, dailyLimitReached: false, activityVerified: true }));
  app.responses.set('POST /student/parent-control/unlock', ({ body, json }) => body.pin === '123456'
    ? json({ dailyMinutes: 45 })
    : json({ error: { code: 'PARENT_PIN_INVALID', message: 'PIN không hợp lệ.' } }, 403));
  app.responses.set('GET /student/app-usage/week', ({ json }) => json({ today: '2026-11-20', totalMillis: 0,
    days: [{ date: '2026-11-16', elapsedMillis: 0 }, { date: '2026-11-17', elapsedMillis: 0 }, { date: '2026-11-18', elapsedMillis: 0 },
      { date: '2026-11-19', elapsedMillis: 0 }, { date: '2026-11-20', elapsedMillis: 0 }, { date: '2026-11-21', elapsedMillis: 0 }, { date: '2026-11-22', elapsedMillis: 0 }] }));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/profile`);
  await page.getByRole('button', { name: 'Góc phụ huynh', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
  const dialog = page.getByRole('dialog', { name: 'Mở Góc phụ huynh' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByTestId('pin-cell')).toHaveCount(6);
  await expect(dialog.getByText('Mã PIN 6 số giúp giữ riêng các thiết lập học tập và thời gian của con.')).toHaveCount(0);
  await expect(dialog.getByText('Nhập mã PIN 6 chữ số đã thiết lập cho tài khoản của con.')).toHaveCount(0);
  const pin = dialog.getByLabel('Mã PIN', { exact: true });
  await pin.fill('000000');
  await expect(dialog.getByRole('alert')).toContainText('Mã PIN chưa đúng');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
  await expect(page.getByRole('button', { name: 'Khóa Góc phụ huynh', exact: true })).toHaveCount(0);
  await pin.fill('123456');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/parent-mode`);
  await expect(page.getByRole('dialog', { name: 'Mở Góc phụ huynh' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Tiến độ học tập', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Tổng hợp học tập', exact: true })).toBeVisible();
  await expect(page.getByText('Bài học hoàn thành', { exact: true }).last()).toBeVisible();
  await page.getByRole('button', { name: 'Khóa Góc phụ huynh', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
  await expect(page.getByRole('dialog', { name: 'Mở Góc phụ huynh' })).toHaveCount(0);
  await page.goto(`${sites.portal.origin}/study/parent-mode`);
  await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
  await expect(page.getByRole('dialog', { name: 'Mở Góc phụ huynh' })).toHaveCount(0);
  expect(app.requests.filter(request => request.path === '/student/parent-control/unlock').map(request => request.body.pin)).toEqual(['000000', '123456']);
});
