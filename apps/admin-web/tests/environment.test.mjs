import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveAppConfig } from '../src/config/environment.ts';
import viteConfig from '../vite.config.ts';

const links = [
  {
    "property": "portalOrigin",
    "variable": "VITE_PORTAL_URL",
    "fallback": "http://localhost:5172"
  }
];
const validEnv = {
  VITE_API_BASE_URL: 'https://api.mathvision.example/api/v1/',
  ...Object.fromEntries(links.map(({ variable }, index) => [variable, `https://app${index}.mathvision.example/`])),
};

test('local development retains the backend and web port defaults', () => {
  const config = resolveAppConfig({}, false);
  assert.equal(config.apiBaseUrl, 'http://localhost:8080/api/v1');
  for (const { property, fallback } of links) assert.equal(config[property], fallback);
});

test('production keeps the backend base path and normalizes origins', () => {
  const config = resolveAppConfig(validEnv, true);
  assert.equal(config.apiBaseUrl, 'https://api.mathvision.example/api/v1');
  for (const [index, { property }] of links.entries()) {
    assert.equal(config[property], `https://app${index}.mathvision.example`);
  }
});

for (const variable of Object.keys(validEnv)) {
  test(`production requires ${variable} instead of using a local default`, () => {
    for (const value of [undefined, '', '   ']) {
      assert.throws(() => resolveAppConfig({ ...validEnv, [variable]: value }, true), new RegExp(variable));
    }
  });

  test(`production rejects unsafe ${variable} URLs`, () => {
    for (const value of [
      '/api/v1', '//api.mathvision.example', 'not a URL',
      'http://api.mathvision.example', 'https://localhost', 'https://localhost.',
      'https://127.0.0.1', 'https://127.1', 'https://[::1]',
      'https://10.0.0.1', 'https://192.168.1.1', 'https://172.16.0.1',
      'https://backend.local', 'https://backend', 'javascript:alert(1)',
      'https://user:password@api.mathvision.example',
      'https://api.mathvision.example?token=x', 'https://api.mathvision.example#token',
    ]) {
      assert.throws(() => resolveAppConfig({ ...validEnv, [variable]: value }, true), new RegExp(variable));
    }
  });
}

test('cross-app addresses are origins for standalone BrowserRouter deployments', () => {
  for (const { variable } of links) {
    assert.throws(() => resolveAppConfig({ ...validEnv, [variable]: 'https://app.mathvision.example/teacher' }, true), /without a path/);
  }
});

test('static builds disable demo controls and mock services even when flags are enabled', () => {
  const values = { ...validEnv, VITE_SHOW_DEV_TOOLS: 'true', VITE_USE_MOCK: 'true' };
  const previous = Object.fromEntries(Object.keys(values).map((key) => [key, process.env[key]]));
  try {
    Object.assign(process.env, values);
    // Mode is intentionally development: static builds must still enforce deployment rules.
    const config = viteConfig({ command: 'build', mode: 'development' });
    assert.equal(config.define['import.meta.env.VITE_SHOW_DEV_TOOLS'], '"false"');
    assert.equal(config.define['import.meta.env.VITE_USE_MOCK'], '"false"');
    assert.deepEqual(JSON.parse(config.define.__APP_CONFIG__), resolveAppConfig(validEnv, true));
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});

test('local offline demos are preserved unless explicitly disabled', () => {
  const previous = process.env.VITE_USE_MOCK;
  try {
    for (const [value, expected] of [['', '"true"'], ['true', '"true"'], ['false', '"false"']]) {
      process.env.VITE_USE_MOCK = value;
      const config = viteConfig({ command: 'serve', mode: 'development' });
      assert.equal(config.define['import.meta.env.VITE_USE_MOCK'], expected);
    }
  } finally {
    if (previous === undefined) delete process.env.VITE_USE_MOCK;
    else process.env.VITE_USE_MOCK = previous;
  }
});
