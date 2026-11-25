import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import test from 'node:test';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';

const require = createRequire(import.meta.url);
function load(path, imports, globals = {}) {
  const exports = {};
  const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(source, { exports, ...globals, require: id => imports[id] ?? require(id) });
  return exports;
}

for (const status of [401, null]) test(`logout clears the session when HTTP ${status ?? 'never responds'}`, { timeout: 8000 }, async () => {
  const requests = [];
  const server = createServer((request, response) => {
    let body = '';
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      requests.push({ path: request.url, body, authorization: request.headers.authorization, session: request.headers['x-mathvision-session'] });
      if (status) {
        response.writeHead(status, { 'Content-Type': 'application/json' });
        response.end('{}');
      }
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const values = new Map([['mvk_admin_web_session', 'current-session']]);
  const window = { localStorage: { getItem: key => values.get(key), removeItem: key => values.delete(key) } };
  const { createWebSession } = load('../../../packages/shared-contracts/src/webSession.ts', {}, { window });
  const adminSession = createWebSession('admin', []);
  adminSession.apiClient.defaults.baseURL = `http://127.0.0.1:${server.address().port}/api/v1`;
  const { authService } = load('../src/services/api/authService.ts', {
    './apiClient': { apiClient: adminSession.apiClient }, './tokenStore': { adminSession },
  });
  try {
    await authService.logout();
    assert.equal(adminSession.getSessionId(), null);
    assert.deepEqual(requests, [{ path: '/api/v1/auth/logout', body: '{}', authorization: undefined, session: 'current-session' }]);
  } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
});
