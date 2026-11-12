import { readFile } from 'node:fs/promises';
import { test, expect, login, sites } from './fixtures.mjs';

const batchId = 'batch-review-queue';
const batchPath = `/teacher/batches/${batchId}`;
const reviewUrl = `${sites.teacher.origin}/batches/${batchId}/review`;
const submission = (number, status) => ({
  submissionId: `submission-${number}`,
  studentName: `Học sinh ${number}`,
  status,
});

function respondToBatch(app, details, reviewEntries = []) {
  app.responses.set(`GET ${batchPath}`, ({ json }) => json({
    batchId,
    assignmentId: 'assignment-1',
    assignmentTitle: 'Ôn tập phép cộng',
    className: '5A',
    createdAt: '2026-01-01T00:00:00Z',
    startedAt: '2026-01-01T00:01:00Z',
    completedAt: null,
    totalCount: 0,
    processedCount: 0,
    reviewRequiredCount: 0,
    pendingReviewCount: 0,
    finalizedCount: 0,
    failedCount: 0,
    submissions: [],
    ...details,
  }));
  app.responses.set(`GET ${batchPath}/review-summary`, ({ json }) => json(reviewEntries));
}

test('review queues of 1, 10 and 30 items each load with two data requests', async ({ page, app }, testInfo) => {
  await login(page, 'TEACHER');
  const measurements = [];
  for (const count of [1, 10, 30]) {
    const entries = Array.from({ length: count }, (_, index) => ({
      ...submission(index + 1, 'PROPOSED_GRADE'), maxScore: 100,
      gradeProposal: { suggestedScore: 8, maxScore: 10 },
    }));
    respondToBatch(app, { status: 'COMPLETED', totalCount: count, processedCount: count, pendingReviewCount: count,
      submissions: entries }, entries);
    const requestStart = app.requests.length;
    const start = performance.now();
    await page.goto(reviewUrl);
    await expect(page.getByRole('button', { name: 'Duyệt bài này' })).toHaveCount(count);
    await expect(page.getByText('80 / 100 điểm').first()).toBeVisible();
    const requests = app.requests.slice(requestStart).filter(request => request.method === 'GET'
      && (request.path.startsWith(batchPath) || request.path.startsWith('/teacher/submissions/')));
    measurements.push({ items: count, requests: requests.length, visibleMs: Math.round(performance.now() - start) });
  }
  await testInfo.attach('review-queue-measurements', { body: JSON.stringify(measurements), contentType: 'application/json' });
  console.log(JSON.stringify(measurements));
  expect(measurements.map(({ requests }) => requests)).toEqual([2, 2, 2]);
});

test('teacher sees real progress before the first pending item and receives new items without reloading', async ({ page, app }) => {
  const submissions = Array.from({ length: 30 }, (_, index) => submission(index + 1,
    index < 3 ? 'TEACHER_APPROVED' : 'PROCESSING'));
  respondToBatch(app, { status: 'PROCESSING', totalCount: 30, processedCount: 3, finalizedCount: 3, submissions });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await expect(page.getByText('Đã xử lý 3 / 30 ảnh.')).toBeVisible();
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toHaveCount(0);

  const ready = { ...submission(4, 'PROPOSED_GRADE'), maxScore: 10, gradeProposal: { suggestedScore: 8, maxScore: 10 } };
  respondToBatch(app, {
    status: 'PROCESSING', totalCount: 30, processedCount: 4, finalizedCount: 3, pendingReviewCount: 1,
    submissions: [...submissions.slice(0, 3), ready, ...submissions.slice(4)],
  }, [ready]);
  await expect(page.getByText('Học sinh 4', { exact: true })).toBeVisible();
  await expect(page.getByText('8 / 10 điểm')).toBeVisible();
});

test('teacher can open failed work from an empty queue', async ({ page, app }) => {
  respondToBatch(app, {
    status: 'FAILED', totalCount: 1, processedCount: 1, failedCount: 1, submissions: [submission(1, 'FAILED')],
  });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await expect(page.getByText('1 bài chưa xử lý được.')).toBeVisible();
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toHaveCount(0);
  await page.getByRole('link', { name: 'Xem bài xử lý thất bại' }).click();
  await expect(page.getByRole('heading', { name: 'Bài làm trong đợt' })).toBeVisible();
  await expect(page.getByRole('list', { name: 'Bài làm trong đợt' })).toContainText('Học sinh 1');
});

test('teacher can find and reopen failed work in a mixed batch of thirty', async ({ page, app }) => {
  const submissions = Array.from({ length: 30 }, (_, index) => submission(index + 1,
    index >= 28 ? 'FAILED' : index === 0 ? 'PROPOSED_GRADE' : 'TEACHER_APPROVED'));
  respondToBatch(app, {
    status: 'PARTIAL', totalCount: 30, processedCount: 30, pendingReviewCount: 1,
    failedCount: 2, finalizedCount: 27, submissions,
  }, [submissions[0]]);
  app.responses.set('GET /teacher/submissions/submission-29', ({ json }) => json({
    ...submissions[28], batchId, canRetryProcessing: true, maxScore: 10,
  }));
  app.responses.set('GET /teacher/submissions/submission-29/image', ({ reject }) => reject(503));
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await page.getByRole('link', { name: 'Xem bài xử lý thất bại' }).click();
  const list = page.getByRole('list', { name: 'Bài làm trong đợt' });
  await expect(list.getByRole('listitem')).toHaveCount(2);
  const failedWork = list.getByRole('listitem').filter({ hasText: 'Học sinh 29' });
  await failedWork.getByRole('link', { name: 'Xem bài' }).click();
  await expect(page.getByRole('button', { name: 'Thử xử lý lại' })).toBeVisible();
  await page.getByRole('link', { name: 'Quay lại đợt chấm' }).click();
  await expect(list.getByRole('listitem')).toHaveCount(2);
  await page.getByRole('link', { name: 'Xem tất cả bài' }).click();
  await expect(list.getByRole('listitem')).toHaveCount(30);
});

test('teacher can resume the upload when the batch has not received any images', async ({ page, app }) => {
  respondToBatch(app, { status: 'CREATED', startedAt: null });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await expect(page.getByText('Đợt chấm đang chờ tải ảnh.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Tiếp tục tải ảnh' })).toHaveAttribute('href', `/batches/create?batchId=${batchId}`);
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toHaveCount(0);
});

test('teacher can refresh an inconsistent snapshot and sees completion only after all grades are final', async ({ page, app }) => {
  respondToBatch(app, {
    status: 'COMPLETED', totalCount: 1, processedCount: 1, pendingReviewCount: 1,
    submissions: [submission(1, 'PROPOSED_GRADE')],
  });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await expect(page.getByText('Dữ liệu hàng đợi và tiến độ đợt chấm chưa khớp.')).toBeVisible();
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toHaveCount(0);

  respondToBatch(app, {
    status: 'COMPLETED', totalCount: 1, processedCount: 1, finalizedCount: 1,
    submissions: [submission(1, 'TEACHER_APPROVED')],
  });
  await page.getByRole('button', { name: 'Làm mới' }).click();
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toBeVisible();

  app.responses.set(`GET ${batchPath}`, ({ reject }) => reject(503));
  await page.getByRole('button', { name: 'Làm mới' }).click();
  await expect(page.getByText('Chưa tải được tiến độ đợt chấm.')).toBeVisible();
  await expect(page.getByText('Đã chốt điểm cho toàn bộ bài làm.')).toHaveCount(0);
});

test('teacher receives new work when a queue read started before the latest batch progress', async ({ page, app }) => {
  respondToBatch(app, { status: 'PROCESSING', totalCount: 1, submissions: [submission(1, 'PROCESSING')] });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await expect(page.getByText('Đã xử lý 0 / 1 ảnh.')).toBeVisible();

  const ready = submission(1, 'PROPOSED_GRADE');
  respondToBatch(app, {
    status: 'COMPLETED', totalCount: 1, processedCount: 1, pendingReviewCount: 1, submissions: [ready],
  }, [ready]);

  const { promise, resolve } = Promise.withResolvers();
  const currentQueue = app.responses.get(`GET ${batchPath}/review-summary`);
  app.responses.set(`GET ${batchPath}/review-summary`, async ({ json }) => {
    app.responses.set(`GET ${batchPath}/review-summary`, currentQueue);
    await promise;
    return json([]);
  });
  try {
    const batchResponse = page.waitForResponse(response => response.url().endsWith(batchPath));
    await page.getByRole('button', { name: 'Làm mới' }).click();
    await batchResponse;
    await expect(page.getByText('Đang kiểm tra tiến độ đợt chấm…')).toBeVisible();
  } finally {
    resolve();
  }
  await expect(page.getByText('Học sinh 1', { exact: true })).toBeVisible();
});

test('teacher keeps queue filters through review navigation without putting student search in the URL', async ({ page, app }) => {
  const entries = [submission(1, 'PROPOSED_GRADE'), submission(2, 'NEEDS_CONFIRMATION')];
  respondToBatch(app, { status: 'COMPLETED', totalCount: 2, processedCount: 2, pendingReviewCount: 2,
    submissions: entries }, entries);
  for (const entry of entries) {
    const path = `/teacher/submissions/${entry.submissionId}`;
    app.responses.set(`GET ${path}`, ({ json }) => json({ ...entry, batchId, maxScore: 10 }));
    app.responses.set(`GET ${path}/image`, ({ reject }) => reject(404));
  }

  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  const search = page.getByRole('textbox', { name: 'Tên học sinh' });
  await search.fill('Học sinh 1');
  await page.getByRole('combobox', { name: 'Trạng thái' }).click();
  await page.getByRole('option', { name: 'Có điểm đề xuất' }).click();
  await page.getByRole('combobox', { name: 'Sắp xếp theo' }).click();
  await page.getByRole('option', { name: 'Điểm đề xuất: Cao → Thấp' }).click();
  await expect(page).toHaveURL(reviewUrl);

  const open = page.getByRole('button', { name: 'Duyệt bài này' });
  await open.click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/submissions/submission-1?from=review`);
  await page.goBack();
  await expect(search).toHaveValue('Học sinh 1');
  await open.click();
  await page.getByRole('link', { name: 'Quay lại hàng đợi duyệt' }).click();
  await page.reload();
  await expect(page).toHaveURL(reviewUrl);
  await expect(search).toHaveValue('Học sinh 1');
  await expect(page.getByRole('combobox', { name: 'Trạng thái' })).toHaveText('Có điểm đề xuất');
  await expect(page.getByRole('combobox', { name: 'Sắp xếp theo' })).toHaveText('Điểm đề xuất: Cao → Thấp');

  await page.evaluate(() => sessionStorage.setItem('teacher_session_id', 'different-test-session'));
  await page.reload();
  await expect(search).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Duyệt bài này' })).toHaveCount(2);
});

test('after saving, next review skips finished work and keeps the filtered queue', async ({ page, app }) => {
  const image = await readFile(new URL('../../apps/teacher-web/public/ui/mathvision-star.png', import.meta.url));
  const entries = [1, 2, 3, 4].map(number => ({
    ...submission(number, number === 4 ? 'NEEDS_CONFIRMATION' : 'PROPOSED_GRADE'),
    batchId, maxScore: 10, gradeProposal: { suggestedScore: 8, maxScore: 10 },
  }));
  respondToBatch(app, { status: 'COMPLETED', totalCount: 4, processedCount: 4, pendingReviewCount: 4 }, entries);
  for (const entry of entries) {
    const path = `/teacher/submissions/${entry.submissionId}`;
    app.responses.set(`GET ${path}`, ({ json }) => json(entry));
    app.responses.set(`GET ${path}/image`, ({ route }) => route.fulfill({
      body: image, contentType: 'image/png', headers: { 'access-control-allow-origin': '*' },
    }));
  }
  const firstPath = '/teacher/submissions/submission-1';
  app.responses.set(`POST ${firstPath}/approve`, ({ route }) => {
    app.responses.set(`GET ${firstPath}`, ({ json }) => json({
      ...entries[0], status: 'TEACHER_APPROVED', teacherScore: 8,
    }));
    respondToBatch(app, { status: 'COMPLETED', totalCount: 4, processedCount: 4, pendingReviewCount: 2, finalizedCount: 2 },
      entries.slice(2));
    app.responses.set(`GET ${batchPath}/review-summary`, ({ reject }) => reject(503));
    return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*' } });
  });
  await login(page, 'TEACHER');
  await page.goto(reviewUrl);
  await page.getByRole('combobox', { name: 'Trạng thái' }).click();
  await page.getByRole('option', { name: 'Có điểm đề xuất' }).click();
  await page.getByRole('button', { name: 'Duyệt bài này' }).first().click();
  const next = page.getByRole('button', { name: 'Duyệt bài tiếp theo' });
  await expect(next).toHaveCount(0);
  await page.getByRole('button', { name: 'Duyệt điểm 8' }).click();
  await next.click();
  await expect(page.getByText('Chưa tải được hàng đợi. Hãy thử lại hoặc quay lại hàng đợi duyệt.')).toBeVisible();
  await expect(page).toHaveURL(`${sites.teacher.origin}/submissions/submission-1?from=review`);
  app.responses.set(`GET ${batchPath}/review-summary`, ({ json }) => json(entries.slice(2)));
  await next.click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/submissions/submission-3?from=review`);
  await expect(page.getByRole('heading', { name: /Học sinh 3/ })).toBeVisible();
  await page.getByRole('link', { name: 'Quay lại hàng đợi duyệt' }).click();
  await expect(page.getByRole('combobox', { name: 'Trạng thái' })).toHaveText('Có điểm đề xuất');
  await expect(page.getByRole('button', { name: 'Duyệt bài này' })).toHaveCount(1);
});
