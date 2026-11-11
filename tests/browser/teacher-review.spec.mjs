import { test, expect, login, sites } from './fixtures.mjs';

test('teacher opens the assigned class roster and filters assignments to that class', async ({ page, app }) => {
  app.assignments.push(
    { assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài của lớp 5A', operationType: 'VERTICAL_ADDITION', maxScore: 100 },
    { assignmentId: 'assignment-2', classId: 'class-5b', title: 'Bài của lớp 5B', operationType: 'VERTICAL_SUBTRACTION', maxScore: 10 },
  );
  await login(page, 'TEACHER');
  await page.goto(sites.teacher.origin + '/classes');
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
});
