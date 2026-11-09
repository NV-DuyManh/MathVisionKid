import { test, expect, login, sites } from './fixtures.mjs';

const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jYqsAAAAASUVORK5CYII=', 'base64');

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

test('teacher can approve a batch with only proposed grades and reopen the recorded score', async ({ page, app }) => {
  const id = 'submission-1';
  let approved = false;
  const status = () => approved ? 'TEACHER_APPROVED' : 'PROPOSED_GRADE';
  app.responses.set('GET /teacher/batches/batch-1', ({ json }) => json({
    batchId: 'batch-1', assignmentId: 'assignment-1', assignmentTitle: 'Phép cộng 100 điểm', className: '5A',
    status: 'COMPLETED', totalCount: 1, processedCount: 1, reviewRequiredCount: 0,
    pendingReviewCount: approved ? 0 : 1, finalizedCount: approved ? 1 : 0, failedCount: 0,
    submissions: [{ submissionId: id, studentName: 'An kiểm thử', status: status() }],
  }));
  app.responses.set('GET /teacher/batches/batch-1/review', ({ json }) => json(approved ? [] : [id]));
  app.responses.set('GET /teacher/submissions/' + id, ({ json }) => json({
    submissionId: id, batchId: 'batch-1', studentName: 'An kiểm thử', status: status(), maxScore: 100,
    gradeProposal: { suggestedScore: 8, maxScore: 10 }, ...(approved ? { teacherScore: 80 } : {}),
  }));
  app.responses.set('GET /teacher/submissions/' + id + '/image', ({ route }) => route.fulfill({
    contentType: 'image/png',
    body: png,
    headers: { 'access-control-allow-origin': '*' },
  }));
  app.responses.set('POST /teacher/submissions/' + id + '/approve', ({ route }) => {
    approved = true;
    return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*' } });
  });

  await login(page, 'TEACHER');
  await page.goto(sites.teacher.origin + '/batches/batch-1');
  await page.getByRole('link', { name: 'Vào hàng đợi duyệt (1 bài)' }).click();
  await page.getByRole('button', { name: 'Duyệt bài này' }).click();
  await page.getByRole('button', { name: 'Duyệt điểm 80' }).click();
  await expect(page).toHaveURL(/\/batches\/batch-1\/review$/);
  await page.goto(sites.teacher.origin + '/batches/batch-1');
  await expect(page.getByRole('link', { name: /Vào hàng đợi duyệt/ })).toHaveCount(0);
  await page.getByRole('link', { name: 'Xem bài' }).click();
  await expect(page.getByText('Điểm chính thức 80 / 100')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Điều chỉnh', exact: true })).toHaveCount(0);
});

test('teacher resumes an empty batch, confirms image privacy and uploads into that same batch', async ({ page, app }) => {
  let uploaded = false;
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài thu ảnh', operationType: 'VERTICAL_ADDITION' });
  app.responses.set('GET /teacher/batches/resume-1', ({ json }) => json({
    batchId: 'resume-1', assignmentId: 'assignment-1', assignmentTitle: 'Bài thu ảnh', className: '5A',
    status: uploaded ? 'PROCESSING' : 'CREATED', totalCount: uploaded ? 1 : 0,
    processedCount: 0, pendingReviewCount: 0, reviewRequiredCount: 0,
    submissions: uploaded ? [{ submissionId: 'sub-new', studentName: 'Kiểm thử STUDENT', status: 'PROCESSING' }] : [],
  }));
  app.responses.set('POST /teacher/batches/resume-1/submissions', ({ json, route }) => {
    const payload = route.request().postData();
    expect(payload).toContain('filename="synthetic.jpg"');
    expect(payload).toContain('"studentId":"fixture-STUDENT"');
    uploaded = true;
    return json(null, 202);
  });
  await login(page, 'TEACHER');
  await page.goto(sites.teacher.origin + '/batches/resume-1');
  await page.getByRole('link', { name: 'Tiếp tục tải ảnh' }).click();
  await expect(page.getByRole('combobox', { name: 'Bài tập cần chấm' })).toBeDisabled();
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'synthetic.png', mimeType: 'image/png', buffer: png });
  await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
  await page.getByRole('option', { name: 'Kiểm thử STUDENT' }).click();
  await page.getByRole('button', { name: 'Che thông tin cá nhân' }).click();
  const save = page.getByRole('button', { name: 'Lưu ảnh đã che' });
  await expect(save).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await save.click();
  await page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI' }).click();
  await expect(page).toHaveURL(sites.teacher.origin + '/batches/resume-1');
  await expect(page.getByRole('list', { name: 'Bài làm trong đợt' }).getByText('Kiểm thử STUDENT')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Tiếp tục tải ảnh' })).toHaveCount(0);
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/teacher/batches')).toHaveLength(0);
});
