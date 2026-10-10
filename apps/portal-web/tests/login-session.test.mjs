import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import React, { act } from 'react';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

const require = createRequire(import.meta.url);

for (const oldResult of ['expired', 'old-teacher']) {
  test(`a late ${oldResult} session check cannot undo a new student login`, async () => {
    const dom = new JSDOM('<div id="root"></div>', { url: 'https://portal.mathvision.example/login' });
    const previous = { window: globalThis.window, document: globalThis.document,
      IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
    Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
    const fields = {};
    let submit;
    let resolveOld;
    let rejectOld;
    let cleared = 0;
    let ssoRequests = 0;
    const navigations = [];
    const oldProfile = new Promise((resolve, reject) => { resolveOld = resolve; rejectOld = reject; });
    const placeholder = ({ children, component, onSubmit }) => {
      if (component === 'form') submit = onSubmit;
      return React.createElement(component === 'form' ? 'form' : 'div', null, children);
    };
    const imports = {
      '@mui/material': new Proxy({}, { get: (_, name) => name === 'TextField'
        ? props => { fields[props.id] = props; return React.createElement('input', { id: props.id }); }
        : placeholder }),
      'react-router-dom': { useNavigate: () => navigate, useSearchParams: () => [params] },
      '../services/authService': { authService: {
        getMe: () => oldProfile,
        login: async () => ({ role: 'STUDENT' }),
        requestSsoTicket: async () => { ssoRequests++; return { code: 'old-session' }; },
      } },
      '../services/apiClient': { tokenStore: { hasTokens: () => true, clearTokens: () => { cleared++; } } },
      '../config/runtime': { appConfig: { teacherOrigin: 'https://teacher.mathvision.example', adminOrigin: 'https://admin.mathvision.example' }, showDevTools: false },
    };
    const navigate = path => navigations.push(path);
    const params = new URLSearchParams();
    const exports = {};
    const source = transpileModule(readFileSync(new URL('../src/pages/LoginPage.tsx', import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: dom.window, AbortController,
      require: id => imports[id] ?? (id.startsWith('@mui/icons-material/') ? placeholder : require(id)) });
    const root = (await import('react-dom/client')).createRoot(dom.window.document.getElementById('root'));
    try {
      await act(async () => root.render(React.createElement(exports.LoginPage)));
      await act(async () => {
        fields.email.onChange({ target: { value: 'student@gmail.com' } });
        fields.password.onChange({ target: { value: '123' } });
      });
      await act(async () => submit({ preventDefault() {} }));
      assert.deepEqual(navigations, ['/student']);
      await act(async () => {
        if (oldResult === 'expired') rejectOld(new Error('Expired old session'));
        else resolveOld({ role: 'TEACHER' });
      });
      assert.equal(cleared, 0, 'The old request erased the new login tokens.');
      assert.equal(ssoRequests, 0, 'The old profile opened an unrelated role after the new login.');
      assert.deepEqual(navigations, ['/student']);
    } finally {
      await act(async () => root.unmount());
      Object.assign(globalThis, previous);
      dom.window.close();
    }
  });
}

for (const oldResult of ['late-refresh-success', 'late-refresh-failure', 'cancelled-refresh']) {
  test(`${oldResult} cannot replace or erase a newer login`, async () => {
    const dom = new JSDOM('', { url: 'https://portal.mathvision.example/login' });
    let onError;
    let resolveRefresh;
    let rejectRefresh;
    let retries = 0;
    const pending = new Promise((resolve, reject) => { resolveRefresh = resolve; rejectRefresh = reject; });
    const api = () => { retries++; return Promise.resolve({}); };
    api.interceptors = { request: { use() {} }, response: { use: (_, rejected) => { onError = rejected; } } };
    const exports = {};
    const source = transpileModule(readFileSync(new URL('../src/services/apiClient.ts', import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: dom.window, Event: dom.window.Event,
      sessionStorage: dom.window.sessionStorage,
      require: id => id === 'axios' ? { create: () => api, post: () => pending }
        : { appConfig: { apiBaseUrl: 'https://portal.mathvision.example/api/v1' } } });
    try {
      const { tokenStore } = exports;
      tokenStore.setTokens('old-access', 'old-refresh');
      const controller = new AbortController();
      const result = onError({ response: { status: 401 }, config: { url: '/me', headers: {}, signal: controller.signal } });
      if (oldResult === 'cancelled-refresh') controller.abort();
      tokenStore.setTokens('new-access', 'new-refresh', true);
      if (oldResult === 'late-refresh-success') resolveRefresh({ data: { accessToken: 'refreshed-old-access', refreshToken: 'refreshed-old-refresh' } });
      else rejectRefresh(new Error('Old refresh rejected'));
      await assert.rejects(result);
      assert.equal(tokenStore.getAccessToken(), 'new-access');
      assert.equal(tokenStore.getRefreshToken(), 'new-refresh');
      assert.equal(retries, 0);
    } finally { dom.window.close(); }
  });
}
