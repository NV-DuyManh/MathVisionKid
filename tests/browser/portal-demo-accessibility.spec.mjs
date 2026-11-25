import { test, expect, sites } from './fixtures.mjs';

test('Portal grade selectors and demo calculation activate with keyboard navigation', async ({ page, app }) => {
  await page.goto(sites.portal.origin);
  const grade3 = page.getByRole('button', { name: 'Lớp 3', exact: true });
  await expect(grade3).toBeVisible();

  // Test selecting Grade 2
  const grade2 = page.getByRole('button', { name: 'Lớp 2', exact: true });
  await grade2.focus();
  await page.keyboard.press('Enter');
  await expect(grade2).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('Lớp 2B')).toBeVisible();

  // Test selecting Grade 4 via click
  const grade4 = page.getByRole('button', { name: 'Lớp 4', exact: true });
  await grade4.click();
  await expect(grade4).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('Lớp 4C')).toBeVisible();

  // Test child answer button activation via keyboard
  const answerBtn = page.getByRole('button', { name: /Con trả lời:/ });
  await expect(answerBtn).toBeVisible();
  await answerBtn.focus();
  await page.keyboard.press('Space');
  await expect(page.getByRole('button', { name: '✓ Đã kiểm tra lại' })).toBeVisible();
});

test('Portal socratic method and philosophy sections are keyboard accessible and navigate to login', async ({ page, app }) => {
  await page.goto(sites.portal.origin);
  const socraticSection = page.locator('#phuong-phap');
  await expect(socraticSection).toBeVisible();

  // Test CTA button activates and navigates to login
  const ctaLogin = page.getByRole('button', { name: 'Tiếp tục với Google' });
  await expect(ctaLogin).toBeVisible();
  await ctaLogin.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
});
