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
  const workspaceEnvironment = { EXPO_PUBLIC_TEACHER_URL: 'https://teacher.mathvision.example', EXPO_PUBLIC_ADMIN_URL: 'https://admin.mathvision.example' };
  const browser = {
    sessionStorage: dom.window.sessionStorage,
    location: { get pathname() { return dom.window.location.pathname; }, replace: path => redirects.push(path) },
    dispatchEvent: event => dom.window.dispatchEvent(event),
  };
  const load = (path, imports = {}, browserWindow = browser, development = false) => {
    const exports = {};
    const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(source, { exports, window: browserWindow === 'server' ? undefined : browserWindow, Event: dom.window.Event,
      AbortController, setTimeout, clearTimeout, URL, __DEV__: development, process: { env: workspaceEnvironment },
      require: id => imports[id] ?? require(id) });
    return exports;
  };
  const { tokenStorage } = load('../../services/auth/tokenStorage.web.ts');
  const { workspaceOrigin } = load('../../config/workspaceOrigin.web.ts');
  const profile = { userId: 'student-id', displayName: 'Bình Minh', email: 'private-account@example.com',
    role: 'STUDENT', active: true, gradeLevel: 3 };
  let currentContext;
  let getProfile;
  let logoutCalls = 0;
  let logoutError;
  const logoutRequests = [];
  let sharedPostCalls = 0;
  let clearDraftCalls = 0;
  const ssoRequests = [];
  const ssoCode = 'mvk_sso_' + 'a'.repeat(64);
  let createTicket = async target => ({ data: { targetApp: target, code: ssoCode, expiresIn: 60 } });
  const api = { defaults: { headers: { common: {} } }, get: path => {
    assert.equal(path, '/me');
    return getProfile();
  }, post: async () => {
    sharedPostCalls++;
    return { data: { accessToken: 'login-access', refreshToken: 'login-refresh' } };
  } };
  const placeholder = ({ children }) => React.createElement('div', null, children);
  const router = { replace() {} };
  const { AuthProvider, AuthContext } = load('../AuthContext.web.tsx', {
    'react-native': { View: placeholder, Text: placeholder, ActivityIndicator: placeholder, Pressable: placeholder },
    'expo-router': { useRouter: () => router, usePathname: () => dom.window.location.pathname },
    '../services/auth/tokenStorage': { tokenStorage },
    '../services/auth/sessionEvents': { sessionEvents: { subscribe: () => () => {} } },
    '../services/api/apiClient': api,
    axios: { get: async (url, config) => {
      assert.equal(url, 'https://api.mathvision.example/api/v1/me');
      assert.equal(config.headers.Authorization, 'Bearer login-access');
      assert.equal(await tokenStorage.getAccessToken(), null);
      return getProfile();
    }, post: async (url, body, config) => {
      if (url.endsWith('/auth/sso/ticket')) {
        ssoRequests.push({ url, body, config });
        assert.equal(await tokenStorage.getAccessToken(), null);
        return createTicket(body.targetApp);
      }
      logoutCalls++;
      logoutRequests.push({ url, body, config });
      if (logoutError) throw logoutError;
    } },
    '../config/env': { ENV: { API_BASE_URL: 'https://api.mathvision.example/api/v1' } },
    '../config/workspaceOrigin.web': { workspaceOrigin },
    '../features/recognition/api/RecognitionService': { RecognitionService: { clearCache() {} } },
    '../features/recognition/state/recognitionDraftStore': { recognitionDraftStore: { clearDraft: () => { clearDraftCalls++; } } },
    '../features/recognition/analytics/recognitionAnalyticsStore': { recognitionAnalyticsStore: { setUserScope() {} } },
    '../constants/theme': { COLORS: {}, FONTS: {} },
  });
  const Probe = () => {
    currentContext = React.useContext(AuthContext);
    return React.createElement('div', null, currentContext.user ? `Protected ${currentContext.user.name}` : 'Login form');
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
      getProfile = async () => { throw Object.assign(new Error('Session rejected'), { response: { status: 401 } }); };
      await mount();
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      assert.equal(redirects.at(-1), '/login?session=expired');
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      await unmount();
    });

    await t.test('offline restore clears cached authority and explains the connection failure', async () => {
      await tokenStorage.saveTokens('offline-access', 'offline-refresh');
      await tokenStorage.saveUser(profile);
      getProfile = async () => { throw new Error('Network Error'); };
      await mount();
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      assert.equal(redirects.at(-1), '/login?connection=failed');
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      await unmount();
    });

    await t.test('nonstudent and inactive profiles never enter the student app', async () => {
      for (const rejected of [{ ...profile, role: 'ADMIN' }, { ...profile, role: 'TEACHER' }, { ...profile, active: false }]) {
        await tokenStorage.saveTokens('valid-other-access', 'valid-other-refresh');
        getProfile = async () => ({ data: rejected });
        await mount();
        assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
        assert.equal(redirects.at(-1), '/access-denied');
        assert.equal(await tokenStorage.getAccessToken(), null);
        await unmount();
      }
    });

    await t.test('logout clears the shared portal session, drafts, and returns to the portal root', async () => {
      await tokenStorage.saveTokens('valid-other-access', 'valid-other-refresh');
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
    await t.test('standalone /login renders without tokens and never reloads itself', async () => {
      dom.reconfigure({ url: 'https://mathvision.example/login' });
      redirects.length = 0;
      await tokenStorage.clearTokens();
      await mount();
      assert.equal(currentContext.isLoading, false);
      assert.equal(dom.window.document.body.textContent, 'Login form');
      assert.equal(redirects.length, 0);
      getProfile = async () => ({ data: profile });
      await act(async () => currentContext.login({ email: 'synthetic-student', password: 'test-only' }));
      assert.equal(currentContext.user.role, 'STUDENT');
      assert.equal(dom.window.document.body.textContent, 'Protected Bình Minh');
      await act(async () => currentContext.logout());
      assert.equal(dom.window.document.body.textContent, 'Login form');
      assert.equal(redirects.length, 0);
      await unmount();
    });
    await t.test('Teacher and Admin use a verified one-time handoff without entering or persisting a Student session', async () => {
      for (const role of ['TEACHER', 'ADMIN']) {
        redirects.length = 0;
        await tokenStorage.clearTokens();
        getProfile = async () => ({ data: { ...profile, role } });
        await mount();
        await act(async () => currentContext.login({ email: 'synthetic-workspace', password: 'test-only' }));
        assert.equal(currentContext.user, null);
        assert.equal(currentContext.isAuthenticated, false);
        assert.equal(await tokenStorage.getAccessToken(), null);
        assert.equal(await tokenStorage.getRefreshToken(), null);
        assert.equal(await tokenStorage.getUser(), null);
        assert.equal(redirects.at(-1), `https://${role.toLowerCase()}.mathvision.example/login#sso=${ssoCode}`);
        assert.equal(ssoRequests.at(-1).body.targetApp, role);
        assert.equal(ssoRequests.at(-1).config.headers.Authorization, 'Bearer login-access');
        assert.equal(redirects.at(-1).includes('login-access'), false);
        await unmount();
      }
    });
    await t.test('inactive authority, a mismatched SSO ticket and SSO failure never grant access', async () => {
      for (const scenario of ['inactive', 'mismatched', 'offline']) {
        redirects.length = 0;
        await tokenStorage.clearTokens();
        getProfile = async () => ({ data: { ...profile, role: 'TEACHER', active: scenario !== 'inactive' } });
        createTicket = async () => {
          if (scenario === 'offline') throw new Error('offline');
          return { data: { targetApp: 'ADMIN', code: ssoCode, expiresIn: 60 } };
        };
        await mount();
        await act(async () => { await assert.rejects(currentContext.login({ email: 'synthetic', password: 'test-only' })); });
        assert.equal(redirects.length, 0);
        assert.equal(currentContext.user, null);
        assert.equal(await tokenStorage.getAccessToken(), null);
        await unmount();
      }
    });
    await t.test('an obsolete Teacher handoff cannot redirect after a newer Student login', async () => {
      redirects.length = 0;
      await tokenStorage.clearTokens();
      let resolveTicket;
      createTicket = () => new Promise(resolve => { resolveTicket = resolve; });
      getProfile = async () => ({ data: { ...profile, role: 'TEACHER' } });
      await mount();
      let oldLogin;
      await act(async () => {
        oldLogin = currentContext.login({ email: 'old-workspace', password: 'test-only' }).catch(error => error);
        await new Promise(resolve => setTimeout(resolve, 0));
      });
      assert.equal(typeof resolveTicket, 'function');
      getProfile = async () => ({ data: profile });
      await act(async () => currentContext.login({ email: 'new-student', password: 'test-only' }));
      await act(async () => {
        resolveTicket({ data: { targetApp: 'TEACHER', code: ssoCode, expiresIn: 60 } });
        await oldLogin;
      });
      assert.equal(redirects.length, 0);
      assert.equal(currentContext.user.role, 'STUDENT');
      assert.equal(await tokenStorage.getAccessToken(), 'login-access');
      await unmount();
    });
    await t.test('production workspace configuration rejects missing, insecure or injected redirect destinations', () => {
      const valid = workspaceEnvironment.EXPO_PUBLIC_TEACHER_URL;
      try {
        assert.equal(workspaceOrigin('TEACHER'), valid);
        for (const origin of [undefined, 'http://teacher.mathvision.example', 'https://localhost',
          'https://teacher.mathvision.example/login', 'https://user:secret@teacher.mathvision.example',
          'https://teacher.mathvision.example?redirect=elsewhere', 'javascript:alert(1)']) {
          workspaceEnvironment.EXPO_PUBLIC_TEACHER_URL = origin;
          assert.throws(() => workspaceOrigin('TEACHER'));
        }
      } finally { workspaceEnvironment.EXPO_PUBLIC_TEACHER_URL = valid; }
    });
    await t.test('local web handoff uses the current machine hostname and the correct role port', () => {
      const saved = { ...workspaceEnvironment };
      try {
        delete workspaceEnvironment.EXPO_PUBLIC_TEACHER_URL;
        delete workspaceEnvironment.EXPO_PUBLIC_ADMIN_URL;
        for (const hostname of ['localhost', '127.0.0.1', '192.168.1.25']) {
          const local = load('../../config/workspaceOrigin.web.ts', {}, { location: { hostname } }, true);
          assert.equal(local.workspaceOrigin('TEACHER'), `http://${hostname}:5173`);
          assert.equal(local.workspaceOrigin('ADMIN'), `http://${hostname}:5174`);
        }
      } finally { Object.assign(workspaceEnvironment, saved); }
    });
  } finally {
    if (root) await unmount();
    Object.assign(globalThis, previous);
    dom.window.close();
  }
});
