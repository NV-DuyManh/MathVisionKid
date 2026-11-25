import { test, expect, sites } from './fixtures.mjs';

test('Portal demo tabs connect their keyboard navigation to the visible lesson', async ({ page, app }) => {
  await page.goto(sites.portal.origin);
  const tablist = page.getByRole('tablist', { name: 'Chế độ xem thực nghiệm số học ô ly' });
  const notebook = tablist.getByRole('tab', { name: '1. Trang vở ô ly' });
  const recognition = tablist.getByRole('tab', { name: '2. AI nhận diện' });
  await expect(page.getByRole('tabpanel', { name: '1. Trang vở ô ly' })).toBeVisible();
  await notebook.focus();
  await page.keyboard.press('ArrowRight');
  await expect(recognition).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(recognition).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('tabpanel', { name: '2. AI nhận diện' })).toBeVisible();
  await expect(page.getByRole('tabpanel')).toHaveCount(1);
  const grade = page.getByRole('button', { name: 'Lớp 1–2', exact: true });
  await grade.click();
  await expect(grade).toHaveAttribute('aria-pressed', 'true');
});

test('Portal workflow cards and progress buttons activate without a mouse', async ({ page, app }) => {
  await page.goto(sites.portal.origin);
  const workflow = page.locator('#socratic');
  const step = workflow.getByRole('button', { name: /^02\. Bóc tách nét chữ viết tay/ });
  await step.focus();
  await page.keyboard.press('Enter');
  await expect(step).toHaveAttribute('aria-pressed', 'true');
  await expect(workflow.getByText('CHI TIẾT TRẢI NGHIỆM · BƯỚC 02', { exact: true })).toBeVisible();
  const progress = workflow.getByRole('button', { name: 'Xem bước 3' });
  expect(await progress.evaluate(button => button.getBoundingClientRect().height)).toBeGreaterThanOrEqual(24);
  await progress.focus();
  await page.keyboard.press('Space');
  await expect(progress).toHaveAttribute('aria-pressed', 'true');
  await expect(workflow.getByText('CHI TIẾT TRẢI NGHIỆM · BƯỚC 03', { exact: true })).toBeVisible();
});
