import { expect, login, test } from '../browser/fixtures.mjs';

async function capture(page, testInfo, label) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize().width + 1);
  await page.evaluate(() => document.fonts.ready);
  const path = testInfo.outputPath(`${label}.png`);
  await page.screenshot({ path, animations: 'disabled' });
  await testInfo.attach(label, { path, contentType: 'image/png' });
}

for (const width of [390, 768, 1024, 1280, 1440, 1672]) {
  test(`Student dashboard, quiz and games at ${width}px`, async ({ page, app }, testInfo) => {
    await page.setViewportSize({ width, height: width === 390 ? 844 : width === 768 ? 1024 : 941 });
    app.realStudent = true;
    await login(page, 'STUDENT');
    await expect(page.getByTestId('home-hero')).toBeVisible();
    await expect(page.getByTestId('quick-actions-grid').getByRole('button')).toHaveCount(5);
    await expect(page.getByTestId('learning-journey').getByRole('button')).toHaveCount(4);
    await expect(page.getByTestId('learning-streak').getByText('Em đã học liên tiếp 1 ngày!')).toBeVisible();
    await capture(page, testInfo, 'dashboard');

    if (width >= 768) {
      const nav = page.getByRole('navigation', { name: 'Điều hướng học sinh' });
      await expect(nav.getByRole('link', { name: '1 sao' })).toHaveCount(0);
      await expect(page.getByRole('link', { name: '1 sao', exact: true })).toBeVisible();
      await expect(nav.getByRole('link')).toHaveCount(7);
      await expect(nav.getByRole('link', { name: 'Trang chủ' })).toHaveAttribute('aria-current', 'page');
      await nav.getByRole('link', { name: 'Trang chủ' }).focus();
      await page.keyboard.press('ArrowDown');
      await expect(nav.getByRole('link', { name: 'Bài học' })).toBeFocused();
      const search = page.getByRole('searchbox', { name: 'Tìm bài học, chủ đề' });
      await page.keyboard.press('Control+k');
      await expect(search).toBeFocused();
      await search.fill('cong so thap phan');
      const searchResult = page.getByRole('link', { name: 'Cộng số thập phân', exact: true });
      await expect(searchResult).toBeVisible();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/\/study\/lessons\?q=/);
      await expect(page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true })).toBeVisible();
      const account = page.getByRole('button', { name: 'Menu tài khoản học sinh' });
      await account.click();
      await expect(page.getByRole('link', { name: 'Hồ sơ của em' })).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(account).toBeFocused();
      await expect(page.getByRole('link', { name: 'Hồ sơ của em' })).toHaveCount(0);
      await account.click();
      await page.getByRole('link', { name: 'Đăng xuất', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Xác nhận đăng xuất' })).toBeVisible();
      await page.getByRole('button', { name: 'Ở lại', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Xác nhận đăng xuất' })).toHaveCount(0);
      const toggle = page.getByRole('button', { name: 'Thu gọn menu' });
      await toggle.click();
      await expect(page.getByRole('button', { name: 'Mở rộng menu' })).toHaveAttribute('aria-expanded', 'false');
      await nav.getByRole('link', { name: 'Câu đố', exact: true }).click();
      await expect(page.getByRole('button', { name: 'Mở rộng menu' })).toBeVisible();
      await page.getByRole('button', { name: 'Mở rộng menu' }).click();
    } else {
      await page.getByTestId('learning-journey').getByRole('button', { name: /^Kiểm tra/ }).click();
    }
    await expect(page.getByRole('heading', { name: 'Danh sách câu đố' })).toBeVisible();
    await expect(page.getByText('Chưa có câu đố mới')).toBeVisible();
    await capture(page, testInfo, 'quiz');
    await page.getByRole('button', { name: 'Đã xong', exact: true }).click();
    await expect(page.getByText('Cùng tạo thành tích đầu tiên!')).toBeVisible();

    if (width >= 768) {
      await page.getByRole('link', { name: 'Trò chơi', exact: true }).click();
    } else {
      const url = new URL(page.url());
      await page.goto(new URL('/study/games', url).href);
    }
    await expect(page.getByRole('heading', { name: 'Khu trò chơi toán học' })).toBeVisible();
    await expect(page.getByTestId('game-star-quest')).toBeVisible();
    await expect(page.getByTestId(/^training-card-/)).toHaveCount(5);
    await capture(page, testInfo, 'games');
    await page.getByRole('button', { name: 'Phân số', exact: true }).click();
    await expect(page.getByTestId(/^training-card-/)).toHaveCount(2);
    await expect(page.getByTestId('training-card-planet-rescue')).toBeVisible();
    await page.getByRole('button', { name: 'Tất cả', exact: true }).click();
    await expect(page.getByTestId(/^training-card-/)).toHaveCount(5);
  });
}
