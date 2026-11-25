import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('sets and recovers the parent PIN with the account email in one dialog', async ({ page, app }) => {
  app.realStudent = true;
  let pin;
  app.responses.set('GET /student/parent-control/status', ({ json }) =>
    json({ pinConfigured: Boolean(pin), dailyLimitReached: false, activityVerified: true }));
  app.responses.set('POST /student/parent-control/pin-code/request', ({ body, json }) => {
    expect(body).toEqual({ purpose: pin ? 'RESET' : 'SETUP' });
    return json({ maskedEmail: 'st***@example.test' });
  });
  app.responses.set('POST /student/parent-control/pin-code/confirm', ({ body, route, json }) => {
    if (body.code !== '716025') return json({ error: { code: 'PARENT_PIN_CODE_INVALID' } }, 403);
    pin = body.pin;
    return route.fulfill({ status: 204 });
  });
  app.responses.set('POST /student/parent-control/unlock', ({ body, json }) =>
    body.pin === pin ? json({ dailyMinutes: null, gameMinutes: null }) : json({ error: { code: 'PARENT_PIN_INVALID' } }, 403));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/profile`);
  await page.getByRole('button', { name: 'Góc phụ huynh', exact: true }).click();

  async function complete(title, nextPin) {
    const dialog = page.getByRole('dialog', { name: title, exact: true });
    await dialog.getByRole('button', { name: 'Gửi mã xác nhận', exact: true }).click();
    await expect(dialog.getByText(/st\*\*\*@example\.test/)).toBeVisible();
    const confirmation = dialog.getByLabel('Nhập lại mã PIN mới', { exact: true });
    await dialog.getByLabel('Mã xác nhận từ email', { exact: true }).fill('000000');
    await dialog.getByLabel('Mã PIN mới', { exact: true }).fill(nextPin);
    await confirmation.fill('999999');
    const save = dialog.getByRole('button', { name: 'Lưu mã PIN mới' });
    await save.click();
    await expect(dialog.getByRole('alert')).toContainText('Hai mã PIN chưa giống nhau');
    await confirmation.fill(nextPin);
    await save.click();
    await expect(dialog.getByRole('alert')).toContainText('Mã xác nhận chưa đúng');
    await dialog.getByLabel('Mã xác nhận từ email', { exact: true }).fill('716025');
    await save.click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByText(/Đã lưu mã PIN mới/)).toBeVisible();
  }

  await page.getByRole('button', { name: 'Thiết lập mã PIN', exact: true }).click();
  await complete('Thiết lập mã PIN', '824615');
  await page.getByRole('button', { name: 'Quên mã PIN?', exact: true }).click();
  await complete('Đặt lại mã PIN', '516824');
  await page.getByLabel('Mã PIN', { exact: true }).fill('824615');
  await expect(page.getByRole('alert')).toContainText('Mã PIN chưa đúng');
  await page.getByLabel('Mã PIN', { exact: true }).fill('516824');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/parent-mode`);
});

test('browser Back and Forward do not reopen the parent dashboard without the PIN', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('GET /student/parent-control/status', ({ json }) =>
    json({ pinConfigured: true, dailyLimitReached: false, activityVerified: true }));
  app.responses.set('POST /student/parent-control/unlock', ({ json }) => json({ dailyMinutes: 45 }));
  app.responses.set('GET /student/app-usage/week', ({ json }) =>
    json({ today: '2026-11-20', totalMillis: 0, days: [] }));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/profile`);
  const profileEntry = page.getByRole('button', { name: 'Góc phụ huynh', exact: true });
  await profileEntry.click();
  await page.getByLabel('Mã PIN', { exact: true }).fill('516824');
  const lock = page.getByRole('button', { name: 'Khóa Góc phụ huynh' });
  await expect(lock).toBeVisible();
  await page.goBack();
  await expect(profileEntry).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
  await expect(lock).toHaveCount(0);
  await profileEntry.click();
  await expect(page.getByRole('dialog', { name: 'Mở Góc phụ huynh' })).toBeVisible();
});
