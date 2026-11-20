import { test, expect, sites, login } from '../browser/fixtures.mjs';

const widths = [360, 390, 430, 768, 1024, 1280, 1440];

for (const width of widths) {
  test(`onboarding opens the login form without a verification loop at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(`${sites.portal.origin}/study/onboarding`);
    if (width >= 768) {
      await expect(page).toHaveURL(sites.portal.origin + '/login');
      await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
      expect(app.requests.filter(request => request.path === '/me')).toHaveLength(0);
      return;
    }
    await expect(page.getByRole('heading', { name: 'Học Toán thông minh cùng AI', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Trang giới thiệu trước', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Trang giới thiệu tiếp theo', exact: true })).toHaveCount(0);
    await expect(page.getByText(/^Trang [123] trên 3$/)).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true })).toBeVisible();
    await page.getByRole('tab', { name: 'Trang giới thiệu 3', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Mỗi ngày tiến bộ một chút', exact: true })).toBeVisible();
    await page.getByRole('tab', { name: 'Trang giới thiệu 1', exact: true }).click();
    const firstTab = page.getByRole('tab', { name: 'Trang giới thiệu 1', exact: true });
    await firstTab.focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByRole('tab', { name: 'Trang giới thiệu 2', exact: true })).toBeFocused();
    await page.keyboard.press('End');
    await expect(page.getByRole('tab', { name: 'Trang giới thiệu 3', exact: true })).toHaveAttribute('aria-selected', 'true');
    await page.keyboard.press('Home');
    await expect(firstTab).toBeFocused();
    await expect(firstTab).toHaveAttribute('aria-selected', 'true');
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    expect(app.requests.filter(request => request.path === '/me')).toHaveLength(0);
    await testInfo.attach(`onboarding-${width}`, { body: await page.screenshot({ path: testInfo.outputPath('onboarding-recovered.png') }), contentType: 'image/png' });
    await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click();
    await expect(page).toHaveURL(`${sites.portal.origin}/login`);
    expect(await page.evaluate(() => localStorage.getItem('mathvision_onboarding_completed_v1'))).toBe('true');
    await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
    await expect(page.getByText('Đang xác minh tài khoản…', { exact: true })).toHaveCount(0);
  });
}

test('touch swipes update onboarding cards and Start reaches login', async ({ page, app, isMobile }) => {
  test.skip(!isMobile, 'Touch gesture verification uses the mobile browser context.');
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  const pager = page.getByTestId('welcome-pager');
  await expect(page.getByRole('heading', { name: 'Học Toán thông minh cùng AI', exact: true })).toBeVisible();
  const bounds = await pager.boundingBox();
  const session = await page.context().newCDPSession(page);
  const y = bounds.y + bounds.height / 2;
  await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: bounds.x + bounds.width * .85, y }] });
  for (let step = 1; step <= 12; step++) {
    await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: bounds.x + bounds.width * (.85 - step * .7 / 12), y }] });
    await page.waitForTimeout(20);
  }
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(page.getByRole('tab', { name: 'Trang giới thiệu 2', exact: true })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('heading', { name: 'Hiểu bài qua từng bước nhỏ', exact: true })).toBeVisible();
  await session.detach();
  await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
});

test('the former Student login leads to the common Portal login', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/login`);
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
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
    localStorage.setItem('mvk_portal_web_session', 'expired-tab-id');
  });
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
  await expect(page.getByText('Đang xác minh tài khoản…', { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => localStorage.getItem('mvk_portal_web_session'))).toBeNull();
  expect(app.requests.some(request => request.path === '/me')).toBe(true);
});

test('a verified student can deliberately reopen introduction and skip directly home', async ({ page, app }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  await expect(page.getByRole('button', { name: 'Bắt đầu', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true }).click();
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Bắt đầu', exact: true })).toHaveCount(0);
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/);
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


for (const authenticated of [false, true]) {
  test(`Skip introduction persists completion for ${authenticated ? 'verified student' : 'anonymous visitor'}`, async ({ page, app }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    app.realStudent = true;
    if (authenticated) {
      await login(page, 'STUDENT');
      await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    }
    await page.goto(`${sites.portal.origin}/study/onboarding`);
    const skip = page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true });
    await expect(skip).toBeVisible();
    await skip.click();
    if (authenticated) await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    else await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem('mathvision_onboarding_completed_v1'))).toBe('true');
    await page.reload();
    await expect(page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true })).toHaveCount(0);
  });
}

test('small phone introduction keeps Start and Continue together without horizontal overflow', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto(`${sites.portal.origin}/study/onboarding`);
  await expect(page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true })).toBeVisible();
  const start = page.getByRole('button', { name: 'Bắt đầu', exact: true });
  const continueLearning = page.getByRole('button', { name: 'Tiếp tục học', exact: true });
  await continueLearning.scrollIntoViewIfNeeded();
  await expect(start).toBeInViewport();
  await expect(continueLearning).toBeInViewport();
  const [pager, primary, secondary] = await Promise.all([page.getByRole('tablist').boundingBox(), start.boundingBox(), continueLearning.boundingBox()]);
  expect(primary.y - pager.y - pager.height).toBeLessThan(30);
  expect(secondary.y - primary.y - primary.height).toBeLessThan(12);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  await testInfo.attach('onboarding-small-phone', { body: await page.screenshot({ path: testInfo.outputPath('onboarding-small-phone.png') }), contentType: 'image/png' });
  await continueLearning.click();
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
});
