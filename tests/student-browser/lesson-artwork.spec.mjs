import { readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { test, expect, sites, profile } from '../browser/fixtures.mjs';

const curriculum = JSON.parse(readFileSync(new URL('../../apps/student-mobile/src/data/primaryMathCurriculumData.json', import.meta.url), 'utf8'));
const inventory = JSON.parse(readFileSync(new URL('../../apps/student-mobile/src/features/lesson-artwork/lessonArtworkInventory.json', import.meta.url), 'utf8'));

for (const grade of [1, 2, 3, 4, 5]) {
  test(`grade ${grade} loads twenty distinct lesson artworks from their stable IDs`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.route('**/api/v1/me', route => route.fulfill({ json: {
      ...profile('STUDENT'), userId: '550e8400-e29b-41d4-a716-446655440000', gradeLevel: grade,
    } }));
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${sites.portal.origin}/study/login`);
    await page.getByRole('textbox', { name: 'Email', exact: true }).fill('student@example.test');
    await page.getByRole('textbox', { name: 'Mật khẩu', exact: true }).fill('synthetic-password');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/lessons`);
    const cards = page.getByRole('button', { name: /^Mở bài: / });
    await expect(cards).toHaveCount(20);
    const images = cards.locator('img');
    await expect(images).toHaveCount(20);
    await expect.poll(() => images.evaluateAll(items => items.every(item => item.complete && item.naturalWidth > 0))).toBe(true);
    expect(await images.evaluateAll(items => new Set(items.map(item => item.src)).size)).toBe(20);
    for (const lesson of curriculum.filter(item => item.grade === grade)) {
      const artwork = inventory[lesson.id];
      expect(artwork.status).toBe('GENERATED_REVIEWED');
      const stem = basename(artwork.assetPath, '.webp');
      await expect(page.getByRole('button', { name: `Mở bài: ${lesson.title}`, exact: true }).locator('img')).toHaveAttribute('src', new RegExp(`${stem}[^/]*\\.webp`));
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
    await page.screenshot({ path: testInfo.outputPath(`grade-${grade}-artworks.png`) });
  });
}
