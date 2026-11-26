import { test, expect, sites, login } from '../browser/fixtures.mjs';

for (const width of [1280,1366,1440,1920,390]) test(`game catalog uses the available width at ${width}px`, async ({ page, app, isMobile }, info) => {
  test.skip(isMobile !== (width < 768), 'Use the corresponding desktop/touch input.');
  app.realStudent = true;
  await page.setViewportSize({ width, height: width < 768 ? 844 : 900 });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/games`);
  const cards = page.locator('[data-testid^="training-card-"]');
  await expect(cards).toHaveCount(5);
  if (width >= 768) {
    const heading = await page.getByRole('heading', { name: 'Khu trò chơi toán học', exact: true }).boundingBox();
    const grid = page.locator('[data-student-game-grid]');
    const box = await grid.boundingBox();
    expect(Math.abs(box.x + box.width - heading.x - heading.width), 'The grid must reach the same right edge as the page header').toBeLessThan(2);
    const layout = await grid.evaluate(element => {
      const style = getComputedStyle(element);
      return { width: element.clientWidth, gap: parseFloat(style.columnGap), columns: style.gridTemplateColumns.split(' ').length };
    });
    const expected = Math.max(1, Math.floor((layout.width + layout.gap) / (240 + layout.gap)));
    expect(layout.columns).toBe(expected);
    expect(expected).toBeGreaterThanOrEqual(3);
    const boxes = await cards.evaluateAll(elements => elements.map(element => ({ top: element.getBoundingClientRect().top })));
    expect(boxes.filter(rect => Math.abs(rect.top - boxes[0].top) < 2)).toHaveLength(Math.min(5,expected));
    await page.getByRole('button', { name: 'Phân số', exact: true }).click();
    await expect(cards).toHaveCount(2);
    await page.getByRole('button', { name: 'Tất cả', exact: true }).click();
    await expect(cards).toHaveCount(5);
  } else {
    const first = await cards.nth(0).boundingBox(), second = await cards.nth(1).boundingBox();
    expect(second.y).toBeGreaterThan(first.y);
    expect(Math.abs(first.x - second.x)).toBeLessThan(2);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await cards.first().scrollIntoViewIfNeeded();
  await info.attach('catalog grid', { body: await page.screenshot({ path: info.outputPath('catalog.png') }), contentType: 'image/png' });
});
