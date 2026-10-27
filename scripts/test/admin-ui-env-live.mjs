// Read-only UI verification against the owner's local dev stack. Credentials stay in memory.
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(process.env.MVK_PLAYWRIGHT_ROOT + '/package.json');
const { chromium } = require('playwright');
const root = new URL('../../', import.meta.url);
const phase = process.argv[2] === 'before' ? 'before' : 'after';
const output = new URL('report/admin-ui-env/', root);
mkdirSync(output, { recursive: true });
const seed = readFileSync(new URL('backend/business-api/src/main/java/com/mathvisionkids/api/config/SeedDataInitializer.java', root), 'utf8');
const password = process.env.MVK_DEV_PASSWORD || seed.match(/passwordEncoder\.encode\("([^"]+)"\)/)?.[1];
assert.ok(password, 'Supply a local dev password in MVK_DEV_PASSWORD.');
const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const results = [], errors = [];
page.on('pageerror', () => errors.push('Browser runtime error'));
try {
  const health = await page.request.get('http://localhost:8080/actuator/health');
  const body = await health.json();
  assert.ok(JSON.stringify(body).includes('MathVisonKid'), 'Only the verified local checkout is allowed.');
  await page.goto('http://localhost:5172/login');
  await page.getByLabel(/^Email/).fill('admin.demo@mathvision.local');
  await page.getByLabel(/^Mật khẩu/).fill(password);
  const profile = page.waitForResponse(r => new URL(r.url()).pathname === '/api/v1/me' && r.status() === 200);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  assert.equal((await (await profile).json()).role, 'ADMIN');
  await page.waitForURL('http://localhost:5174/dashboard');
  await page.getByRole('heading', { name: 'Tổng quan vận hành', level: 1 }).waitFor();
  await page.locator('.metric-grid .MuiTypography-h4').first().filter({ hasText: /\d/ }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  results.push('Portal SSO and /me ADMIN verified on localhost:5174');
  for (const width of phase === 'before' ? [1440, 390] : [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.screenshot({ path: new URL(`${phase}-dashboard-${width}.png`, output).pathname.replace(/^\/(\w:)/, '$1'), fullPage: true, animations: 'disabled' });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
    results.push(`Dashboard ${width}px fits`);
  }
  if (phase === 'after') {
    // Read existing record IDs only. All CRUD remains in the isolated H2 harness.
    const access = await page.evaluate(() => localStorage.getItem('mvk_admin_access_token'));
    const headers = { Authorization: `Bearer ${access}` };
    const users = await (await page.request.get('http://localhost:8080/api/v1/admin/users?size=1', { headers })).json();
    const classes = await (await page.request.get('http://localhost:8080/api/v1/admin/classes?size=1', { headers })).json();
    const routes = ['/users', '/classes', '/audit', '/recognition/analytics'];
    if (users.content?.[0]) routes.push('/users/' + users.content[0].userId);
    if (classes.content?.[0]) routes.push('/classes/' + classes.content[0].classId);
    for (const width of [390, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      for (const route of routes) {
        await page.goto('http://localhost:5174' + route);
        await page.locator('.workspace-content').waitFor();
        await page.waitForLoadState('networkidle');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
        results.push(`Route ${route.replace(/[0-9a-f]{8}-[0-9a-f-]+/g, ':id')} ${width}px fits`);
      }
    }
  }
  assert.equal(errors.length, 0);
  console.log(JSON.stringify({ phase, results, runtimeErrors: errors.length }));
} catch {
  console.error('FAIL local UI check; no credentials or response bodies logged.');
  process.exitCode = 1;
} finally {
  writeFileSync(new URL(`${phase}-live-results.json`, output), JSON.stringify({ phase, results, runtimeErrors: errors.length }, null, 2));
  await browser.close();
}
