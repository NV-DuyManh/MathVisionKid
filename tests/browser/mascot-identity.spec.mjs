import { test, expect, sites, login, openNavigation } from './fixtures.mjs';

async function expectRobotBranding(page) {
  const robots = page.locator('img[src="/ui/robot-mascot.webp"]');
  expect(await robots.count()).toBeGreaterThan(0);
  await expect.poll(() => robots.evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0)),
    { message: 'Every rendered robot mascot loads successfully' }).toBe(true);
  await expect(page.locator('img[src*="mathvision-star"], img[src*="icon-v2"], img[alt="Star mascot"]')).toHaveCount(0);
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', '/ui/robot-mascot.webp');
}

test('Portal landing and shared login use the robot mascot', async ({ page, app }, testInfo) => {
  await page.goto(`${sites.portal.origin}/`);
  await expect(page.getByRole('banner')).toBeVisible();
  await expectRobotBranding(page);
  await testInfo.attach('Portal robot mascot', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('banner').getByRole('link', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Đăng nhập', exact: true })).toBeVisible();
  await expectRobotBranding(page);
  await testInfo.attach('Shared login robot mascot', { body: await page.screenshot(), contentType: 'image/png' });
});

test('Teacher dashboard and navigation use the robot mascot', async ({ page, app }, testInfo) => {
  await login(page, 'TEACHER');
  await expectRobotBranding(page);
  await expect(page.locator('header img[src="/ui/robot-mascot.webp"]')).toBeVisible();
  await openNavigation(page, 'TEACHER');
  await expect(page.locator('img[src="/ui/robot-mascot.webp"]')).toHaveCount(2);
  await expectRobotBranding(page);
  await testInfo.attach('Teacher robot mascot', { body: await page.screenshot(), contentType: 'image/png' });
});

test('Admin dashboard, navigation and access status use the robot mascot', async ({ page, app }, testInfo) => {
  await login(page, 'ADMIN');
  await expectRobotBranding(page);
  await expect(page.locator('.hero-illustration[src="/ui/robot-mascot.webp"]')).toBeVisible();
  await openNavigation(page, 'ADMIN');
  await expect(page.locator('img[src="/ui/robot-mascot.webp"]')).toHaveCount(2);
  await expectRobotBranding(page);
  await testInfo.attach('Admin robot mascot', { body: await page.screenshot(), contentType: 'image/png' });
  await page.goto(`${sites.admin.origin}/403`);
  await expect(page.getByRole('heading', { name: 'Bạn không có quyền truy cập', exact: true })).toBeVisible();
  await expectRobotBranding(page);
  await testInfo.attach('Admin status robot mascot', { body: await page.screenshot(), contentType: 'image/png' });
});
