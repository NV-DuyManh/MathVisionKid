import { test, expect, sites, login } from '../browser/fixtures.mjs';

const studentId = '550e8400-e29b-41d4-a716-446655440000';
const title = 'Lan có 7 viên bi';
const note = 'Em bắt đầu từ số viên bi của Lan.';
const routes = {
  achievements: 'Bảng xếp hạng khối 5',
  progress: 'Hoạt động 7 ngày gần đây',
  profile: 'Góc học tập',
  saved: 'Sổ học tập',
  account: 'Quyền riêng tư',
};

for (const width of [390, 1672]) {
  test('personal workspace uses real browser storage and reads profile data at ' + width + 'px', async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: width === 1672 ? 941 : 844 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    app.studentProfile.history = [{ source: 'LESSON', completedAt: new Date(Date.now() - 60_000).toISOString(), stars: 1 }];
    app.studentProfile.titles = [
      { id: 'learner', name: 'Tân Binh Tri Thức', description: 'Hoàn thành bài học đầu tiên', rarity: 'Phổ thông', progress: 1, goal: 1, unlocked: true },
      { id: 'solver', name: 'Bạn Giải Toán', description: 'Giải đúng 5 câu đố', rarity: 'Phổ thông', progress: 0, goal: 5, unlocked: false },
    ];
    app.studentProfile.selectedTitle = 'learner';
    await page.evaluate(({ id, title, note }) => {
      const key = owner => 'mathvision_lessons_' + Array.from(owner).map(character => character.codePointAt(0).toString(16)).join('_');
      const lesson = { id: 'lan-marbles', timestamp: Date.now() - 60_000, problemText: title, workText: '', reflection: note, reviewedSteps: 1 };
      localStorage.setItem(key(id), JSON.stringify([lesson]));
      localStorage.setItem(key('another-student'), JSON.stringify([{ ...lesson, problemText: 'Bài riêng của bạn khác' }]));
    }, { id: studentId, title, note });
    for (const [route, heading] of Object.entries(routes)) {
      await page.goto(sites.portal.origin + '/study/' + route);
      await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
      if (route === 'progress') {
        await expect(page.getByLabel(/: 1 lượt nhận sao$/)).toBeVisible();
        await expect(page.getByText('Quiz giải đúng', { exact: true })).toBeVisible();
      }
      if (route === 'profile' || route === 'saved') {
        await expect(page.getByRole('button', { name: 'Học tiếp: ' + title, exact: true })).toBeVisible();
        await expect(page.getByText('Bài riêng của bạn khác', { exact: true })).toHaveCount(0);
      }
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(1);
      await page.evaluate(() => document.fonts.ready);
      const filename = route + '-' + width + '.png';
      const screenshot = await page.screenshot({ path: testInfo.outputPath(filename), animations: 'disabled' });
      await testInfo.attach(filename, { body: screenshot, contentType: 'image/png' });
    }
    await page.goto(sites.portal.origin + '/study/saved?tab=notes');
    const notes = page.getByRole('button', { name: 'Ghi chú', exact: true });
    await expect(notes).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByText(note, { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Bài làm', exact: true }).press('Enter');
    await expect(page.getByText('Chưa có bài làm đã lưu', { exact: true })).toBeVisible();
    await page.goto(sites.portal.origin + '/study/account?section=privacy');
    await expect(page.getByRole('heading', { name: 'Quyền riêng tư', exact: true })).toBeFocused();
  });
}
