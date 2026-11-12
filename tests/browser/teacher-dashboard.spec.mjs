import { test, expect, login, sites } from './fixtures.mjs';

test.use({ timezoneId: 'UTC' });

test('teacher opens pending work outside the ten recent batches directly from the dashboard', async ({ page, app }) => {
  const batchId = 'older-batch-with-pending-work';
  const submission = { submissionId: 'older-submission', studentName: 'Học sinh kiểm thử',
    status: 'PROPOSED_GRADE', maxScore: 10 };
  const batch = { batchId, assignmentTitle: 'Bài cũ chờ duyệt', status: 'COMPLETED', totalCount: 1,
    processedCount: 1, pendingReviewCount: 1, finalizedCount: 0, failedCount: 0, submissions: [submission] };
  app.responses.set('GET /teacher/dashboard', ({ json }) => json({
    todayTotal: 0, processedCount: 10, reviewRequiredCount: 1, nextReviewBatchId: batchId,
    recentBatches: Array.from({ length: 10 }, (_, index) => ({
      ...batch, batchId: `recent-${index}`, pendingReviewCount: 0, finalizedCount: 1,
      createdAt: '2026-11-10T17:00:00Z',
    })),
  }));
  app.responses.set(`GET /teacher/batches/${batchId}`, ({ json }) => json(batch));
  app.responses.set(`GET /teacher/batches/${batchId}/review-summary`, ({ json }) => json([submission]));
  await login(page, 'TEACHER');
  await page.getByText('Xử lý ngay', { exact: true }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/${batchId}/review`);
  await expect(page.getByRole('button', { name: 'Duyệt bài này' })).toBeVisible();
});

test('teacher opens a recent batch by keyboard and can read its counts on a narrow screen', async ({ page, app }) => {
  const batchId = 'batch-dashboard';
  const title = 'Ôn tập phép trừ có nhớ trong phạm vi một nghìn';
  const batch = { batchId, assignmentTitle: title, className: '5A', status: 'COMPLETED', totalCount: 30,
    processedCount: 30, pendingReviewCount: 24, finalizedCount: 6, failedCount: 0, submissions: [],
    createdAt: '2026-11-10T17:00:00Z' };
  app.responses.set('GET /teacher/dashboard', ({ json }) => json({
    todayTotal: 30, processedCount: 30, reviewRequiredCount: 24, recentBatches: [batch],
  }));
  app.responses.set(`GET /teacher/batches/${batchId}`, ({ json }) => json(batch));

  await login(page, 'TEACHER');
  const link = page.getByRole('link', { name: new RegExp(title) });
  await expect(link).toHaveAttribute('href', `/batches/${batchId}`);
  await expect(link.getByText('11/11/2026', { exact: true })).toBeVisible();
  const counts = ['30 bài', '30 đã xử lý', '24 cần xem'];
  const rowBox = await link.boundingBox();
  expect(rowBox).not.toBeNull();
  for (const label of counts) {
    const count = link.getByText(label, { exact: true });
    await expect(count).toBeVisible();
    const countBox = await count.boundingBox();
    expect(countBox.x + countBox.width).toBeLessThanOrEqual(rowBox.x + rowBox.width);
  }

  await page.getByRole('button', { name: 'Xem tất cả đợt chấm' }).focus();
  await page.keyboard.press('Tab');
  await expect(link).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/${batchId}`);
  await expect(page.getByRole('heading', { name: title })).toBeVisible();
});
