// Browser integration evidence against an actual static export. Authentication
// is an intercepted /me fixture; this is not physical-device or backend evidence.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

const baseArg = process.argv.indexOf('--base');
const base = (baseArg >= 0 ? process.argv[baseArg + 1] : 'http://127.0.0.1:4178/study/').replace(/\/?$/, '/');
const output = path.join(__dirname, 'browser');
const fixture = { userId: '33333333-3333-4333-8333-333333333333', id: '33333333-3333-4333-8333-333333333333', displayName: 'Học sinh', role: 'STUDENT', active: true, gradeLevel: 5 };
const games = ['race-to-finish', 'terrain-racing', 'energy-defense', 'planet-rescue', 'block-island'];

async function exercise(page, gameId) {
  const byId = id => page.getByTestId(id);
  await byId(`training-player-${gameId}`).waitFor();
  switch (gameId) {
    case 'race-to-finish':
      // TouchableOpacity exposes a div on web, so Playwright's enabled check
      // alone does not wait for the game's asset-readiness guard. Wait for its
      // ready text, choose the smallest supported race, then start the setup.
      await page.getByText('2 Người chơi', { exact: true }).click();
      await byId('start-race-button').filter({ hasText: 'XUẤT PHÁT ĐUA NGAY' }).click();
      await byId('race-board').waitFor();
      await page.screenshot({ path: path.join(output, `${gameId}-playing.png`) });
      await byId('race-pause').first().click();
      await byId('race-pause-menu').waitFor();
      await byId('race-exit').click();
      break;
    case 'terrain-racing':
      await byId('supercar-question').waitFor();
      await page.screenshot({ path: path.join(output, `${gameId}-playing.png`) });
      await byId('supercar-pause').click();
      await byId('supercar-exit').click();
      break;
    case 'energy-defense':
      await byId('energy-start').click();
      await byId('energy-defense').waitFor();
      await page.screenshot({ path: path.join(output, `${gameId}-playing.png`) });
      await page.getByRole('button', { name: 'Về sảnh', exact: true }).click();
      break;
    case 'planet-rescue':
      await byId('rescue-start').click();
      await byId('rescue-mobile-play').waitFor();
      await page.screenshot({ path: path.join(output, `${gameId}-playing.png`) });
      await byId('rescue-exit').click();
      break;
    case 'block-island':
      await byId('island-start').click();
      await byId('island-confirm-new').click();
      await byId('island-play').waitFor();
      await byId('island-menu').waitFor({ state: 'hidden' });
      await page.screenshot({ path: path.join(output, `${gameId}-playing.png`) });
      await byId('island-exit').click();
      break;
  }
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const report = { evidence: 'Desktop Chromium at a phone-sized viewport, real static-export game modules, intercepted authentication only. Not an Android/Expo Go test.', base, viewport: { width: 390, height: 844 }, games: [], errors: [], failedRequests: [], httpErrors: [], consoleErrors: [] };
  try {
    const context = await browser.newContext({ viewport: report.viewport, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    await context.addInitScript(() => sessionStorage.setItem('portal_access_token', 'isolated-kha-browser-fixture'));
    await context.route('**/api/v1/**', route => {
      const request = route.request();
      const headers = { 'access-control-allow-origin': '*', 'access-control-allow-methods': 'GET, POST, OPTIONS', 'access-control-allow-headers': '*' };
      if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
      if (new URL(request.url()).pathname.endsWith('/me')) return route.fulfill({ status: 200, headers, contentType: 'application/json', body: JSON.stringify(fixture) });
      return route.fulfill({ status: 404, headers, contentType: 'application/json', body: JSON.stringify({ message: 'No fixture for this endpoint' }) });
    });
    const page = await context.newPage();
    page.setDefaultTimeout(20000);
    page.on('pageerror', error => report.errors.push({ gameId: report.currentGame, message: error.message }));
    page.on('console', message => { if (message.type() === 'error') report.consoleErrors.push({ gameId: report.currentGame, message: message.text() }); });
    page.on('requestfailed', request => report.failedRequests.push({ gameId: report.currentGame, url: request.url(), error: request.failure()?.errorText }));
    page.on('response', response => { if (response.status() >= 400) report.httpErrors.push({ gameId: report.currentGame, url: response.url(), status: response.status() }); });
    // Stay in one browser context and use real catalog links, preserving SPA
    // navigation and module lifecycle across all five entries and exits.
    await page.goto(new URL('games', base).href);
    for (const gameId of games) {
      report.currentGame = gameId;
      const viewport = gameId === 'race-to-finish' ? { width: 844, height: 390 } : report.viewport;
      const row = { gameId, viewport, status: 'running', phases: [] };
      report.games.push(row);
      try {
        // The native host requests landscape only for Race. This browser check
        // changes viewport geometry; it does not claim to test device rotation.
        await page.setViewportSize(viewport);
        const play = page.getByTestId(`training-play-${gameId}`);
        await play.click();
        row.phases.push('catalog-play-click');
        await page.getByTestId(`training-player-${gameId}`).waitFor();
        await page.screenshot({ path: path.join(output, `${gameId}-entry.png`) });
        row.phases.push('actual-export-entry-mounted');
        await exercise(page, gameId);
        row.phases.push('game-started-and-exit-clicked');
        await page.getByTestId(`training-play-${gameId}`).waitFor();
        assert.match(new URL(page.url()).pathname, /\/games\/?$/);
        assert.equal(await page.getByTestId(`training-player-${gameId}`).count(), 0);
        row.phases.push('catalog-restored-and-game-unmounted');
        row.status = 'passed';
      } catch (error) {
        row.status = 'failed'; row.error = error.message;
        row.pageText = (await page.locator('body').innerText()).slice(0, 5000);
        await page.screenshot({ path: path.join(output, `${gameId}-failure.png`) });
        await page.goto(new URL('games', base).href);
      }
    }
    delete report.currentGame;
    report.passed = report.games.every(game => game.status === 'passed') && report.errors.length === 0 && report.httpErrors.length === 0;
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ passed: report.passed, games: report.games.map(({ gameId, status, error }) => ({ gameId, status, error })), pageErrors: report.errors.length, httpErrors: report.httpErrors.length, results: path.join(output, 'results.json') }, null, 2));
    if (!report.passed) process.exitCode = 1;
    await context.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
