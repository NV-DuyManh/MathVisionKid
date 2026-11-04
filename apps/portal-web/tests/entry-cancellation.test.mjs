import React, { act } from 'react';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';
const require = createRequire(import.meta.url);

for (const stage of ['profile', 'ticket']) {
  test(`leaving Teacher entry during ${stage} cancels the request and cannot redirect later`, async () => {
    const dom = new JSDOM('<div id="root"></div>', { url: 'https://portal.mathvision.example/teacher' });
    const previous = { window: globalThis.window, document: globalThis.document, IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
    Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
    let resolve, signal, tickets = 0, redirected = false;
    const pending = new Promise(done => { resolve = done; });
    const block = ({ children }) => React.createElement('div', null, children);
    const imports = {
      '@mui/material': new Proxy({}, { get: () => block }),
      '@mui/icons-material/Person': block,
      'react-router-dom': { useNavigate: () => navigate, Link: block },
      '../services/apiClient': { tokenStore: { hasTokens: () => true } },
      '../config/runtime': { appConfig: { teacherOrigin: 'https://teacher.mathvision.example' } },
      '../services/authService': { authService: {
        getMe: async s => { signal = s; return stage === 'profile' ? pending : { role: 'TEACHER' }; },
        requestSsoTicket: async (_role, s) => { tickets++; signal = s; return pending; },
      } },
    };
    const navigate = () => { throw new Error('Unexpected navigation'); };
    const source = transpileModule(readFileSync(new URL('../src/pages/TeacherEntryPage.tsx', import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.ReactJSX, esModuleInterop: true },
    }).outputText;
    const exports = {};
    vm.runInNewContext(source, { exports, AbortController,
      window: { location: { set href(_value) { redirected = true; } } }, require: id => imports[id] ?? require(id) });
    const root = require('react-dom/client').createRoot(dom.window.document.getElementById('root'));
    try {
      await act(async () => root.render(React.createElement(exports.TeacherEntryPage)));
      await act(async () => root.unmount());
      assert.equal(signal.aborted, true);
      await act(async () => resolve(stage === 'profile' ? { role: 'TEACHER' } : { code: 'old-ticket' }));
      assert.equal(redirected, false);
      assert.equal(tickets, stage === 'profile' ? 0 : 1);
    } finally { Object.assign(globalThis, previous); dom.window.close(); }
  });
}
