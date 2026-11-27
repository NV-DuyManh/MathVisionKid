import { chooseTrainingGrade, expectRaceCameraFramed } from './game-controls.mjs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

async function prepare(page, app, width, height) {
  app.realStudent = true;
  await page.setViewportSize({ width, height });
  await page.addInitScript(() => {
    HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Controlled browser viewport'); };
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.locator('.student-workspace')).toBeVisible();
}

async function inside(page, control) {
  const box = await control.boundingBox();
  const size = page.viewportSize();
  expect(box, 'Control is rendered').not.toBeNull();
  expect(box.x).toBeGreaterThanOrEqual(-1);
  expect(box.y).toBeGreaterThanOrEqual(-1);
  expect(box.x + box.width).toBeLessThanOrEqual(size.width + 1);
  expect(box.y + box.height).toBeLessThanOrEqual(size.height + 1);
}

async function rescueState(page) {
  return page.getByTestId('rescue-screen').evaluate(element => {
    let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
    while (fiber) {
      for (let hook = fiber.memoizedState, i = 0; hook && i < 100; hook = hook.next, i++) {
        // The reducer queue is shared by both Fiber trees, even when a host node
        // still points to the previous tree after a parent render.
        const state = hook.queue?.lastRenderedState ?? hook.memoizedState;
        if (state?.rooms && state?.a && typeof state.revision === 'number') return state;
      }
      fiber = fiber.return;
    }
    return null;
  });
}

const gcd = (a, b) => b ? gcd(b, a % b) : a;
function solve(s) {
  switch (s.phase) {
    case 'reduce-first': return gcd(s.a.num, s.a.den);
    case 'reduce-sum': return gcd(s.sum.num, s.sum.den);
    case 'denominator': return s.a.den * s.b.den / gcd(s.a.den, s.b.den);
    case 'numerator-a': return s.a.num * s.denominator / s.a.den;
    case 'numerator-b': return s.b.num * s.denominator / s.b.den;
    case 'compare': return s.a.num * s.b.den >= s.b.num * s.a.den ? 0 : 1;
    case 'sum': return s.a.num + s.b.num;
    default: throw new Error(`Unexpected question phase: ${s.phase}`);
  }
}

for (const [width, height, mode] of [[1280, 660, 'easy'], [1280, 660, 'medium'], [1280, 660, 'hard'], [1366, 768, 'hard'], [1920, 1080, 'medium']]) {
  test(`planet questions and all answers fit ${width}x${height} in ${mode}`, async ({ page, app, isMobile }, info) => {
    test.skip(isMobile, 'Desktop fit; mobile uses the separate native-style layout.');
    test.setTimeout(150000);
    await prepare(page, app, width, height);
    await page.goto(`${sites.portal.origin}/study/games/planet-rescue`);
    await page.getByTestId(`rescue-mode-${mode}`).click();
    await page.getByTestId('rescue-start').click();
    const mission = page.getByTestId('rescue-mission');
    const next = page.getByTestId('rescue-next');
    await expect(mission).toBeVisible();
    const phases = new Set();
    let completed = 0;
    for (let step = 0; step < 35 && completed < 2; step++) {
      await expect(page.getByTestId('rescue-screen')).toBeVisible();
      let state = await rescueState(page);
      expect(state).not.toBeNull();
      const card = state.phase.startsWith('reduce') ? 'simplify' : state.phase === 'ready' ? 'cannon' : 'common';
      if (state.selected !== card) {
        const cardControl = page.getByTestId(`rescue-card-${card}`);
        await inside(page, cardControl);
        await cardControl.click();
        await expect.poll(async () => (await rescueState(page))?.selected).toBe(card);
        state = await rescueState(page);
      }
      if (state.phase === 'ready') {
        const fire = page.getByTestId('rescue-fire');
        await inside(page, fire);
        await fire.click();
        await expect(next).toBeVisible({ timeout: 15000 });
        await inside(page, next);
        await next.click();
        const planet = String(completed + 2).padStart(2, '0');
        await expect(mission).toContainText(`HÀNH TINH ${planet} /`, { timeout: 15000 });
        completed++;
        continue;
      }
      phases.add(state.phase);
      // Check bounds before clicking: auto-scroll must not hide an unreachable answer.
      await inside(page, page.getByTestId('rescue-phase'));
      const answers = page.locator('[data-testid^="rescue-answer-"]');
      await expect(answers).not.toHaveCount(0);
      for (const answer of await answers.all()) await inside(page, answer);
      if (phases.size === 1) await page.screenshot({ path: info.outputPath(`planet-${mode}-question.png`) });
      await page.getByTestId(`rescue-answer-${solve(state)}`).click();
      await expect.poll(async () => (await rescueState(page))?.revision).toBeGreaterThan(state.revision);
    }
    expect(completed).toBe(2);
    if (mode === 'hard') for (const phase of ['reduce-first', 'denominator', 'numerator-a', 'numerator-b', 'compare', 'sum', 'reduce-sum']) expect(phases.has(phase), phase).toBe(true);
    await page.getByTestId('rescue-pause').click();
    await expect(page.getByTestId('rescue-menu')).toBeVisible();
  });
}

test('Planet resize preserves the run and restores visible desktop answers', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Explicit browser reflow through desktop and phone widths.');
  test.setTimeout(60000);
  await prepare(page, app, 1280, 660);
  await page.goto(`${sites.portal.origin}/study/games/planet-rescue`);
  await page.getByTestId('rescue-start').click();
  const options = page.getByTestId('rescue-options');
  await expect(options).toHaveCSS('display', 'grid');
  const before = await rescueState(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByTestId('rescue-screen')).toBeVisible();
  await expect(page.getByTestId('rescue-page')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Thẻ Rút Gọn/ })).toBeVisible();
  const phone = await rescueState(page);
  expect([phone.session, phone.index, phone.phase, phone.score]).toEqual([before.session, before.index, before.phase, before.score]);
  await page.screenshot({ path: info.outputPath('planet-phone-reflow.png') });
  await page.setViewportSize({ width: 1280, height: 660 });
  await expect(options).toHaveCSS('display', 'grid');
  for (const answer of await page.locator('[data-testid^="rescue-answer-"]').all()) await inside(page, answer);
  const restored = await rescueState(page);
  expect([restored.session, restored.index, restored.phase, restored.score]).toEqual([before.session, before.index, before.phase, before.score]);
});

test('Race and Terrain use themed backgrounds and preserve desktop controls', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop background only.');
  test.setTimeout(90000);
  await prepare(page, app, 1280, 660);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  await chooseTrainingGrade(page,'race-to-finish');
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  expect(await page.getByTestId('game-camera').evaluate(el => getComputedStyle(el).backgroundImage)).toContain('gradient');
  await expectRaceCameraFramed(page);
  await inside(page, page.getByTestId('roll-dice-button'));
  await page.screenshot({ path: info.outputPath('race-wood-backdrop.png') });
  await page.goto(`${sites.portal.origin}/study/games/terrain-racing`);
  await chooseTrainingGrade(page,'terrain-racing');
  await expect(page.getByTestId('supercar-question')).toBeVisible({ timeout: 20000 });
  expect(await page.locator('[data-game="terrain-racing"]').evaluate(el => getComputedStyle(el).backgroundImage)).toContain('gradient');
  for (const answer of await page.locator('[data-testid^="supercar-answer-"]').all()) await inside(page, answer);
  await page.screenshot({ path: info.outputPath('terrain-pit-backdrop.png') });
  await page.getByTestId('supercar-pause').click();
  await expect(page.getByTestId('supercar-resume')).toBeVisible();
  await page.getByTestId('supercar-resume').click();
});
