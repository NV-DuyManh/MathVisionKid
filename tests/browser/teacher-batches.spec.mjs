import { test, expect, login, sites } from './fixtures.mjs';

test('teacher filters batch history and opens a failed batch without horizontal scrolling', async ({ page, app }, testInfo) => {
  const batches = [
    { batchId: 'pending', assignmentTitle: 'Bài chờ duyệt', status: 'COMPLETED', pendingReviewCount: 2 },
    { batchId: 'failed', assignmentTitle: 'Bài có ảnh cần xử lý lại', status: 'PARTIAL', failedCount: 1,
      submissions: [
        { submissionId: 'failure', studentName: 'Học sinh kiểm thử', status: 'FAILED' },
        { submissionId: 'success', studentName: 'Học sinh đã duyệt', status: 'TEACHER_APPROVED' },
      ] },
    { batchId: 'empty', assignmentTitle: 'Đợt chưa gửi ảnh', status: 'CREATED' },
  ].map(batch => ({ className: '5A', totalCount: 3, processedCount: 3,
    createdAt: '2026-11-10T17:00:00Z', ...batch }));
  app.responses.set('GET /teacher/batches', ({ json }) => json(batches));
  app.responses.set('GET /teacher/batches/failed', ({ json }) => json(batches[1]));
  app.responses.set('GET /teacher/batches/pending', ({ json }) => json(batches[0]));
  app.responses.set('GET /teacher/batches/pending/review-summary', ({ json }) => json([]));
  await login(page, 'TEACHER');
  await page.goto(sites.teacher.origin + '/batches');
  const controls = page.getByRole('group', { name: 'Lọc đợt chấm' });
  const table = page.getByRole('table', { name: 'Danh sách đợt chấm' });
  await controls.getByRole('button', { name: 'Chờ duyệt' }).click();
  await expect(table.getByRole('row')).toHaveCount(2);
  await expect(table.getByRole('link', { name: 'Duyệt (2)' })).toHaveAttribute('href', '/batches/pending/review');
  await table.getByRole('link', { name: 'Duyệt (2)' }).click();
  await page.getByRole('link', { name: 'Quay lại chi tiết đợt chấm' }).click();
  await page.getByRole('link', { name: 'Quay lại danh sách đợt chấm' }).click();
  await expect(page).toHaveURL(sites.teacher.origin + '/batches?filter=pending');
  await controls.getByRole('button', { name: 'Có bài lỗi' }).click();
  await expect(table).toContainText('Bài có ảnh cần xử lý lại');
  await expect(table).not.toContainText('Bài chờ duyệt');
  await expect(controls.getByRole('button', { name: 'Có bài lỗi' })).toHaveAttribute('aria-pressed', 'true');
  const details = table.getByRole('link', { name: 'Chi tiết' });
  if (testInfo.project.name === 'mobile') {
    const viewport = page.viewportSize();
    const rect = await details.boundingBox();
    expect(rect.x + rect.width).toBeLessThanOrEqual(viewport.width);
  }
  await details.click();
  await expect(page.getByRole('heading', { name: 'Bài có ảnh cần xử lý lại' })).toBeVisible();
  const progress = page.getByRole('region', { name: 'Tiến độ đợt chấm' });
  await expect(progress.getByRole('progressbar')).toHaveAttribute('aria-valuetext', '3 trên 3 ảnh');
  const failures = progress.getByRole('link', { name: 'Xem bài xử lý thất bại' });
  await failures.focus();
  await failures.press('Enter');
  await expect(page).toHaveURL(/\/batches\/failed\?status=failed$/);
  const submissions = page.getByRole('list', { name: 'Bài làm trong đợt' });
  await expect(submissions.getByRole('link', { name: 'Xem bài của Học sinh kiểm thử' })).toBeVisible();
  await expect(submissions.getByRole('listitem')).toHaveCount(1);
  await page.getByRole('link', { name: 'Xem tất cả bài' }).click();
  await expect(submissions.getByRole('listitem')).toHaveCount(2);
  await testInfo.attach('Teacher batch detail', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('link', { name: 'Quay lại danh sách đợt chấm' }).click();
  await expect(page).toHaveURL(sites.teacher.origin + '/batches?filter=failed');
  await controls.getByRole('button', { name: 'Tất cả' }).click();
  await expect(table.getByRole('row')).toHaveCount(4);
});
