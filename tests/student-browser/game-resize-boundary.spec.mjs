import { expectTrainingGameReady } from './game-controls.mjs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

async function prepare(page, app, width, height) {
  app.realStudent = true;
  await page.setViewportSize({ width, height });
  await page.addInitScript(() => { HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Controlled viewport'); }; });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.locator('.student-workspace')).toBeVisible();
}
async function cameraFits(page) {
  const box = await page.getByTestId('game-camera').boundingBox(), size = page.viewportSize();
  return !!box && box.x >= -1 && box.y >= -1 && box.x + box.width <= size.width + 1 && box.y + box.height <= size.height + 1;
}
test('fine-pointer Terrain keeps its proportional stage through 999 and 1000px', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop pointer regression; touch viewport matrix runs separately.');
  test.setTimeout(60000);
  await prepare(page, app, 1100, 720);
  await page.goto(`${sites.portal.origin}/study/games/terrain-racing`);
  await expectTrainingGameReady(page,'terrain-racing');
  await expect(page.getByTestId('supercar-question')).toBeVisible({ timeout: 20000 });
  const stage = page.locator('[data-testid^="supercar-state-"]');
  for (const width of [1001, 1000, 999, 990, 1100]) {
    await page.setViewportSize({ width, height: 720 });
    await expect.poll(async () => (await stage.boundingBox())?.width).toBeCloseTo(720 * 540 / 970, 0);
    expect(await page.locator('[data-game="terrain-racing"]').evaluate(el => getComputedStyle(el).backgroundImage)).toContain('gradient');
    await expect(page.getByTestId('supercar-question')).toBeVisible();
  }
  await page.screenshot({ path: info.outputPath('terrain-resize.png') });
});
test('fine-pointer Race keeps the camera viewport through 999 and 1000px', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop pointer regression.'); test.setTimeout(60000);
  await prepare(page, app, 1100, 720);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  await expectTrainingGameReady(page,'race-to-finish');
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  for (const width of [1001, 1000, 999, 990, 1100]) {
    await page.setViewportSize({ width, height: 720 });
    await expect.poll(() => cameraFits(page)).toBe(true);
    expect(await page.getByTestId('game-camera').evaluate(el => getComputedStyle(el).backgroundImage)).toContain('gradient');
    await expect(page.getByTestId('roll-dice-button')).toBeEnabled();
  }
  await page.screenshot({ path: info.outputPath('race-boundary.png') });
});
test('Race drag then shrink reconciles the camera viewport without restarting its live turn', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop pointer regression.'); test.setTimeout(60000);
  await prepare(page, app, 1440, 900);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  await expectTrainingGameReady(page,'race-to-finish');
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  const tokens = await page.locator('[data-testid^="token-"]').count();
  await page.mouse.move(700, 450); await page.mouse.down();
  await page.mouse.move(850, 480, { steps: 8 }); await page.mouse.up();
  await page.setViewportSize({ width: 1280, height: 720 });
  await expect.poll(() => cameraFits(page)).toBe(true);
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled();
  expect(await page.locator('[data-testid^="token-"]').count()).toBe(tokens);
  await page.screenshot({ path: info.outputPath('race-pan-shrink.png') });
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByTestId('math-prompt')).toBeVisible({ timeout: 15000 });
});
