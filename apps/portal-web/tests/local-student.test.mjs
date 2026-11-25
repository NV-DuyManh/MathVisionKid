import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium, expect } from '@playwright/test';

// Opt-in live check: start the local stack before running test:student:local.
const runtime = new URL('../../../infra/local-runtime/', import.meta.url);
const portsFile = new URL('ports.json', runtime);
const portalPort = existsSync(portsFile) ? JSON.parse(readFileSync(portsFile, 'utf8')).portal : 5172;
const origin = process.env.LOCAL_STUDENT_WEB_URL || `http://localhost:${portalPort}`;
const get = path => fetch(new URL(path, origin), { signal: AbortSignal.timeout(20000) });

test('Student entry and protected deep links serve the real shared app and its assets', async () => {
  for (const path of ['/study/', '/study/learning/math-guide', '/study/quiz']) {
    const response = await get(path), html = await response.text();
    assert.equal(response.status, 200, path);
    assert.ok(response.headers.get('cache-control')?.includes('no-store'), path);
    assert.ok(!html.includes('/src/main.tsx'), 'Student entry returned the marketing portal');
    const entries = [...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(match => match[1]);
    assert.ok(entries.length && entries.every(entry => entry.startsWith('/study/')), `missing mounted Student bundle: ${path}`);
    if (path === '/study/') {
      const scripts = await Promise.all(entries.map(async entry => {
        const script = await get(entry);
        assert.equal(script.status, 200);
        assert.ok(!script.headers.get('content-type')?.includes('text/html'));
        assert.match(script.headers.get('cache-control') || '', /\bimmutable\b/, entry);
        return script.text();
      }));
      const bundle = scripts.join('\n');
      assert.ok(bundle.includes('portal_access_token'), 'Student must restore the shared Portal session');
      assert.ok(bundle.includes('/api/v1'), 'Student must use the same-origin API proxy');
      const favicon = html.match(/<link[^>]+href="([^"]*favicon[^"]*)"/);
      if (favicon) assert.equal((await get(favicon[1])).status, 200);
    }
  }
  assert.equal((await get('/study/_expo/static/js/web/missing-entry.js')).status, 404);
});

test('the Student API proxy validates the account with the backend and refuses anonymous access', async () => {
  assert.equal((await get('/api/v1/me')).status, 401);
  const response = await fetch(new URL('/api/v1/auth/login', origin), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'student', password: '123' }), signal: AbortSignal.timeout(15000),
  });
  assert.equal(response.status, 200);
  const { accessToken } = await response.json();
  assert.ok(accessToken);
  const headers = { Authorization: `Bearer ${accessToken}` };
  try {
    const profile = await fetch(new URL('/api/v1/me', origin), { headers, signal: AbortSignal.timeout(10000) });
    assert.equal(profile.status, 200);
    const user = await profile.json();
    assert.equal(user.role, 'STUDENT');
    assert.equal(user.active, true);
  } finally {
    await fetch(new URL('/api/v1/auth/logout', origin), { method: 'POST', headers, signal: AbortSignal.timeout(5000) });
  }
});

test('a new local Portal server reuses the unchanged Student preview', { timeout: 90000 }, async () => {
  const directory = mkdtempSync(fileURLToPath(new URL('student-preview-test-', runtime)));
  const previousDirectory = process.env.MATHVISION_STUDENT_PREVIEW_DIR;
  process.env.MATHVISION_STUDENT_PREVIEW_DIR = directory;
  const startServer = () => createServer({
    root: fileURLToPath(new URL('../', import.meta.url)),
    configFile: fileURLToPath(new URL('../vite.config.ts', import.meta.url)),
    server: { host: '127.0.0.1', port: 0, strictPort: false },
    logLevel: 'error',
  });
  try {
    const initial = await startServer();
    await initial.close();
    const index = join(directory, 'index.html');
    const previousBuild = statSync(index).mtimeMs;
    const server = await startServer();
    try {
      await server.listen();
      assert.equal(statSync(index).mtimeMs, previousBuild, 'unchanged sources must not start another Student export');
      const address = server.httpServer.address();
      const response = await fetch(`http://127.0.0.1:${address.port}/study/`, { signal: AbortSignal.timeout(10000) });
      assert.equal(response.status, 200);
      assert.ok(!(await response.text()).includes('/src/main.tsx'));
    } finally {
      await server.close();
    }
  } finally {
    if (previousDirectory === undefined) delete process.env.MATHVISION_STUDENT_PREVIEW_DIR;
    else process.env.MATHVISION_STUDENT_PREVIEW_DIR = previousDirectory;
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the actual exported Student router renders home, lessons and Quiz under /study', { timeout: 45000 }, async () => {
  const email = `student-router-${randomUUID()}@example.test`;
  const password = 'Local.Student-Test81!';
  const response = await fetch(new URL('/api/v1/auth/register', origin), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email, password, role: 'STUDENT', displayName: 'Học sinh kiểm thử',
      gradeLevel: 1, phoneNumber: '0900000000', gender: 'PREFER_NOT_TO_SAY',
    }),
    signal: AbortSignal.timeout(15000),
  });
  assert.equal(response.status, 201);
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(new URL('/login', origin).href);
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await expect(page).toHaveURL(new URL('/study/', origin).href);
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();

    await page.getByRole('tab', { name: 'Bài học', exact: true })
      .or(page.getByRole('link', { name: 'Bài học', exact: true })).first().click();
    await expect(page).toHaveURL(new URL('/study/lessons', origin).href);
    await expect(page.getByText('Chương trình học của em', { exact: true })).toBeVisible();

    await page.goto(new URL('/study/quiz', origin).href);
    await expect(page.getByRole('heading', { name: 'Câu đố của em', exact: true })).toBeVisible();
    assert.deepEqual(errors, []);
  } finally {
    await browser.close();
  }
});
