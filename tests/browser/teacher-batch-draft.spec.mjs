import { readFile } from 'node:fs/promises';
import { test, expect, login, openNavigation, sites } from './fixtures.mjs';

const image = await readFile(new URL('../../apps/teacher-web/public/ui/mathvision-star.png', import.meta.url));

test('selected images are protected when leaving or reloading the upload page', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();

  await page.getByRole('button', { name: 'Quay lại danh sách đợt chấm' }).click();
  const confirmation = page.getByRole('dialog', { name: 'Rời trang tải ảnh?' });
  await expect(confirmation).toBeVisible();
  await expect(confirmation.getByRole('button', { name: 'Ở lại' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(confirmation).toBeHidden();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();

  const beforeUnload = page.waitForEvent('dialog');
  const reload = page.evaluate(() => { location.reload(); });
  const dialog = await beforeUnload;
  const dialogType = dialog.type();
  await dialog.dismiss();
  await reload;
  expect(dialogType).toBe('beforeunload');
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();

  await page.getByRole('button', { name: 'Quay lại danh sách đợt chấm' }).click();
  await confirmation.getByRole('button', { name: 'Rời trang' }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches`);
});

test('sidebar navigation asks before discarding selected images', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  await page.getByRole('navigation', { name: 'Đường dẫn trang' }).getByRole('link', { name: 'Đợt chấm bài' }).click();
  const confirmation = page.getByRole('dialog', { name: 'Rời trang tải ảnh?' });
  await confirmation.getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.locator('#upload-draft-dialog-title')).toHaveCount(0);
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  if (page.viewportSize().width < 900) await expect(page.getByRole('button', { name: 'Mở điều hướng giáo viên' })).toBeVisible();
  await openNavigation(page, 'TEACHER');
  const modifiedClick = await page.getByRole('link', { name: 'Lớp học', exact: true }).evaluate(link => {
    const originalConfirm = window.confirm;
    let confirmations = 0;
    let prevented = false;
    window.confirm = () => { confirmations++; return false; };
    document.addEventListener('click', event => { prevented = event.defaultPrevented; event.preventDefault(); }, { once: true });
    link.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, button: 0, ctrlKey: true }));
    window.confirm = originalConfirm;
    return { confirmations, prevented };
  });
  expect(modifiedClick).toEqual({ confirmations: 0, prevented: false });
  await page.getByRole('link', { name: 'Lớp học', exact: true }).click();
  await confirmation.getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  await expect(page).toHaveURL(/\/batches\/create/);
  await expect(page.locator('#upload-draft-dialog-title')).toHaveCount(0);
  if (page.viewportSize().width < 900) await expect(page.getByRole('button', { name: 'Mở điều hướng giáo viên' })).toBeVisible();
  await openNavigation(page, 'TEACHER');
  await page.getByRole('link', { name: 'Lớp học', exact: true }).click();
  await confirmation.getByRole('button', { name: 'Rời trang' }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/classes`);
});

test('browser back and forward protect prepared images', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches`);
  await page.getByRole('button', { name: 'Tạo đợt chấm mới' }).click();
  await page.getByRole('combobox', { name: 'Bài tập cần chấm' }).click();
  await page.getByRole('option', { name: 'Bài kiểm thử' }).click();
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.goBack();
  const confirmation = page.getByRole('dialog', { name: 'Rời trang tải ảnh?' });
  await expect(confirmation).toBeVisible();
  await confirmation.getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  await page.goBack();
  await confirmation.getByRole('button', { name: 'Rời trang' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toHaveCount(0);
  await page.goForward();
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.getByRole('button', { name: 'Quay lại danh sách đợt chấm' }).click();
  await confirmation.getByRole('button', { name: 'Rời trang' }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches`);
  await page.goBack();
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.goForward();
  await expect(confirmation).toBeVisible();
  await confirmation.getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  await page.goForward();
  await confirmation.getByRole('button', { name: 'Rời trang' }).click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches`);
});

test('skip link focuses the workspace without adding history and back still guards the draft', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches`);
  await page.getByRole('button', { name: 'Tạo đợt chấm mới' }).click();
  await page.getByRole('combobox', { name: 'Bài tập cần chấm' }).click();
  await page.getByRole('option', { name: 'Bài kiểm thử' }).click();
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  const historyBefore = await page.evaluate(() => ({ length: history.length, state: history.state, url: location.href }));
  await page.getByRole('link', { name: 'Đến nội dung chính' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#workspace-main')).toBeFocused();
  expect(await page.evaluate(() => ({ length: history.length, state: history.state, url: location.href }))).toEqual(historyBefore);
  await page.goBack();
  const confirmation = page.getByRole('dialog', { name: 'Rời trang tải ảnh?' });
  await expect(confirmation).toBeVisible();
  await confirmation.getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
});

test('logout warns once, keeps the draft on cancel and leaves after confirmation', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  const dialogs = [];
  page.on('dialog', async dialog => {
    dialogs.push(dialog.type());
    if (dialogs.length === 1) await dialog.dismiss();
    else await dialog.accept();
  });
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  expect(dialogs).toEqual(['confirm']);
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
  await expect(page).toHaveURL(/\/batches\/create/);
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await expect(page).toHaveURL(new RegExp(`^${sites.portal.origin}/`));
  expect(dialogs).toEqual(['confirm', 'confirm']);
});

test('an existing batch keeps prepared images while its status is checked after reconnecting', async ({ page, app }) => {
  const assignmentId = 'assignment-1';
  const batchId = 'resume-draft';
  app.assignments.push({ assignmentId, classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  const detail = { batchId, assignmentId, status: 'CREATED', totalCount: 0 };
  const batchPath = `/teacher/batches/${batchId}`;
  app.responses.set(`GET ${batchPath}`, ({ json }) => json(detail));
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?batchId=${batchId}`);
  await page.locator('input[type=file][multiple]').first().setInputFiles({ name: 'work.png', mimeType: 'image/png', buffer: image });
  await page.getByRole('combobox', { name: 'Học sinh thực hiện' }).click();
  await page.getByRole('option', { name: 'Kiểm thử STUDENT' }).click();
  await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).click();
  const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
  await editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' }).check();
  await editor.getByRole('button', { name: 'Lưu ảnh đã che' }).click();
  const submit = page.getByRole('button', { name: 'Bắt đầu chấm bài bằng AI', exact: true });
  await expect(submit).toBeEnabled();

  let release;
  const waiting = new Promise(resolve => { release = resolve; });
  app.responses.set(`GET ${batchPath}`, async ({ json }) => {
    await waiting;
    return json(detail);
  });
  try {
    await page.evaluate(() => {
      window.dispatchEvent(new Event('offline'));
      window.dispatchEvent(new Event('online'));
    });
    await expect(page.getByText('Đang kiểm tra đợt chấm…')).toBeVisible();
    await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
    await expect(submit).toBeDisabled();
  } finally {
    release();
  }
  await expect(submit).toBeEnabled();
  const privacyCount = page.getByRole('region', { name: 'Kiểm tra trước khi gửi' })
    .getByRole('listitem').filter({ hasText: 'Đã che thông tin' });
  await expect(privacyCount).toContainText('1/1');

  app.responses.set(`GET ${batchPath}`, ({ json }) => json({ ...detail, status: 'PROCESSING', totalCount: 1 }));
  await page.evaluate(() => {
    window.dispatchEvent(new Event('offline'));
    window.dispatchEvent(new Event('online'));
  });
  await expect(page.getByText('Đợt này đã nhận ảnh hoặc không còn mở để tải ảnh.')).toBeVisible();
  await expect(privacyCount).toContainText('1/1');
  await expect(submit).toBeDisabled();
  await page.getByRole('link', { name: 'Xem đợt chấm' }).click();
  await page.getByRole('dialog', { name: 'Rời trang tải ảnh?' }).getByRole('button', { name: 'Ở lại' }).click();
  await expect(page.getByLabel('Xóa ảnh này')).toBeVisible();
});
