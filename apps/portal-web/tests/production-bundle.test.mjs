import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import test from 'node:test';
import { checkWebBundle } from '../../../scripts/deploy/web_bundle_smoke.mjs';

test('production JavaScript excludes local addresses and demo authentication', async () => {
  const assets = new URL('../dist/assets/', import.meta.url);
  const files = (await readdir(assets)).filter((file) => file.endsWith('.js'));
  assert.ok(files.length > 0, 'Build the application before checking production output.');
  assert.equal(files.some((file) => file.startsWith('DevRuntimePage-')), false, 'The developer page was included in production output.');
  const scripts = (await Promise.all(files.map((file) => readFile(new URL(file, assets), 'utf8')))).join('\n');
  assert.equal(/https?:\/\/(?:localhost|127\.0\.0\.1):(?:8080|8081|5172|5173|5174)/.test(scripts), false, 'A project local address is present in production JavaScript.');
  assert.equal(/@mathvision\.local|mock-admin-access-token|mock-admin-refresh-token/.test(scripts), false, 'Demo authentication is present in production JavaScript.');
  assert.equal(/DEVELOPER & TEST ENVIRONMENT|TÀI KHOẢN MẪU DEV|Công cụ Developer Demo/.test(scripts), false, 'Developer UI is present in production JavaScript.');
});

test('built portal hands the backend-validated student to the shared learning app', async () => {
  await checkWebBundle(new URL('../dist/', import.meta.url), 'portal');
});
