import { test, expect, sites, login } from '../browser/fixtures.mjs';
import { raceState } from './game-controls.mjs';

async function open(page, app, game, grade) {
  app.realStudent = true;
  await page.addInitScript(() => { HTMLElement.prototype.requestFullscreen = async () => { throw Error('Controlled viewport'); }; });
  await login(page, 'STUDENT');
  await expect(page.getByRole('heading', { name: 'Tiện ích nhanh', exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/games/${game}`);
  await page.getByRole('button', { name: `Lớp ${grade}`, exact: true }).click();
  await page.getByTestId('game-grade-start').click();
}

for (const [seed, comparison] of [[1, false], [2, true]]) test(
  `desktop Race intro, grade 5 and bot names with ${comparison ? 'a comparison' : 'a typed answer'}`, async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop camera; lower-grade rendering is checked separately.');
  test.setTimeout(90000);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.addInitScript(value => { Math.random = () => (value + 0.5) / 0xffffffff; }, seed);
  await open(page, app, 'race-to-finish', 5);
  await page.getByText('2 Người chơi', { exact: true }).click();
  await expect(page.getByTestId('race-setup-name-1')).toHaveValue('Cánh Cụt');
  await page.getByTestId('race-setup-name-1').fill('Bạn Cụt');
  await page.getByTestId('start-race-button').click();
  await page.getByTestId('camera-world').waitFor();
  const scales = await page.getByTestId('camera-world').evaluate(el => new Promise(resolve => {
    const values = [], start = performance.now();
    function sample() {
      values.push(new DOMMatrixReadOnly(getComputedStyle(el).transform).a);
      if (performance.now() - start < 3500) requestAnimationFrame(sample); else resolve(values);
    }
    sample();
  }));
  expect(Math.max(...scales) / Math.min(...scales)).toBeGreaterThan(1.45);
  await info.attach('intro-scale-samples', { body: JSON.stringify(scales), contentType: 'application/json' });
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByText('Thử thách Toán lớp 5', { exact: true })).toBeVisible();
  await expect(page.getByTestId('math-prompt')).not.toHaveText(/^Tính: \d+ [−+] \d+$/);
  const { question } = await raceState(page);
  expect(Boolean(question.choices)).toBe(comparison);
  if (question.choices) {
    const wrong = question.choices.find(choice => choice !== question.answer);
    expect(wrong).toBeDefined();
    await page.getByTestId('math-feedback-layer').getByText(wrong, { exact: true }).click();
  } else {
    await page.getByTestId('math-answer-input').fill('-999999');
    await page.getByTestId('math-submit').click();
  }
  await page.getByTestId('math-understood').click();
  await expect(page.getByText('Bạn Cụt đang suy nghĩ...', { exact: true })).toBeVisible({ timeout: 20000 });
  await expect(page.getByTestId('race-current-player')).not.toContainText('Máy');
  await page.screenshot({ path: info.outputPath('bot-name-grade5.png') });
});

test('grade 1 question labels stay grade 1 and defense grade 5 starts with decimal pieces', async ({ page, app }, info) => {
  test.setTimeout(90000);
  if ((page.viewportSize()).width < 900) await page.setViewportSize({ width: 900, height: 600 });
  await open(page, app, 'race-to-finish', 1);
  await page.getByTestId('start-race-button').click();
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByText('Thử thách Toán lớp 1', { exact: true })).toBeVisible();
  await expect(page.getByTestId('math-prompt')).toHaveText(/^Tính: \d+ [−+] \d+$/);
  await page.goto(`${sites.portal.origin}/study/games/energy-defense`);
  await page.getByRole('button', { name: 'Lớp 5', exact: true }).click();
  await page.getByTestId('game-grade-start').click();
  await page.getByTestId('energy-start').click();
  await expect(page.getByRole('button', { name: /^Pha lê .*\,/ }).first()).toBeVisible();
  await page.screenshot({ path: info.outputPath('defense-grade5.png') });
});
