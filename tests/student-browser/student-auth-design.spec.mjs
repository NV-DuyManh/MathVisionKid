import { test, expect, sites } from '../browser/fixtures.mjs';

const loginHeading = 'Đăng nhập';
const registerHeading = 'Bắt đầu hành trình học Toán';
const recoverHeading = 'Lấy lại mật khẩu thật dễ';

for (const width of [390, 1024, 1672]) {
  test(`Student auth layouts fit ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: width === 390 ? 844 : 941 });
    await page.goto(`${sites.portal.origin}/study/login`);

    const capture = async (name, heading) => {
      await expect(page.getByRole('heading', { name: heading, level: 1 })).toBeVisible();
      await page.evaluate(() => document.fonts.ready);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
      const hero = await page.locator('.student-auth-hero').boundingBox();
      expect(hero.width).toBeGreaterThanOrEqual(width * (width < 840 ? .9 : .49));
      expect(hero.width).toBeLessThanOrEqual(width * (width < 840 ? 1 : .54));
      expect(hero.height).toBeGreaterThan(130);
      await page.screenshot({ path: testInfo.outputPath(`${name}-${width}.png`), fullPage: true, animations: 'disabled', scale: 'css' });
    };

    await capture('login', loginHeading);
    await page.getByRole('button', { name: /Đăng ký ngay/ }).click();
    await capture('register', registerHeading);
    await expect(page.getByRole('button', { name: 'Tạo tài khoản', exact: true })).toBeVisible();
    await page.getByRole('button', { name: /Đã có tài khoản/ }).click();
    await page.getByRole('button', { name: 'Quên mật khẩu?' }).click();
    await capture('recover', recoverHeading);
  });
}

test('Password has a keyboard-visible ring around the rounded field and a focusable visibility toggle', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/login`);
  await page.getByRole('textbox', { name: 'Email', exact: true }).focus();
  await page.keyboard.press('Tab');
  const password = page.getByLabel('Mật khẩu', { exact: true });
  await expect(password).toBeFocused();
  await expect(password).toHaveAttribute('autocomplete', 'current-password');
  const wrapper = password.locator('..');
  await expect(password).toHaveCSS('outline-style', 'none');
  await expect(wrapper).toHaveCSS('border-radius', '17px');
  await expect(wrapper).toHaveCSS('border-top-color', 'rgb(113, 60, 247)');
  await expect(wrapper).not.toHaveCSS('box-shadow', 'none');
  await page.emulateMedia({ forcedColors: 'active' });
  await expect(wrapper).toHaveCSS('outline-style', 'solid');
  await page.emulateMedia({ forcedColors: 'none' });
  await page.keyboard.type('synthetic-password');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Hiện mật khẩu' })).toBeFocused();
  await page.keyboard.press('Space');
  await expect(password).toHaveJSProperty('type', 'text');
  await page.keyboard.press('Space');
  await expect(password).toHaveAttribute('type', 'password');
  await password.press('Enter');
  await expect(page.getByRole('alert')).toBeFocused();
  await expect(page.getByRole('alert')).toContainText('Vui lòng nhập đầy đủ email và mật khẩu.');
  expect(app.requests.filter(request => request.path === '/auth/login')).toHaveLength(0);
});

test('Registration preserves required fields and posts the selected grade and account role', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('POST /auth/register', ({ json }) => json({}, 201));
  await page.goto(`${sites.portal.origin}/study/login`);
  await page.getByRole('button', { name: /Đăng ký ngay/ }).click();
  await expect(page.getByRole('heading', { name: registerHeading })).toBeFocused();
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Vui lòng điền đầy đủ thông tin.');
  expect(app.requests.filter(request => request.path === '/auth/register')).toHaveLength(0);
  await page.getByLabel('Họ và tên', { exact: true }).fill('Hoc sinh kiem thu');
  await page.getByLabel('Email đăng nhập', { exact: true }).fill('registration@example.test');
  await page.getByLabel('Số điện thoại', { exact: true }).fill('0900000000');
  await page.getByRole('button', { name: 'Lớp 4', exact: true }).click();
  await page.getByRole('button', { name: 'Nữ', exact: true }).click();
  await page.getByLabel('Mật khẩu', { exact: true }).fill('synthetic-password');
  await page.getByLabel('Nhập lại mật khẩu', { exact: true }).fill('synthetic-password');
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
  await expect(page.getByRole('heading', { name: loginHeading })).toBeFocused();
  await expect(page.getByRole('alert')).toContainText('Tạo tài khoản thành công');
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/auth/register').map(request => request.body)).toEqual([{
    displayName: 'Hoc sinh kiem thu', email: 'registration@example.test', phoneNumber: '0900000000',
    role: 'STUDENT', gender: 'FEMALE', gradeLevel: 4, password: 'synthetic-password',
  }]);
});

test('Password recovery shows a service error, then accepts a new code on retry', async ({ page, app }) => {
  app.realStudent = true;
  app.responses.set('POST /auth/password-reset/request', ({ json }) => json({ error: { code: 'EMAIL_DELIVERY_FAILED' } }, 503));
  app.responses.set('POST /auth/password-reset/confirm', ({ json }) => json({}));
  await page.goto(`${sites.portal.origin}/study/login`);
  await page.getByRole('button', { name: 'Quên mật khẩu?' }).click();
  await expect(page.getByRole('heading', { name: recoverHeading })).toBeFocused();
  await page.getByLabel('Email đăng ký', { exact: true }).fill('recovery@example.test');
  await page.getByRole('button', { name: 'Gửi mã xác nhận' }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa gửi được mã xác nhận.');
  app.responses.set('POST /auth/password-reset/request', ({ json }) => json({}));
  await page.getByRole('button', { name: 'Gửi mã xác nhận' }).click();
  await expect(page.getByRole('alert')).toContainText('Nếu email đã đăng ký');
  await page.getByRole('button', { name: 'Gửi lại mã' }).click();
  await expect(page.getByLabel('Email đăng ký', { exact: true })).toHaveValue('recovery@example.test');
  await page.getByRole('button', { name: 'Gửi mã xác nhận' }).click();
  const resetCode = page.getByLabel('Mã xác nhận 6 số', { exact: true });
  await expect(resetCode).toHaveAttribute('autocomplete', 'one-time-code');
  await resetCode.fill('123456');
  await page.getByLabel('Mật khẩu mới', { exact: true }).fill('new-synthetic-password');
  await page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill('new-synthetic-password');
  await page.getByRole('button', { name: 'Xác nhận và đổi mật khẩu' }).click();
  await expect(page.getByRole('alert')).toContainText('Đổi mật khẩu thành công.');
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/auth/password-reset/confirm').map(request => request.body)).toEqual([{
    email: 'recovery@example.test', code: '123456', newPassword: 'new-synthetic-password',
  }]);
});
