import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('Student can open and complete the parent PIN gate from the profile on desktop and compact web', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('GET /student/parent-control/status', ({ json }) =>
    json({ pinConfigured: true, dailyLimitConfigured: false, dailyLimitReached: false, activityVerified: true }));
  let dailyMinutes = 45;
  app.responses.set('PUT /student/parent-control/daily-limit', ({ body, json }) => {
    if (body.pin !== '123456') return json({ error: { code: 'PARENT_PIN_INVALID' } }, 403);
    dailyMinutes = body.minutes;
    return json({ dailyMinutes });
  });
  app.responses.set('POST /student/parent-control/unlock', ({ body, json }) => body.pin === '123456'
    ? json({ dailyMinutes })
    : json({ error: { code: 'PARENT_PIN_INVALID' } }, 403));
  app.responses.set('GET /student/app-usage/week', ({ json }) => json({ today: '2026-11-20', totalMillis: 0,
    days: [{ date: '2026-11-16', elapsedMillis: 0 }, { date: '2026-11-17', elapsedMillis: 0 }, { date: '2026-11-18', elapsedMillis: 0 },
      { date: '2026-11-19', elapsedMillis: 0 }, { date: '2026-11-20', elapsedMillis: 0 }, { date: '2026-11-21', elapsedMillis: 0 }, { date: '2026-11-22', elapsedMillis: 0 }] }));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);

  for (const width of [1920, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(`${sites.portal.origin}/study/profile`);
    const parentEntry = page.getByRole('button', { name: 'Góc phụ huynh', exact: true });
    await expect(parentEntry).toBeInViewport();
    await expect(page.getByRole('heading', { name: 'Tiến độ học tập', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await parentEntry.click();
    await expect(page).toHaveURL(`${sites.portal.origin}/study/profile`);
    const dialog = page.getByRole('dialog', { name: 'Mở Góc phụ huynh' });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByTestId('pin-cell')).toHaveCount(6);
    await dialog.getByLabel('Mã PIN', { exact: true }).fill('123456');
    await expect(page).toHaveURL(`${sites.portal.origin}/study/parent-mode`);
    await expect(page.getByRole('heading', { name: 'Tiến độ học tập', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Thời gian học theo ngày' })).toBeVisible();
    await expect(page.getByLabel('Thứ 6, hôm nay, 0 phút', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Chủ nhật, Chưa tới', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.getByRole('button', { name: 'Đổi giới hạn' }).click();
    await page.getByRole('button', { name: width === 320 ? 'Chọn 60 phút mỗi ngày' : 'Chọn 90 phút mỗi ngày' }).click();
    await page.getByRole('button', { name: 'Xác nhận thay đổi' }).click();
    const confirmation = page.getByRole('dialog', { name: 'Xác nhận bằng mã PIN' });
    await expect(confirmation).toBeVisible();
    await expect(confirmation.getByTestId('pin-cell')).toHaveCount(6);
    expect(await confirmation.getByTestId('pin-cell').last().evaluate(cell => {
      const { x, y, width, height } = cell.getBoundingClientRect();
      const hit = document.elementFromPoint(x + width / 2, y + height / 2);
      return !!hit && cell.closest('[role="dialog"]').contains(hit);
    })).toBe(true);
    await confirmation.getByRole('button', { name: 'Hủy xác nhận' }).click();
    await expect(confirmation).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Xác nhận thay đổi' })).toBeVisible();
    await page.getByRole('button', { name: 'Xác nhận thay đổi' }).click();
    await confirmation.getByLabel('Mã PIN để lưu', { exact: true }).fill('123456');
    await confirmation.getByRole('button', { name: 'Lưu giới hạn', exact: true }).click();
    await expect(confirmation).toHaveCount(0);
    await expect(page.getByText(/Đã lưu giới hạn trên tài khoản/)).toBeVisible();
  }

  await page.setViewportSize({ width: 1280, height: 844 });
  await page.goto(`${sites.portal.origin}/study/account`);
  await expect(page.getByRole('button', { name: 'Góc phụ huynh', exact: true })).toHaveCount(0);
  await expect(page.getByText('Quyền riêng tư', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'An toàn tài khoản', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Tổng quan học tập của em', exact: true })).toHaveCount(0);
});
