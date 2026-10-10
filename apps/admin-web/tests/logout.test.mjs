import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import test from 'node:test';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';

const require = createRequire(import.meta.url);
function load(path, imports) {
  const exports = {};
  const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(source, { exports, require: id => imports[id] ?? require(id) });
  return exports;
}

for (const status of [401, null]) test(`logout clears the session when HTTP ${status ?? 'never responds'}`, { timeout: 8000 }, async () => {
  const requests = [];
  const server = createServer((request, response) => {
    let body = '';
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      requests.push({ path: request.url, body, authorization: request.headers.authorization });
      if (status) {
        response.writeHead(status, { 'Content-Type': 'application/json' });
        response.end('{}');
      }
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let access = 'current-session';
  const tokenStore = { getAccessToken: () => access, getRefreshToken: () => 'refresh-session', clearTokens: () => { access = null; } };
  const runtime = { appConfig: { apiBaseUrl: `http://127.0.0.1:${server.address().port}` }, useMocks: false };
  const { apiClient } = load('../src/services/api/apiClient.ts', { './tokenStore': { tokenStore }, '../../config/runtime': runtime });
  const { authService } = load('../src/services/api/authService.ts', { './apiClient': { apiClient }, './tokenStore': { tokenStore }, '../../config/runtime': runtime });
  try {
    await authService.logout();
    assert.equal(access, null);
    assert.deepEqual(requests, [{ path: '/auth/logout', body: '{}', authorization: 'Bearer current-session' }]);
  } finally {
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
  }
});
