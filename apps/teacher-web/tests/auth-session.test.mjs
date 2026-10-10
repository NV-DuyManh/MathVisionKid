import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM, VirtualConsole } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

// Match React and its renderer to the hoisted QueryClientProvider in this workspace.
const require = createRequire(new URL('../../../package.json', import.meta.url));
const React = require('react');
const { act } = React;
const { QueryClient, QueryClientProvider } = require('@tanstack/react-query');

function load(path, imports) {
  const exports = {};
  const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(source, { exports, React, window: globalThis.window, document: globalThis.document,
    sessionStorage: globalThis.window.sessionStorage, Event: globalThis.window.Event, URL,
    require: id => imports[id] ?? require(id) });
  return exports;
}

async function session(run, pendingMe = false) {
  const dom = new JSDOM('<div id="root"></div>', {
    url: 'https://teacher.mathvision.example/dashboard', virtualConsole: new VirtualConsole(),
  });
  const previous = { window: globalThis.window, document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const { AuthTokenStore: tokens } = load('../src/services/api/AuthTokenStore.ts', {});
  tokens.setTokens('teacher-a', 'refresh-a');
  client.setQueryData(['submissionImage', 'private-a'], new Blob(['teacher A private image']));
  let resolveMe;
  const me = new Promise(resolve => { resolveMe = resolve; });
  let currentUser = { userId: 'teacher-a', role: 'TEACHER' };
  const location = { pathname: '/dashboard' };
  const navigate = path => { location.pathname = path; };
  const context = load('../src/components/layout/AuthContext.tsx', {
    'react-router-dom': { useNavigate: () => navigate, useLocation: () => location },
    '../../services/api/ServiceLocator': { AppTeacherService: { getMe: () => pendingMe ? me : Promise.resolve(currentUser) } },
    '../../services/api/AuthTokenStore': { AuthTokenStore: tokens },
    '../../services/api/apiClient': { post: async () => ({ data: '' }) },
    '../../config/runtime': { appConfig: { portalOrigin: 'https://portal.mathvision.example' } },
  });
  const requests = [];
  const image = load('../src/components/common/SubmissionImage.tsx', {
    '../../services/api/apiClient': { get: async (_url, options) => {
      requests.push({ token: tokens.getAccessToken(), signal: options.signal });
      throw new Error('Forbidden for current teacher');
    } },
    '../../config/runtime': { useMocks: false },
    '@mui/material': {
      Box: ({ component, src, alt, children }) => React.createElement(component || 'div', { src, alt }, children),
      Alert: ({ children }) => React.createElement('div', { role: 'alert' }, children),
      CircularProgress: () => React.createElement('div', { role: 'status' }, 'Loading image'),
    },
  });
  let auth;
  function Child() {
    auth = context.useAuth();
    if (location.pathname === '/login') return React.createElement('div', null, 'Sign in');
    return React.createElement(image.SubmissionImage, { id: 'private-a', studentName: 'A' });
  }
  const { createRoot } = require('react-dom/client');
  const root = createRoot(dom.window.document.getElementById('root'));
  const render = async () => {
    await act(async () => root.render(React.createElement(QueryClientProvider, { client },
      React.createElement(context.AuthProvider, null, React.createElement(Child)))));
  };
  try {
    await render();
    await run({ dom, client, tokens, requests, render, location, resolveMe,
      getAuth: () => auth, setUser: user => { currentUser = user; } });
  } finally {
    await act(async () => root.unmount());
    client.clear();
    dom.window.close();
    Object.assign(globalThis, previous);
  }
}

test('teacher identity switch removes cached private images and aborts previous session requests', async () => {
  await session(async ({ dom, client, tokens, requests, render, location, setUser }) => {
    assert.equal(dom.window.document.querySelectorAll('img').length, 1);
    let oldSignal;
    const pending = client.fetchQuery({ queryKey: ['old-session-request'], queryFn: ({ signal }) => {
      oldSignal = signal;
      return new Promise(() => {});
    } }).catch(() => {});
    await act(async () => tokens.setTokens('teacher-b', 'refresh-b', true));
    assert.equal(oldSignal.aborted, true);
    await pending;
    assert.equal(client.getQueryCache().getAll().length, 0);
    assert.equal(dom.window.document.querySelectorAll('img').length, 0);
    location.pathname = '/login';
    await render();
    setUser({ userId: 'teacher-b', role: 'TEACHER' });
    location.pathname = '/submissions/private-a';
    await render();
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 20)); });
    assert.equal(requests.length, 1, 'new teacher must request permission again instead of reusing cached image');
    assert.equal(requests[0].token, 'teacher-b');
    assert.equal(dom.window.document.querySelectorAll('img').length, 0);
    assert.ok(dom.window.document.querySelector('[role="alert"]'));
  });
});

test('authentication failure clears private data and a late previous /me response cannot restore it', async () => {
  await session(async ({ client, tokens, resolveMe, dom }) => {
    await act(async () => tokens.clearTokens());
    assert.equal(client.getQueryCache().getAll().length, 0);
    await act(async () => {
      resolveMe({ userId: 'teacher-a', role: 'TEACHER' });
      await Promise.resolve();
    });
    assert.equal(dom.window.document.querySelectorAll('img').length, 0);
    assert.equal(client.getQueryCache().getAll().length, 0);
  }, true);
});

test('token refresh preserves the current teacher cache and logout removes it', async () => {
  await session(async ({ client, tokens, getAuth, dom }) => {
    assert.equal(dom.window.document.querySelectorAll('img').length, 1);
    await act(async () => tokens.setTokens('refreshed-teacher-a', 'refreshed-a'));
    assert.ok(client.getQueryData(['submissionImage', 'private-a']));
    await act(async () => getAuth().logout());
    assert.equal(tokens.getAccessToken(), null);
    assert.equal(client.getQueryCache().getAll().length, 0);
    assert.equal(dom.window.document.querySelectorAll('img').length, 0);
  });
});

test('teacher SSO exchanges a scrubbed ticket once in StrictMode and starts a clean session', async () => {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error));
  const dom = new JSDOM('<div id="root"></div>', {
    url: 'https://teacher.mathvision.example/login#sso=teacher-ticket', virtualConsole,
  });
  const previous = { window: globalThis.window, document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const client = new QueryClient();
  const { AuthTokenStore: tokens } = load('../src/services/api/AuthTokenStore.ts', {});
  tokens.setTokens('teacher-a', 'refresh-a');
  client.setQueryData(['submissionImage', 'private-a'], new Blob(['old private image']));
  let finish;
  const response = new Promise(resolve => { finish = resolve; });
  const calls = [];
  const routes = [];
  const navigate = (to, options) => routes.push({ to, options });
  const location = { pathname: '/login' };
  const context = load('../src/components/layout/AuthContext.tsx', {
    'react-router-dom': { useNavigate: () => navigate, useLocation: () => location },
    '../../services/api/ServiceLocator': { AppTeacherService: {} },
    '../../services/api/AuthTokenStore': { AuthTokenStore: tokens },
    '../../services/api/apiClient': {}, '../../config/runtime': {},
  });
  const placeholder = ({ children }) => React.createElement('div', null, children);
  const params = new URLSearchParams();
  const page = load('../src/pages/LoginPage.tsx', {
    '@mui/material': new Proxy({}, { get: () => placeholder }),
    '@mui/icons-material': new Proxy({}, { get: () => placeholder }),
    'react-router-dom': { useNavigate: () => navigate, useSearchParams: () => [params] },
    '../services/api/ServiceLocator': { AppTeacherService: {} },
    '../services/api/AuthTokenStore': { AuthTokenStore: tokens },
    '../config/runtime': { appConfig: { portalOrigin: 'https://portal.mathvision.example' }, showDevTools: false },
    '../services/api/apiClient': { post: (url, payload) => {
      assert.equal(dom.window.location.hash, '');
      calls.push({ url, payload });
      return response;
    } },
  });
  const root = require('react-dom/client').createRoot(dom.window.document.getElementById('root'));
  try {
    await act(async () => root.render(React.createElement(React.StrictMode, null,
      React.createElement(QueryClientProvider, { client },
        React.createElement(context.AuthProvider, null, React.createElement(page.default))))));
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, '/auth/sso/exchange');
    assert.equal(calls[0].payload.code, 'teacher-ticket');
    assert.equal(errors.length, 0);
    assert.equal(routes.length, 0);
    await act(async () => {
      finish({ data: { accessToken: 'teacher-b', refreshToken: 'refresh-b' } });
      await response;
    });
    assert.equal(tokens.getAccessToken(), 'teacher-b');
    assert.equal(client.getQueryCache().getAll().length, 0);
    assert.equal(calls.length, 1);
    assert.equal(routes[0].to, '/dashboard');
    assert.equal(errors.length, 0);
  } finally {
    await act(async () => root.unmount());
    client.clear();
    dom.window.close();
    Object.assign(globalThis, previous);
  }
});
