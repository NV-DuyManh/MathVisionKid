import { test, expect, sites, login } from '../browser/fixtures.mjs';

async function openGames(page, app) {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/games`);
}
async function selectGrade(page, game, grade) {
  await page.getByTestId(`training-play-${game}`).click();
  const viewport=page.viewportSize();
  if(game==='race-to-finish' && viewport.width<viewport.height) {
    await expect(page.getByText('Xoay ngang điện thoại để xem đủ bàn đua và chọn nhân vật.')).toBeVisible();
    // Chromium cannot resize a fullscreen emulated phone window.
    await page.evaluate(async()=>{if(document.fullscreenElement)await document.exitFullscreen();});
    await page.setViewportSize({width:viewport.height,height:viewport.width});
  }
  await expect(page.getByTestId(`grade-selection-${game}`)).toBeVisible();
  await expect(page.getByTestId('game-grade-start')).toBeDisabled();
  const radio=page.getByRole('button', { name: `Lớp ${grade}`, exact: true });
  await radio.focus();
  await radio.press('Space');
  await expect(page.getByRole('button', { name: `Lớp ${grade}`, exact: true })).toHaveAttribute('aria-pressed','true');
  await page.getByTestId('game-grade-start').click();
}
test('catalog shows recommended grades and race starts with grade 1 arithmetic', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  await openGames(page, app);
  for (const [game, lo] of [['race-to-finish',1],['terrain-racing',2],['energy-defense',1],['planet-rescue',4],['block-island',3]])
    await expect(page.getByTestId(`training-grades-${game}`)).toHaveText(`Khuyến nghị: lớp ${lo}–5`);
  await selectGrade(page,'race-to-finish',1);
  await page.getByTestId('start-race-button').click();
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByText(/Tính: \d+ [−+] \d+/)).toBeVisible();
  await testInfo.attach('Race grade 1 question', { body: await page.screenshot(), contentType:'image/png' });
});
test('terrain excludes grade 1 and checks the selected division answer against the animated result', async ({ page, app }, testInfo) => {
  test.setTimeout(90000);
  await openGames(page, app);
  await page.getByTestId('training-play-terrain-racing').click();
  await expect(page.getByRole('button',{name:'Lớp 1',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Lớp 2',exact:true}).click();
  await testInfo.attach('Grade picker', { body: await page.screenshot(), contentType:'image/png' });
  await page.getByTestId('game-grade-start').click();
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
  await selectGrade(page,'terrain-racing',4);
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
  await openGames(page, app);
  await selectGrade(page,'energy-defense',1);
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
  // A fresh route starts a fresh selection, without carrying an old question.
  await page.goto(`${sites.portal.origin}/study/games/energy-defense`);
  await page.getByRole('button',{name:'Lớp 4',exact:true}).click();await page.getByTestId('game-grade-start').click();
  await page.getByTestId('energy-start').click();
  await expect(page.getByTestId('energy-console')).toBeVisible();
  await expect(page.getByRole('button',{name:/^Pha lê .*\//}).first()).toBeVisible();
});
test('block island keeps building controls and explains area/perimeter progress', async ({ page, app }) => {
  test.setTimeout(60000);
  await openGames(page, app);await page.getByTestId('training-play-block-island').click();
  await page.getByTestId('island-start').click();
  await page.getByTestId('island-confirm-new').click();
  await expect(page.getByTestId('island-play')).toBeVisible();
  await expect(page.getByTestId('island-area')).toBeVisible();
  await page.getByTestId('island-coach-skip').click();
  await expect(page.getByTestId('island-feedback')).toContainText(/Thiếu|Thừa|Đủ/);
});
