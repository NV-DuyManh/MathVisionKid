import { test, expect, sites, login } from '../browser/fixtures.mjs';

test('hidden tabs stop reporting usage and resume when visible', async ({ page, app }) => {
  app.realStudent = true;
  const heartbeats = () => app.requests.filter(request => request.path === '/student/app-usage/heartbeat');
  await login(page, 'STUDENT');
  await expect.poll(() => heartbeats().at(-1)?.body.active).toBe(true);
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect.poll(() => heartbeats().at(-1)?.body.active).toBe(false);
  const stopped = heartbeats().at(-1).body.connectionId;
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect.poll(() => heartbeats().at(-1)?.body.active).toBe(true);
  expect(heartbeats().at(-1).body.connectionId).not.toBe(stopped);
});

test('training stops when the account limit cannot be verified and can reopen after recovery', async ({ page, app }) => {
  app.realStudent = true;
  let online = true;
  app.responses.set('GET /student/parent-control/status', ({ json, reject }) => online
    ? json({ pinConfigured: true, dailyLimitConfigured: true, dailyLimitReached: false, activityVerified: true })
    : reject(503));
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.setViewportSize({ width: 900, height: 500 });
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  const player = page.getByTestId('training-player-race-to-finish');
  await expect(player).toBeVisible();
  online = false;
  await expect(page.getByText(/Chưa xác minh được thời gian sử dụng/)).toBeVisible({ timeout: 10_000 });
  await expect(player).toHaveCount(0);
  online = true;
  await page.getByRole('button', { name: 'Kiểm tra lại', exact: true }).click();
  await expect(player).toBeVisible({ timeout: 10_000 });
});

test('a temporary game heartbeat failure keeps the run during its valid lease', async ({ page, app, isMobile }) => {
  test.skip(isMobile, 'Checks the desktop Planet Rescue mission view.');
  app.realStudent = true;
  let failNext = false;
  await page.setViewportSize({ width: 1280, height: 660 });
  await page.route('**/api/v1/student/app-usage/game-heartbeat', async route => {
    if (failNext && route.request().postDataJSON().active) {
      failNext = false;
      await route.fulfill({ status: 503, json: {} });
    } else await route.fallback();
  });
  await login(page, 'STUDENT');
  await page.goto(`${sites.portal.origin}/study/games/planet-rescue`);
  await page.getByTestId('rescue-start').click();
  const mission = page.getByTestId('rescue-mission');
  await expect(mission).toContainText('HÀNH TINH 01');
  const heartbeat = response => response.url().endsWith('/game-heartbeat') && response.request().postDataJSON().active;
  const failed = page.waitForResponse(response => heartbeat(response) && response.status() === 503);
  const renewed = page.waitForResponse(response => heartbeat(response) && response.ok());
  failNext = true;
  await failed;
  await expect(mission).toBeVisible();
  await renewed;
  await expect(mission).toContainText('HÀNH TINH 01');
  await expect(page.getByRole('heading', { name: 'Chưa xác minh được thời gian sử dụng' })).toHaveCount(0);
});

test('the game player stops when its server lease expires and does not lock learning', async ({ page, app }) => {
  app.realStudent = true;
  await page.setViewportSize({ width: 1000, height: 650 });
  let granted = false;
  app.responses.set('POST /student/app-usage/game-heartbeat', ({ body, json }) => {
    if (!body.active) return json({ remainingMillis: 0, leaseMillis: 0, gameLimitReached: true });
    const remaining = granted ? 0 : 1500;
    granted = true;
    return json({ remainingMillis: remaining, leaseMillis: remaining, gameLimitReached: remaining === 0 });
  });
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  const player = page.getByTestId('training-player-race-to-finish');
  await expect(player).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Đã hết giờ chơi hôm nay' })).toBeVisible();
  await expect(player).toHaveCount(0);
  await page.getByRole('button', { name: 'Kiểm tra lại', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Đã hết giờ chơi hôm nay' })).toBeVisible();
  await page.getByRole('button', { name: 'Trở về danh sách trò chơi' }).click();
  await expect(page).toHaveURL(/\/study\/games$/);
  await page.goto(`${sites.portal.origin}/study/lessons`);
  await expect(page.getByRole('dialog', { name: 'Đến giờ nghỉ rồi!' })).toHaveCount(0);
});

test('a daily stop keeps an unsent quiz answer in the open page without exposing it through the dialog', async ({ page, app }) => {
  app.realStudent = true;
  let limit = 'available';
  const id = 'daily-limit-in-progress';
  const path = `/student/quizzes/${id}`;
  const now = new Date().toISOString();
  const quiz = {
    quizId: id, sourceType: 'LESSON', sourceId: 'fixture', topicCode: 'ADD', topicName: 'Phép cộng',
    skillCode: 'ADD', gradeLevel: 3, taxonomyVersion: '1', verificationStatus: 'VERIFIED', confidencePercent: 100,
    questionText: 'Tính 17 + 25', unit: '', answerFormat: 'INTEGER', status: 'IN_PROGRESS',
    createdAt: now, startedAt: now, completedAt: null, serverNow: now, elapsedMillis: 5000, stars: 0,
    wrongAttempts: 0, solutionViewed: false, completedWithSolution: false, canRevealSolution: false,
    attempts: [], explanationText: null, correctAnswer: null, timerRunning: false,
  };
  app.responses.set('GET /student/parent-control/status', ({ json, reject }) => limit === 'unknown'
    ? reject(503)
    : json({ pinConfigured: true, dailyLimitConfigured: true, dailyLimitReached: limit === 'reached', activityVerified: true }));
  app.responses.set(`GET ${path}`, ({ json }) => json(quiz));
  app.responses.set(`POST ${path}/activity`, ({ json }) => json(quiz));
  app.responses.set(`POST ${path}/narration`, ({ reject }) => reject(422));

  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await page.goto(`${sites.portal.origin}/study/quiz/${id}`);
  const answer = page.getByRole('textbox', { name: 'Đáp án của em' });
  await answer.fill('42');
  limit = 'reached';
  await page.evaluate(() => window.dispatchEvent(new Event('online')));
  const dialog = page.getByRole('dialog', { name: 'Đến giờ nghỉ rồi!' });
  await expect(dialog).toBeVisible();
  await expect(dialog.locator('#student-rest-scrim')).toHaveCSS('background-color', 'rgba(27, 19, 56, 0.55)');
  await expect(dialog.getByText(/Nếu em đang làm bài/)).toBeVisible();
  await expect(answer).toHaveCount(0);
  await expect(page.locator('[inert] input[aria-label="Đáp án của em"]')).toHaveValue('42');
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: /Góc phụ huynh|Đăng xuất/ }).filter({ visible: true }).and(page.locator(':focus'))).toHaveCount(1);
  expect(app.requests.filter(request => request.method === 'POST' && request.path === `${path}/submit`)).toHaveLength(0);

  await dialog.getByRole('button', { name: 'Góc phụ huynh', exact: true }).click();
  await expect(page.getByLabel('Mã PIN', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Quay lại', exact: true }).click();
  await expect(dialog).toBeVisible();
  await expect(answer).toHaveCount(0);

  limit = 'unknown';
  const failure = page.waitForResponse(response => response.url().includes('/student/parent-control/status') && response.status() === 503);
  await page.evaluate(() => window.dispatchEvent(new Event('online')));
  await failure;
  await expect(dialog).toBeVisible();
  limit = 'available';
  await page.evaluate(() => window.dispatchEvent(new Event('online')));
  await expect(dialog).toHaveCount(0);
  await expect(answer).toHaveValue('42');
});
