import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';
const require = createRequire(import.meta.url);
function harness() {
  let access = 'session-old', finishLogout, finishA;
  let profile = { userId: 'b', role: 'ADMIN', active: true };
  const tokens = { getSessionId: () => access, clearTokens: () => { access = null; } };
  const logout = new Promise(resolve => { finishLogout = resolve; });
  const old = new Promise(resolve => { finishA = resolve; });
  const webSession = {
    async establish(path, body, _config, isCurrent) {
      if (path === '/auth/google') assert.equal(body.profileAccessToken, 'fixture-profile-token');
      const id = body.email === 'a@validation.test' || body.credential === 'older-credential' ? await old : 'session-b';
      if (!isCurrent()) throw new Error('Phiên đăng nhập đã thay đổi.');
      access = id;
    },
    logout() { access = null; return logout; },
  };
  const apiClient = { get: async () => ({ data: profile }) };
  const exports = {};
  vm.runInNewContext(transpileModule(readFileSync(new URL('../src/services/authService.ts', import.meta.url), 'utf8'), { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }).outputText,
    { exports, window: { dispatchEvent() {} }, Event: class {}, require: id => id === './apiClient' ? { apiClient, tokenStore: tokens, webSession } : require(id) });
  return { service: exports.authService, tokens, finishLogout, finishA, setProfile: value => { profile = value; } };
}
test('late Portal logout cannot erase the next account', async () => {
  const h = harness();
  const logout = h.service.logout();
  assert.equal(h.tokens.getSessionId(), null);
  await h.service.login('b@validation.test', 'fixture-only');
  h.finishLogout({}); await logout;
  assert.equal(h.tokens.getSessionId(), 'session-b');
});
test('late Portal login A cannot replace verified account B', async () => {
  const h = harness();
  const old = h.service.login('a@validation.test', 'fixture-only');
  await h.service.login('b@validation.test', 'fixture-only');
  h.finishA('session-a');
  await assert.rejects(old, /thay đổi/);
  assert.equal(h.tokens.getSessionId(), 'session-b');
});
test('Portal only accepts active known roles from /me', async () => {
  const h = harness();
  for (const profile of [{ role: 'ADMIN', active: false }, { role: 'ADMIN' }, { role: 'OWNER', active: true }]) {
    h.setProfile(profile);
    await assert.rejects(h.service.login('b@validation.test', 'fixture-only'));
    assert.equal(h.tokens.getSessionId(), null);
  }
});

for (const method of ['loginWithGoogle','loginWithFacebook']) {
  test(`late ${method} cannot replace a newer verified password login`, async () => {
    const h=harness();
    const credential = method === 'loginWithGoogle'
      ? { idToken: 'older-credential', profileAccessToken: 'fixture-profile-token' }
      : 'older-credential';
    const older=h.service[method](credential,'TEACHER');
    await h.service.login('b@validation.test','fixture-only');
    h.finishA('session-a-social');
    await assert.rejects(older,/thay đổi/);
    assert.equal(h.tokens.getSessionId(),'session-b');
  });
}
