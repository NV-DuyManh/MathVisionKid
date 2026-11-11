import { readFile } from 'node:fs/promises';
import { test, expect, login, sites } from './fixtures.mjs';

const image = await readFile(new URL('../../apps/teacher-web/public/ui/mathvision-star.png', import.meta.url));
const path = '/teacher/submissions/grading-fixture';
const submissionUrl = `${sites.teacher.origin}/submissions/grading-fixture?from=review`;
const proposed = {
  submissionId: 'grading-fixture', batchId: 'fixture-batch', studentName: 'Học sinh kiểm thử',
  maxScore: 10, status: 'PROPOSED_GRADE', gradeProposal: { suggestedScore: 8, maxScore: 10 },
};

async function openSubmission(page, app, detail = proposed) {
  app.responses.set(`GET ${path}`, ({ json }) => json(detail));
  app.responses.set(`GET ${path}/image`, ({ route }) => route.fulfill({
    body: image, contentType: 'image/png', headers: { 'access-control-allow-origin': '*' },
  }));
  await login(page, 'TEACHER');
  await page.goto(submissionUrl);
  await expect(page.getByRole('img', { name: /Bài làm của Học sinh kiểm thử/i })).toBeVisible();
}

test('teacher replaces a retake image only after reviewing privacy and sees the same submission reprocessed', async ({ page, app }) => {
  await openSubmission(page, app, { ...proposed, status: 'NEEDS_RETAKE', imageVersion: 'first-image' });
  const originalImageReads = app.requests.filter(request => request.path === `${path}/image`).length;
  app.responses.set(`POST ${path}/retake`, ({ route }) => {
    const body = route.request().postDataBuffer();
    expect(body.includes(Buffer.from('Content-Type: image/jpeg'))).toBe(true);
    expect(body.includes(Buffer.from([0xff, 0xd8, 0xff]))).toBe(true);
    expect(body.includes(image.subarray(0, 8))).toBe(false);
    let reads = 0;
    app.responses.set(`GET ${path}`, ({ json }) => json({ ...proposed, imageVersion: 'new-image',
      status: ++reads === 1 ? 'PROCESSING' : 'PROPOSED_GRADE' }));
    return route.fulfill({ status: 202, headers: { 'access-control-allow-origin': '*' } });
  });

  await page.getByLabel('Chọn ảnh chụp lại').setInputFiles({ name: 'replacement.png', mimeType: 'image/png', buffer: image });
  const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
  const save = editor.getByRole('button', { name: 'Lưu ảnh đã che' });
  await expect(save).toBeDisabled();
  await editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await save.click();
  await page.getByRole('button', { name: 'Gửi ảnh chụp lại' }).click();
  await expect(page.getByText('Đang xử lý ảnh bài làm.')).toBeVisible();
  await expect(page.getByRole('button', { name: /Duyệt điểm 8/ })).toBeEnabled();
  await expect(page).toHaveURL(submissionUrl);
  expect(app.requests.filter(request => request.path === `${path}/retake` && request.method === 'POST')).toHaveLength(1);
  expect(app.requests.filter(request => request.path === `${path}/image`).length).toBeGreaterThan(originalImageReads);
});

test('teacher retries a technical failure on the same image and checks a lost response before retrying again', async ({ page, app }) => {
  const detail = { ...proposed, status: 'FAILED', gradeProposal: undefined, canRetryProcessing: true, imageVersion: 'same-image' };
  await openSubmission(page, app, detail);
  app.responses.set(`POST ${path}/retry-processing`, ({ reject }) => {
    let reads = 0;
    app.responses.set(`GET ${path}`, ({ json }) => json(++reads === 1
      ? { ...detail, status: 'PROCESSING', canRetryProcessing: false }
      : { ...proposed, imageVersion: detail.imageVersion, canRetryProcessing: false }));
    return reject(503);
  });

  await page.getByRole('button', { name: 'Thử xử lý lại' }).click();
  await expect(page.getByRole('button', { name: 'Thử xử lý lại' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Kiểm tra lại' }).click();
  await expect(page.getByText('Đang xử lý ảnh bài làm.')).toBeVisible();
  await expect(page.getByRole('button', { name: /Duyệt điểm 8/ })).toBeEnabled();
  await expect(page).toHaveURL(submissionUrl);
  const writes = app.requests.filter(request => request.method === 'POST' && request.path.startsWith(path));
  expect(writes).toHaveLength(1);
  expect(writes[0].path).toBe(`${path}/retry-processing`);
  expect(writes[0].body).toBeNull();
});

test('approval remains confirmed when the follow-up detail read fails', async ({ page, app }) => {
  await openSubmission(page, app);
  app.responses.set(`POST ${path}/approve`, ({ route }) => {
    app.responses.set(`GET ${path}`, ({ reject }) => reject(503));
    return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*' } });
  });

  await page.getByRole('button', { name: 'Duyệt điểm 8' }).click();
  await expect(page.getByText('Đã lưu quyết định chấm điểm.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Thử tải lại chi tiết' })).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Đã lưu quyết định chấm điểm.' })).toBeFocused();
  await expect(page.getByRole('button', { name: /Duyệt điểm/ })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Quay lại hàng đợi duyệt' })).toBeVisible();
  expect(app.requests.filter(request => request.path === `${path}/approve` && request.method === 'POST')).toHaveLength(1);
});

test('lost write response requires a fresh read before any further grading action', async ({ page, app }) => {
  await openSubmission(page, app);
  app.responses.set(`POST ${path}/approve`, ({ route }) => {
    app.responses.set(`GET ${path}`, ({ json }) => json({ ...proposed, status: 'TEACHER_APPROVED', teacherScore: 8 }));
    return route.abort('connectionreset');
  });

  await page.getByRole('button', { name: 'Duyệt điểm 8' }).click();
  await expect(page.getByText('Chưa xác nhận được kết quả lưu điểm.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: /Duyệt điểm/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'Kiểm tra kết quả lưu' }).click();
  await expect(page.getByText('Điểm chính thức 8 / 10', { exact: true })).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'Điểm chính thức 8 / 10' })).toBeFocused();
  expect(app.requests.filter(request => request.path === `${path}/approve` && request.method === 'POST')).toHaveLength(1);
});

test('uncertain OCR can be graded manually only after the teacher confirms legibility and supplies a score and reason', async ({ page, app }) => {
  const detail = { ...proposed, status: 'NEEDS_CONFIRMATION', gradeProposal: undefined };
  await openSubmission(page, app, detail);
  app.responses.set(`POST ${path}/override`, ({ body, route }) => {
    app.responses.set(`GET ${path}`, ({ json }) => json({ ...detail, status: 'TEACHER_OVERRIDDEN', teacherScore: body.score, teacherReason: body.reason }));
    return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*' } });
  });

  await expect(page.getByRole('button', { name: /Duyệt điểm/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'Chấm thủ công', exact: true }).click();
  const save = page.getByRole('button', { name: 'Lưu điểm thủ công' });
  const score = page.getByRole('spinbutton', { name: 'Điểm chính thức' });
  await expect(score).toHaveValue('');
  await score.fill('0');
  await page.getByLabel('Lý do điều chỉnh').fill('Bài làm đọc rõ, phép tính sai.');
  await expect(save).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Tôi đã xem ảnh và đọc rõ bài làm.' }).check();
  await save.click();
  await expect(page.getByText('Điểm chính thức 0 / 10', { exact: true })).toBeVisible();
  const writes = app.requests.filter(request => request.path === `${path}/override` && request.method === 'POST');
  expect(writes.map(request => request.body)).toEqual([{ score: 0, reason: 'Bài làm đọc rõ, phép tính sai.', imageLegible: true }]);
});

test('a submission marked for retake stays unresolved and explains how to get a clearer image', async ({ page, app }) => {
  await openSubmission(page, app, { ...proposed, status: 'NEEDS_RETAKE', gradeProposal: undefined });

  await expect(page.getByText(/Chụp lại ảnh rõ toàn bộ bài làm/)).toBeVisible();
  await expect(page.getByRole('button', { name: /Duyệt điểm|Chấm thủ công|Điều chỉnh/ })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Quay lại hàng đợi duyệt' })).toBeVisible();
});
