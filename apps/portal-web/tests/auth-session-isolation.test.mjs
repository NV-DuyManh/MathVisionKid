import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';
const require = createRequire(import.meta.url);
function harness() {
  let access = 'old-access', refresh = 'old-refresh', finishLogout, finishA;
  let profile = { userId: 'b', role: 'ADMIN', active: true };
  const tokens = { getAccessToken: () => access, getRefreshToken: () => refresh, clearTokens: () => { access = refresh = null; }, setTokens: (a, r) => { access = a; refresh = r; } };
  const logout = new Promise(resolve => { finishLogout = resolve; });
  const old = new Promise(resolve => { finishA = resolve; });
  const apiClient = { post: async (path, body) => path === '/auth/logout' ? logout : body.email === 'a@validation.test' || body.credential === 'older-credential' ? old : { data: { accessToken: 'b-access', refreshToken: 'b-refresh' } }, get: async () => ({ data: profile }) };
  const exports = {};
  vm.runInNewContext(transpileModule(readFileSync(new URL('../src/services/authService.ts', import.meta.url), 'utf8'), { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }).outputText,
    { exports, require: id => id === './apiClient' ? { apiClient, tokenStore: tokens } : require(id) });
  return { service: exports.authService, tokens, finishLogout, finishA, setProfile: value => { profile = value; } };
}
test('late Portal logout cannot erase the next account', async () => {
  const h = harness();
  const logout = h.service.logout();
  assert.equal(h.tokens.getAccessToken(), null);
  await h.service.login('b@validation.test', 'fixture-only');
  h.finishLogout({}); await logout;
  assert.equal(h.tokens.getAccessToken(), 'b-access');
});
test('late Portal login A cannot replace verified account B', async () => {
  const h = harness();
  const old = h.service.login('a@validation.test', 'fixture-only');
  await h.service.login('b@validation.test', 'fixture-only');
  h.finishA({ data: { accessToken: 'a-access', refreshToken: 'a-refresh' } });
  await assert.rejects(old, /thay đổi/);
  assert.equal(h.tokens.getAccessToken(), 'b-access');
});
test('Portal only accepts active known roles from /me', async () => {
  const h = harness();
  for (const profile of [{ role: 'ADMIN', active: false }, { role: 'ADMIN' }, { role: 'OWNER', active: true }]) {
    h.setProfile(profile);
    await assert.rejects(h.service.login('b@validation.test', 'fixture-only'));
    assert.equal(h.tokens.getAccessToken(), null);
  }
});

for (const method of ['loginWithGoogle','loginWithFacebook']) {
  test(`late ${method} cannot replace a newer verified password login`, async () => {
    const h=harness();
    const older=h.service[method]('older-credential','TEACHER');
    await h.service.login('b@validation.test','fixture-only');
    h.finishA({data:{accessToken:'stale-social-access',refreshToken:'stale-social-refresh'}});
    await assert.rejects(older,/thay đổi/);
    assert.equal(h.tokens.getAccessToken(),'b-access');
  });
}
