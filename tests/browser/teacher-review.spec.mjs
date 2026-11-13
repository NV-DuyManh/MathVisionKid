import { test, expect, login, sites } from './fixtures.mjs';

test('teacher opens the assigned class roster and filters assignments to that class', async ({ page, app }) => {
  app.assignments.push(
    { assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài của lớp 5A', operationType: 'VERTICAL_ADDITION', maxScore: 100 },
    { assignmentId: 'assignment-2', classId: 'class-5b', title: 'Bài của lớp 5B', operationType: 'VERTICAL_SUBTRACTION', maxScore: 10 },
  );
  await login(page, 'TEACHER');
  await page.goto(sites.teacher.origin + '/classes');
  const list = page.getByRole('list', { name: 'Lớp được phân công' });
  await expect(list).toBeVisible();
  const originalViewport = page.viewportSize();
  for (const width of [768, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(list.getByRole('link', { name: 'Giao bài tập' })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
  await page.setViewportSize(originalViewport);
  await page.getByRole('link', { name: 'Xem học sinh' }).click();
  await expect(page.getByRole('heading', { name: 'Danh sách học sinh' })).toBeVisible();
  const search = page.getByRole('textbox', { name: 'Tìm theo tên học sinh' });
  await search.fill('không có tên này');
  await expect(page.getByRole('status')).toContainText('0 / 1 học sinh');
  await search.fill('kiểm thử');
  await expect(page.getByRole('list', { name: 'Học sinh trong lớp' })).toContainText('Kiểm thử STUDENT');
  await page.getByRole('link', { name: 'Bài tập của lớp' }).click();
  await expect(page.getByText('Bài của lớp 5A')).toBeVisible();
  await expect(page.getByText('Bài của lớp 5B')).toHaveCount(0);
  await expect(page.getByText('Thang điểm 100')).toBeVisible();
  await page.goto(sites.teacher.origin + '/settings');
  await expect(page.getByRole('region', { name: 'Hồ sơ giáo viên' })).toContainText('Kiểm thử TEACHER');
  await expect(page.getByRole('region', { name: 'Bảo vệ bài làm' })).toBeVisible();
});
