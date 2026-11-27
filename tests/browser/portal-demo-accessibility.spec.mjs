import { test, expect, sites } from './fixtures.mjs';

test('Portal has a single main landmark, working skip link, and accessible grade contrast', async ({ page, app }) => {
  void app;
  await page.goto(sites.portal.origin);

  // Single <main> landmark and skip link focus
  await expect(page.getByRole('main')).toHaveCount(1);
  const skipLink = page.getByRole('link', { name: 'Đến nội dung chính' });
  await skipLink.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#main-content')).toBeFocused();

  // Check WCAG AA contrast (>= 4.5:1) on all 5 grade buttons on desktop & mobile viewports
  for (const viewport of [
    { width: 1280, height: 800 },
    { width: 375, height: 812 },
  ]) {
    await page.setViewportSize(viewport);
    for (const grade of [1, 2, 3, 4, 5]) {
      const btn = page.getByRole('button', { name: `Lớp ${grade}`, exact: true });
      await expect(btn).toBeVisible();
      const contrast = await btn.evaluate((el) => {
        const parseRgb = (str) => {
          const m = str.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
          return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : [0, 0, 0];
        };
        const luminance = ([r, g, b]) => {
          const toLin = (c) => {
            const s = c / 255;
            return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
          };
          return 0.2126 * toLin(r) + 0.7152 * toLin(g) + 0.0722 * toLin(b);
        };
        const style = window.getComputedStyle(el);
        const l1 = luminance(parseRgb(style.color));
        const l2 = luminance(parseRgb(style.backgroundColor));
        return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      });
      expect(contrast, `Grade ${grade} contrast at ${viewport.width}px`).toBeGreaterThanOrEqual(4.5);
    }
  }
});

test('Portal grade selectors and demo calculation activate with keyboard navigation and show corrected result', async ({ page, app }) => {
  void app;
  await page.goto(sites.portal.origin);
  const grade3 = page.getByRole('button', { name: 'Lớp 3', exact: true });
  await expect(grade3).toBeVisible();
  await expect(grade3).toHaveAttribute('aria-pressed', 'true');

  // Grade 3 initially highlights units column (col 2: 5 + 8) rather than tens column (col 1)
  await expect(page.getByTestId('demo-row1-col-2')).toHaveAttribute('data-active', 'true');
  await expect(page.getByTestId('demo-row1-col-1')).toHaveAttribute('data-active', 'false');
  await expect(page.getByTestId('demo-result-col-1')).toHaveText('1');

  // Activate answer in Grade 3 -> updates active column to col 1, shows corrected 423 and historical note
  const grade3AnswerBtn = page.getByRole('button', { name: /Con trả lời: 5 \+ 8 = 13/ });
  await grade3AnswerBtn.focus();
  await page.keyboard.press('Space');
  await expect(page.getByRole('button', { name: '↺ Xem lại bài làm ban đầu' })).toBeVisible();
  await expect(page.getByTestId('demo-row1-col-1')).toHaveAttribute('data-active', 'true');
  await expect(page.getByTestId('demo-result-col-1')).toHaveText('2');
  await expect(page.getByText('(Bài làm ban đầu: 413 → Đã sửa: 423)')).toBeVisible();

  // Test selecting Grade 2 resets answered state and updates active grade
  const grade2 = page.getByRole('button', { name: 'Lớp 2', exact: true });
  await grade2.focus();
  await page.keyboard.press('Enter');
  await expect(grade2).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('Lớp 2B')).toBeVisible();
  await expect(page.getByRole('button', { name: /Con trả lời:/ })).toBeVisible();

  // Test selecting Grade 4 via click
  const grade4 = page.getByRole('button', { name: 'Lớp 4', exact: true });
  await grade4.click();
  await expect(grade4).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByText('Lớp 4C')).toBeVisible();
});

test('Portal socratic method and philosophy sections are keyboard accessible and navigate to login without unsupported social promises', async ({ page, app }) => {
  void app;
  await page.goto(sites.portal.origin);
  const socraticSection = page.locator('#phuong-phap');
  await expect(socraticSection).toBeVisible();

  await expect(page.getByRole('link', { name: 'Tiếp tục với Facebook' })).toHaveCount(0);

  // Test CTA button activates and navigates to login
  const ctaLogin = page.getByRole('link', { name: 'Đăng nhập', exact: true }).last();
  await expect(ctaLogin).toBeVisible();
  await ctaLogin.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
});
