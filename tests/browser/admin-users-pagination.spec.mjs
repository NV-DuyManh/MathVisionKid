import { test, expect, login, profile, sites } from './fixtures.mjs';

test('admin restores a filtered page after viewing user details and resets it when changing size', async ({ page, app }) => {
  const searchTerm = '@pagination.example.test';
  const users = Array.from({ length: 25 }, (_, index) => ({
    ...profile('STUDENT'),
    userId: `pupil-${index + 1}`,
    displayName: `Học sinh ${index + 1}`,
    email: `pupil-${index + 1}${searchTerm}`,
    active: false,
  }));
  users.push(
    { ...profile('TEACHER'), email: `teacher${searchTerm}`, active: false },
    { ...profile('STUDENT'), userId: 'active-pupil', email: `active-pupil${searchTerm}` },
    { ...profile('STUDENT'), userId: 'other-pupil', email: 'other-pupil@example.test', active: false },
  );
  app.responses.set('GET /admin/users', ({ json, route }) => {
    const params = new URL(route.request().url()).searchParams;
    const pageIndex = Number(params.get('page'));
    const size = Number(params.get('size'));
    const role = params.get('role');
    const active = params.get('active');
    const query = params.get('query')?.toLowerCase();
    const matching = users.filter(user =>
      (!role || user.role === role) &&
      (active === null || String(user.active) === active) &&
      (!query || user.displayName.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)),
    );
    return json({
      content: matching.slice(pageIndex * size, (pageIndex + 1) * size),
      totalElements: matching.length,
      totalPages: Math.ceil(matching.length / size),
      number: pageIndex,
      size,
    });
  });
  app.responses.set('GET /admin/users/pupil-21', ({ json }) => json({ ...users[20], classes: [] }));

  await login(page, 'ADMIN');
  await page.goto(`${sites.admin.origin}/users`);
  const roleFilter = page.getByRole('combobox', { name: 'Vai trò', exact: true });
  const activeFilter = page.getByRole('combobox', { name: 'Trạng thái', exact: true });
  const search = page.getByLabel('Tìm theo tên hoặc email');
  const pageSize = page.getByRole('combobox', { name: /^Số dòng:/ });
  await roleFilter.click();
  await page.getByRole('option', { name: 'Học sinh', exact: true }).click();
  await activeFilter.click();
  await page.getByRole('option', { name: 'Đã bị khóa', exact: true }).click();
  await search.fill(searchTerm);
  await page.getByRole('button', { name: 'Tìm kiếm', exact: true }).click();
  await pageSize.click();
  await page.getByRole('option', { name: '20', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Go to next page' })).toBeEnabled();
  await page.getByRole('button', { name: 'Go to next page' }).click();

  const detail = page.getByRole('link', { name: 'Xem chi tiết Học sinh 21', exact: true });
  const expectSecondPage = async () => {
    await expect(detail).toBeVisible();
    await expect(page.getByText('21–25 / 25', { exact: true })).toBeVisible();
    await expect(pageSize).toHaveText('20');
    await expect(roleFilter).toHaveText('Học sinh');
    await expect(activeFilter).toHaveText('Đã bị khóa');
    await expect(search).toHaveValue(searchTerm);
    expect(Object.fromEntries(new URL(page.url()).searchParams)).toEqual({
      role: 'STUDENT', active: 'false', page: '1', size: '20',
    });
  };

  await detail.click();
  await expect(page.getByRole('heading', { name: 'Học sinh 21', exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Danh sách người dùng', exact: true }).click();
  await expectSecondPage();

  await detail.click();
  await expect(page.getByRole('heading', { name: 'Học sinh 21', exact: true })).toBeVisible();
  await page.goBack();
  await expectSecondPage();

  await pageSize.click();
  await page.getByRole('option', { name: '50', exact: true }).click();
  await expect.poll(() => app.requests.filter(request =>
    request.method === 'GET' && request.path === '/admin/users',
  ).at(-1)?.query).toEqual({ role: 'STUDENT', active: 'false', query: searchTerm, page: '0', size: '50' });
  await expect(page.getByRole('link', { name: 'Xem chi tiết Học sinh 1', exact: true })).toBeVisible();
  await expect(page.getByText('1–25 / 25', { exact: true })).toBeVisible();
  expect(Object.fromEntries(new URL(page.url()).searchParams)).toEqual({
    role: 'STUDENT', active: 'false', size: '50',
  });
});
