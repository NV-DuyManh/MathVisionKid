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
  await page.setViewportSize({ width: 900, height: 500 });
  await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
  const player = page.getByTestId('training-player-race-to-finish');
  await expect(player).toBeVisible();
  online = false;
  await expect(page.getByText(/Chưa xác minh được thời gian sử dụng/)).toBeVisible({ timeout: 10_000 });
  await expect(player).toHaveCount(0);
  online = true;
  await page.evaluate(() => window.dispatchEvent(new Event('online')));
  await expect(player).toBeVisible({ timeout: 10_000 });
});
