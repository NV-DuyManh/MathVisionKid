import { test, expect, sites, login } from '../browser/fixtures.mjs';

for (const width of [320, 390, 1024]) {
  test(`compact profile supports avatar hover/focus and cancellable name editing at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: 844 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/account`);
    const avatar = page.getByRole('button', { name: 'Thay ảnh đại diện', exact: true });
    await expect(avatar).toBeVisible();
    const overlay = page.getByTestId('avatar-change-overlay');
    await expect(overlay).toHaveCSS('opacity', '0');
    await avatar.hover();
    await expect(overlay).toHaveCSS('opacity', '1');
    await page.mouse.move(0, 0);
    await expect(overlay).toHaveCSS('opacity', '0');
    await avatar.focus();
    await expect(overlay).toHaveCSS('opacity', '1');
    await expect(page.getByRole('textbox', { name: 'Tên hiển thị', exact: true })).toHaveCount(0);
    await page.getByRole('button', { name: 'Đổi tên hiển thị', exact: true }).click();
    const name = page.getByRole('textbox', { name: 'Tên hiển thị', exact: true });
    await expect(name).toBeFocused();
    await name.fill('123');
    await page.getByRole('button', { name: 'Lưu tên', exact: true }).click();
    await expect(name).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByRole('alert')).toContainText('tối đa 40');
    expect(app.requests.filter(request => request.method === 'PUT' && request.path === '/student/profile')).toHaveLength(0);
    await page.getByRole('button', { name: 'Đóng Đổi tên của em', exact: true }).click();
    await expect(name).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Lưu thay đổi', exact: true })).toBeDisabled();
    await expect(page.getByText('Góc học tập', { exact: true })).toHaveCount(0);
    await expect(page.getByText('Ảnh và tên hiển thị của em', { exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /^Chọn hình / })).toHaveCount(0);
    const editorBox = await page.getByTestId('account-profile-editor').boundingBox();
    const savedBox = await page.getByText('Thông tin của em đã được lưu.', { exact: true }).boundingBox();
    expect(savedBox.y + savedBox.height).toBeLessThan(editorBox.y + editorBox.height);
    const nameBox = await page.getByRole('heading', { name: 'Kiểm thử STUDENT', exact: true }).boundingBox();
    expect(nameBox.height).toBeLessThanOrEqual(width < 480 ? 50 : 60);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: testInfo.outputPath(`compact-profile-${width}.png`), fullPage: true });
  });
}

for (const mode of ['current', 'legacy-update-response', 'unconfirmed']) {
  test(`participating with a visible name never flips the switch after saving: ${mode}`, async ({ page, app }) => {
    app.realStudent = true;
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.route('**/api/v1/student/profile', async route => {
      if (route.request().method() === 'PUT') {
        const patch = route.request().postDataJSON();
        expect(patch.leaderboardVisible).toBe(true);
        expect(patch.leaderboardNameHidden).toBe(false);
        app.studentProfile = { ...app.studentProfile, ...patch, leaderboardNameHidden: mode === 'unconfirmed' ? true : false };
        const response = { ...app.studentProfile };
        if (mode !== 'current') delete response.leaderboardNameHidden;
        return route.fulfill({ json: response });
      }
      return route.fulfill({ json: app.studentProfile });
    });
    await page.goto(`${sites.portal.origin}/study/account`);
    const participate = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng', exact: true });
    const hidden = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng', exact: true });
    await participate.click();
    await hidden.click();
    await expect(participate).toBeChecked();
    await expect(hidden).not.toBeChecked();
    await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
    if (mode === 'unconfirmed') {
      await expect(page.getByRole('alert')).toContainText('Chưa xác nhận được lựa chọn quyền riêng tư đã lưu');
      await expect(hidden).not.toBeChecked();
      await expect(participate).toBeChecked();
      await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Lưu thay đổi', exact: true })).toBeEnabled();
    } else {
      await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
      await expect(hidden).not.toBeChecked();
      await expect(page.getByRole('button', { name: 'Lưu thay đổi', exact: true })).toBeDisabled();
      await page.reload();
      await expect(participate).toBeChecked();
      await expect(hidden).not.toBeChecked();
    }
  });
}
