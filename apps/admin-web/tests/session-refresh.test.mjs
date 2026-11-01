import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';
const require = createRequire(import.meta.url);
const clients = [
  ['Admin', '../src/services/api/apiClient.ts'],
  ['Portal', '../../portal-web/src/services/apiClient.ts'],
  ['Student', '../../student-mobile/src/services/api/apiClient.ts'],
];
function harness(path) {
  let id = 'session-a', access = 'access-a', refresh = 'refresh-a';
  const store = {
    getSessionId: () => id, getAccessToken: () => access, getRefreshToken: () => refresh,
    setTokens: (a, r) => { access = a; refresh = r; }, saveTokens: async (a, r) => { access = a; refresh = r; },
    clearTokens: () => { id = null; access = refresh = null; },
  };
  let onRequest, onSuccess, onError, resolveRefresh, refreshes = 0, retries = 0;
  const pending = new Promise(resolve => { resolveRefresh = resolve; });
  const api = async config => { retries++; return { config, data: {} }; };
  api.defaults = { headers: { common: {} } };
  api.interceptors = { request: { use: fn => { onRequest = fn; } }, response: { use: (yes, no) => { onSuccess = yes; onError = no; } } };
  let profile = { role: path.includes('student-mobile') ? 'STUDENT' : 'ADMIN', active: true };
  const axios = { get: async () => ({ data: profile }), create: () => api, post: () => { refreshes++; return pending; }, CanceledError: Error };
  const exports = {};
  const globals = { window: { dispatchEvent() {} }, Event: class {}, CustomEvent: class {}, FormData: class {},
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} } };
  const imports = {
    'react-native': { Platform: { OS: 'web' } },
    axios, './tokenStore': { tokenStore: store }, '../auth/tokenStorage': { tokenStorage: store },
    '../auth/sessionEvents': { sessionEvents: { expired() {} } },
    '../../config/runtime': { appConfig: { apiBaseUrl: 'https://api.validation.test/api/v1' } },
    '../config/runtime': { appConfig: { apiBaseUrl: 'https://api.validation.test/api/v1' } },
    '../../config/env': { ENV: { API_BASE_URL: 'https://api.validation.test/api/v1' } },
  };
  vm.runInNewContext(transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }).outputText, { exports, ...globals, require: key => imports[key] ?? require(key) });
  if (exports.tokenStore) Object.assign(exports.tokenStore, store);
  return { onRequest: config => onRequest(config), onSuccess: result => onSuccess(result), onError: error => onError(error),
    store, setProfile: value => { profile = value; }, finish: () => resolveRefresh({ data: { accessToken: 'rotated-access', refreshToken: 'rotated-refresh' } }),
    counts: () => ({ refreshes, retries }), switchAccount: () => { id = 'session-b'; access = 'access-b'; refresh = 'refresh-b'; } };
}
for (const [name, path] of clients) {
  test(name + ': simultaneous 401 responses share one refresh and keep current-session data', async () => {
    const h = harness(path);
    const first = await h.onRequest({ url: '/me', headers: {} });
    const second = await h.onRequest({ url: '/admin/dashboard', headers: {} });
    const a = h.onError({ response: { status: 401 }, config: first });
    const b = h.onError({ response: { status: 401 }, config: second });
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(h.counts().refreshes, 1);
    h.finish(); await Promise.all([a, b]);
    assert.equal(h.counts().retries, 2);
    assert.equal(h.store.getAccessToken(), 'rotated-access');
    await h.onSuccess({ config: first, data: { userId: 'same-user' } });
    h.switchAccount();
    await assert.rejects(async () => h.onSuccess({ config: first, data: { userId: 'old-user' } }));
  });
  test(name + ': refresh completion cannot resurrect an older account', async () => {
    const h = harness(path);
    const config = await h.onRequest({ url: '/me', headers: {} });
    const pending = h.onError({ response: { status: 401 }, config });
    await new Promise(resolve => setImmediate(resolve));
    h.switchAccount(); h.finish();
    await assert.rejects(pending);
    assert.equal(h.store.getAccessToken(), 'access-b');
    assert.equal(h.store.getRefreshToken(), 'refresh-b');
  });
}

for (const [name, path] of clients.filter(([name]) => name !== 'Portal')) {
  test(name + ': a forbidden response revalidates the current role and discards lost authority', async () => {
    const h = harness(path);
    h.setProfile({ role: name === 'Admin' ? 'STUDENT' : 'ADMIN', active: true });
    const config = await h.onRequest({ url: name === 'Admin' ? '/admin/dashboard' : '/student/dashboard', headers: {} });
    await assert.rejects(h.onError({ response: { status: 403 }, config }));
    assert.equal(h.store.getAccessToken(), null);
  });
  test(name + ': a resource-level 403 keeps a backend-verified allowed role', async () => {
    const h = harness(path);
    const config = await h.onRequest({ url: name === 'Admin' ? '/admin/users/target' : '/student/resource', headers: {} });
    await assert.rejects(h.onError({ response: { status: 403 }, config }));
    assert.equal(h.store.getAccessToken(), 'access-a');
  });
}
