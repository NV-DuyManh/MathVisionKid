import assert from 'node:assert/strict';
import test from 'node:test';
import { statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { JSDOM, VirtualConsole } from 'jsdom';

// Opt-in live check: start the local stack before running test:student:local.
const origin = process.env.LOCAL_STUDENT_WEB_URL || 'http://localhost:5172';
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

test('a new local Portal server reuses the unchanged Student preview', { timeout: 30000 }, async () => {
  const index = new URL('../../../infra/local-runtime/student-web-preview/index.html', import.meta.url);
  const previousBuild = statSync(index).mtimeMs;
  const server = await createServer({
    root: fileURLToPath(new URL('../', import.meta.url)),
    configFile: fileURLToPath(new URL('../vite.config.ts', import.meta.url)),
    server: { host: '127.0.0.1', port: 0, strictPort: false },
    logLevel: 'error',
  });
  try {
    await server.listen();
    assert.equal(statSync(index).mtimeMs, previousBuild, 'unchanged sources must not start another Student export');
    const address = server.httpServer.address();
    const response = await fetch(`http://127.0.0.1:${address.port}/study/`, { signal: AbortSignal.timeout(10000) });
    assert.equal(response.status, 200);
    assert.ok(!(await response.text()).includes('/src/main.tsx'));
  } finally { await server.close(); }
});

test('the actual exported Student router renders home, lessons and Quiz under /study', { timeout: 45000 }, async () => {
  const response = await fetch(new URL('/api/v1/auth/login', origin), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'student', password: '123' }), signal: AbortSignal.timeout(15000),
  });
  assert.equal(response.status, 200);
  const tokens = await response.json();
  try {
    for (const [path, expected] of [['/study/', 'Tiện ích nhanh'], ['/study/lessons', 'Hôm nay em học gì?'], ['/study/quiz', 'Câu đố của em']]) {
      const html = await (await get(path)).text(), errors = [];
      const virtualConsole = new VirtualConsole();
      virtualConsole.on('jsdomError', error => {
        if (error.type === 'unhandled exception') errors.push(error.detail?.message || error.message);
      });
      const dom = new JSDOM(html, {
        url: new URL(path, origin).href, runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole,
        beforeParse(window) {
          window.sessionStorage.setItem('portal_access_token', tokens.accessToken);
          window.sessionStorage.setItem('portal_refresh_token', tokens.refreshToken);
          window.TextEncoder = TextEncoder; window.TextDecoder = TextDecoder;
          window.fetch = (url, options) => fetch(new URL(url, window.location.href), options);
          window.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
          window.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
          // jsdom has no font/image renderer: supply readiness, not app/router mocks.
          window.CSSFontFaceRule = window.CSSRule;
          Object.defineProperty(window.document, 'fonts', { value: { status: 'loaded', ready: Promise.resolve(), load: async () => [], check: () => true, addEventListener() {}, removeEventListener() {} } });
          const src = Object.getOwnPropertyDescriptor(window.HTMLImageElement.prototype, 'src');
          Object.defineProperty(window.HTMLImageElement.prototype, 'src', { get: src.get, set(value) {
            src.set.call(this, value); queueMicrotask(() => this.dispatchEvent(new window.Event('load')));
          } });
          Object.defineProperties(window.HTMLImageElement.prototype, { naturalWidth: { get: () => 256 }, naturalHeight: { get: () => 256 }, decode: { value: async () => {} } });
        },
      });
      try {
        for (let attempt = 0; attempt < 100; attempt++) {
          const text = dom.window.document.body.textContent;
          if (text.includes(expected) || text.includes('Unmatched Route') || errors.length) break;
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        const text = dom.window.document.body.textContent;
        assert.deepEqual(errors, [], path);
        assert.ok(!text.includes('Unmatched Route'), `${path} did not match an application route`);
        assert.ok(text.includes(expected), `${path} did not finish rendering ${expected}; body: ${text.slice(0, 400)}`);
        if (path === '/study/') {
          const lessonTab = [...dom.window.document.querySelectorAll('[role="tab"], a')]
            .find(node => node.textContent.includes('Bài học'));
          assert.ok(lessonTab, 'the actual home page must expose the lessons tab');
          lessonTab.click();
          for (let attempt = 0; attempt < 50 && !dom.window.document.body.textContent.includes('Hôm nay em học gì?'); attempt++) {
            await new Promise(resolve => setTimeout(resolve, 100));
          }
          assert.equal(dom.window.location.pathname, '/study/lessons', 'internal navigation must retain the Student mount');
          assert.ok(dom.window.document.body.textContent.includes('Hôm nay em học gì?'));
        }
      } finally { dom.window.close(); }
    }
  } finally {
    await fetch(new URL('/api/v1/auth/logout', origin), { method: 'POST', headers: { Authorization: `Bearer ${tokens.accessToken}` }, signal: AbortSignal.timeout(5000) });
  }
});
