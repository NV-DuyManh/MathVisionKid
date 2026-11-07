import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('Portal login enters the real Student bundle, navigates and survives a deep-link reload', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Bài học' }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/lessons`);
  await expect(page.getByText('Hôm nay em học gì?', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Hôm nay em học gì?', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/quiz`);
  await expect(page.getByText('Câu đố của em', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Unmatched Route', { exact: true })).toHaveCount(0);
  expect(app.requests.some(request => request.path === '/student/quizzes')).toBe(true);
});

test('anonymous Student deep link returns to login and missing bundles return 404', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/quiz`);
  // Mounted Student deliberately delegates login to the shared Portal.
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeVisible();
  const missing = await page.request.get('http://127.0.0.1:43173/study/_expo/static/js/web/missing.js');
  expect(missing.status()).toBe(404);
});

test('Student calculator keeps simple answers compact and supports mixed numbers and exact unit conversion', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  // Complete the Portal -> Student handoff before starting another navigation.
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  // Calculator is independent of lesson generation; open it without a source draft.
  await page.goto(`${sites.portal.origin}/study/learning/math-guide`);
  await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
  const expression = page.getByRole('textbox', { name: 'Phép tính', exact: true });
  await expression.fill('2+3');
  await page.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Xem cách tính', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Nhập hỗn số', exact: true }).click();
  await page.getByRole('textbox', { name: 'Phần nguyên hỗn số', exact: true }).fill('2');
  await page.getByRole('textbox', { name: 'Tử số hỗn số', exact: true }).fill('1');
  await page.getByRole('textbox', { name: 'Mẫu số hỗn số', exact: true }).fill('4');
  await page.getByRole('button', { name: 'Thêm hỗn số vào phép tính', exact: true }).click();
  await expect(expression).toHaveValue('2 1/4');
  await expression.fill('1/3+2/5');
  await page.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Xem cách tính', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Đổi đơn vị', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo cần đổi', exact: true }).fill('15');
  await page.getByRole('button', { name: 'Thêm số đo', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo thêm', exact: true }).fill('25');
  await page.getByRole('button', { name: 'Đơn vị đích: cm', exact: true }).click();
  await page.getByRole('button', { name: 'Chọn m', exact: true }).click();
  await page.getByRole('button', { name: 'Đổi đơn vị ngay', exact: true }).click();
  await expect(page.getByText('15,25 m', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Đổi diện tích', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo cần đổi', exact: true }).fill('2');
  await page.getByRole('button', { name: 'Đổi đơn vị ngay', exact: true }).click();
  await expect(page.getByText('200 dm²', { exact: true })).toBeVisible();
  await page.screenshot({ path: `.local-artifacts/dependency-setup-20261107/calculator-conversion-${test.info().project.name}.png` });
  await page.getByRole('button', { name: 'Tính toán', exact: true }).click();
  await expect(expression).toHaveValue('1/3+2/5');
  await page.getByRole('button', { name: 'Đóng máy tính', exact: true }).click();
  await expect(expression).toHaveCount(0);
});
