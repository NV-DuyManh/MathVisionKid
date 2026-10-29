const assert = require('node:assert/strict');
const path = require('node:path');
const { test } = require('node:test');
const config = require('../../apps/student-mobile/metro.config');
const root = path.resolve(__dirname, '../..');
const blocked = relative => config.resolver.blockList.some(rule => rule.test(path.join(root, relative)));

test('Metro indexes Student source but excludes generated local services and old dependency copies', () => {
  assert.equal(blocked('infra/local-runtime/sdk58-reinstall/root-node_modules.before/react/index.js'), true);
  assert.equal(blocked('infra/local-runtime/logs/service.log'), true);
  assert.equal(blocked('.local-artifacts/review-builds-20261029/bundle.hbc'), true);
  assert.equal(blocked('demoUI/assets/local-only.png'), true);
  assert.equal(blocked('apps/student-mobile/src/app/index.tsx'), false);
  assert.equal(blocked('apps/student-mobile/assets/fonts/Nunito-Regular.ttf'), false);
});
