import { test, expect, sites, login } from '../browser/fixtures.mjs';

const desktopSizes = [[1280, 720], [1366, 768], [1440, 900], [1920, 1080], [2560, 1440]];
// CSS viewport equivalents for a 1280x720 window at 125% and 80% zoom.
// These exercise reflow, not Chromium's browser-chrome zoom setting.
const zoomReflowSizes = [[1024, 576], [1600, 900]];
const mobileSizes = [[375, 812], [390, 844], [430, 932], [768, 1024]];

async function prepare(page, app) {
  app.realStudent = true;
  app.gameAssetFailures = [];
  page.on('response', response => {
    if (response.status() >= 400 && /\/study\/(?:assets|_expo)\//.test(response.url())) {
      app.gameAssetFailures.push(`${response.status()} ${new URL(response.url()).pathname}`);
    }
  });
  await page.addInitScript(() => {
    HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Viewport controlled by the browser test'); };
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.locator('.student-workspace')).toBeVisible();
}

test('terrain answers, loss, replay, five stages, pause, resize and exit preserve the live session', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'The viewport matrix covers touch framing.');
  test.setTimeout(180000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await prepare(page, app);
  await open(page, 'terrain-racing');
  const question = page.getByTestId('supercar-question');
  const speed = async () => {
    await expect(question).toBeVisible({ timeout: 15000 });
    const text = await question.innerText();
    const values = text.match(/Quãng đường\s*(\d+)\s*m\s*Thời gian\s*(\d+)\s*s/);
    expect(values, 'The visible distance and time define the answer').not.toBeNull();
    return Number(values[1]) / Number(values[2]);
  };
  const correct = await speed();
  const wrong = page.locator('[data-testid^="supercar-answer-"]').filter({ hasNot: page.getByText(`${correct} m/s`, { exact: true }) }).first();
  await wrong.click();
  await expect(page.getByTestId('supercar-loss')).toBeVisible({ timeout: 15000 });
  await inside(page, page.getByTestId('supercar-replay'));
  await capture(page, info, 'terrain-loss');
  await page.getByTestId('supercar-replay').click();
  for (let stage = 1; stage <= 5; stage++) {
    const answer = await speed();
    await expect(page.getByTestId('supercar-stage')).toHaveText(`Chặng ${stage}/5`);
    if (stage === 1) {
      const state = await page.locator('[data-testid^="supercar-state-"]').getAttribute('data-testid');
      await page.getByTestId('supercar-pause').click();
      await expect(page.getByTestId('supercar-resume')).toBeVisible();
      const hero = await page.getByTestId('supercar-hero').boundingBox();
      await page.waitForTimeout(300); // Observe a frozen animation across real frames.
      const pausedHero = await page.getByTestId('supercar-hero').boundingBox();
      expect(hero).not.toBeNull();
      expect(pausedHero).not.toBeNull();
      for (const key of ['x', 'y', 'width', 'height']) expect(Math.abs(hero[key] - pausedHero[key])).toBeLessThan(0.5);
      const player = page.getByTestId('training-player-terrain-racing');
      for (const width of [1001, 1000, 999, 990, 1280]) {
        await page.setViewportSize({ width, height: 720 });
        await expect.poll(async () => {
          const box = await player.boundingBox();
          return box ? box.width / box.height : Number.POSITIVE_INFINITY;
        }).toBeLessThan(.8);
        await inside(page, page.getByTestId('supercar-resume'));
      }
      await page.getByTestId('supercar-resume').click();
      await expect(page.locator('[data-testid^="supercar-state-"]')).toHaveAttribute('data-testid', state);
    }
    await page.getByTestId(`supercar-answer-${answer}`).click();
    await expect(question).toBeHidden();
  }
  await expect(page.getByTestId('supercar-victory')).toBeVisible({ timeout: 20000 });
  await capture(page, info, 'terrain-victory');
  await page.getByTestId('supercar-replay').click();
  await expect(page.getByTestId('supercar-stage')).toHaveText('Chặng 1/5');
  await page.getByTestId('supercar-pause').click();
  await page.getByTestId('supercar-exit').click();
  await expect(page.getByTestId('training-play-terrain-racing')).toBeVisible();
  await expect.poll(() => page.locator('img').evaluateAll(images => images.every(image => image.complete))).toBe(true);
  await open(page, 'terrain-racing');
  await expect(page.getByTestId('supercar-question')).toBeVisible({ timeout: 15000 });
  expect(app.gameAssetFailures).toEqual([]);
});

// Observe the mounted reducer without writing its state or adding a test API to
// production. All construction still uses the real pointer controls and checks.
async function islandState(page) {
  return page.getByTestId('island-screen').evaluate(element => {
    let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
    let root = fiber;
    while (root?.return) root = root.return;
    if (root?.stateNode?.current !== root && fiber?.alternate) fiber = fiber.alternate;
    while (fiber) {
      for (let hook = fiber.memoizedState, i = 0; hook && i < 100; hook = hook.next, i++) {
        const state = hook.memoizedState;
        if (state?.quests && state?.blocks && typeof state.index === 'number') return state;
      }
      fiber = fiber.return;
    }
    return null;
  });
}

async function raceState(page) {
  return page.locator('[data-testid^="token-"]').first().evaluate(element => {
    let fiber = element[Object.keys(element).find(key => key.startsWith('__reactFiber$'))];
    while (fiber) {
      for (let hook = fiber.memoizedState, i = 0; hook && i < 100; hook = hook.next, i++) {
        const value = hook.memoizedState;
        if (typeof value?.getSnapshot === 'function' && typeof value?.startGame === 'function') return value.getSnapshot();
      }
      fiber = fiber.return;
    }
    return null;
  });
}

test('race supports wrong and correct answers, turn handover, victory, replay and resized question overlays', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Touch orientation and question layout run in the viewport matrix.');
  test.setTimeout(300000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => { Math.random = () => 1 / 0xffffffff; });
  await prepare(page, app);
  await open(page, 'race-to-finish');
  await page.getByText('Chơi cùng bạn', { exact: true }).click();
  await page.getByText('2 Người chơi', { exact: true }).click();
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  const camera = page.getByTestId('game-camera');
  const world = page.getByTestId('camera-world');
  const frame = await camera.boundingBox();
  expect(frame).not.toBeNull();
  await page.mouse.move(frame.x + frame.width / 2, frame.y + frame.height / 2);
  await page.mouse.down();
  await page.mouse.move(frame.x + frame.width / 2 + 120, frame.y + frame.height / 2 + 40, { steps: 10 });
  await page.mouse.up();
  for (const width of [1001, 1000, 999, 990, 1440]) {
    await page.setViewportSize({ width, height: 720 });
    await expect.poll(async () => {
      const [viewport, content] = await Promise.all([camera.boundingBox(), world.boundingBox()]);
      if (!viewport || !content) return Number.POSITIVE_INFINITY;
      return Math.max(Math.abs(viewport.width - content.width), Math.abs(viewport.height - content.height));
    }).toBeLessThan(2);
    await inside(page, page.getByTestId('roll-dice-button'));
    if (width === 999) await capture(page, info, 'race-overview-999');
  }
  let wrongVerified = false;
  for (let turn = 0; turn < 70; turn++) {
    await expect.poll(async () => (await raceState(page))?.gamePhase, { timeout: 20000 })
      .toMatch(/^(ready_to_roll|turn_handover|finished)$/);
    let state = await raceState(page);
    if (state.gamePhase === 'finished') break;
    if (state.gamePhase === 'turn_handover') await page.getByText('🎲 SẴN SÀNG ĐỔ XÚC XẮC', { exact: true }).click();
    await page.getByTestId('roll-dice-button').click();
    await expect(page.getByTestId('math-prompt')).toBeVisible({ timeout: 15000 });
    state = await raceState(page);
    const question = state.question;
    expect(question).not.toBeNull();
    const correct = typeof question.answer === 'object' ? `${question.answer.n}/${question.answer.d}` : String(question.answer);
    if (!wrongVerified) {
      await page.getByTestId('race-modal-host').getByTestId('race-pause').click();
      await page.setViewportSize({ width: 1280, height: 720 });
      await inside(page, page.getByTestId('race-resume'));
      await page.getByTestId('race-resume').click();
      expect((await raceState(page)).actionId).toBe(state.actionId);
    }
    if (question.choices) {
      const answer = !wrongVerified ? question.choices.find(choice => choice !== correct) : correct;
      await page.getByTestId('math-feedback-layer').getByText(answer, { exact: true }).click();
    } else {
      await page.getByTestId('math-answer-input').fill(!wrongVerified ? '-999999' : correct);
      await page.getByTestId('math-submit').click();
    }
    if (!wrongVerified) {
      await expect(page.getByTestId('math-understood')).toBeVisible();
      await inside(page, page.getByTestId('math-understood'));
      await capture(page, info, 'race-wrong-feedback');
      await page.getByTestId('math-understood').click();
      wrongVerified = true;
    }
    await expect(page.getByTestId('math-prompt')).toBeHidden();
  }
  await expect(page.getByTestId('victory-exit')).toBeVisible();
  await capture(page, info, 'race-victory');
  await page.getByText('🔄 Chơi Lại Trận Mới', { exact: true }).click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  await page.getByTestId('race-pause').click();
  await page.getByTestId('race-exit').click();
  await expect(page.getByTestId('training-play-race-to-finish')).toBeVisible();
  await expect.poll(() => page.locator('img').evaluateAll(images => images.every(image => image.complete))).toBe(true);
  await open(page, 'race-to-finish');
  await expect(page.getByTestId('start-race-button')).toBeEnabled();
  expect(app.gameAssetFailures).toEqual([]);
});

test('island pointer construction completes six missions and preserves blocks through resize and reopening', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop pointer interaction; touch framing runs in the matrix.');
  test.setTimeout(180000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await prepare(page, app);
  await open(page, 'block-island');
  await page.getByTestId('island-mode-medium').click();
  await page.getByTestId('island-start').click();
  await page.getByTestId('island-confirm-new').click();
  await page.getByTestId('island-check').click();
  await expect(page.getByTestId('island-feedback')).not.toHaveText('');
  const entities = page.getByTestId('island-play').locator('[data-testid^="island-entity-"]');
  for (let mission = 0; mission < 6; mission++) {
    await page.getByTestId('island-hint').click();
    await expect.poll(async () => (await islandState(page))?.hint?.target?.length ?? 0).toBeGreaterThan(0);
    const state = await islandState(page);
    expect(state?.index).toBe(mission);
    expect(state.hint).not.toBeNull();
    const additions = state.hint.target.filter(point => !state.blocks.some(block =>
      block.blockType === 'floor' && point.x === block.x && point.y === block.y && point.floorIndex === block.floorIndex));
    for (const point of additions) {
      // Camera interpolation uses the live viewport size. Wait for the painted
      // camera to settle after hints/resize before targeting a world coordinate.
      let previous, stable = 0;
      await expect.poll(async () => {
        const transform = await page.getByTestId('island-scene').evaluate(element => getComputedStyle(element).transform);
        stable = transform === previous ? stable + 1 : 0;
        previous = transform;
        return stable;
      }).toBeGreaterThanOrEqual(2);
      const scene = await page.getByTestId('island-scene').boundingBox();
      const x = scene.x + (720 + (point.x - point.y) * 24) * scene.width / 1440;
      const y = scene.y + (100 + (point.x + point.y + 1) * 14) * scene.height / 980;
      const before = await entities.count();
      await page.mouse.click(x, y);
      await expect(entities).toHaveCount(before + 1);
      await expect(page.getByTestId(`island-entity-floor:${point.floorIndex}:${point.x},${point.y}`)).toBeAttached();
    }
    if (mission === 0) {
      const before = (await islandState(page)).blocks;
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.getByTestId('island-pause').click();
      await page.getByTestId('island-resume').click();
      expect((await islandState(page)).blocks).toEqual(before);
    }
    await page.getByTestId('island-check').click();
    await expect(page.getByTestId(mission < 5 ? 'island-next' : 'island-show-result')).toBeVisible();
    if (mission < 5) await page.getByTestId('island-next').click();
  }
  await page.getByTestId('island-show-result').click();
  await inside(page, page.getByTestId('island-result-score'));
  await capture(page, info, 'island-complete');
  await page.getByTestId('island-result-back').click();
  const completed = (await islandState(page)).blocks;
  await page.getByTestId('island-exit').click();
  await expect(page.getByTestId('training-play-block-island')).toBeVisible();
  await expect.poll(() => page.locator('img').evaluateAll(images => images.every(image => image.complete))).toBe(true);
  await open(page, 'block-island');
  await page.getByTestId('island-mode-medium').click();
  await page.getByTestId('island-continue').click();
  expect((await islandState(page)).blocks).toEqual(completed);
  await page.getByTestId('island-pause').click();
  await page.getByTestId('island-restart').click();
  await page.getByTestId('island-confirm-new').click();
  expect((await islandState(page)).blocks).toEqual([]);
  expect(app.gameAssetFailures).toEqual([]);
});

async function open(page, game) {
  const player = page.getByTestId(`training-player-${game}`);
  if (!await player.isVisible()) {
    const play = page.getByTestId(`training-play-${game}`);
    if (await play.isVisible()) await play.click();
    else await page.goto(`${sites.portal.origin}/study/games/${game}`);
  }
  await expect(player).toBeVisible();
  expect(await page.evaluate(() => Number(getComputedStyle(document.documentElement).zoom))).toBe(1);
}

async function inside(page, locator) {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox(), viewport = page.viewportSize();
  expect(box.x).toBeGreaterThanOrEqual(-1);
  expect(box.y).toBeGreaterThanOrEqual(-1);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width + 1);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 1);
}

async function capture(page, info, name) {
  await info.attach(name, { body: await page.screenshot({ path: info.outputPath(`${name}.png`) }), contentType: 'image/png' });
}

for (const [width, height] of [...desktopSizes, ...zoomReflowSizes, ...mobileSizes]) {
  test(`training games retain usable framing at ${width}x${height}`, async ({ page, app, isMobile }, info) => {
    test.skip(isMobile !== (width < 1000), 'Each viewport runs with its corresponding input policy.');
    test.setTimeout(90000);
    await page.setViewportSize({ width, height });
    await prepare(page, app);

    await open(page, 'block-island');
    await expect(page.getByTestId('island-start')).toBeEnabled();
    await capture(page, info, 'island-intro');
    const introBoard = await page.getByTestId('island-board').boundingBox();
    expect.soft(introBoard.height, 'Island illustration must use the available height').toBeGreaterThan(150);
    await page.getByTestId('island-start').click();
    await page.getByTestId('island-confirm-new').click();
    await inside(page, page.getByTestId('island-world-frame'));
    await inside(page, page.getByTestId('island-control-dock'));
    await capture(page, info, 'island-play');
    await page.getByTestId('island-pause').click();
    await inside(page, page.getByTestId('island-resume'));
    await page.getByTestId('island-resume').click();
    await page.getByTestId('island-exit').click();
    await expect(page.getByTestId('training-play-block-island')).toBeVisible();
    await expect.poll(() => page.evaluate(() => Number(getComputedStyle(document.documentElement).zoom)))
      .toBe(!isMobile && width >= 1100 ? 1.07 : 1);
    await expect.poll(() => page.locator('img').evaluateAll(images => images.every(image => image.complete))).toBe(true);

    await open(page, 'terrain-racing');
    await expect(page.getByTestId('supercar-question')).toBeVisible({ timeout: 15000 });
    await inside(page, page.getByTestId('supercar-pause'));
    for (const answer of await page.locator('[data-testid^="supercar-answer-"]').all()) await inside(page, answer);
    await capture(page, info, 'terrain-question');
    const player = await page.getByTestId('training-player-terrain-racing').boundingBox();
    if (!isMobile) expect.soft(player.width / player.height, 'Portrait world must not stretch across desktop').toBeLessThan(.8);
    await page.getByTestId('supercar-pause').click();
    await inside(page, page.getByTestId('supercar-resume'));
    await page.getByTestId('supercar-resume').click();
    await expect(page.getByTestId('supercar-question')).toBeVisible();
    await page.getByTestId('supercar-pause').click();
    await page.getByTestId('supercar-exit').click();
    await expect(page.getByTestId('training-play-terrain-racing')).toBeVisible();

    if (width < 700) {
      await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
      await expect(page.getByRole('button', { name: 'Về danh sách trò chơi', exact: true })).toBeVisible();
      await page.setViewportSize({ width: height, height: width });
    } else if (isMobile) {
      await page.setViewportSize({ width: height, height: width });
    }
    await open(page, 'race-to-finish');
    await expect(page.getByTestId('start-race-button')).toBeEnabled();
    await inside(page, page.getByTestId('start-race-button'));
    await page.getByTestId('start-race-button').click();
    await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
    await capture(page, info, 'race-board');
    if (!isMobile) await inside(page, page.getByTestId('race-board'));
    await page.getByTestId('race-pause').click();
    await inside(page, page.getByTestId('race-resume'));
    await page.getByTestId('race-resume').click();
    await page.getByTestId('roll-dice-button').click();
    await expect(page.getByTestId('math-prompt')).toBeVisible({ timeout: 15000 });
    await inside(page, page.getByTestId('math-prompt'));
    if (await page.getByTestId('math-answer-input').isVisible()) {
      await inside(page, page.getByTestId('math-answer-input'));
      await inside(page, page.getByTestId('math-submit'));
    } else {
      for (const choice of await page.getByTestId('math-feedback-layer').getByRole('button').all()) await inside(page, choice);
    }
    await capture(page, info, 'race-question');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(app.gameAssetFailures).toEqual([]);
  });
}
