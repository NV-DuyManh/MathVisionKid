import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import React, { act } from 'react';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

const require = createRequire(import.meta.url);

test('student web session validates the backend, rejects cached authority, and shares portal logout', async t => {
  const dom = new JSDOM('<div id="root"></div>', { url: 'https://mathvision.example/learn/lessons' });
  const previous = { window: globalThis.window, document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const redirects = [];
  const browser = {
    sessionStorage: dom.window.sessionStorage,
    location: { replace: path => redirects.push(path) },
    dispatchEvent: event => dom.window.dispatchEvent(event),
  };
  const load = (path, imports = {}, browserWindow = browser) => {
    const exports = {};
    const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: browserWindow === 'server' ? undefined : browserWindow, Event: dom.window.Event,
      require: id => imports[id] ?? require(id) });
    return exports;
  };
  const { tokenStorage } = load('../../services/auth/tokenStorage.web.ts');
  const profile = { userId: 'student-id', displayName: 'Bình Minh', email: 'private-account@example.com',
    role: 'STUDENT', active: true, gradeLevel: 3 };
  let currentContext;
  let getProfile;
  let logoutCalls = 0;
  let logoutError;
  const logoutRequests = [];
  let sharedPostCalls = 0;
  let clearDraftCalls = 0;
  const api = { defaults: { headers: { common: {} } }, get: path => {
    assert.equal(path, '/me');
    return getProfile();
  }, post: async () => {
    sharedPostCalls++;
    return { data: { accessToken: 'login-access', refreshToken: 'login-refresh' } };
  } };
  const placeholder = ({ children }) => React.createElement('div', null, children);
  const { AuthProvider, AuthContext } = load('../AuthContext.web.tsx', {
    'react-native': { View: placeholder, Text: placeholder, ActivityIndicator: placeholder },
    'expo-router': { useRouter: () => ({ replace() {} }) },
    '../services/auth/tokenStorage': { tokenStorage },
    '../services/api/apiClient': api,
    axios: { post: async (url, body, config) => {
      logoutCalls++;
      logoutRequests.push({ url, body, config });
      if (logoutError) throw logoutError;
    } },
    '../config/env': { ENV: { API_BASE_URL: 'https://api.mathvision.example/api/v1' } },
    '../features/recognition/api/RecognitionService': { RecognitionService: { clearCache() {} } },
    '../features/recognition/state/recognitionDraftStore': { recognitionDraftStore: { clearDraft: () => { clearDraftCalls++; } } },
    '../features/recognition/analytics/recognitionAnalyticsStore': { recognitionAnalyticsStore: { setUserScope() {} } },
    '../constants/theme': { COLORS: {}, FONTS: {} },
  });
  const Probe = () => {
    currentContext = React.useContext(AuthContext);
    return React.createElement('div', null, `Protected ${currentContext.user.name}`);
  };
  const { createRoot } = await import('react-dom/client');
  let root;
  const mount = async () => {
    root = createRoot(dom.window.document.getElementById('root'));
    await act(async () => root.render(React.createElement(AuthProvider, null, React.createElement(Probe))));
  };
  const unmount = async () => { await act(async () => root.unmount()); root = null; };
  try {
    await t.test('storage reads the portal session and remains safe for static rendering', async () => {
      dom.window.sessionStorage.setItem('portal_access_token', 'portal-access');
      dom.window.sessionStorage.setItem('portal_refresh_token', 'portal-refresh');
      assert.equal(await tokenStorage.getAccessToken(), 'portal-access');
      assert.equal(await tokenStorage.getRefreshToken(), 'portal-refresh');
      const serverStorage = load('../../services/auth/tokenStorage.web.ts', {}, 'server').tokenStorage;
      assert.equal(await serverStorage.getAccessToken(), null);
    });

    await t.test('protected deep links wait for the backend and show a safe mapped profile', async () => {
      let resolveProfile;
      getProfile = () => new Promise(resolve => { resolveProfile = resolve; });
      await mount();
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      await act(async () => resolveProfile({ data: profile }));
      assert.ok(dom.window.document.body.textContent.includes('Protected Bình Minh'));
      assert.equal(currentContext.user.grade, 3);
      assert.equal(currentContext.user.email, undefined);
      assert.equal(JSON.stringify(await tokenStorage.getUser()).includes('@'), false);
      assert.equal(redirects.length, 0);
      await unmount();
    });

    await t.test('a saved profile cannot authenticate when the backend rejects the session', async () => {
      getProfile = async () => { throw new Error('Session rejected'); };
      await mount();
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      assert.equal(redirects.at(-1), '/login');
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      await unmount();
    });

    await t.test('nonstudent and inactive profiles never enter the student app', async () => {
      for (const rejected of [{ ...profile, role: 'TEACHER' }, { ...profile, active: false }]) {
        await tokenStorage.saveTokens('valid-other-access', 'valid-other-refresh');
        getProfile = async () => ({ data: rejected });
        await mount();
        assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
        assert.equal(redirects.at(-1), '/access-denied');
        await unmount();
      }
    });

    await t.test('logout clears the shared portal session, drafts, and returns to the portal root', async () => {
      getProfile = async () => ({ data: { ...profile, displayName: profile.email } });
      await mount();
      assert.equal(currentContext.user.name, 'Học sinh');
      await act(async () => currentContext.logout());
      assert.equal(logoutCalls, 1);
      assert.equal(logoutRequests[0].url, 'https://api.mathvision.example/api/v1/auth/logout');
      assert.equal(JSON.stringify(logoutRequests[0].body), '{}');
      assert.equal(logoutRequests[0].config.timeout, 5000);
      assert.equal(logoutRequests[0].config.headers.Authorization, 'Bearer valid-other-access');
      assert.equal(sharedPostCalls, 0);
      assert.equal(clearDraftCalls, 1);
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      assert.equal(redirects.at(-1), '/logout?source=student');
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      await unmount();
    });

    await t.test('a failed logout still clears local access and does not attempt token refresh', async () => {
      await tokenStorage.saveTokens('valid-other-access', 'valid-other-refresh');
      logoutError = { response: { status: 401 } };
      await mount();
      await act(async () => currentContext.logout());
      assert.equal(logoutCalls, 2);
      assert.equal(logoutRequests[1].config.timeout, 5000);
      assert.equal(sharedPostCalls, 0);
      assert.equal(clearDraftCalls, 2);
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      assert.equal(redirects.at(-1), '/logout?source=student');
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      await unmount();
    });
  } finally {
    if (root) await unmount();
    Object.assign(globalThis, previous);
    dom.window.close();
  }
});
