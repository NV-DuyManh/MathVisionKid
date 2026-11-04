import { readFileSync } from 'node:fs';
import { transpileModule, ModuleKind } from 'typescript';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';

function client() {
  const dom = new JSDOM('', { url: 'https://teacher.mathvision.example/login' });
  const load = (file, imports) => {
    const exports = {};
    const source = transpileModule(readFileSync(new URL(`../src/services/api/${file}.ts`, import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: dom.window, sessionStorage: dom.window.sessionStorage,
      Event: dom.window.Event, require: id => imports[id] });
    return exports;
  };
  const { AuthTokenStore: tokens } = load('AuthTokenStore', {});
  let before, rejectResponse, acceptResponse, finish, fail, refreshes = 0, retries = 0;
  const pending = new Promise((resolve, reject) => { finish = resolve; fail = reject; });
  const api = async () => { retries++; return {}; };
  api.interceptors = { request: { use: fn => { before = fn; } },
    response: { use: (good, bad) => { acceptResponse = good; rejectResponse = bad; } } };
  load('apiClient', { axios: { create: () => api, post: () => { refreshes++; return pending; } },
    './AuthTokenStore': { AuthTokenStore: tokens }, '../../config/runtime': { appConfig: { apiBaseUrl: 'https://teacher.mathvision.example/api/v1' } } });
  return { dom, tokens, before: config => before(config), response: response => acceptResponse(response),
    rejected: error => rejectResponse(error), finish, fail, stats: () => ({ refreshes, retries }) };
}

for (const outcome of ['success', 'failure']) {
  test(`late Teacher refresh ${outcome} cannot overwrite or log out a new account`, async () => {
    const c = client();
    try {
      c.tokens.setTokens('a', 'ra', true);
      const config = c.before({ url: '/me', headers: {} });
      const request = c.rejected({ config, response: { status: 401 } });
      c.tokens.setTokens('b', 'rb', true);
      if (outcome === 'success') c.finish({ data: { accessToken: 'a2', refreshToken: 'ra2' } });
      else c.fail(new Error('old request failed'));
      await assert.rejects(request);
      assert.equal(c.tokens.getAccessToken(), 'b');
      assert.equal(c.tokens.getRefreshToken(), 'rb');
      assert.equal(c.stats().retries, 0);
    } finally { c.dom.window.close(); }
  });
}

test('concurrent Teacher 401 responses share one refresh and preserve the session identity', async () => {
  const c = client();
  try {
    c.tokens.setTokens('a', 'ra', true);
    const identity = c.tokens.getSessionId();
    const one = c.before({ url: '/teacher/classes', headers: {} });
    const two = c.before({ url: '/teacher/batches', headers: {} });
    const pending = [c.rejected({ config: one, response: { status: 401 } }), c.rejected({ config: two, response: { status: 401 } })];
    c.finish({ data: { accessToken: 'a2', refreshToken: 'ra2' } });
    await Promise.all(pending);
    assert.deepEqual(c.stats(), { refreshes: 1, retries: 2 });
    assert.equal(c.tokens.getSessionId(), identity);
    const late = c.before({ url: '/teacher/classes', headers: {} });
    c.tokens.setTokens('b', 'rb', true);
    assert.throws(() => c.response({ config: late }), /Phiên đăng nhập đã thay đổi/);
  } finally { c.dom.window.close(); }
});
