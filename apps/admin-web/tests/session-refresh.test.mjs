import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';

const require = createRequire(import.meta.url);
const path = new URL('../../../packages/shared-contracts/src/webSession.ts', import.meta.url);
const source = transpileModule(readFileSync(path, 'utf8'), {
  compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
}).outputText;

for (const client of ['admin', 'portal', 'teacher']) {
  test(`${client} rejects an expired session once without refreshing or retrying`, async () => {
    const key = `mvk_${client}_web_session`;
    const values = new Map([[key, 'session-a']]);
    const exports = {};
    vm.runInNewContext(source, { exports, require, window: { localStorage: {
      getItem: name => values.get(name), removeItem: name => values.delete(name),
    } } });
    const session = exports.createWebSession(client, []);
    let expired = 0;
    const requests = [];
    session.onExpired(() => { expired++; });
    session.apiClient.defaults.adapter = async config => {
      requests.push(config.url);
      assert.equal(config.headers.get('X-MathVision-Session'), 'session-a');
      assert.equal(config.headers.get('X-MathVision-Web'), client);
      assert.equal(config.headers.has('Authorization'), false);
      throw Object.assign(Error('Unauthorized'), { config, response: { status: 401 } });
    };
    await Promise.all([
      assert.rejects(session.apiClient.get('/resource'), /Unauthorized|thay đổi/),
      assert.rejects(session.apiClient.get('/another'), /Unauthorized|thay đổi/),
    ]);
    assert.equal(expired, 1);
    assert.equal(session.getSessionId(), null);
    assert.deepEqual(requests, ['/resource', '/another']);
  });
}
