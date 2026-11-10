// Opt-in only. Uses real local services and creates records in a disposable database.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

function required(name) {
  const value = process.env[name];
  assert(value, `Missing ${name}`);
  return value;
}
assert.equal(process.env.MATHVISION_LIVE_DISPOSABLE, 'true', 'Explicit disposable environment required');
const api = required('MATHVISION_LIVE_API').replace(/\/$/, '');
const portal = required('MATHVISION_LIVE_PORTAL').replace(/\/$/, '');
const teacherSite = required('MATHVISION_LIVE_TEACHER').replace(/\/$/, '');
for (const address of [api, portal, teacherSite]) {
  assert(['127.0.0.1', 'localhost'].includes(new URL(address).hostname), 'This check targets local services');
}
const email = required('MATHVISION_LIVE_TEACHER_EMAIL');
const password = required('MATHVISION_LIVE_TEACHER_PASSWORD');
const imagePath = resolve(required('MATHVISION_LIVE_IMAGE'));
const output = resolve(required('MATHVISION_LIVE_OUTPUT'));
const source = await readFile(imagePath);
const expectedScore = Number(required('MATHVISION_LIVE_SCORE'));
assert(Number.isInteger(expectedScore) && expectedScore >= 0 && expectedScore <= 100);
const decisionReason = required('MATHVISION_LIVE_REASON');
await mkdir(output, { recursive: true });
const results = { started: new Date().toISOString(), mockedResponses: false, checks: [] };
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
async function json(path, token, method = 'GET', body) {
  const response = await fetch(api + path, {
    method, signal: AbortSignal.timeout(70000),
    headers: { ...(token ? { Authorization: 'Bearer ' + token } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  assert(response.ok, `${method} ${path} returned ${response.status}`);
  return response.status === 204 || response.headers.get('content-length') === '0' ? null : response.json();
}
const auth = await json('/auth/login', null, 'POST', { email, password });
const classes = await json('/teacher/classes', auth.accessToken);
assert(classes.length, 'An assigned classroom is required');
const classroom = await json('/teacher/classes/' + classes[0].classId, auth.accessToken);
assert(classroom.students.length, 'An assigned student is required');
const student = classroom.students[0];
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(20000);
  await page.addInitScript(() => {
    const send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (body) {
      if (body instanceof FormData && body.has('images')) {
        window.reviewUploadedImages = Promise.all(body.getAll('images').map(async file => {
          const bytes = await file.arrayBuffer();
          const digest = await crypto.subtle.digest('SHA-256', bytes);
          return { bytes: bytes.byteLength, sha256: Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('') };
        }));
      }
      return send.call(this, body);
    };
  });
  await page.goto(teacherSite + '/dashboard');
  await page.waitForURL(url => url.origin === new URL(portal).origin);
  results.checks.push('Guest guard and development application bootstrap');
  await page.goto(portal + '/login');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(email);
  await page.getByLabel(/^Mật khẩu/).fill(password);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page).toHaveURL(teacherSite + '/dashboard');
  results.checks.push('Portal login and one-time Teacher SSO');
  await page.goto(teacherSite + '/assignments/create?classId=' + classroom.classId);
  await page.getByLabel('Tên bài tập', { exact: true }).fill('Live image review ' + Date.now());
  await page.getByRole('spinbutton', { name: 'Thang điểm tối đa' }).fill('100');
  await page.getByRole('button', { name: 'Tạo bài tập & Thu thập ảnh', exact: true }).click();
  await expect(page).toHaveURL(/\/batches\/create\?assignmentId=/);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'worksheet.jpg', mimeType: 'image/jpeg', buffer: source });
  await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
  await page.getByRole('option', { name: student.displayName, exact: true }).click();
  await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Lưu ảnh đã che', exact: true })).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await page.getByRole('button', { name: 'Lưu ảnh đã che', exact: true }).click();
  const uploadRequest = page.waitForRequest(request => request.method() === 'POST' && /\/teacher\/batches\/[^/]+\/submissions$/.test(new URL(request.url()).pathname));
  await page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true }).click();
  await uploadRequest;
  const uploadedImages = await page.evaluate(() => window.reviewUploadedImages);
  assert.equal(uploadedImages?.length, 1, 'Actual multipart image is required');
  await expect(page).toHaveURL(/\/batches\/[a-f0-9-]+$/);
  const batchId = new URL(page.url()).pathname.split('/').at(-1);
  const deadline = Date.now() + 120000;
  let batch;
  do {
    batch = await json('/teacher/batches/' + batchId, auth.accessToken);
    if (batch.processedCount === 1) break;
    await new Promise(resolve => setTimeout(resolve, 1000));
  } while (Date.now() < deadline);
  assert.equal(batch.processedCount, 1, 'Real AI worker must finish the uploaded image');
  const id = batch.submissions[0].submissionId;
  const detail = await json('/teacher/submissions/' + id, auth.accessToken);
  assert.equal(detail.studentId, student.userId);
  results.analysis = { status: detail.status, analysisStatus: detail.analysisStatus, reasonCode: detail.reasonCode, validation: detail.validation };
  const imageResponse = await fetch(api + '/teacher/submissions/' + id + '/image', { headers: { Authorization: 'Bearer ' + auth.accessToken } });
  assert.equal(imageResponse.status, 200);
  assert.equal(imageResponse.headers.get('cache-control'), 'no-store');
  const returnedImage = Buffer.from(await imageResponse.arrayBuffer());
  assert.equal(hash(returnedImage), uploadedImages[0].sha256, 'Private storage must return the exact redacted upload');
  results.image = { sha256: hash(returnedImage), bytes: returnedImage.length };
  results.checks.push('Real upload, private storage round-trip and asynchronous AI callback');
  await page.goto(teacherSite + '/submissions/' + id);
  const image = page.getByRole('img', { name: 'Bài làm của ' + student.displayName, exact: true });
  await expect(image).toBeVisible();
  await expect.poll(() => image.evaluate(img => img.complete && img.naturalWidth > 100 && img.naturalHeight > 100)).toBe(true);
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 });
    for (const quarterTurn of [1, 2, 3, 4]) {
      await page.getByRole('button', { name: 'Xoay ảnh 90 độ', exact: true }).click();
      await page.waitForTimeout(250);
      const edges = await image.evaluate(img => {
        const area = img.closest('[role=region]');
        area.scrollLeft = 0; area.scrollTop = 0;
        const start = img.getBoundingClientRect(); const box = area.getBoundingClientRect();
        area.scrollLeft = area.scrollWidth; area.scrollTop = area.scrollHeight;
        const end = img.getBoundingClientRect();
        return [box.left - start.left, box.top - start.top, end.right - box.right, end.bottom - box.bottom];
      });
      assert(edges.every(edge => edge <= 1), `Unreachable edge at ${width}px and turn ${quarterTurn}`);
    }
    await page.screenshot({ path: resolve(output, `teacher-image-${width}.png`), fullPage: true });
  }
  results.checks.push('All four image edges after 0/90/180/270 degree rotation at 100%, desktop and narrow viewport');
  await page.getByRole('button', { name: 'Xem chi tiết toàn màn hình', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect.poll(() => page.evaluate(() => !!document.activeElement?.closest('[role=dialog]'))).toBe(true);
  for (let count = 0; count < 12; count++) {
    await page.keyboard.press('Tab');
    assert(await page.evaluate(() => !!document.activeElement?.closest('[role=dialog]')), 'Tab escaped the image dialog');
  }
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Xem chi tiết toàn màn hình', exact: true })).toBeFocused();
  results.checks.push('Fullscreen focus, Tab containment and Escape');
  await page.getByRole('button', { name: 'Điều chỉnh', exact: true }).click();
  await page.getByRole('spinbutton', { name: 'Điểm chính thức', exact: true }).fill(String(expectedScore));
  await page.getByLabel('Lý do điều chỉnh').fill(decisionReason);
  await page.getByRole('button', { name: 'Xác nhận ghi đè điểm', exact: true }).click();
  await expect(page).toHaveURL(/\/batches\/[a-f0-9-]+$/);
  await page.goto(teacherSite + '/submissions/' + id);
  await expect(page.getByText(`Điểm chính thức ${expectedScore} / 100`, { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(`Điểm chính thức ${expectedScore} / 100`, { exact: true })).toBeVisible();
  const saved = await json('/teacher/submissions/' + id, auth.accessToken);
  assert.equal(saved.teacherScore, expectedScore); assert.equal(saved.teacherReason, decisionReason);
  results.checks.push('Actual teacher decision and persistence after reload');
  const admin = await json('/auth/login', null, 'POST', { email: required('MATHVISION_LIVE_ADMIN_EMAIL'), password: required('MATHVISION_LIVE_ADMIN_PASSWORD') });
  const foreignEmail = 'review-' + Date.now() + '@example.test';
  const foreignPassword = 'LocalReview-' + Date.now();
  await json('/admin/users', admin.accessToken, 'POST', { email: foreignEmail, displayName: 'Giáo viên khác lớp', role: 'TEACHER', initialPassword: foreignPassword });
  const foreign = await json('/auth/login', null, 'POST', { email: foreignEmail, password: foreignPassword });
  for (const [method, suffix, body] of [['GET', '', null], ['GET', '/image', null], ['POST', '/approve', null], ['POST', '/override', { score: 100, reason: 'Cross-class request' }]]) {
    const denied = await fetch(api + '/teacher/submissions/' + id + suffix, {
      method, headers: { Authorization: 'Bearer ' + foreign.accessToken, 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}),
    });
    assert.equal(denied.status, 403, `Foreign teacher ${method} ${suffix} must be forbidden`);
  }
  results.checks.push('Real foreign-account login receives 403 for metadata, image, approve and override');
  results.passed = true;
  console.log('Live Teacher review passed ' + results.checks.length + ' checks');
} catch (error) {
  results.passed = false;
  results.error = error.message.replace(/([#?&](?:sso|code)=)[^\s"']+/g, '$1[redacted]');
  throw new Error(results.error);
} finally {
  results.finished = new Date().toISOString();
  await writeFile(resolve(output, 'teacher-live-results.json'), JSON.stringify(results, null, 2));
  await browser.close();
}
