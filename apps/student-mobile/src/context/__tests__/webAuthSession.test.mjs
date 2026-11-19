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
    location: { get pathname() { return dom.window.location.pathname; }, get search() { return dom.window.location.search; }, replace: path => redirects.push(path) },
    addEventListener: (...args) => dom.window.addEventListener(...args),
    removeEventListener: (...args) => dom.window.removeEventListener(...args),
    performance: dom.window.performance,
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
  let expireSession;
  let logoutCalls = 0;
  let logoutError;
  const logoutRequests = [];
  let sharedPostCalls = 0;
  let clearDraftCalls = 0;
  const photoOwners = [], photoListeners = new Set();
  let photoRecovery = { restoring: false, issue: 'none' }, recoveryGate;
  const publishRecovery = restoring => { photoRecovery = { restoring, issue: 'none' }; photoListeners.forEach(listener => listener()); };
  const api = { defaults: { headers: { common: {} } }, get: path => {
    assert.equal(path, '/me');
    return getProfile();
  }, post: async () => {
    sharedPostCalls++;
    return { data: { accessToken: 'login-access', refreshToken: 'login-refresh' } };
  } };
  const placeholder = ({ children }) => React.createElement('div', null, children);
  const routeReplacements = [];
  const router = { replace: path => routeReplacements.push(path) };
  const { AuthProvider, AuthContext } = load('../AuthContext.web.tsx', {
    'react-native': { View: placeholder, Text: placeholder, ActivityIndicator: placeholder, Pressable: placeholder },
    'expo-router': { useRouter: () => router, usePathname: () => dom.window.location.pathname },
    '../services/auth/tokenStorage': { tokenStorage },
    '../services/auth/sessionEvents': { sessionEvents: { subscribe: listener => {
      expireSession = listener;
      return () => { expireSession = null; };
    } } },
    '../services/api/apiClient': api,
    axios: { post: async (url, body, config) => {
      logoutCalls++;
      logoutRequests.push({ url, body, config });
      if (logoutError) throw logoutError;
    } },
    '../config/env': { ENV: { API_BASE_URL: 'https://api.mathvision.example/api/v1' } },
    '../features/recognition/api/RecognitionService': { RecognitionService: { clearCache() {} } },
    '../features/recognition/state/recognitionDraftStore': { recognitionDraftStore: { clearDraft: () => { clearDraftCalls++; } } },
    '../features/recognition/state/imageDraftPersistence': { imageDraftPersistence: {
      subscribe: listener => { photoListeners.add(listener); return () => photoListeners.delete(listener); },
      getSnapshot: () => photoRecovery,
      activate: async owner => {
        photoOwners.push(owner || null);
        if (owner && recoveryGate) { publishRecovery(true); await recoveryGate; publishRecovery(false); }
      },
    } },
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

    await t.test('photo restoration uses verified ownership and finishes before protected screens mount', async () => {
      await tokenStorage.saveTokens('valid-access', 'valid-refresh');
      getProfile = async () => ({ data: profile });
      let finish;
      recoveryGate = new Promise(resolve => { finish = resolve; });
      await mount();
      assert.equal(photoOwners.at(-1), profile.userId);
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      assert.ok(dom.window.document.body.textContent.includes('Đang khôi phục ảnh của em...'));
      await act(async () => finish()); recoveryGate = undefined;
      assert.ok(dom.window.document.body.textContent.includes('Protected Bình Minh'));
      await unmount();
    });

    await t.test('an interceptor expiry during restore reaches login while an active session expiry uses the recovery page', async () => {
      dom.window.history.replaceState({}, '', '/study/onboarding');
      await tokenStorage.saveTokens('expired-access', 'expired-refresh');
      getProfile = async () => {
        await tokenStorage.clearTokens();
        expireSession('expired');
        throw Object.assign(new Error('Refresh rejected'), { response: { status: 401 } });
      };
      await mount();
      assert.equal(redirects.at(-1), '/login?session=expired');
      assert.equal(currentContext.isAuthenticated, false);
      assert.equal(currentContext.isLoading, false);
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      await unmount();

      for (const [reason, destination] of [['expired', '/session-expired'], ['forbidden', '/access-denied']]) {
        await tokenStorage.saveTokens('active-access', 'active-refresh');
        getProfile = async () => ({ data: profile });
        await mount();
        assert.equal(currentContext.isAuthenticated, true);
        await act(async () => {
          await tokenStorage.clearTokens();
          expireSession(reason);
        });
        assert.equal(currentContext.isAuthenticated, false);
        assert.equal(redirects.at(-1), destination);
        await unmount();
      }
      dom.window.history.replaceState({}, '', '/learn/lessons');
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
      assert.equal(logoutRequests[0].config.timeout, 2000);
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
      assert.equal(logoutRequests[1].config.timeout, 2000);
      assert.equal(sharedPostCalls, 0);
      assert.equal(clearDraftCalls, 2);
      assert.equal(await tokenStorage.getAccessToken(), null);
      assert.equal(await tokenStorage.getRefreshToken(), null);
      assert.equal(await tokenStorage.getUser(), null);
      assert.equal(redirects.at(-1), '/logout?source=student');
      assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
      await unmount();
    });
    await t.test('standalone /login allows its portal redirect to mount without requesting a profile', async () => {
      dom.reconfigure({ url: 'https://mathvision.example/login' });
      redirects.length = 0;
      await tokenStorage.clearTokens();
      await mount();
      assert.equal(currentContext.isLoading, false);
      assert.equal(dom.window.document.body.textContent, 'Login form');
      assert.equal(redirects.length, 0);
      await unmount();
    });
    await t.test('a verified student opening any login entry returns to learning', async () => {
      for (const path of ['/login', '/study/login', '/learn/login']) {
        dom.reconfigure({ url: `https://mathvision.example${path}` });
        routeReplacements.length = 0;
        await tokenStorage.saveTokens('valid-student-access', 'valid-student-refresh');
        getProfile = async () => ({ data: profile });
        await mount();
        assert.equal(currentContext.isAuthenticated, true);
        assert.equal(routeReplacements.at(-1), '/(tabs)');
        if (path !== '/login') assert.equal(dom.window.document.body.textContent.includes('Protected'), false);
        await unmount();
      }
    });
    await t.test('signed-out welcome is public while adjacent student deep links still require login', async () => {
      await tokenStorage.clearTokens();
      getProfile = async () => { assert.fail('A signed-out welcome never requests an authenticated profile'); };
      for (const path of ['/study/welcome', '/learn/welcome', '/welcome', '/study/onboarding', '/learn/onboarding', '/onboarding']) {
        dom.reconfigure({ url: `https://mathvision.example${path}` });
        redirects.length = 0;
        await mount();
        assert.equal(currentContext.isLoading, false);
        assert.equal(currentContext.isAuthenticated, false);
        assert.equal(dom.window.document.body.textContent, 'Login form');
        assert.equal(redirects.length, 0);
        await unmount();
      }
      dom.reconfigure({ url: 'https://mathvision.example/study/lessons' });
      routeReplacements.length = 0;
      await mount();
      assert.equal(routeReplacements.length, 0);
      assert.deepEqual(redirects, ['/login']);
      assert.equal(dom.window.document.body.textContent.includes('Login form'), false);
      await unmount();
      dom.reconfigure({ url: 'https://mathvision.example/login' });
    });
    await t.test('mounted /study/login hands off to the portal without mounting a second form', async () => {
      await tokenStorage.clearTokens();
      getProfile = async () => { assert.fail('A signed-out login route never requests an authenticated profile'); };
      dom.reconfigure({ url: 'https://mathvision.example/study/login?session=expired' });
      redirects.length = 0;
      await mount();
      assert.equal(currentContext.isLoading, false);
      assert.equal(currentContext.isAuthenticated, false);
      assert.equal(dom.window.document.body.textContent.includes('Login form'), false);
      assert.deepEqual(redirects, ['/login?session=expired']);
      await unmount();
      dom.reconfigure({ url: 'https://mathvision.example/login' });
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
