import { test, expect, sites, login } from '../browser/fixtures.mjs';

for (const width of [360, 390, 430, 768, 1024, 1280, 1440]) {
  test(`grade leaderboard and privacy controls remain usable at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
    let profile = {
      displayName: 'Tên riêng của em', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
      leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: 'Hươu Sao', selectedTitle: null,
      stars: 1, rank, highestRank: rank.name, position: 1,
      stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 },
      titles: [], history: [],
    };
    await page.route('**/api/v1/student/profile', async route => {
      if (route.request().method() === 'PUT') profile = { ...profile, ...route.request().postDataJSON() };
      await route.fulfill({ json: profile });
    });
    await page.route('**/api/v1/student/leaderboard*', route => route.fulfill({ json: {
      gradeLevel: 5, ownPosition: profile.leaderboardVisible ? 1 : null,
      entries: profile.leaderboardVisible ? [{ position: 1, alias: profile.leaderboardNameHidden ? profile.publicAlias : profile.displayName,
        avatar: 'star', stars: 1, rank, self: true }] : [],
    } }));
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/achievements`);
    await expect(page.getByRole('heading', { name: 'Bảng xếp hạng khối 5', exact: true })).toBeVisible();
    if (width < 768) await expect(page.getByRole('heading', { name: 'Em đang dùng bí danh', exact: true })).toBeVisible();
    await expect(page.getByTestId('leaderboard-entry')).toContainText('Hươu Sao');
    await expect(page.getByTestId('leaderboard-entry')).not.toContainText(profile.displayName);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
    await testInfo.attach(`achievements-${width}`, { body: await page.screenshot(), contentType: 'image/png' });
    if (width < 768) {
      await page.getByRole('button', { name: 'Đổi quyền riêng tư', exact: true }).click();
    } else {
      await expect(page.getByRole('button', { name: 'Đổi quyền riêng tư', exact: true })).toHaveCount(0);
      await page.getByRole('link', { name: 'Mở trang Của em', exact: true }).click();
      await page.getByRole('button', { name: 'Chỉnh sửa hồ sơ', exact: true }).click();
      await expect(page).toHaveURL(/\/study\/account$/);
    }
    await page.getByRole('switch', { name: 'Tham gia bảng xếp hạng', exact: true }).click();
    await expect(page.getByText('Em đang ẩn khỏi bảng xếp hạng. Thành tích vẫn được lưu trong tài khoản của em.', { exact: false })).toBeVisible();
    await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
    await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/achievements`);
    if (width < 768) await expect(page.getByRole('heading', { name: 'Em đang ẩn khỏi bảng xếp hạng', exact: true })).toBeVisible();
    await expect(page.getByText('Em chưa tham gia bảng xếp hạng', { exact: true })).toBeVisible();
    // Expo retains the previous, aria-hidden stack screen after opening a fresh tab route.
    await expect(page.getByTestId('leaderboard-entry').filter({ visible: true })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
  });
}

test('rejects a wrong-grade board and opens the private self row beyond the first page', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  const rank = { name: 'Sắt III', masterStars: 0, progress: 1, goal: 3 };
  const profile = {
    displayName: 'Tên riêng của em', gradeLevel: 5, joinedAt: null, classrooms: [], avatar: 'star',
    leaderboardVisible: true, leaderboardNameHidden: true, publicAlias: 'Hươu Sao', selectedTitle: null,
    stars: 1, rank, highestRank: rank.name, position: 12,
    stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 }, titles: [], history: [],
  };
  const entries = Array.from({ length: 12 }, (_, index) => ({ position: index + 1,
    alias: index === 11 ? profile.displayName : `Bí danh ${index + 1}`, avatar: 'star', stars: 20 - index, rank, self: index === 11 }));
  let gradeLevel = 4;
  await page.route('**/api/v1/student/profile', route => route.fulfill({ json: profile }));
  await page.route('**/api/v1/student/leaderboard*', route => route.fulfill({ json: { gradeLevel, ownPosition: 12, entries } }));
  await page.setViewportSize({ width: 390, height: 900 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/achievements`);
  await expect(page.getByText('Bảng xếp hạng chưa đúng khối lớp', { exact: true })).toBeVisible();
  await expect(page.getByTestId('leaderboard-entry')).toHaveCount(0);
  gradeLevel = 5;
  await page.getByRole('button', { name: 'Tải lại bảng xếp hạng đúng khối lớp', exact: true }).click();
  await expect(page.getByTestId('leaderboard-entry')).toHaveCount(10);
  await page.getByRole('button', { name: 'Xem vị trí của em', exact: true }).click();
  await expect(page.getByTestId('leaderboard-entry')).toHaveCount(12);
  await expect(page.getByTestId('leaderboard-entry').last()).toContainText('Hươu Sao');
  await expect(page.getByTestId('leaderboard-entry').last()).not.toContainText(profile.displayName);
  await page.getByTestId('leaderboard-entry').last().scrollIntoViewIfNeeded();
  await testInfo.attach('leaderboard-private-self-page-two', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Thu gọn bảng xếp hạng', exact: true }).click();
  await expect(page.getByTestId('leaderboard-entry')).toHaveCount(10);
});
