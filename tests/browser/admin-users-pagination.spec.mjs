import { test, expect, login, profile, sites } from './fixtures.mjs';

test('admin returns from user details to the same page and page size', async ({ page, app }) => {
  const users = Array.from({ length: 25 }, (_, index) => ({
    ...profile('STUDENT'),
    userId: `pupil-${index + 1}`,
    displayName: `Học sinh ${index + 1}`,
  }));
  app.responses.set('GET /admin/users', ({ json, route }) => {
    const params = new URL(route.request().url()).searchParams;
    const pageIndex = Number(params.get('page'));
    const size = Number(params.get('size'));
    return json({
      content: users.slice(pageIndex * size, (pageIndex + 1) * size),
      totalElements: users.length,
      totalPages: Math.ceil(users.length / size),
      number: pageIndex,
      size,
    });
  });
  app.responses.set('GET /admin/users/pupil-21', ({ json }) => json({ ...users[20], classes: [] }));

  await login(page, 'ADMIN');
  await page.goto(`${sites.admin.origin}/users`);
  await page.getByRole('combobox', { name: /^Số dòng:/ }).click();
  await page.getByRole('option', { name: '20', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Go to next page' })).toBeEnabled();
  await page.getByRole('button', { name: 'Go to next page' }).click();

  const detail = page.getByRole('link', { name: 'Xem chi tiết Học sinh 21', exact: true });
  await detail.click();
  await expect(page.getByRole('heading', { name: 'Học sinh 21', exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Danh sách người dùng', exact: true }).click();
  await expect(detail).toBeVisible();
  await expect(page.getByRole('combobox', { name: /^Số dòng:/ })).toHaveText('20');

  await detail.click();
  await expect(page.getByRole('heading', { name: 'Học sinh 21', exact: true })).toBeVisible();
  await page.goBack();
  await expect(detail).toBeVisible();
  await expect(page.getByText('21–25 / 25', { exact: true })).toBeVisible();
});
