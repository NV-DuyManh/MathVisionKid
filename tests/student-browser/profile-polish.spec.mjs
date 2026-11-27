import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('a Google-linked student can set a MathVisionKid password using email verification', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, { googleLinked: true, passwordLoginAvailable: false });
  app.responses.set('POST /auth/password-reset/request', ({ body, json }) => {
    expect(body.email).toBe('student@example.test');
    return json({});
  });
  app.responses.set('POST /auth/password-reset/confirm', ({ body, json }) => {
    expect(body.email).toBe('student@example.test');
    return body.code === '123456' ? json({}) : json({}, 400);
  });

  await page.goto(`${sites.portal.origin}/study/account`);
  await page.getByRole('button', { name: 'Đổi mật khẩu MathVisionKid' }).click();
  const email = page.getByRole('textbox', { name: 'Email đã đăng ký' });
  await expect(email).toHaveValue('student@example.test');
  await expect(email).toHaveAttribute('readonly', '');
  await page.getByRole('button', { name: 'Gửi mã xác nhận' }).click();
  const code = page.getByRole('textbox', { name: 'Mã xác nhận 6 chữ số' });
  await code.fill('000000');
  await page.getByLabel('Mật khẩu mới').fill('synthetic-new-password');
  const submit = page.getByRole('button', { name: 'Xác nhận và đổi mật khẩu' });
  await submit.click();
  await expect(page.getByRole('alert')).toContainText('Mã không đúng hoặc đã hết hạn');
  await code.fill('123456');
  await submit.click();
  await expect(page.getByRole('status')).toContainText('Đổi mật khẩu thành công');
  expect(await page.evaluate(() => localStorage.getItem('mvk_portal_web_session'))).toBeNull();
});

test('empty activity keeps seven zeroes only on desktop', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  app.studentProfile.history = [];
  await page.goto(`${sites.portal.origin}/study/profile`);
  const chart = page.getByLabel('Biểu đồ hoạt động', { exact: true });
  if (testInfo.project.name === 'desktop') {
    await expect(chart.getByLabel(/: 0 lượt nhận sao$/)).toHaveCount(7);
    await expect(chart.getByText('Nay', { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText('Chưa có lượt nhận sao nào trong 7 ngày qua.')).toBeVisible();
    await expect(chart).toHaveCount(0);
  }
});

test('the student profile loads a Google avatar and falls back if the image is unavailable', async ({ page, app }) => {
  const picture = 'https://lh3.googleusercontent.com/a/synthetic-avatar';
  app.realStudent = true;
  await page.route(picture, route => route.fulfill({
    contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="blue"/></svg>',
  }));

  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  app.studentProfile.avatarPhoto = picture;
  await page.goto(`${sites.portal.origin}/study/profile`);
  const images = page.locator(`img[src="${picture}"]`);
  const avatar = images.filter({ visible: true }).first();
  await expect(avatar).toBeVisible();
  await expect.poll(() => avatar.evaluate(image => image.naturalWidth)).toBe(8);

  await page.unroute(picture);
  await page.route(picture, route => route.abort());
  const failedImage = page.waitForEvent('requestfailed', request => request.url() === picture);
  await page.reload();
  await failedImage;
  await expect(images).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Kiểm thử STUDENT', exact: true })).toBeVisible();
});

test('leaderboards show the private profile photo only on the signed-in student row', async ({ page, app }, testInfo) => {
  const picture = 'https://lh3.googleusercontent.com/a/synthetic-avatar';
  const ownAlias = 'Hươu Sao Của Em';
  const peerAlias = 'Cá Heo Chăm Học';
  let imageAvailable = true;
  app.realStudent = true;
  await page.route(picture, route => imageAvailable ? route.fulfill({
    contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>',
  }) : route.fulfill({ status: 404 }));
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, {
    avatarPhoto: picture, leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: ownAlias,
  });
  const { rank } = app.studentProfile;
  const peerRank = { ...rank, name: 'Đồng II' };
  await page.route('**/api/v1/student/leaderboard*', route => route.fulfill({ json: {
    gradeLevel: null, ownPosition: 1, entries: [
      { position: 1, alias: ownAlias, avatar: 'planet', stars: 10, rank, self: true },
      { position: 2, alias: peerAlias, avatar: 'rocket', stars: 9, rank: peerRank, self: false },
    ],
  } }));

  if (testInfo.project.name === 'desktop') {
    await page.goto(`${sites.portal.origin}/study/`);
    const homeRows = page.getByTestId('home-leaderboard-entry');
    const ownRow = homeRows.filter({ hasText: ownAlias });
    const peerRow = homeRows.filter({ hasText: peerAlias });
    await expect(ownRow.locator(`img[src="${picture}"]`)).toBeVisible();
    await expect(peerRow).toBeVisible();
    await expect(peerRow.locator(`img[src="${picture}"]`)).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Hạng của em', exact: true })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Mục tiêu tuần', exact: true })).toHaveCount(0);
    for (const [row, alias, rankName] of [[ownRow, ownAlias, rank.name], [peerRow, peerAlias, peerRank.name]]) {
      const nameText = row.getByText(alias, { exact: true });
      const rankText = row.getByText(rankName, { exact: true });
      await expect(rankText).toBeVisible();
      expect((await rankText.boundingBox()).y).toBeGreaterThan((await nameText.boundingBox()).y);
    }
    await page.getByRole('button', { name: 'Xem bảng xếp hạng', exact: true }).click();
  } else {
    await page.goto(`${sites.portal.origin}/study/achievements`);
  }

  const rows = page.getByTestId('leaderboard-entry');
  await expect(rows.filter({ hasText: ownAlias }).locator(`img[src="${picture}"]`)).toBeVisible();
  await expect(rows.filter({ hasText: peerAlias })).toBeVisible();
  await expect(rows.filter({ hasText: peerAlias }).locator(`img[src="${picture}"]`)).toHaveCount(0);

  imageAvailable = false;
  await page.reload();
  await expect(rows.filter({ hasText: ownAlias })).toBeVisible();
  await expect(rows.filter({ hasText: ownAlias }).locator(`img[src="${picture}"]`)).toHaveCount(0);

  app.studentProfile.leaderboardVisible = false;
  await page.reload();
  await expect(page.getByText('Em chưa tham gia bảng xếp hạng', { exact: true })).toBeVisible();
  await expect(rows.filter({ hasText: ownAlias })).toHaveCount(0);
  await expect(rows.filter({ hasText: peerAlias })).toBeVisible();
  if (testInfo.project.name === 'desktop') {
    await page.goto(`${sites.portal.origin}/study/`);
    await expect(page.getByText(peerAlias, { exact: true })).toBeVisible();
    await expect(page.getByText(ownAlias, { exact: true })).toHaveCount(0);
  }
});

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
    await name.fill(Array(51).fill('Em5').join('  '));
    await page.getByRole('button', { name: 'Lưu tên', exact: true }).click();
    await expect(name).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByRole('alert')).toContainText('tối đa 50 từ');
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
    await page.getByRole('button', { name: 'Đổi tên hiển thị', exact: true }).click();
    const maximum = Array(50).fill('5Nguyễn').join('  ');
    await name.fill(maximum);
    await page.getByRole('button', { name: 'Lưu tên', exact: true }).click();
    await expect(name).toHaveCount(0);
    await expect(page.getByRole('heading', { name: /^5Nguyễn/ })).toBeVisible();
    expect(app.studentProfile.displayName).toBe(maximum);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
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
      const dialog = page.getByRole('alertdialog', { name: 'Chưa lưu được thay đổi' });
      await expect(dialog).toContainText('Chưa xác nhận được lựa chọn quyền riêng tư đã lưu');
      await dialog.getByRole('button', { name: 'Đóng thông báo' }).click();
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
