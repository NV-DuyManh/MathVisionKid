import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';
const require = createRequire(import.meta.url);
function load(path, imports, globals = {}) {
  const exports = {};
  const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }).outputText;
  vm.runInNewContext(source, { exports, ...globals, require: id => imports[id] ?? require(id) });
  return exports;
}
function harness() {
  let access = null, refresh = null;
  const store = { getAccessToken: () => access, getRefreshToken: () => refresh, clearTokens: () => { access = refresh = null; },
    setTokens: (a, r) => { access = a; refresh = r; } };
  const requests = [];
  let post = async () => ({ data: { accessToken: 'verified-access', refreshToken: 'verified-refresh' } });
  let profile = { userId: 'admin-id', email: 'owner@overhaul.test', role: 'ADMIN', active: true };
  const api = { post: async (path, body) => { requests.push(path); return post(path, body); }, get: async path => { requests.push(path); return { data: profile }; } };
  const { authService } = load('../src/services/api/authService.ts', {
    './apiClient': { apiClient: api }, './tokenStore': { tokenStore: store },
    '../../config/runtime': { useMocks: true, appConfig: { apiBaseUrl: 'https://api.overhaul.test/api/v1' } },
  });
  return { authService, store, requests, setProfile: value => { profile = value; }, setPost: value => { post = value; } };
}
for (const role of ['STUDENT', 'TEACHER']) test(`${role} cannot enter Admin after login or SSO`, async () => {
  for (const sso of [false, true]) {
    const h = harness(); h.setProfile({ userId: 'other', role, active: true });
    await assert.rejects(sso ? h.authService.exchangeSsoTicket('test-ticket') : h.authService.login('account@overhaul.test', 'fixture-only'), /quyền quản trị/);
    assert.equal(h.store.getAccessToken(), null);
    assert.ok(h.requests.includes('/me'));
  }
});
test('inactive and unknown-role profiles are rejected', async () => {
  for (const profile of [{ role: 'ADMIN', active: false }, { role: 'ADMIN' }, { role: 'OWNER', active: true }]) {
    const h = harness(); h.setProfile(profile);
    await assert.rejects(h.authService.login('account@overhaul.test', 'fixture-only'));
    assert.equal(h.store.getRefreshToken(), null);
  }
});
test('backend offline never creates an Admin session even with the mock flag', async () => {
  const h = harness(); h.setPost(async () => { throw Object.assign(new Error('Network Error'), { code: 'ERR_NETWORK' }); });
  await assert.rejects(h.authService.login('admin.demo@mathvision.local', 'fixture-only'));
  assert.equal(h.store.getAccessToken(), null);
});
test('valid Admin session requires backend /me', async () => {
  const h = harness();
  const profile = await h.authService.exchangeSsoTicket('test-ticket');
  assert.equal(profile.role, 'ADMIN');
  assert.deepEqual(h.requests, ['/auth/sso/exchange', '/me']);
});
test('invalid SSO discards any older Admin session', async () => {
  const h = harness(); h.store.setTokens('old-access', 'old-refresh');
  h.setPost(async () => { throw Object.assign(new Error('Invalid ticket'), { response: { status: 401 } }); });
  await assert.rejects(h.authService.exchangeSsoTicket('invalid-ticket'));
  assert.equal(h.store.getAccessToken(), null);
  assert.equal(h.store.getRefreshToken(), null);
});
test('stored mock authority is rejected before /me', async () => {
  const h = harness(); h.store.setTokens('mock-admin-access-token', 'mock-admin-refresh-token');
  await assert.rejects(h.authService.getMe(), /thử nghiệm/);
  assert.equal(h.requests.length, 0);
});
test('late login A cannot replace a successful login B', async () => {
  const h = harness();
  let finishA;
  const pendingA = new Promise(resolve => { finishA = resolve; });
  h.setPost(async (_, body) => body.email === 'a@overhaul.test' ? pendingA : { data: { accessToken: 'b-access', refreshToken: 'b-refresh' } });
  const a = h.authService.login('a@overhaul.test', 'fixture-only');
  await h.authService.login('b@overhaul.test', 'fixture-only');
  finishA({ data: { accessToken: 'a-access', refreshToken: 'a-refresh' } });
  await assert.rejects(a, /thay đổi/);
  assert.equal(h.store.getAccessToken(), 'b-access');
});
for (const result of ['success', 'failure']) test(`late refresh ${result} cannot overwrite a new account`, async () => {
  const h = harness(); h.store.setTokens('a-access', 'a-refresh');
  let onError, onRequest, complete, reject;
  const pending = new Promise((yes, no) => { complete = yes; reject = no; });
  const api = async () => ({ data: {} });
  api.interceptors = { request: { use: handler => { onRequest = handler; } }, response: { use: (_, handler) => { onError = handler; } } };
  const axios = { create: () => api, post: () => pending, CanceledError: Error };
  load('../src/services/api/apiClient.ts', {
    axios, './tokenStore': { tokenStore: h.store },
    '../../config/runtime': { appConfig: { apiBaseUrl: 'https://api.overhaul.test/api/v1' } },
  }, { window: { dispatchEvent() {} }, CustomEvent: class {} });
  const config = onRequest({ url: '/me', headers: {} });
  const refresh = onError({ response: { status: 401 }, config });
  h.store.setTokens('b-access', 'b-refresh');
  if (result === 'success') complete({ data: { accessToken: 'a-new', refreshToken: 'a-new-refresh' } });
  else reject(new Error('Refresh failed'));
  await assert.rejects(refresh);
  assert.equal(h.store.getAccessToken(), 'b-access');
});
test('administrative data reads propagate network failures without fixtures', async () => {
  const apiClient = { get: async () => { throw new Error('Offline'); } };
  const { adminService } = load('../src/services/api/adminService.ts', { './apiClient': { apiClient }, '../../config/runtime': { useMocks: true } });
  for (const action of [() => adminService.getDashboard(), () => adminService.getUsers(), () => adminService.getUser('x'), () => adminService.getClasses(), () => adminService.getClass('x'), () => adminService.getAudit()]) await assert.rejects(action, /Offline/);
});
