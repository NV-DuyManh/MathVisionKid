import { readFile } from 'node:fs/promises';
import { test, expect, login, sites } from './fixtures.mjs';

const image = await readFile(new URL('../../apps/teacher-web/public/ui/mathvision-star.png', import.meta.url));

test('lost create response retries the same batch operation and uploads once', async ({ page, app }) => {
  const assignmentId = 'assignment-idempotency';
  const batchId = 'batch-idempotency';
  app.assignments.push({ assignmentId, classId: 'class-5a', title: 'Bài kiểm thử idempotency', operationType: 'ADDITION' });
  app.responses.set(`GET /teacher/assignments/${assignmentId}`, ({ json }) => json({ assignmentId, classId: 'class-5a' }));

  const creates = [];
  let storedBatch;
  app.responses.set('POST /teacher/batches', async ({ body, json, route }) => {
    creates.push(body);
    if (!storedBatch) {
      storedBatch = { batchId, assignmentId, status: 'CREATED', totalCount: 0,
        creationRequestId: body.creationRequestId };
      // The server committed the creation, but the response was lost in transit.
      return route.abort('connectionreset');
    }
    expect(body.creationRequestId).toBe(storedBatch.creationRequestId);
    return json(storedBatch, 200);
  });

  const uploads = [];
  app.responses.set(`POST /teacher/batches/${batchId}/submissions`, ({ route }) => {
    uploads.push(route.request().url());
    return route.fulfill({ status: 202, body: '', headers: { 'access-control-allow-origin': '*' } });
  });
  app.responses.set(`GET /teacher/batches/${batchId}`, ({ json }) => json({
    batchId, assignmentId, assignmentTitle: 'Bài kiểm thử idempotency', status: 'PROCESSING', totalCount: 1,
    processedCount: 0, failedCount: 0, pendingReviewCount: 0,
  }));

  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  const prepareAndSubmit = async () => {
    await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
    await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
    await page.getByRole('option', { name: 'Kiểm thử STUDENT' }).click();
    await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).click();
    const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
    await editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
    await editor.getByRole('button', { name: 'Lưu ảnh đã che', exact: true }).click();
    await page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true }).click();
  };

  await prepareAndSubmit();
  await expect(page.getByRole('alert').filter({ hasText: /chưa xác nhận|lỗi xảy ra|thử gửi lại/i })).toBeVisible();
  await page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/${batchId}`);

  expect(creates).toHaveLength(2);
  expect(creates[0].creationRequestId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  expect(creates[1].creationRequestId).toBe(creates[0].creationRequestId);
  expect(uploads).toHaveLength(1);

  // A new entry point is a new operation and must receive a fresh idempotency key.
  const firstOperationId = creates[0].creationRequestId;
  const nextBatchId = 'batch-idempotency-next';
  app.responses.set('POST /teacher/batches', ({ body, json }) => {
    creates.push(body);
    return json({ batchId: nextBatchId, assignmentId, status: 'CREATED', totalCount: 0 }, 201);
  });
  app.responses.set(`POST /teacher/batches/${nextBatchId}/submissions`, ({ route }) => {
    uploads.push(route.request().url());
    return route.fulfill({ status: 202, body: '', headers: { 'access-control-allow-origin': '*' } });
  });
  app.responses.set(`GET /teacher/batches/${nextBatchId}`, ({ json }) => json({
    batchId: nextBatchId, assignmentId, assignmentTitle: 'Bài kiểm thử idempotency', status: 'PROCESSING', totalCount: 1,
    processedCount: 0, failedCount: 0, pendingReviewCount: 0,
  }));
  await page.getByRole('link', { name: 'Quay lại danh sách đợt chấm' }).click();
  await page.getByRole('button', { name: 'Tạo đợt chấm mới', exact: true }).click();
  await page.getByRole('combobox', { name: 'Bài tập cần chấm' }).click();
  await page.getByRole('option', { name: 'Bài kiểm thử idempotency', exact: true }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  await prepareAndSubmit();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/${nextBatchId}`);
  expect(creates).toHaveLength(3);
  expect(creates[2].creationRequestId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  expect(creates[2].creationRequestId).not.toBe(firstOperationId);
  expect(uploads).toHaveLength(2);
});

test('a replay that already has images keeps the current draft and offers guarded batch navigation', async ({ page, app }) => {
  const assignmentId = 'assignment-idempotency-resume';
  const batchId = 'batch-idempotency-resume';
  app.assignments.push({ assignmentId, classId: 'class-5a', title: 'Bài kiểm thử tiếp tục', operationType: 'ADDITION' });
  app.responses.set(`GET /teacher/assignments/${assignmentId}`, ({ json }) => json({ assignmentId, classId: 'class-5a' }));
  let created;
  const creates = [];
  app.responses.set('POST /teacher/batches', async ({ body, json, route }) => {
    creates.push(body);
    if (!created) {
      created = { batchId, assignmentId, status: 'CREATED', totalCount: 0,
        creationRequestId: body.creationRequestId };
      return route.abort('connectionreset');
    }
    return json({ ...created, status: 'PROCESSING', totalCount: 1,
      submissions: [{ submissionId: 'submission-resume', status: 'PROCESSING' }] }, 200);
  });
  let uploads = 0;
  app.responses.set(`POST /teacher/batches/${batchId}/submissions`, ({ json }) => {
    uploads++;
    return json({}, 202);
  });

  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
  await page.getByRole('option', { name: 'Kiểm thử STUDENT' }).click();
  await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).click();
  const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
  await editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await editor.getByRole('button', { name: 'Lưu ảnh đã che', exact: true }).click();
  const submit = page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true });
  await submit.click();
  await expect(page.getByRole('alert').filter({ hasText: /chưa xác nhận|lỗi xảy ra|thử gửi lại/i })).toBeVisible();
  await submit.click();

  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  await expect(page.getByRole('button', { name: 'Kiểm tra đợt chấm', exact: true })).toBeVisible();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  expect(creates).toHaveLength(2);
  expect(creates[1].creationRequestId).toBe(creates[0].creationRequestId);
  expect(uploads).toBe(0);

  await page.getByRole('button', { name: 'Kiểm tra đợt chấm', exact: true }).click();
  await page.getByRole('dialog', { name: 'Rời trang tải ảnh?' }).getByRole('button', { name: 'Ở lại' }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  expect(uploads).toBe(0);
});

test('leaving while create is pending prevents a late upload or redirect', async ({ page, app }) => {
  const assignmentId = 'assignment-idempotency-pending';
  const batchId = 'batch-idempotency-pending';
  app.assignments.push({ assignmentId, classId: 'class-5a', title: 'Bài kiểm thử đang tạo', operationType: 'ADDITION' });
  app.responses.set(`GET /teacher/assignments/${assignmentId}`, ({ json }) => json({ assignmentId, classId: 'class-5a' }));

  let beginCreate;
  const createStarted = new Promise(resolve => { beginCreate = resolve; });
  let releaseCreate;
  const createHeld = new Promise(resolve => { releaseCreate = resolve; });
  app.responses.set('POST /teacher/batches', async ({ body, json }) => {
    beginCreate(body);
    await createHeld;
    return json({ batchId, assignmentId, status: 'CREATED', totalCount: 0 }, 201);
  });
  let uploads = 0;
  app.responses.set(`POST /teacher/batches/${batchId}/submissions`, ({ json }) => {
    uploads++;
    return json({}, 202);
  });

  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=${assignmentId}`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
  await page.getByRole('option', { name: 'Kiểm thử STUDENT' }).click();
  await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).click();
  const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
  await editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await editor.getByRole('button', { name: 'Lưu ảnh đã che', exact: true }).click();
  await page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true }).click();
  const requestBody = await createStarted;
  expect(requestBody.creationRequestId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);

  await page.getByRole('button', { name: 'Quay lại danh sách đợt chấm' }).click();
  const guard = page.getByRole('dialog', { name: 'Rời trang tải ảnh?' });
  await expect(guard).toBeVisible();
  await guard.getByRole('button', { name: 'Rời trang', exact: true }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches`);
  releaseCreate();

  const lateUpload = page.waitForRequest(request => request.method() === 'POST'
    && request.url().includes(`/teacher/batches/${batchId}/submissions`), { timeout: 5000 })
    .then(() => true, () => false);
  expect(await lateUpload).toBe(false);
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches`);
  expect(uploads).toBe(0);
});
