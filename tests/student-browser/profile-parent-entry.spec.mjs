import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('Student can open and complete the parent PIN gate from the profile on desktop and compact web', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('GET /student/parent-control/status', ({ json }) =>
    json({ pinConfigured: true, dailyLimitConfigured: false, dailyLimitReached: false, activityVerified: true }));
  app.responses.set('POST /student/parent-control/unlock', ({ body, json }) => body.pin === '123456'
    ? json({ dailyMinutes: null })
    : json({ error: { code: 'PARENT_PIN_INVALID' } }, 401));
  app.responses.set('GET /student/app-usage/week', ({ json }) => json({ today: '2026-11-20', totalMillis: 0,
    days: [{ date: '2026-11-16', elapsedMillis: 0 }, { date: '2026-11-17', elapsedMillis: 0 }, { date: '2026-11-18', elapsedMillis: 0 },
      { date: '2026-11-19', elapsedMillis: 0 }, { date: '2026-11-20', elapsedMillis: 0 }, { date: '2026-11-21', elapsedMillis: 0 }, { date: '2026-11-22', elapsedMillis: 0 }] }));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);

  for (const width of [1280, 320]) {
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
  }

  await page.setViewportSize({ width: 1280, height: 844 });
  await page.goto(`${sites.portal.origin}/study/account`);
  await expect(page.getByRole('button', { name: 'Góc phụ huynh', exact: true })).toHaveCount(0);
  await expect(page.getByText('Quyền riêng tư', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'An toàn tài khoản', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Tổng quan học tập của em', exact: true })).toHaveCount(0);
});
