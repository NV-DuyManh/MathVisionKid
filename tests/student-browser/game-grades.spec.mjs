import { test, expect, sites, login } from '../browser/fixtures.mjs';
import { expectTrainingGameReady } from './game-controls.mjs';

const gamesUrl = `${sites.portal.origin}/study/games`;

async function openGames(page, app, grade = 5) {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await expect.poll(() => Boolean(app.studentProfile)).toBe(true);
  // Auth still reports grade 5. Games must use the grade from the personal profile.
  app.studentProfile.gradeLevel = grade;
  await page.goto(gamesUrl);
}
async function openGame(page, game) {
  await page.getByTestId(`training-play-${game}`).click();
  const viewport=page.viewportSize();
  if(game==='race-to-finish' && viewport.width<viewport.height) {
    await expect(page.getByText('Xoay ngang điện thoại để xem đủ bàn đua và chọn nhân vật.')).toBeVisible();
    // Chromium cannot resize a fullscreen emulated phone window.
    await page.evaluate(async()=>{if(document.fullscreenElement)await document.exitFullscreen();});
    await page.setViewportSize({width:viewport.height,height:viewport.width});
  }
  await expectTrainingGameReady(page, game);
}
test('grade 1 hides unsupported games and starts Race with grade 1 arithmetic', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  await openGames(page, app, 1);
  await expect(page.getByTestId('training-grades-race-to-finish')).toHaveText('Toán lớp 1');
  await expect(page.getByTestId('training-grades-energy-defense')).toHaveText('Toán lớp 1');
  for (const game of ['terrain-racing', 'planet-rescue', 'block-island'])
    await expect(page.getByTestId(`training-card-${game}`)).toHaveCount(0);
  await page.goto(`${gamesUrl}/planet-rescue`);
  await expect(page.getByText('Trò chơi này chưa có câu hỏi cho lớp 1.')).toBeVisible();
  await page.getByRole('button', { name: 'Trở về danh sách game' }).click();
  await openGame(page, 'race-to-finish');
  const startRace = page.getByTestId('start-race-button');
  await expect(startRace).toContainText('XUẤT PHÁT ĐUA NGAY');
  await startRace.click();
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByText(/Tính: \d+ [−+] \d+/)).toBeVisible();
  await testInfo.attach('Race grade 1 question', { body: await page.screenshot(), contentType:'image/png' });
});
test('terrain checks division for profile grades 2 and 4 against the animated result', async ({ page, app }) => {
  test.setTimeout(90000);
  await openGames(page, app, 2);
  await openGame(page, 'terrain-racing');
  const question=page.getByTestId('supercar-question');
  await expect(question).toBeVisible({timeout:30000});
  const text=await question.innerText(),match=text.match(/(\d+) : (2|5) = \?/);
  expect(match).toBeTruthy();
  const answer=Number(match[1])/Number(match[2]);
  await page.getByTestId(`supercar-answer-${answer}`).click();
  await expect(page.getByTestId('supercar-stage')).toHaveText('Chặng 2/5',{timeout:20000});
  await page.getByTestId('supercar-pause').click();
  await page.getByTestId('supercar-exit').click();
  await expect(page.getByTestId('training-play-terrain-racing')).toBeVisible();
  app.studentProfile.gradeLevel = 4;
  await page.goto(gamesUrl);
  await expect(page.getByTestId('training-grades-terrain-racing')).toHaveText('Toán lớp 4');
  await openGame(page, 'terrain-racing');
  await expect(question).toBeVisible({timeout:30000});
  const nextText=await question.innerText();
  const division=nextText.match(/(\d+) : ([1-9]\d) = \?/);
  expect(division).toBeTruthy();
  const correct=Number(division[1])/Number(division[2]);
  await page.getByTestId(`supercar-answer-${correct+1}`).click();
  await expect(page.getByTestId('supercar-loss')).toBeVisible({timeout:20000});
  await expect(page.getByTestId('supercar-loss')).toContainText(`Đáp án đúng: ${correct} m/s`);
});
test('defense grade 1 can solve a natural addition and switch to fraction questions in grade 4', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  await openGames(page, app, 1);
  await openGame(page, 'energy-defense');
  await expect(page.getByText('Cộng trong 100, không nhớ').first()).toBeVisible();
  await page.getByTestId('energy-start').click();
  const target=Number((await page.getByTestId('energy-target').innerText()).replace(/\s/g,''));
  const crystals=page.locator('[data-testid^="energy-crystal-p"]');
  await expect(crystals).toHaveCount(4);
  const values=await crystals.evaluateAll(nodes=>nodes.map(n=>Number(n.getAttribute('aria-label').replace('Pha lê ',''))));
  let pair;
  for(let i=0;i<values.length;i++)for(let j=i+1;j<values.length;j++)if(values[i]+values[j]===target)pair=[i,j];
  expect(pair).toBeTruthy();expect(values[pair[0]]%10+values[pair[1]]%10).toBeLessThan(10);
  await crystals.nth(pair[0]).click();await crystals.nth(pair[1]).click();
  await expect(page.getByText(/Vừa đủ!/).first()).toBeVisible();
  await testInfo.attach('Defense grade 1 solved addition', {body:await page.screenshot(),contentType:'image/png'});
  const fire = page.getByTestId('energy-fire');
  await fire.click();
  await expect(fire).toContainText(/đang khai hỏa/i);
  await expect(page.getByTestId('energy-feedback')).toHaveCount(0);
  app.studentProfile.gradeLevel = 4;
  await page.goto(`${gamesUrl}/energy-defense`);
  await expectTrainingGameReady(page, 'energy-defense');
  await page.getByTestId('energy-start').click();
  await expect(page.getByTestId('energy-console')).toBeVisible();
  await expect(page.getByRole('button',{name:/^Pha lê .*\//}).first()).toBeVisible();
});
test('grade 3 Block Island keeps building controls and explains area/perimeter progress', async ({ page, app }) => {
  test.setTimeout(60000);
  await openGames(page, app, 3);
  await openGame(page, 'block-island');
  await expect(page.getByTestId('island-mode-hard')).toHaveCount(0);
  await page.getByTestId('island-start').click();
  await page.getByTestId('island-confirm-new').click();
  await expect(page.getByTestId('island-play')).toBeVisible();
  await expect(page.getByTestId('island-area')).toBeVisible();
  await page.getByTestId('island-coach-skip').click();
  await expect(page.getByTestId('island-feedback')).toContainText(/Thiếu|Thừa|Đủ/);
});

test('catalog can retry when the profile has no grade', async ({ page, app }) => {
  await openGames(page, app, null);
  await expect(page.getByText('Chưa đọc được khối lớp', { exact: true })).toBeVisible();
  await expect(page.locator('[data-testid^="training-card-"]')).toHaveCount(0);
  app.studentProfile.gradeLevel = 5;
  await page.getByRole('button', { name: 'Thử lại', exact: true }).click();
  await expect(page.locator('[data-testid^="training-card-"]')).toHaveCount(5);
});

test('grade 5 Defense gives the battlefield more room and fits compact crystal controls', async ({ page, app, isMobile }, testInfo) => {
  test.skip(isMobile, 'Mouse and keyboard layout.');
  await page.setViewportSize({ width: 1366, height: 768 });
  await openGames(page, app);
  await expect(page.getByTestId('training-grades-planet-rescue')).toHaveText('Toán lớp 5');
  await openGame(page, 'energy-defense');
  await page.getByTestId('energy-start').click();
  await expect(page.getByRole('button', { name: /^Pha lê .*[,]/ }).first()).toBeVisible();
  const battlefield = page.getByTestId('energy-combat-viewport');
  const panel = page.getByTestId('energy-question-column');
  const crystal = page.locator('[data-testid^="energy-crystal-"]').first();
  await expect.poll(async () => (await battlefield.boundingBox()).width / (await panel.boundingBox()).width).toBeGreaterThan(1.85);
  await expect.poll(async () => (await crystal.boundingBox()).height).toBeLessThanOrEqual(52);
  await expect(page.getByTestId('energy-fire')).toBeInViewport();
  const creep = battlefield.getByTestId(/^energy-creep-\d+$/).first();
  await expect(creep).toBeVisible();
  await expect.poll(() => creep.evaluate(enemy => {
    const viewport = enemy.closest('[data-testid="energy-combat-viewport"]');
    const portal = viewport.querySelector('[data-testid="energy-spawn-gate"]');
    const stoneLayer = viewport.querySelector('[data-testid="energy-portal-front"]').parentElement;
    const gate = portal.getBoundingClientRect();
    const sprite = enemy.getBoundingClientRect();
    const spawnX = (sprite.x + sprite.width / 2 - gate.x) / gate.width;
    return spawnX >= .37 && spawnX <= .62 && sprite.top < gate.bottom && sprite.bottom > gate.top
      && Number(getComputedStyle(enemy).zIndex) > Number(getComputedStyle(stoneLayer).zIndex);
  }), { timeout: 800 }).toBe(true);
  const screenshot = testInfo.outputPath('thu-thanh-lop-5.png');
  await page.screenshot({ path: screenshot });
  await testInfo.attach('Defense desktop layout', { path: screenshot, contentType: 'image/png' });
});
