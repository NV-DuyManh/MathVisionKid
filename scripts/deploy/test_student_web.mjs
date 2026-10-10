import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import test from 'node:test';
import { validateStudentApiBundle } from './check_student_export.mjs';
import { transpileModule, ModuleKind } from 'typescript';

const require = createRequire(import.meta.url);
const config = require('../../apps/student-mobile/app.json').expo;
const configure = require('../../apps/student-mobile/app.config.js');

test('a cached student export is rejected when its API differs from the target', () => {
  assert.throws(() => validateStudentApiBundle('const api="https://old-service.trycloudflare.com/api/v1";', 'https://new-service.trycloudflare.com/api/v1'));
  assert.throws(() => validateStudentApiBundle('const api="https://new-service.trycloudflare.com/api/v1"; const other="https://old-service.trycloudflare.com/api/v1";', 'https://new-service.trycloudflare.com/api/v1'));
  assert.throws(() => validateStudentApiBundle('const api=undefined;', 'https://new-service.trycloudflare.com/api/v1'));
  validateStudentApiBundle('const api="https://new-service.trycloudflare.com/api/v1";', 'https://new-service.trycloudflare.com/api/v1');
});

test('student web mount is opt-in and leaves native identity and configuration intact', () => {
  const before = process.env.MATHVISION_WEB_EXPORT;
  try {
    delete process.env.MATHVISION_WEB_EXPORT;
    assert.equal(configure({ config }), config);
    process.env.MATHVISION_WEB_EXPORT = 'true';
    const web = configure({ config });
    assert.equal(web.experiments.baseUrl, '/study');
    assert.deepEqual(web.android, config.android);
    assert.deepEqual(web.ios, config.ios);
    assert.equal(config.experiments.baseUrl, undefined);
  } finally {
    if (before === undefined) delete process.env.MATHVISION_WEB_EXPORT;
    else process.env.MATHVISION_WEB_EXPORT = before;
  }
});

test('SDK router preserves learning routes with the student website base path', () => {
  const { stripBaseUrl } = require('expo-router/build/fork/getStateFromPath-forks.js');
  assert.equal(stripBaseUrl('/learning/math-guide', '/study'), '/learning/math-guide');
  assert.equal(stripBaseUrl('/study/learning/math-guide', '/study'), '/learning/math-guide');
  assert.equal(stripBaseUrl('/study/lessons', '/study'), '/lessons');
});

test('production student API address is required and rejects unsafe configuration', () => {
  const source = transpileModule(readFileSync(new URL('../../apps/student-mobile/src/config/apiResolver.web.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS },
  }).outputText;
  function resolve(address) {
    const exports = {};
    vm.runInNewContext(source, { exports, URL, __DEV__: false, process: { env: { EXPO_PUBLIC_API_BASE_URL: address } } });
    return exports.resolveApiBaseUrl();
  }
  assert.equal(resolve('https://api.mathvisionkids.com/api/v1/'), 'https://api.mathvisionkids.com/api/v1');
  for (const address of [undefined, 'http://api.mathvisionkids.com/api/v1', 'https://localhost/api/v1', 'https://127.0.0.1/api/v1', 'https://user:secret@api.mathvisionkids.com/api/v1', 'https://api.mathvisionkids.com/api/v1?secret=value', 'https://api.mathvisionkids.com']) {
    assert.throws(() => resolve(address));
  }
});
