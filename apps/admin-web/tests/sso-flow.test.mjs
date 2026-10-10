import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import React, { act } from 'react';
import { JSDOM, VirtualConsole } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';

const require = createRequire(import.meta.url);

function load(path, imports) {
  const exports = {};
  const source = transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.React, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(source, {
    exports, window: globalThis.window, document: globalThis.document,
    URLSearchParams, require: id => imports[id] ?? require(id),
  });
  return exports;
}

for (const strict of [false, true]) test(`admin SSO scrubs once and survives delayed exchange${strict ? ' in StrictMode' : ''}`, async () => {
  const navigationErrors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => navigationErrors.push(error));
  const dom = new JSDOM('<div id="root"></div>', {
    url: 'https://admin.mathvision.example/login#sso=one-use-ticket', virtualConsole,
  });
  const previous = { window: globalThis.window, document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const routes = [];
  const exchanges = [];
  let completeExchange;
  const pending = new Promise(resolve => { completeExchange = resolve; });
  const context = load('../src/context/AuthContext.tsx', {
    '../services/api/authService': { authService: {
      exchangeSsoTicket: code => {
        assert.equal(dom.window.location.hash, '', 'ticket must be scrubbed before calling backend');
        exchanges.push(code);
        return pending;
      },
    } },
    '../services/api/tokenStore': { tokenStore: { hasTokens: () => false } },
    '../config/runtime': { appConfig: { portalOrigin: 'https://portal.mathvision.example' } },
  });
  const navigate = (to, options) => routes.push({ to, options });
  const location = { search: '', state: null };
  const placeholder = ({ children }) => React.createElement('div', null, children);
  const page = load('../src/pages/LoginPage.tsx', {
    '@mui/material': new Proxy({}, { get: () => placeholder }),
    '@mui/icons-material/Visibility': placeholder,
    '@mui/icons-material/VisibilityOff': placeholder,
    '@mui/icons-material/AdminPanelSettings': placeholder,
    '@mui/icons-material/FlashOn': placeholder,
    '../context/AuthContext': context,
    'react-router-dom': { useNavigate: () => navigate, useLocation: () => location },
    '../config/runtime': { appConfig: { portalOrigin: 'https://portal.mathvision.example' }, showDevTools: false },
  });
  const { createRoot } = await import('react-dom/client');
  const root = createRoot(dom.window.document.getElementById('root'));
  try {
    await act(async () => {
      const pageElement = React.createElement(context.AuthProvider, null, React.createElement(page.LoginPage));
      root.render(strict ? React.createElement(React.StrictMode, null, pageElement) : pageElement);
    });
    assert.deepEqual(exchanges, ['one-use-ticket']);
    assert.equal(routes.length, 0, 'dashboard must wait for the backend exchange');
    assert.equal(navigationErrors.length, 0, 'loading must not redirect back to Portal after fragment scrub');
    await act(async () => {
      completeExchange({ userId: 'owner', role: 'ADMIN' });
      await pending;
    });
    assert.deepEqual(exchanges, ['one-use-ticket']);
    assert.equal(routes.length, 1);
    assert.equal(routes[0].to, '/dashboard');
    assert.equal(routes[0].options.replace, true);
    assert.equal(navigationErrors.length, 0);
  } finally {
    await act(async () => root.unmount());
    dom.window.close();
    Object.assign(globalThis, previous);
  }
});
