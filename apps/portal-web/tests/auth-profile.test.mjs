import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import React, { act } from 'react';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

const require = createRequire(import.meta.url);

test('portal logout clears the header, rejects late old profiles and updates it for the next login', async () => {
  const dom = new JSDOM('<div id="root"></div>', { url: 'https://portal.mathvision.example/login' });
  const previous = { window: globalThis.window, document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const load = (path, imports) => {
    const exports = {};
    const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: dom.window, document: dom.window.document,
      sessionStorage: dom.window.sessionStorage, Event: dom.window.Event,
      require: id => imports[id] ?? require(id) });
    return exports;
  };
  const pendingProfiles = [];
  const api = {
    interceptors: { request: { use() {} }, response: { use() {} } },
    get: () => new Promise(resolve => pendingProfiles.push(resolve)),
    post: async () => ({ data: '' }),
  };
  const { tokenStore } = load('../src/services/apiClient.ts', {
    axios: { create: () => api }, '../config/runtime': { appConfig: { apiBaseUrl: 'https://api.mathvision.example/api/v1' } },
  });
  const { authService } = load('../src/services/authService.ts', { './apiClient': { apiClient: api, tokenStore } });
  tokenStore.setTokens('old-access', 'old-refresh');
  const placeholder = ({ children }) => React.createElement('div', null, children);
  let showLogout = false;
  const params = new URLSearchParams();
  const router = { useNavigate: () => () => {}, Link: placeholder, useSearchParams: () => [params] };
  const { LogoutPage } = load('../src/pages/LogoutPage.tsx', {
    '@mui/material': new Proxy({}, { get: () => placeholder }),
    'react-router-dom': router,
    '@mui/icons-material/CheckCircle': placeholder, '@mui/icons-material/Login': placeholder,
    '@mui/icons-material/Home': placeholder,
    '../services/authService': { authService }, '../services/apiClient': { tokenStore },
  });
  const { PortalLayout } = load('../src/components/layout/PortalLayout.tsx', {
    '@mui/material': new Proxy({}, { get: () => placeholder }),
    'react-router-dom': { ...router, Outlet: () => showLogout ? React.createElement(LogoutPage) : null },
    '@mui/icons-material/Logout': placeholder, '@mui/icons-material/School': placeholder,
    '@mui/icons-material/DeveloperMode': placeholder, '../common/RoleBadge': { RoleBadge: placeholder },
    '../../services/authService': { authService }, '../../services/apiClient': { tokenStore },
    '../../config/runtime': { showDevTools: false },
  });
  const root = (await import('react-dom/client')).createRoot(dom.window.document.getElementById('root'));
  try {
    await act(async () => root.render(React.createElement(PortalLayout)));
    assert.equal(pendingProfiles.length, 1);
    showLogout = true;
    await act(async () => root.render(React.createElement(PortalLayout)));
    assert.equal(tokenStore.hasTokens(), false);
    await act(async () => pendingProfiles[0]({ data: { displayName: 'Old Teacher', role: 'TEACHER' } }));
    assert.equal(dom.window.document.body.textContent.includes('Old Teacher'), false);
    showLogout = false;
    await act(async () => root.render(React.createElement(PortalLayout)));
    await act(async () => tokenStore.setTokens('new-access', 'new-refresh', true));
    assert.equal(pendingProfiles.length, 2);
    await act(async () => pendingProfiles[1]({ data: { displayName: 'New Student', role: 'STUDENT' } }));
    assert.ok(dom.window.document.body.textContent.includes('New Student'));
    await act(async () => tokenStore.clearTokens());
    assert.equal(dom.window.document.body.textContent.includes('New Student'), false);
  } finally {
    await act(async () => root.unmount());
    dom.window.close();
    Object.assign(globalThis, previous);
  }
});
