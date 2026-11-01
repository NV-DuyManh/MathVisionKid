import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { transpileModule, ModuleKind } from 'typescript';
const require = createRequire(import.meta.url);
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const original = execFileSync('git', ['show', 'HEAD:apps/student-mobile/src/services/api/authApi.ts'], { cwd: root, encoding: 'utf8' });
const exports = {};
let backendCalls = 0;
const source = transpileModule(original, { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }).outputText;
vm.runInNewContext(source, { exports, console: { error() {} }, require: id =>
  id === '../../config/env' ? { ENV: { USE_MOCK: true } } :
  id === '../auth/tokenStorage' ? { tokenStorage: { getUser: async () => null } } :
  id === './apiClient' ? { post: async () => { backendCalls++; throw new Error('No backend in source replay'); } } : require(id) });
const replay = await exports.authApi.login({ email: 'admin.demo@mathvision.local', password: 'fixture-only' });
console.log(JSON.stringify({ verification: 'Original HEAD source replay; not browser E2E', entry: 'Student mock authentication',
  account: 'admin.demo@mathvision.local', resultRole: replay.user.role, backendCalls }));
if (process.argv.includes('--live-read')) {
  // Only authentication and /me; never admin CRUD or logout that could revoke other sessions.
  const guide = readFileSync(resolve(root, 'docs/LOCAL_SETUP.md'), 'utf8');
  const credential = guide.match(/\| Admin \| `admin\.demo@mathvision\.local` \| `([^`]+)`/);
  if (!credential) throw new Error('Development seed credential is not available in local setup documentation.');
  const response = await fetch('http://127.0.0.1:8080/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: 'admin.demo@mathvision.local', password: credential[1] }), signal: AbortSignal.timeout(10000) });
  if (!response.ok) throw new Error('Local demo authentication returned HTTP ' + response.status);
  const session = await response.json();
  const me = await fetch('http://127.0.0.1:8080/api/v1/me', { headers: { Authorization: 'Bearer ' + session.accessToken }, signal: AbortSignal.timeout(10000) });
  if (!me.ok) throw new Error('Local /me returned HTTP ' + me.status);
  const profile = await me.json();
  console.log(JSON.stringify({ verification: 'Live local backend /me', account: profile.email, role: profile.role, active: profile.active }));
}
