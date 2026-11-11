import { test, expect, login, sites } from './fixtures.mjs';

test.use({ timezoneId: 'UTC' });

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
