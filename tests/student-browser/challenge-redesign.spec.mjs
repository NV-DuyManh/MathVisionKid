import { chooseTrainingGrade } from './game-controls.mjs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

for (const [width, height] of [[1280, 660], [1366, 768], [1920, 1080]]) test(`quest answer stays inside the desktop viewport at ${width}x${height}`, async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop fit; touch layout remains scrollable.');
  test.setTimeout(90000);
  await page.setViewportSize({ width, height });
  await challenges(page, app);
  await page.goto(`${sites.portal.origin}/study/games/arithmetic-quest`);
  const gamesLink = page.getByRole('navigation', { name: 'Điều hướng học sinh' }).getByRole('link', { name: 'Trò chơi' });
  await expect(gamesLink).toBeVisible();
  await expect(gamesLink).toHaveAttribute('aria-current', 'page');
  await page.getByRole('button', { name: 'Bắt đầu đường đua', exact: true }).click();
  await expect(gamesLink).toBeVisible();
  const input = page.getByRole('textbox', { name: 'Đáp án', exact: true });
  const submit = page.getByRole('button', { name: 'Gửi đáp án', exact: true });
  for (let stage = 0; stage < 5; stage++) {
    await expect(page.getByText(`Chặng ${stage + 1}/5 · ${stage} câu đúng`, { exact: true })).toBeVisible();
    // Assert before actions: automatic scrolling during click/fill would mask this bug.
    for (const control of [input, submit]) {
      const box = await control.boundingBox();
      expect(box.y).toBeGreaterThanOrEqual(0);
      expect(box.y + box.height).toBeLessThanOrEqual(height);
    }
    if (!stage) {
      await submit.click();
      await expect(page.getByRole('alert')).toContainText('Em nhập đáp án');
      const box = await submit.boundingBox(); expect(box.y + box.height).toBeLessThanOrEqual(height);
      await capture(page, info, 'quest-desktop-answer');
    }
    await input.fill('12'); await submit.click();
  }
  await expect(page.getByText('Em nhận được 2 sao!', { exact: true })).toBeVisible();
});

test('desktop race framing, readable dice and ten-second bot thinking', async ({ page, app, isMobile }, info) => {
  test.skip(isMobile, 'Desktop framing; touch dice regression runs separately.');
  test.setTimeout(90000); app.realStudent = true;
  await page.setViewportSize({ width: 1280, height: 660 });
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.addInitScript(() => {
    Math.random = () => 1 / 0xffffffff;
    HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Controlled viewport'); };
    window.raceTiming = {};
    new MutationObserver(() => {
      const label = document.querySelector('[data-testid="dice-result"]');
      if (label && !window.raceTiming.started) {
        window.raceTiming.started = performance.now();
        const sample = () => {
          if (!label.isConnected) { window.raceTiming.ended = performance.now(); return; }
          if (!window.raceTiming.readable && Number(getComputedStyle(label.parentElement).opacity) === 1) window.raceTiming.readable = performance.now();
          requestAnimationFrame(sample);
        }; requestAnimationFrame(sample);
      }
    }).observe(document, { childList: true, subtree: true });
  });
  await login(page, 'STUDENT'); await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  await chooseTrainingGrade(page,'race-to-finish');
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled({ timeout: 15000 });
  const camera = await page.getByTestId('game-camera').boundingBox();
  expect(camera.y).toBeGreaterThanOrEqual(0); expect(camera.y + camera.height).toBeLessThanOrEqual(660);
  expect(await page.getByTestId('camera-world').evaluate(el => new DOMMatrixReadOnly(getComputedStyle(el).transform).a)).toBeGreaterThan(1);
  await capture(page, info, 'race-desktop-board');
  await page.getByTestId('roll-dice-button').click();
  await expect(page.getByTestId('dice-result')).toBeVisible();
  await expect(page.getByTestId('math-prompt')).toBeVisible({ timeout: 15000 });
  const timing = await page.evaluate(() => window.raceTiming);
  expect(timing.ended - timing.readable).toBeGreaterThanOrEqual(1750);
  await info.attach('dice-readable-duration', { body: JSON.stringify(timing), contentType: 'application/json' });
  await page.getByTestId('math-answer-input').fill('-999999');
  await page.getByTestId('math-submit').click(); await page.getByTestId('math-understood').click();
  const thinking = page.getByText('Cánh Cụt đang suy nghĩ...', { exact: true });
  await expect(thinking).toBeVisible({ timeout: 15000 });
  const began = Date.now();
  await page.waitForTimeout(8500); // Observe the actual timer without clock acceleration.
  await expect(thinking).toBeVisible();
  await expect(page.getByTestId('math-feedback')).toBeVisible({ timeout: 5000 });
  expect(Date.now() - began).toBeGreaterThanOrEqual(9300);
  await capture(page, info, 'race-bot-answer');
});

// Real production bundles/inputs/navigation; synthetic HTTP results are labelled.
async function challenges(page, app) {
  app.realStudent = true;
  const now = new Date().toISOString();
  const id = 'challenge-design';
  let quiz = {
    quizId: id, sourceType: 'LESSON', sourceId: 'fixture', topicCode: 'ADD', topicName: 'Cộng các phân số',
    skillCode: 'ADD', gradeLevel: 4, taxonomyVersion: '1', verificationStatus: 'VERIFIED', confidencePercent: 100,
    questionText: 'Một câu đố mới cùng dạng toán em vừa học. Bấm Bắt đầu để mở đề nhé.', unit: '', answerFormat: 'FRACTION', status: 'READY',
    createdAt: now, startedAt: null, completedAt: null, serverNow: now, elapsedMillis: 0, stars: 0, wrongAttempts: 0,
    solutionViewed: false, completedWithSolution: false, canRevealSolution: false, attempts: [], explanationText: null, correctAnswer: null, timerRunning: false,
  };
  const root = `/student/quizzes/${id}`;
  app.responses.set(`GET ${root}`, ({ json }) => json(quiz));
  app.responses.set(`POST ${root}/start`, ({ json }) => {
    quiz = { ...quiz, status: 'IN_PROGRESS', startedAt: now, questionText: 'Tính 3/4 + 1/4', timerRunning: true };
    return json(quiz);
  });
  app.responses.set(`POST ${root}/activity`, ({ json, body }) => {
    quiz = { ...quiz, timerRunning: body.active };
    return json(quiz);
  });
  app.responses.set(`POST ${root}/narration`, ({ reject }) => reject(422));
  app.responses.set(`POST ${root}/submit`, ({ json, body }) => {
    expect(body.requestId).toEqual(expect.any(String));
    const correct = body.answer === (quiz.answerFormat === 'CHOICE' ? '2' : '1');
    const awarded = correct && quiz.verifiedStars == null && !quiz.replayMode && !quiz.solutionViewed;
    if (awarded) app.studentProfile.stars = 200;
    const attempt = { number: quiz.attempts.length + 1, answer: body.answer, correct, submittedAt: now, elapsedMillis: 45000, stars: correct ? 2 : 0 };
    quiz = { ...quiz, attempts: [...quiz.attempts, attempt], wrongAttempts: quiz.wrongAttempts + (correct ? 0 : 1),
      ...(correct ? { status: 'COMPLETED', completedAt: now, elapsedMillis: 45000, timerRunning: false, stars: 2,
        verifiedStars: quiz.verifiedStars ?? (quiz.replayMode || quiz.solutionViewed ? 0 : 1),
        explanationText: '3/4 + 1/4 = 4/4 = 1' } : {}) };
    return json({ quiz, attempt });
  });
  app.responses.set(`POST ${root}/defer`, ({ json }) => { quiz = { ...quiz, status: 'DEFERRED', timerRunning: false }; return json(quiz); });
  app.responses.set(`POST ${root}/replay`, ({ json, body }) => {
    quiz = { ...quiz, status: 'IN_PROGRESS', replayMode: body.mode, timerRunning: true, startedAt: new Date().toISOString(), explanationText: null };
    return json(quiz);
  });
  await page.route('**/api/v1/student/quizzes?**', route => {
    const group = new URL(route.request().url()).searchParams.get('group');
    const visible = group === 'COMPLETED' ? quiz.status === 'COMPLETED' : group === 'IN_PROGRESS' ? quiz.status === 'IN_PROGRESS' : ['READY','DEFERRED'].includes(quiz.status);
    return route.fulfill({ json: { items: visible ? [quiz] : [], page: 0, totalPages: visible ? 1 : 0, totalElements: visible ? 1 : 0 } });
  });
  let count = 0;
  const game = () => ({ id: 'quest-design', question: count, prompt: count < 5 ? '3 × 4' : null, correct: count, length: 5, completed: count === 5, stars: count === 5 ? 2 : 0, rewardStatus: count === 5 ? 'AWARDED' : null });
  app.responses.set('POST /student/game-runs', ({ json }) => { count = 0; return json(game()); });
  app.responses.set('POST /student/game-runs/quest-design/answers', ({ json, body }) => {
    expect(body).toEqual({ question: count, answer: 12 }); count++; return json(game());
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.locator('.student-workspace')).toBeVisible();
  return { quizUrl: `${sites.portal.origin}/study/quiz/${id}`, getQuiz: () => quiz, setQuiz: next => { quiz = { ...quiz, ...next }; } };
}

async function noOverflow(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}
async function capture(page, info, name) {
  await info.attach(name, { body: await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true }), contentType: 'image/png' });
}

for (const [width,height] of [[1366,768],[1440,900],[1920,1080],[768,1024],[1024,768],[360,800],[390,844],[430,932]]) {
  test(`challenge workspace and API progress at ${width}x${height}`, async ({ page, app, isMobile }, info) => {
    test.skip(isMobile !== (width <= 1024), 'Match the requested viewport to its desktop/touch input.');
    test.setTimeout(120000);
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const fixture = await challenges(page, app);
    await page.goto(fixture.quizUrl);
    await expect(page.getByTestId('quiz-timer')).toHaveText('0:00');
    const main = await page.getByTestId('quiz-question-area').boundingBox();
    const aside = await page.getByTestId('quiz-support-panel').boundingBox();
    if (width >= 1366) {
      expect(aside.x).toBeGreaterThanOrEqual(main.x + main.width);
      expect(main.width / aside.width).toBeGreaterThan(1.7);
      expect(main.width / aside.width).toBeLessThan(2.2);
    } else if (width < 768) expect(aside.y).toBeGreaterThanOrEqual(main.y + main.height);
    await noOverflow(page);
    await capture(page, info, 'quiz-ready');
    await page.getByRole('button', { name: 'Bắt đầu thử thách', exact: true }).click();
    const input = page.getByRole('textbox', { name: 'Đáp án của em', exact: true });
    await input.fill('3/4');
    await page.getByRole('button', { name: 'Hoàn thành', exact: true }).click();
    await expect(page.getByText('Chưa đúng rồi, nhưng em thử kiểm tra lại nhé!', { exact: true })).toBeVisible();
    await capture(page, info, 'quiz-playing');
    await input.fill('1');
    await page.getByRole('button', { name: 'Hoàn thành', exact: true }).click();
    await expect(page.getByLabel('2 điểm luyện tập', { exact: true })).toBeVisible();
    await expect(page.getByText('Lượt này: 2 điểm luyện tập · Kỷ lục: 2 điểm luyện tập', { exact: true })).toBeVisible();
    await expect(page.getByText('1 sao', { exact: true })).toBeVisible();
    const starTotal = page.locator('.student-workspace-stars');
    await expect(starTotal).toHaveText(/200 sao$/);
    if (width >= 768) await expect(starTotal).toBeVisible();
    await noOverflow(page);
    await capture(page, info, 'quiz-result');
    await page.getByRole('button', { name: 'Xem cách giải', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Đóng Cách giải', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng Cách giải', exact: true }).click();
    await page.goto(`${sites.portal.origin}/study/games/arithmetic-quest`);
    await expect(page.getByRole('button', { name: 'Bắt đầu đường đua', exact: true })).toBeVisible();
    await expect(page.getByTestId('quest-track')).toHaveAttribute('aria-label', 'Đã hoàn thành 0 trên 5 chặng');
    await noOverflow(page);
    await capture(page, info, 'quest-ready');
    await page.getByRole('button', { name: 'Bắt đầu đường đua', exact: true }).click();
    for (let stage = 0; stage < 5; stage++) {
      await expect(page.getByText(`Chặng ${stage + 1}/5 · ${stage} câu đúng`, { exact: true })).toBeVisible();
      await expect(page.getByTestId(`quest-checkpoint-${stage + 1}`)).toHaveAttribute('aria-label', `Chặng ${stage + 1}: Đang thực hiện`);
      if (!stage) await capture(page, info, 'quest-playing');
      await page.getByRole('textbox', { name: 'Đáp án', exact: true }).fill('12');
      await page.getByRole('button', { name: 'Gửi đáp án', exact: true }).click();
    }
    await expect(page.getByText('Em nhận được 2 sao!', { exact: true })).toBeVisible();
    await expect(page.getByTestId('quest-track')).toHaveAttribute('aria-label', 'Đã hoàn thành 5 trên 5 chặng');
    await noOverflow(page);
    await capture(page, info, 'quest-result');
    await page.getByRole('button', { name: 'Chơi lượt mới', exact: true }).click();
    await expect(page.getByText('Chặng 1/5 · 0 câu đúng', { exact: true })).toBeVisible();
  });
}

test('Quiz saves and restores the server run, supports choices, and keeps practice rewards unchanged', async ({ page, app }, info) => {
  test.setTimeout(90000);
  const fixture = await challenges(page, app);
  await page.goto(fixture.quizUrl);
  await page.getByRole('button', { name: 'Lưu để làm sau', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/quiz`);
  await expect(page.getByRole('button', { name: /Cộng các phân số.*Bắt đầu/ })).toBeVisible();
  fixture.setQuiz({ status: 'IN_PROGRESS', startedAt: new Date().toISOString(), elapsedMillis: 17000, timerRunning: true, answerFormat: 'CHOICE', questionText: 'Chọn phân số bằng 1.\nA. 3/4\nB. 4/4' });
  await page.goto(fixture.quizUrl);
  await expect(page.getByTestId('quiz-timer')).toHaveText('0:17');
  await page.getByRole('radio', { name: 'B. 4/4', exact: true }).click();
  await expect(page.getByRole('radio', { name: 'B. 4/4', exact: true })).toHaveAttribute('aria-checked', 'true');
  await page.reload();
  await expect(page.getByRole('radio', { name: 'B. 4/4', exact: true })).toHaveAttribute('aria-checked', 'true');
  expect(fixture.getQuiz().attempts).toHaveLength(0);
  await page.getByRole('button', { name: 'Hoàn thành', exact: true }).click();
  await expect.poll(() => fixture.getQuiz().attempts.at(-1)?.answer).toBe('2');
  await expect(page.getByLabel('2 điểm luyện tập', { exact: true })).toBeVisible();
  fixture.setQuiz({ replayMode: 'PRACTICE', completedWithSolution: true, stars: 2 });
  await page.reload();
  await expect(page.getByText('Em đã ôn lại bài cũ. Thành tích của em được giữ nguyên.', { exact: true })).toBeVisible();
  await expect(page.getByLabel('2 điểm luyện tập', { exact: true })).toHaveCount(0);
  await capture(page, info, 'quiz-practice-result');
});

test('Quiz recovers a failed start and keeps answer controls reachable in a short viewport', async ({ page, app }, info) => {
  test.setTimeout(90000);
  const fixture = await challenges(page, app);
  let fail = true;
  const start = app.responses.get('POST /student/quizzes/challenge-design/start');
  app.responses.set('POST /student/quizzes/challenge-design/start', request => fail ? request.reject(503) : start(request));
  await page.goto(fixture.quizUrl);
  await page.getByRole('button', { name: 'Bắt đầu thử thách', exact: true }).click();
  const failedStart = page.getByRole('alertdialog', { name: 'Chưa bắt đầu được câu đố' });
  await expect(failedStart).toBeVisible();
  await failedStart.getByRole('button', { name: 'Kiểm tra lại trạng thái' }).click();
  await expect(failedStart).toHaveCount(0);
  fail = false;
  await page.getByRole('button', { name: 'Bắt đầu thử thách', exact: true }).click();
  await page.setViewportSize({ width: 390, height: 480 });
  await page.getByRole('textbox', { name: 'Đáp án của em', exact: true }).fill('1');
  const submit = page.getByRole('button', { name: 'Hoàn thành', exact: true });
  await submit.scrollIntoViewIfNeeded();
  const box = await submit.boundingBox();
  const dock = await page.getByTestId('quiz-fixed-tools').boundingBox();
  expect(box.y + box.height).toBeLessThanOrEqual(dock.y + 1);
  await noOverflow(page);
  await capture(page, info, 'quiz-short-viewport');
  await submit.click();
  await expect(page.getByLabel('2 điểm luyện tập', { exact: true })).toBeVisible();
});

for (const reduced of [false,true]) test(`dice pips match the controller result with reduced motion ${reduced}`, async ({ page, app, isMobile }, info) => {
  test.setTimeout(60000);
  app.realStudent = true;
  await page.setViewportSize(isMobile ? { width: 844, height: 390 } : { width: 1366, height: 768 });
  await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
  await page.addInitScript(() => {
    HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Controlled viewport'); };
    window.diceFrames = [];
    window.diceSettled = null;
    let watching = false;
    new MutationObserver(() => {
      if (watching || !document.querySelector('[data-testid="rolling-dice"]')) return;
      watching = true;
      const sample = () => {
        const die = document.querySelector('[data-testid="rolling-dice"]');
        if (!die) return;
        const label = document.querySelector('[data-testid="dice-result"]');
        const shadow = document.querySelector('[data-testid="dice-contact-shadow"]');
        window.diceFrames.push({ transform: getComputedStyle(die).transform, shadow: Number(getComputedStyle(shadow).opacity) });
        if (label && Number(getComputedStyle(label.parentElement).opacity) === 1) {
          const value = Number(label.textContent.match(/\d+/)?.[0]);
          const model = document.querySelector(`[data-testid="dice-model-${value}"]`);
          window.diceSettled = { value, pips: model.querySelectorAll('[data-testid="dice-front-pip"]').length, opacity: Number(getComputedStyle(model).opacity) };
        }
        requestAnimationFrame(sample);
      };
      requestAnimationFrame(sample);
    }).observe(document, { subtree: true, childList: true });
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  await chooseTrainingGrade(page,'race-to-finish');
  await page.getByTestId('start-race-button').click();
  await expect(page.getByTestId('roll-dice-button')).toBeEnabled();
  await page.getByTestId('roll-dice-button').click();
  if (reduced) {
    await expect(page.getByTestId('rolling-dice')).toBeVisible();
    await capture(page, info, 'dice-result');
  }
  await expect(page.getByTestId('math-prompt')).toBeVisible({ timeout: 15000 });
  const observation = await page.evaluate(() => ({ settled: window.diceSettled, frames: window.diceFrames }));
  expect(observation.settled.value).toBeGreaterThanOrEqual(1);
  expect(observation.settled.value).toBeLessThanOrEqual(6);
  expect(observation.settled.pips).toBe(observation.settled.value);
  expect(observation.settled.opacity).toBe(1);
  const transforms = new Set(observation.frames.map(frame => frame.transform));
  if (reduced) expect(transforms.size).toBe(1);
  else {
    expect(transforms.size).toBeGreaterThan(2);
    const shadows = observation.frames.map(frame => frame.shadow);
    expect(Math.max(...shadows) - Math.min(...shadows)).toBeGreaterThan(.05);
  }
  await info.attach('dice-animation-observation', { body: JSON.stringify(observation), contentType: 'application/json' });
});

test('Quiz choices support keyboard selection and scoped web focus styles', async ({ page, app, isMobile }, info) => {
  test.setTimeout(60000);
  const fixture = await challenges(page, app);
  await page.goto(fixture.quizUrl);
  const start = page.getByRole('button', { name: 'Bắt đầu thử thách', exact: true });
  await start.focus();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Shift+Tab');
  await expect(start).toBeFocused();
  await expect(start).toHaveCSS('outline-style', 'solid');
  await expect(start).toHaveCSS('outline-color', 'rgb(112, 85, 246)');
  if (!isMobile) {
    await start.hover();
    await expect(start).toHaveCSS('box-shadow', /112, 85, 246/);
  }
  await page.keyboard.press('Enter');
  await expect(page.getByRole('textbox', { name: 'Đáp án của em', exact: true })).toBeVisible();
  fixture.setQuiz({ answerFormat: 'CHOICE', questionText: 'Chọn phân số bằng 1.\nA. 3/4\nB. 4/4' });
  await page.reload();
  const first = page.getByRole('radio', { name: 'A. 3/4', exact: true });
  const second = page.getByRole('radio', { name: 'B. 4/4', exact: true });
  await first.focus();
  await page.keyboard.press('Space');
  await expect(first).toHaveAttribute('aria-checked', 'true');
  await page.keyboard.press('ArrowRight');
  await expect(second).toBeFocused();
  await expect(second).toHaveAttribute('aria-checked', 'true');
  await expect(first).toHaveAttribute('tabindex', '-1');
  await page.keyboard.press('Home');
  await expect(first).toHaveAttribute('aria-checked', 'true');
  await page.keyboard.press('End');
  await expect(second).toHaveAttribute('aria-checked', 'true');
  await capture(page, info, 'quiz-keyboard-selection');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Hoàn thành', exact: true })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('2 điểm luyện tập', { exact: true })).toBeVisible();
});

test('Quiz library distinguishes pending, running and completed server states', async ({ page, app }, info) => {
  test.setTimeout(60000);
  const fixture = await challenges(page, app);
  await page.route('**/api/v1/student/quizzes/pending-count', route => route.fulfill({ json: {
    pendingCount: fixture.getQuiz().status === 'COMPLETED' ? 0 : 1,
    totalStars: 291,
    verifiedStars: 137,
  } }));
  await page.goto(`${sites.portal.origin}/study/quiz`);
  await expect(page.getByRole('button', { name: /Cộng các phân số.*Sẵn sàng để thử/ })).toBeVisible();
  await capture(page, info, 'quiz-library-pending');
  fixture.setQuiz({ status: 'IN_PROGRESS', startedAt: new Date().toISOString(), questionText: 'Tính 3/4 + 1/4' });
  await page.getByRole('button', { name: /^Đang làm/ }).click();
  await expect(page.getByRole('button', { name: /Cộng các phân số.*Đang làm dở/ })).toBeVisible();
  await capture(page, info, 'quiz-library-running');
  fixture.setQuiz({ status: 'COMPLETED', stars: 2 });
  await page.getByRole('button', { name: /^Đã xong/ }).click();
  await expect(page.getByRole('button', { name: /Cộng các phân số.*Đã hoàn thành · 2 điểm luyện tập/ })).toBeVisible();
  await expect(page.getByText('291', { exact: true })).toHaveCount(0);
  await expect(page.getByText(/^(137|137 sao đã nhận)$/)).toBeVisible();
  await noOverflow(page);
  await capture(page, info, 'quiz-library-completed');
});
