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

for (const path of ['/teacher/submissions/item/override', '/auth/sso/ticket', '/me']) {
  for (const status of [200, 401]) test(`an old Teacher ${path} response (${status}) cannot cross sessions`, async () => {
    const key = 'mvk_teacher_web_session';
    const values = new Map([[key, 'session-a']]);
    const exports = {};
    vm.runInNewContext(source, { exports, require, window: { localStorage: {
      getItem: name => values.get(name), removeItem: name => values.delete(name),
    } } });
    const session = exports.createWebSession('teacher', []);
    let release, received;
    const started = new Promise(resolve => { received = resolve; });
    session.apiClient.defaults.adapter = config => new Promise((resolve, reject) => {
      assert.equal(config.headers.get('X-MathVision-Session'), 'session-a');
      assert.equal(config.headers.has('Authorization'), false);
      release = () => {
        if (status === 200) resolve({ config, data: {}, status, headers: {} });
        else reject(Object.assign(Error('Unauthorized'), { config, response: { status } }));
      };
      received();
    });
    const response = session.apiClient.post(path, {});
    await started;
    values.set(key, 'session-b');
    release();
    await assert.rejects(response, /Phiên đăng nhập đã thay đổi/);
    assert.equal(session.getSessionId(), 'session-b');
  });
}
