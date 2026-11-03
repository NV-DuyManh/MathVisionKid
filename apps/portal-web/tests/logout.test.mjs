import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import React, { act } from 'react';
import { JSDOM } from 'jsdom';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

const require = createRequire(import.meta.url);
function load(path, imports) {
  const exports = {};
  vm.runInNewContext(transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
  }).outputText, { exports, require: id => imports[id] ?? require(id) });
  return exports;
}

for (const source of ['', '?source=teacher', '?source=admin']) {
  for (const outcome of ['pending', 'offline', 'expired']) {
    test(`${source || 'portal'} logout returns home while revocation is ${outcome}`, async () => {
      const dom = new JSDOM('<div id="root"></div>', { url: 'https://portal.mathvision.example/' });
      const previous = { window: globalThis.window, document: globalThis.document,
        IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
      Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
      let access = outcome === 'expired' ? null : 'old-access', refresh = 'old-refresh', requests = 0, finish;
      const pending = new Promise(resolve => { finish = resolve; });
      const tokenStore = { getAccessToken: () => access, clearTokens: () => { access = refresh = null; } };
      const { authService } = load('../src/services/authService.ts', { './apiClient': { tokenStore, apiClient: {
        post: (_path, _body, options) => {
          requests++;
          assert.equal(access, null, 'clear local access before the server request');
          assert.equal(options.headers.Authorization, 'Bearer old-access');
          assert.equal(options.timeout, 5000);
          return outcome === 'offline' ? Promise.reject(new Error('Network unavailable')) : pending;
        },
      } } });
      const { LogoutPage } = load('../src/pages/LogoutPage.tsx', { '../services/authService': { authService } });
      const router = createMemoryRouter([
        { path: '/', element: React.createElement('h1', null, 'Trang chủ') },
        { path: '/login', element: React.createElement('h1', null, 'Đăng nhập') },
        { path: '/logout', element: React.createElement(LogoutPage) },
      ], { initialEntries: ['/login', `/logout${source}`] });
      const root = (await import('react-dom/client')).createRoot(dom.window.document.getElementById('root'));
      try {
        await act(async () => root.render(React.createElement(React.StrictMode, null, React.createElement(RouterProvider, { router }))));
        assert.equal(router.state.location.pathname, '/');
        assert.equal(access, null);
        assert.equal(refresh, null);
        assert.equal(dom.window.document.body.textContent, 'Trang chủ');
        assert.equal(requests, outcome === 'expired' ? 0 : 1);
        // A late logout response must not clear a newly signed-in account.
        access = 'new-access'; refresh = 'new-refresh';
        await act(async () => { finish({}); await pending; });
        assert.equal(access, 'new-access');
        await act(async () => router.navigate(-1));
        assert.equal(router.state.location.pathname, '/login', 'replace the logout history entry');
        assert.equal(access, 'new-access');
      } finally {
        await act(async () => root.unmount()); router.dispose(); dom.window.close();
        Object.assign(globalThis, previous);
      }
    });
  }
}
