import { readFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
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

  const corruptUpload = 'data:image/png;base64,bm90IGFuIGltYWdl';
  app.studentProfile.avatarPhoto = corruptUpload;
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Kiểm thử STUDENT', exact: true })).toBeVisible();
  await expect(page.locator(`img[src="${corruptUpload}"]`)).toHaveCount(0);
});

test('student can choose who sees their profile photo on the leaderboard', async ({ page, app }, testInfo) => {
  const picture = 'https://lh3.googleusercontent.com/a/synthetic-profile-sharing';
  app.realStudent = true;
  await page.route(picture, route => route.fulfill({
    contentType: 'image/png',
    body: readFileSync(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url)),
  }));
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  await page.goto(`${sites.portal.origin}/study/account`);
  const photo = page.getByRole('switch', { name: 'Hiện ảnh hồ sơ trên bảng xếp hạng', exact: true });
  const rank = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng', exact: true });
  const save = page.getByRole('button', { name: 'Lưu thay đổi', exact: true });
  await expect(photo).toBeDisabled();
  await rank.click();
  await expect(photo).toBeDisabled();

  app.studentProfile.avatarPhoto = picture;
  await page.reload();
  await rank.click();
  await expect(photo).toBeEnabled();
  await expect(photo).not.toBeChecked();
  await photo.focus();
  await page.keyboard.press('Space');
  await expect(photo).toBeChecked();
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  expect(app.studentProfile.leaderboardPhotoVisible).toBe(true);
  await page.reload();
  await expect(photo).toBeChecked();
  await photo.scrollIntoViewIfNeeded();
  await page.getByTestId('account-profile-editor').screenshot({ path: testInfo.outputPath('avatar-sharing.png') });

  await photo.click();
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  expect(app.studentProfile.leaderboardPhotoVisible).toBe(false);
  await page.reload();
  await expect(photo).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Thay ảnh đại diện' }).locator(`img[src="${picture}"]`)).toBeVisible();
});

test('saving a name preserves privacy settings refreshed while the account editor is open', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  await page.goto(`${sites.portal.origin}/study/account`);
  const participation = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng' });
  const namePrivacy = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng' });
  await expect(participation).not.toBeChecked();
  await expect(namePrivacy).toBeChecked();
  await participation.click();
  await namePrivacy.click();
  await expect(participation).toBeChecked();
  await expect(namePrivacy).not.toBeChecked();

  // Tab B saves the same settings. Uploading from A now renders the saved state.
  Object.assign(app.studentProfile, { leaderboardVisible: true, leaderboardNameHidden: false, privacyRevision: randomUUID() });
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Thay ảnh đại diện' }).click();
  await (await chooser).setFiles({
    name: 'avatar.png', mimeType: 'image/png',
    buffer: readFileSync(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url)),
  });
  await expect(page.getByText('Đã cập nhật ảnh đại diện.')).toBeVisible();
  await expect(participation).toBeChecked();
  await expect(namePrivacy).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Lưu thay đổi' })).toBeDisabled();

  // After B revokes, A changes only the name. Its old switches must not be sent.
  Object.assign(app.studentProfile, { leaderboardVisible: false, leaderboardNameHidden: true, privacyRevision: randomUUID() });
  await page.getByRole('button', { name: 'Đổi tên hiển thị' }).click();
  await page.getByRole('textbox', { name: 'Tên hiển thị' }).fill('Minh Anh');
  await page.getByRole('button', { name: 'Lưu tên' }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em.')).toBeVisible();
  expect(app.requests.findLast(request => request.method === 'PUT' && request.path === '/student/profile').body)
    .toEqual({ displayName: 'Minh Anh' });
  expect(app.studentProfile).toMatchObject({ displayName: 'Minh Anh', leaderboardVisible: false, leaderboardNameHidden: true });

  // A save from the open editor must also preserve newer settings that it
  // has not fetched yet.
  Object.assign(app.studentProfile, { leaderboardVisible: true, leaderboardNameHidden: false });
  await page.getByRole('button', { name: 'Đổi tên hiển thị' }).click();
  await page.getByRole('textbox', { name: 'Tên hiển thị' }).fill('Sao Sáng');
  await page.getByRole('button', { name: 'Lưu tên' }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em.')).toBeVisible();
  expect(app.studentProfile).toMatchObject({ displayName: 'Sao Sáng', leaderboardVisible: true, leaderboardNameHidden: false });
});

test('showing a name from a stale profile requires confirmation after the student is renamed', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, { displayName: 'Tên Ban Đầu', leaderboardVisible: true });
  await page.goto(`${sites.portal.origin}/study/account`);
  await expect(page.getByRole('heading', { name: 'Tên Ban Đầu' })).toBeVisible();
  const hidden = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng' });
  const save = page.getByRole('button', { name: 'Lưu thay đổi', exact: true });
  await expect(hidden).toBeChecked();
  await hidden.click();
  Object.assign(app.studentProfile, { displayName: 'Tên Mới', privacyRevision: randomUUID() });
  await save.click();
  const dialog = page.getByRole('alertdialog', { name: 'Chưa lưu được thay đổi' });
  await expect(dialog).toContainText('Em kiểm tra hồ sơ và chọn lại quyền chia sẻ nhé.');
  await dialog.getByRole('button', { name: 'Đóng thông báo' }).click();
  await expect(page.getByRole('heading', { name: 'Tên Mới' })).toBeVisible();
  await expect(hidden).toBeChecked();
  await expect(save).toBeDisabled();

  await hidden.click();
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.')).toBeVisible();
  expect(app.studentProfile).toMatchObject({ displayName: 'Tên Mới', leaderboardNameHidden: false });
});

test('a stale photo draft refreshes privacy and requires a new confirmation', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect.poll(() => app.studentProfile).toBeDefined();
  const picture = 'data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%221%22%20height%3D%221%22%2F%3E';
  Object.assign(app.studentProfile, { avatarPhoto: picture, leaderboardVisible: true });
  await page.goto(`${sites.portal.origin}/study/account`);
  const share = page.getByRole('switch', { name: 'Hiện ảnh hồ sơ trên bảng xếp hạng' });
  await share.click();
  await expect(share).toBeChecked();
  // The same picture was shared and revoked by B. Current booleans still match A's snapshot.
  app.studentProfile.privacyRevision = randomUUID();
  app.studentProfile.displayName = 'Tên phiên khác';
  const save = page.getByRole('button', { name: 'Lưu thay đổi', exact: true });
  await save.click();
  const conflict = page.getByRole('alertdialog', { name: 'Chưa lưu được thay đổi' });
  await expect(conflict).toContainText('Em kiểm tra hồ sơ và chọn lại quyền chia sẻ');
  await conflict.getByRole('button', { name: 'Đóng thông báo' }).click();
  await expect(share).not.toBeChecked();
  await expect(save).toBeDisabled();
  await expect(page.getByRole('heading', { name: 'Tên phiên khác', exact: true })).toBeVisible();
  expect(app.studentProfile.leaderboardPhotoVisible).toBe(false);

  await share.click();
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.')).toBeVisible();
  expect(app.requests.findLast(request => request.method === 'PUT' && request.path === '/student/profile').body)
    .toEqual({ leaderboardPhotoVisible: true, privacyRevision: expect.any(String) });
  expect(app.studentProfile.displayName).toBe('Tên phiên khác');
});

test('changing the photo preserves unsaved privacy reductions for explicit saving', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, { leaderboardVisible: true, leaderboardNameHidden: false });
  await page.goto(`${sites.portal.origin}/study/account`);
  const participation = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng' });
  const hideName = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng' });
  await participation.click();
  await hideName.click();

  await page.getByRole('button', { name: 'Đổi tên hiển thị' }).click();
  await page.getByRole('textbox', { name: 'Tên hiển thị' }).fill('Minh Anh');
  await page.getByRole('button', { name: 'Lưu tên' }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em. Lựa chọn giảm chia sẻ vẫn chờ lưu.', { exact: true })).toBeVisible();
  expect(app.requests.findLast(request => request.method === 'PUT' && request.path === '/student/profile').body)
    .toEqual({ displayName: 'Minh Anh' });
  await expect(participation).not.toBeChecked();
  await expect(hideName).toBeChecked();

  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Thay ảnh đại diện' }).click();
  await (await chooser).setFiles({
    name: 'avatar.png', mimeType: 'image/png',
    buffer: readFileSync(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url)),
  });
  await expect(page.getByText(/Đã cập nhật ảnh đại diện.*Lựa chọn giảm chia sẻ vẫn chờ lưu/)).toBeVisible();
  await expect(participation).not.toBeChecked();
  await expect(hideName).toBeChecked();
  expect(app.studentProfile).toMatchObject({ leaderboardVisible: true, leaderboardNameHidden: false });
  const updatedRevision = app.studentProfile.privacyRevision;
  const save = page.getByRole('button', { name: 'Lưu thay đổi', exact: true });
  await expect(save).toBeEnabled();
  await page.getByTestId('account-profile-editor').screenshot({ path: testInfo.outputPath('pending-privacy-revocation.png') });
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  expect(app.requests.findLast(request => request.method === 'PUT' && request.path === '/student/profile').body)
    .toEqual({ leaderboardVisible: false, leaderboardNameHidden: true, privacyRevision: updatedRevision });
  await page.reload();
  await expect(participation).not.toBeChecked();
  await expect(hideName).toBeChecked();
});

test('changing the photo discards consent drafted for the old image', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  const avatar = readFileSync(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url));
  Object.assign(app.studentProfile, { leaderboardVisible: true, avatarPhoto: `data:image/png;base64,${avatar.toString('base64')}` });
  await page.goto(`${sites.portal.origin}/study/account`);
  const share = page.getByRole('switch', { name: 'Hiện ảnh hồ sơ trên bảng xếp hạng' });
  await share.click();
  await expect(share).toBeChecked();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Thay ảnh đại diện' }).click();
  await (await chooser).setFiles({ name: 'avatar.png', mimeType: 'image/png', buffer: avatar });
  await expect(page.getByText(/Em cần chọn lại nếu muốn mở thêm quyền chia sẻ/)).toBeVisible();
  await expect(share).not.toBeChecked();
  expect(app.studentProfile.leaderboardPhotoVisible).toBe(false);
  await expect(page.getByRole('button', { name: 'Lưu thay đổi', exact: true })).toBeDisabled();
});

test('a missing privacy revision blocks expansion and still allows a student to leave the leaderboard', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  app.legacyStudentProfile = true;
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, { leaderboardVisible: true, leaderboardNameHidden: true });
  await page.goto(`${sites.portal.origin}/study/account`);
  const participation = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng' });
  const hideName = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng' });
  await expect(hideName).toBeDisabled();
  await expect(participation).toBeEnabled();
  await expect(participation).toBeChecked();
  await expect(page.getByText('Cần cập nhật để mở quyền chia sẻ', { exact: true })).toBeVisible();
  await page.getByTestId('account-profile-editor').screenshot({ path: testInfo.outputPath('legacy-privacy-update.png') });
  await participation.click();
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  await expect(participation).toBeDisabled();
  await expect(participation).not.toBeChecked();
  expect(app.studentProfile.leaderboardVisible).toBe(false);
});

test('a failed conflict refresh keeps privacy locked until the profile is reloaded', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect.poll(() => app.studentProfile).toBeDefined();
  await page.goto(`${sites.portal.origin}/study/account`);
  const participate = page.getByRole('switch', { name: 'Tham gia bảng xếp hạng' });
  const hideName = page.getByRole('switch', { name: 'Ẩn tên trên bảng xếp hạng' });
  await expect(hideName).toBeEnabled();
  await participate.click();
  app.studentProfile.privacyRevision = randomUUID();
  app.studentProfile.displayName = 'Tên từ phiên khác';

  let unavailable = true;
  await page.route('**/api/v1/student/profile', route => route.request().method() === 'GET' && unavailable
    ? route.fulfill({ status: 503, json: {} }) : route.fallback());
  const save = page.getByRole('button', { name: 'Lưu thay đổi', exact: true });
  await save.click();
  const reload = page.getByRole('button', { name: 'Tải lại hồ sơ', exact: true });
  await expect(reload).toBeVisible();
  await expect(participate).toBeDisabled();
  await expect(hideName).toBeDisabled();
  await expect(save).toBeDisabled();
  await Promise.all([
    page.waitForResponse(response => response.url().endsWith('/student/profile') && response.status() === 503),
    reload.click(),
  ]);
  await expect(reload).toBeEnabled();
  await expect(participate).toBeDisabled();

  unavailable = false;
  await reload.click();
  await expect(page.getByRole('heading', { name: 'Tên từ phiên khác', exact: true })).toBeVisible();
  await expect(participate).toBeEnabled();
  await expect(participate).not.toBeChecked();
  const writes = () => app.requests.filter(request => request.method === 'PUT' && request.path === '/student/profile');
  expect(writes()).toHaveLength(1);
  await participate.click();
  await save.click();
  await expect(page.getByText('Đã lưu hồ sơ của em.')).toBeVisible();
  expect(writes()).toHaveLength(2);
  expect(app.studentProfile).toMatchObject({ displayName: 'Tên từ phiên khác', leaderboardVisible: true });
});

test('leaderboards show peer photos only when shared and preserve the private self preview', async ({ page, app }, testInfo) => {
  const picture = 'https://lh3.googleusercontent.com/a/synthetic-avatar';
  const ownAlias = 'Hươu Sao Của Em';
  const peerAlias = 'Cá Heo Chăm Học';
  const peerPicture = 'https://lh3.googleusercontent.com/a/synthetic-peer-avatar';
  let imageAvailable = true;
  let peerShared = false;
  let failedHomeRefresh;
  app.realStudent = true;
  await page.route(peerPicture, route => route.fulfill({
    contentType: 'image/webp',
    body: readFileSync(new URL('../../apps/student-mobile/assets/illustrations/web/student-avatar.webp', import.meta.url)),
  }));
  await page.route(picture, route => imageAvailable ? route.fulfill({
    contentType: 'image/svg+xml',
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="#8264c7"/></svg>',
  }) : route.fulfill({ status: 404 }));
  await login(page, 'STUDENT');
  await expect.poll(() => app.studentProfile).toBeDefined();
  Object.assign(app.studentProfile, {
    avatarPhoto: picture, leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: ownAlias,
  });
  const { rank } = app.studentProfile;
  const peerRank = { ...rank, name: 'Đồng II' };
  await page.route('**/api/v1/student/leaderboard*', async route => {
    if (failedHomeRefresh) {
      await failedHomeRefresh;
      return route.fulfill({ status: 503 });
    }
    return route.fulfill({ json: {
    gradeLevel: null, ownPosition: 1, entries: [
      { position: 1, alias: ownAlias, avatar: 'planet', stars: 10, rank, self: true },
      { position: 2, alias: peerAlias, avatar: 'rocket', stars: 9, rank: peerRank, self: false, avatarPhoto: peerShared ? peerPicture : undefined },
    ],
    } });
  });

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

  await expect(rows.filter({ hasText: peerAlias }).locator(`img[src="${peerPicture}"]`)).toHaveCount(0);
  peerShared = true;
  await page.reload();
  const peerImage = rows.filter({ hasText: peerAlias }).locator(`img[src="${peerPicture}"]`);
  await expect(peerImage).toBeVisible();
  await expect.poll(() => peerImage.evaluate(image => image.naturalWidth)).toBeGreaterThan(0);
  await rows.first().locator('..').screenshot({ path: testInfo.outputPath('avatar-leaderboard.png') });
  if (testInfo.project.name === 'desktop') {
    await page.goto(`${sites.portal.origin}/study/`);
    const homePeerImage = page.getByTestId('home-leaderboard-entry').filter({ hasText: peerAlias })
      .locator(`img[src="${peerPicture}"]`);
    await expect(homePeerImage).toBeVisible();
    await page.getByRole('button', { name: 'Xem bảng xếp hạng', exact: true }).click();
    await expect(peerImage).toBeVisible();
    peerShared = false;
    const delayed = Promise.withResolvers();
    failedHomeRefresh = delayed.promise;
    const pendingRefresh = page.waitForRequest(request => request.url().includes('/student/leaderboard'));
    const failedRefresh = page.waitForResponse(response => response.url().includes('/student/leaderboard') && response.status() === 503);
    try {
      await page.goBack();
      await pendingRefresh;
      await expect(homePeerImage).toHaveCount(0);
    } finally {
      delayed.resolve();
    }
    await failedRefresh;
    await expect(homePeerImage).toHaveCount(0);
    failedHomeRefresh = undefined;
    await page.goto(`${sites.portal.origin}/study/achievements`);
  }
  peerShared = false;
  imageAvailable = false;
  await page.reload();
  await expect(rows.filter({ hasText: peerAlias })).toBeVisible();
  await expect(peerImage).toHaveCount(0);
  await rows.first().locator('..').screenshot({ path: testInfo.outputPath('avatar-leaderboard-hidden.png') });
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
