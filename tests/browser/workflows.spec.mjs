import { test, expect, sites, login, openNavigation } from './fixtures.mjs';

test('student login hands off to /study/ (downstream Student UI is outside this suite)', async ({ page, app }) => {
  // Observe the entry request only; do not substitute a fake Student app.
  await page.route(`${sites.portal.origin}/study/`, route => route.fulfill({ status: 204 }));
  const entry = page.waitForRequest(request => request.isNavigationRequest() && request.url() === `${sites.portal.origin}/study/`);
  await Promise.all([entry, login(page, 'STUDENT')]);
  expect(app.requests.filter(r => r.path === '/auth/sso/ticket')).toEqual([]);
});

test('portal invalid login remains usable and keyboard retry succeeds', async ({ page, app }) => {
  await page.goto(`${sites.portal.origin}/login`);
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('admin@example.test');
  await page.getByLabel(/^Mật khẩu/).fill('wrong-password');
  await page.getByLabel(/^Mật khẩu/).press('Enter');
  await expect(page.getByRole('alert')).toContainText('Tài khoản hoặc mật khẩu chưa đúng');
  await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toHaveValue('admin@example.test');
  await expect(page.getByLabel(/^Mật khẩu/)).toHaveValue('');
  await page.getByLabel(/^Mật khẩu/).fill('synthetic-password');
  await page.getByLabel(/^Mật khẩu/).press('Enter');
  await expect(page).toHaveURL(`${sites.admin.origin}/dashboard`);
  expect(app.requests.filter(r => r.path === '/auth/login')).toHaveLength(2);
});

for (const role of ['TEACHER', 'ADMIN']) {
  const site = sites[role.toLowerCase()];
  const signedOutUrl = role === 'TEACHER' ? `${sites.portal.origin}/` : `${site.origin}/login`;
  test(`${role} guest cannot open protected pages`, async ({ page, app }) => {
    await page.goto(`${site.origin}/dashboard`);
    await expect(page).toHaveURL(signedOutUrl);
    expect(app.requests.filter(r => r.path.startsWith(`/${role.toLowerCase()}/`))).toEqual([]);
  });

  test(`${role} SSO, reload and logout preserve the correct session boundaries`, async ({ page, app }) => {
    await login(page, role);
    await expect(page.getByRole('heading', { name: `Xin chào, Kiểm thử ${role}`, exact: true })).toBeVisible();
    expect(new URL(page.url()).hash).toBe('');
    expect(app.requests.filter(r => r.path === '/auth/sso/exchange')).toHaveLength(1);
    await page.reload();
    await expect(page.getByRole('heading', { name: `Xin chào, Kiểm thử ${role}`, exact: true })).toBeVisible();
    expect(app.requests.filter(r => r.path === '/auth/sso/exchange')).toHaveLength(1);
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await expect(page).toHaveURL(`${sites.portal.origin}/`);
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem('portal_access_token'))).toBeNull();
    await expect(page.getByRole('link', { name: 'Đăng nhập →', exact: true })).toBeVisible();
    await page.goto(`${site.origin}/dashboard`);
    await expect(page).toHaveURL(signedOutUrl);
  });

  test(`${role} expired credentials leave the protected page instead of looping`, async ({ page, app }) => {
    // Finish the valid dashboard load before expiring this session. Otherwise
    // its pending requests can refresh in the old document just before reload,
    // and the test counts that aborted refresh alongside the new document's.
    const initialPaths = role === 'ADMIN' ? ['/admin/dashboard', '/admin/audit'] : ['/teacher/dashboard'];
    await Promise.all([
      ...initialPaths.map(path => page.waitForResponse(response =>
        new URL(response.url()).pathname === `/api/v1${path}` && response.status() === 200)),
      login(page, role),
    ]);
    app.expired = true;
    await page.reload();
    await expect(page).toHaveURL(signedOutUrl);
    // Teacher returns to Portal, which has its own isolated expired session.
    // Wait for that cleanup rather than counting requests during its startup.
    if (role === 'TEACHER') {
      await expect.poll(() => page.evaluate(() => sessionStorage.getItem('portal_access_token'))).toBeNull();
      await expect(page.getByRole('link', { name: 'Đăng nhập →', exact: true })).toBeVisible();
    }
    const refreshes = app.requests.filter(r => r.path === '/auth/refresh');
    expect(refreshes.filter(r => r.origin === site.origin)).toHaveLength(1);
    expect(refreshes.filter(r => r.origin === sites.portal.origin)).toHaveLength(role === 'TEACHER' ? 1 : 0);
    expect(refreshes).toHaveLength(role === 'TEACHER' ? 2 : 1);
    await page.goto(`${site.origin}/dashboard`);
    await expect(page).toHaveURL(signedOutUrl);
    expect(app.requests.filter(r => r.path === '/auth/refresh')).toHaveLength(refreshes.length);
  });
}

test('student account cannot open admin dashboard', async ({ context, page, app }) => {
  await context.addInitScript(origin => {
    if (location.origin === origin) {
      localStorage.setItem('mvk_admin_access_token', 'fixture.STUDENT.access');
      localStorage.setItem('mvk_admin_refresh_token', 'fixture.STUDENT.refresh');
    }
  }, sites.admin.origin);
  await page.goto(`${sites.admin.origin}/dashboard`);
  await expect(page).toHaveURL(`${sites.admin.origin}/403`);
  await expect(page.getByRole('heading', { name: 'Bạn không có quyền truy cập' })).toBeVisible();
  expect(app.requests.filter(r => r.path.startsWith('/admin/'))).toEqual([]);
  expect(await page.evaluate(() => localStorage.getItem('mvk_admin_access_token'))).toBeNull();
});

test('teacher cannot cross into the admin portal', async ({ page, app }) => {
  await login(page, 'TEACHER');
  await page.goto(`${sites.portal.origin}/admin`);
  await expect(page).toHaveURL(/\/access-denied\?/);
  expect(app.requests.filter(r => r.path === '/auth/sso/ticket' && r.body.targetApp === 'ADMIN')).toEqual([]);
});

test('teacher creates a selected-class subtraction assignment with a custom grading scale', async ({ page, app }) => {
  await login(page, 'TEACHER');
  await openNavigation(page, 'TEACHER');
  await page.getByRole('link', { name: 'Lớp học', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Danh sách Lớp học' })).toBeVisible();
  await page.getByRole('button', { name: 'Tạo bài tập cho lớp', exact: true }).click();
  const submit = page.getByRole('button', { name: 'Tạo bài tập & Thu thập ảnh', exact: true });
  await expect(submit).toBeDisabled();
  await page.getByLabel('Tên bài tập', { exact: true }).fill('Phép trừ kiểm thử');
  const maxScore = page.getByRole('spinbutton', { name: 'Thang điểm tối đa' });
  await expect(maxScore).toHaveValue('10');
  await maxScore.fill('100');
  await page.getByRole('combobox', { name: 'Dạng phép tính (Phạm vi hỗ trợ MVP)' }).click();
  await page.getByRole('option', { name: /Phép trừ đặt tính dọc/ }).click();
  await submit.click();
  await expect(page).toHaveURL(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
  await expect(page.getByRole('heading', { name: 'Tạo đợt chấm bài', exact: true })).toBeVisible();
  await expect.poll(() => app.requests.some(r => r.path === '/teacher/classes/class-5a')).toBe(true);
  expect(app.requests.filter(r => r.path === '/teacher/assignments' && r.method === 'POST').map(r => r.body))
    .toEqual([{ classId: 'class-5a', title: 'Phép trừ kiểm thử', operationType: 'VERTICAL_SUBTRACTION', maxScore: 100 }]);
});

test('teacher can retry a failed class list without reloading the page', async ({ page, app }) => {
  await login(page, 'TEACHER');
  app.classesDown = true;
  await page.goto(`${sites.teacher.origin}/classes`);
  await expect(page.getByRole('alert')).toContainText('Chưa tải được danh sách');
  app.classesDown = false;
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Lớp 5A', exact: true })).toBeVisible();
});

test('admin filters users by role, locked state and search then clears the state filter', async ({ page, app }) => {
  await login(page, 'ADMIN');
  await openNavigation(page, 'ADMIN');
  await page.getByRole('link', { name: 'Người dùng', exact: true }).click();
  await page.getByRole('combobox', { name: 'Vai trò', exact: true }).click();
  await page.getByRole('option', { name: 'Học sinh', exact: true }).click();
  await page.getByRole('combobox', { name: 'Trạng thái', exact: true }).click();
  await page.getByRole('option', { name: 'Đã bị khóa', exact: true }).click();
  await page.getByLabel('Tìm theo tên hoặc email').fill('An');
  await page.getByLabel('Tìm theo tên hoặc email').press('Enter');
  await expect.poll(() => app.requests.filter(r => r.path === '/admin/users').at(-1)?.query)
    .toMatchObject({ role: 'STUDENT', active: 'false', query: 'An' });
  await expect(page.getByRole('table', { name: 'Danh sách người dùng' })).toContainText('An kiểm thử');
  await page.getByRole('combobox', { name: 'Trạng thái', exact: true }).click();
  await page.getByRole('option', { name: 'Tất cả trạng thái', exact: true }).click();
  await expect.poll(() => app.requests.filter(r => r.path === '/admin/users').at(-1)?.query.active).toBeUndefined();
});
