import { test, expect, sites, login } from '../browser/fixtures.mjs';

for (const width of [360, 375, 390, 430, 768, 1024, 1280, 1440, 1920]) {
  test(`legacy introduction URLs go directly to Web login at ${width}px`, async ({ page, app }) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['welcome', 'onboarding']) {
      await page.goto(`${sites.portal.origin}/study/${route}`);
      await expect(page).toHaveURL(`${sites.portal.origin}/study/login`);
      await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
      await expect(page.getByText('Học Toán thông minh cùng AI', { exact: true })).toHaveCount(0);
      await expect(page.getByRole('navigation')).toHaveCount(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    }
    expect(app.requests.filter(request => request.path === '/me')).toHaveLength(0);
  });
}

test('the mounted Student login authenticates directly without visiting Portal', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/login`);
  await expect(page).toHaveURL(`${sites.portal.origin}/study/login`);
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
  await expect(page.getByText('Đang xác minh tài khoản…', { exact: true })).toHaveCount(0);
  expect(app.requests.filter(request => request.path === '/me')).toHaveLength(0);
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('student@example.test');
  await page.getByLabel(/^Mật khẩu/).fill('synthetic-password');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
});

test('expired onboarding credentials recover to login and clear the stale session', async ({ page, app }) => {
  app.realStudent = true;
  app.expired = true;
  await page.addInitScript(() => {
    if (location.pathname !== '/study/onboarding') return;
    sessionStorage.setItem('portal_access_token', 'fixture.STUDENT.access');
    sessionStorage.setItem('portal_refresh_token', 'fixture.STUDENT.refresh');
  });
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
  await expect(page.getByText('Đang xác minh tài khoản…', { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem('portal_access_token'))).toBeNull();
  expect(await page.evaluate(() => sessionStorage.getItem('portal_refresh_token'))).toBeNull();
  expect(app.requests.some(request => request.path === '/me')).toBe(true);
});

test('a verified student opening an old introduction link goes directly home', async ({ page, app }) => {
  app.realStudent = true;
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await expect(page.getByText('Học Toán thông minh cùng AI', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Thông báo học tập' }).click();
  await expect(page.getByText('Chưa có thông báo mới.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Mở lại giới thiệu MathVisionKid' })).toHaveCount(0);
});

test('a verified student opening the mounted login stays in the learning app', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  const loginNavigations = [];
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame() && new URL(frame.url()).pathname === '/login') loginNavigations.push(frame.url());
  });
  await page.goto(`${sites.portal.origin}/study/login`);
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/);
  expect(loginNavigations).toEqual([]);
});
