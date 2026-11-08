import { test, expect, sites, login, profile } from './fixtures.mjs';

// Keep the request unresolved until assertions finish: no timing-dependent sleep.
test('portal login visibly waits and blocks duplicate submits', async ({ page, app }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  let calls = 0;
  await page.route('**/api/v1/auth/login', async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    calls++; await gate; return route.fallback();
  });
  try {
    await page.goto(`${sites.portal.origin}/login`);
    await page.getByRole('textbox', { name: 'Email', exact: true }).fill('admin@example.test');
    const password = page.getByLabel(/^Mật khẩu/);
    await password.fill('synthetic-password');
    await password.press('Enter');
    const pending = page.getByRole('button', { name: /Đang xác thực/ });
    await expect(pending).toBeVisible();
    await expect(pending).toBeDisabled();
    await page.keyboard.press('Enter');
    expect(calls).toBe(1);
    release();
    await expect(page).toHaveURL(`${sites.admin.origin}/dashboard`);
    expect(app.requests.filter(row => row.path === '/auth/login')).toHaveLength(1);
  } finally { release(); }
});

test('teacher assignment shows activity at submit and creates only one assignment', async ({ page, app }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  let calls = 0;
  await page.route('**/api/v1/teacher/assignments', async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    calls++; await gate; return route.fallback();
  });
  try {
    await login(page, 'TEACHER');
    await page.goto(`${sites.teacher.origin}/classes`);
    await page.getByRole('button', { name: 'Tạo bài tập cho lớp', exact: true }).click();
    await page.getByLabel('Tên bài tập', { exact: true }).fill('Bài tập đang chờ');
    await page.getByRole('button', { name: 'Tạo bài tập & Thu thập ảnh', exact: true }).click();
    const pending = page.getByRole('button', { name: /Đang tạo bài tập/ });
    await expect(pending).toBeVisible();
    await expect(pending).toBeDisabled();
    expect(calls).toBe(1);
    release();
    await expect(page).toHaveURL(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
    expect(app.assignments).toHaveLength(1);
  } finally { release(); }
});

test('admin confirmation shows activity and recovers in place after failure', async ({ page, app }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  let calls = 0;
  const userId = 'loading-pupil';
  await page.route(`**/api/v1/admin/users/${userId}`, route => route.fulfill({ json: {
    ...profile('STUDENT'), userId, displayName: 'Học sinh kiểm thử', classes: [],
  }, headers: { 'access-control-allow-origin': '*' } }));
  await page.route(`**/api/v1/admin/users/${userId}/disable`, async route => {
    if (route.request().method() === 'OPTIONS') return route.fallback();
    calls++; await gate;
    return route.fulfill({ status: 503, json: { error: { code: 'TEMPORARY', message: 'Chưa thực hiện được. Vui lòng thử lại.' } },
      headers: { 'access-control-allow-origin': '*' } });
  });
  try {
    await login(page, 'ADMIN');
    await page.goto(`${sites.admin.origin}/users/${userId}`);
    await page.getByRole('button', { name: 'Khóa tài khoản', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('button', { name: 'Xác nhận', exact: true }).click();
    const pending = dialog.getByRole('button', { name: 'Đang xử lý…', exact: true });
    await expect(pending).toBeDisabled();
    await expect(pending).toHaveAttribute('aria-busy', 'true');
    await expect(dialog.locator('[role="progressbar"]')).toBeVisible();
    expect(calls).toBe(1);
    release();
    await expect(dialog.getByRole('alert')).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Xác nhận', exact: true })).toBeEnabled();
    await dialog.getByRole('button', { name: 'Hủy bỏ', exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Học sinh kiểm thử', exact: true })).toBeVisible();
  } finally { release(); }
});
