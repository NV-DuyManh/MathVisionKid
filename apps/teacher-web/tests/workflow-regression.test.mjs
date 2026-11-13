import React, { act } from 'react';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation } from 'react-router-dom';
import * as queryRuntime from '@tanstack/react-query';
import * as routerRuntime from 'react-router-dom';

const require = createRequire(import.meta.url);
function load(name, imports, globals = {}) {
  const source = transpileModule(readFileSync(new URL(`../src/${name}.tsx`, import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, ...globals, require: id => imports[id] ?? require(id) });
  return exports.default;
}

async function screen(run) {
  const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/' });
  const previous = { window: globalThis.window, document: globalThis.document, IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const root = require('react-dom/client').createRoot(dom.window.document.getElementById('root'));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const controls = {};
  const block = ({ children, title, action, label }) => React.createElement('div', null, title, label, children, action);
  const makeMui = name => {
    if (name === 'Button' || name === 'IconButton') return ({ children, onClick, disabled, ...p }) =>
      React.createElement('button', { onClick, disabled, 'aria-label': p['aria-label'] }, children);
    if (name === 'Alert') return ({ children, action }) => React.createElement('div', { role: 'alert' }, children, action);
    if (name === 'Dialog') return ({ open, children }) => open ? React.createElement('div', { role: 'dialog' }, children) : null;
    if (name === 'Select') return props => {
      controls[props.label] = props;
      return React.createElement('div', null, props.children);
    };
    if (name === 'Box') return ({ children, onKeyDown, tabIndex, ...p }) => React.createElement('div', { ref: p.ref, onKeyDown, tabIndex }, children);
    return block;
  };
  const mui = new Proxy({}, { get: (target, name) => target[name] ??= makeMui(name) });
  let path;
  function Path() { const location = useLocation(); React.useEffect(() => { path = location; }, [location]); return null; }
  const render = async (Component, props = {}, entry = '/') => {
    await act(async () => root.render(React.createElement(QueryClientProvider, { client },
      React.createElement(MemoryRouter, { initialEntries: [entry] }, React.createElement(Path), React.createElement(Component, props)))));
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 15)); });
  };
  const imports = { '@tanstack/react-query': queryRuntime, 'react-router-dom': routerRuntime,
    '@mui/material': mui, '@mui/icons-material': new Proxy({}, { get: () => () => null }),
    '../services/api/newCreationRequestId': { newCreationRequestId: () => '173f718e-2c21-4a98-8c0e-f01337cabaf1' },
    '../services/api/AuthTokenStore': { AuthTokenStore: { getSessionId: () => null } },
    '../hooks/useUploadDraftGuard': { useUploadDraftGuard: () => ({ confirmation: null, allowNextNavigation() {} }) },
    '../components/common/PageHeader': { PageHeader: block }, '../components/common/EmptyState': { EmptyState: block },
    '../components/common/StatusChip': { StatusChip: block } };
  try { await run({ dom, root, render, imports, controls, path: () => path }); }
  finally { await act(async () => root.unmount()); client.clear(); Object.assign(globalThis, previous); dom.window.close(); }
}

for (const [page, method, empty] of [
  ['ClassesPage', 'getClasses', 'Chưa có lớp học nào được phân công'],
  ['AssignmentsPage', 'getAssignments', 'Chưa có bài tập nào'],
  ['BatchesPage', 'getBatches', 'Chưa có đợt chấm bài nào'],
]) {
  test(`${page}: network failure stays an error, retry can show a genuine empty list`, () => screen(async ({ dom, render, imports }) => {
    let attempts = 0;
    const Component = load(`pages/${page}`, { ...imports, '../services/api/ServiceLocator': { AppTeacherService: {
      [method]: async () => { if (++attempts === 1) throw new Error('offline'); return []; },
    } } });
    await render(Component);
    assert.match(dom.window.document.body.textContent, /Chưa tải được danh sách/);
    assert.ok(!dom.window.document.body.textContent.includes(empty));
    await act(async () => [...dom.window.document.querySelectorAll('button')].find(b => b.textContent === 'Thử lại').click());
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 15)); });
    assert.match(dom.window.document.body.textContent, new RegExp(empty));
    assert.equal(attempts, 2);
  }));
}

test('batch creation without navigation state lets the teacher choose an assignment and retains it in the URL', () => screen(async ({ dom, render, imports, controls, path }) => {
  const rosterRequests = [];
  const Component = load('pages/BatchCreatePage', { ...imports, './PrivacyEditorModal': () => null,
    '../services/api/ServiceLocator': { AppTeacherService: {
      getAssignments: async () => [{ assignmentId: 'a-1', title: 'Cộng' }],
      getAssignmentRoster: async id => { rosterRequests.push(id); return [{ id: 's-1', name: 'A' }]; },
    } },
  });
  await render(Component, {}, '/batches/create');
  assert.equal(rosterRequests.length, 0);
  await act(async () => controls['Bài tập cần chấm'].onChange({ target: { value: 'a-1' } }));
  await act(async () => { await new Promise(resolve => setTimeout(resolve, 15)); });
  assert.equal(path().search, '?assignmentId=a-1');
  assert.equal(rosterRequests.join(), 'a-1');
  assert.ok(!dom.window.document.body.textContent.includes('Missing assignment'));
}));

test('privacy editor ignores a previous image load and rejects a failed current image', () => screen(async ({ dom, render, imports }) => {
  const images = [], revoked = [];
  class Image { constructor() { images.push(this); } }
  const Component = load('pages/PrivacyEditorModal', imports, {
    Image, URL: { createObjectURL: file => file.name, revokeObjectURL: url => revoked.push(url) },
    ResizeObserver: class { observe() {} disconnect() {} }, window: dom.window, document: dom.window.document,
  });
  const a = { name: 'first.jpg' }, b = { name: 'second.jpg' };
  const props = { open: true, onClose() {}, onSave() {} };
  await render(Component, { ...props, file: a });
  await render(Component, { ...props, file: b });
  await act(async () => { images[0].onload(); images[1].onerror(); });
  assert.deepEqual(revoked, ['first.jpg']);
  assert.match(dom.window.document.body.textContent, /Chưa mở được ảnh/);
  const save = [...dom.window.document.querySelectorAll('button')].find(b => b.textContent === 'Lưu ảnh đã che');
  assert.equal(save.disabled, true);
}));

test('batch upload uses the redacted JPEG and does not create a second batch after an uncertain upload', () => screen(async ({ dom, render, imports, controls }) => {
  let created = 0, uploaded;
  const redacted = new Blob(['redacted pixels'], { type: 'image/jpeg' });
  const Component = load('pages/BatchCreatePage', { ...imports,
    './PrivacyEditorModal': ({ onSave }) => React.createElement('button', { onClick: () => onSave(redacted) }, 'Save redaction'),
    '../services/api/ServiceLocator': { AppTeacherService: {
      getAssignments: async () => [{ assignmentId: 'a-1', title: 'Cộng' }],
      getAssignmentRoster: async () => [{ id: 's-1', name: 'A' }],
      createBatch: async () => { created++; return { batchId: 'b-1', status: 'CREATED', totalCount: 0 }; },
      uploadImages: async (_id, files) => { uploaded = files; throw new Error('Response lost'); },
    } },
  }, { window: dom.window, File: dom.window.File, URL: { createObjectURL: () => 'blob:preview', revokeObjectURL() {} } });
  await render(Component, {}, '/batches/create?assignmentId=a-1');
  const input = dom.window.document.querySelector('input[type="file"]');
  Object.defineProperty(input, 'files', { value: [new dom.window.File(['original'], 'image.webp', { type: 'image/webp' })] });
  await act(async () => input.dispatchEvent(new dom.window.Event('change', { bubbles: true })));
  await act(async () => controls['Học sinh thực hiện'].onChange({ target: { value: 's-1' } }));
  const button = text => [...dom.window.document.querySelectorAll('button')].find(b => b.textContent.trim() === text);
  assert.ok(button('Che thông tin cá nhân'), JSON.stringify([...dom.window.document.querySelectorAll('button')].map(b => b.textContent)));
  await act(async () => button('Che thông tin cá nhân').click());
  await act(async () => button('Save redaction').click());
  await act(async () => { button('Bắt đầu chấm bài bằng AI').click(); button('Bắt đầu chấm bài bằng AI').click(); });
  assert.equal(created, 1);
  assert.equal(uploaded[0].type, 'image/jpeg');
  assert.equal(uploaded[0].name, 'image.jpg');
  assert.equal(button('Bắt đầu chấm bài bằng AI').disabled, true);
  assert.ok(button('Kiểm tra đợt chấm'));
}));

for (const size of [8 * 1024 * 1024, 8 * 1024 * 1024 + 1, 9 * 1024 * 1024]) {
  test(`batch draft validates the ${size}-byte redacted image against Spring's limit`, () => screen(async ({ dom, render, imports, controls }) => {
    const redacted = new Blob([new Uint8Array(size)], { type: 'image/jpeg' });
    const Component = load('pages/BatchCreatePage', { ...imports,
      './PrivacyEditorModal': ({ onSave }) => React.createElement('button', { onClick: () => onSave(redacted) }, 'Save redaction'),
      '../services/api/ServiceLocator': { AppTeacherService: {
        getAssignments: async () => [{ assignmentId: 'a-1', title: 'Cộng' }],
        getAssignmentRoster: async () => [{ id: 's-1', name: 'A' }],
      } },
    }, { window: dom.window, File: dom.window.File, URL: { createObjectURL: () => 'blob:preview', revokeObjectURL() {} } });
    await render(Component, {}, '/batches/create?assignmentId=a-1');
    const input = dom.window.document.querySelector('input[type="file"]');
    Object.defineProperty(input, 'files', { value: [new dom.window.File(['original'], 'image.webp', { type: 'image/webp' })] });
    await act(async () => input.dispatchEvent(new dom.window.Event('change', { bubbles: true })));
    await act(async () => controls['Học sinh thực hiện'].onChange({ target: { value: 's-1' } }));
    const button = text => [...dom.window.document.querySelectorAll('button')].find(b => b.textContent.trim() === text);
    await act(async () => button('Che thông tin cá nhân').click());
    await act(async () => button('Save redaction').click());
    assert.equal(button('Bắt đầu chấm bài bằng AI').disabled, size > 8 * 1024 * 1024);
    if (size > 8 * 1024 * 1024) assert.match(dom.window.document.body.textContent, /image\.webp.*8 MiB/);
  }));
}

test('privacy masks stay aligned with the original image after viewport resizing and export as JPEG', () => screen(async ({ dom, render, imports }) => {
  let image, resize, outputType, saved;
  const painted = [];
  let containerWidth = 532;
  Object.defineProperty(dom.window.HTMLElement.prototype, 'clientWidth', { get: () => containerWidth });
  dom.window.HTMLCanvasElement.prototype.getContext = function () {
    const canvas = this;
    return { setTransform() {}, drawImage() {}, strokeRect() {}, fillStyle: '', lineWidth: 1,
      fillRect: (...rect) => painted.push({ canvas, rect }) };
  };
  dom.window.HTMLCanvasElement.prototype.toBlob = function (callback, type) { outputType = type; callback(new Blob(['pixels'], { type })); };
  const Component = load('pages/PrivacyEditorModal', imports, {
    Image: class { constructor() { image = this; this.width = 1000; this.height = 500; } },
    URL: { createObjectURL: () => 'blob:image', revokeObjectURL() {} }, crypto: { randomUUID: () => 'mask-1' },
    ResizeObserver: class { constructor(callback) { resize = callback; } observe() {} disconnect() {} }, window: dom.window, document: dom.window.document,
  });
  await render(Component, { open: true, file: { name: 'original.webp' }, onClose() {}, onSave: blob => { saved = blob; } });
  await act(async () => image.onload());
  await act(async () => [...dom.window.document.querySelectorAll('button')].find(b => b.textContent === 'Thêm vùng che').click());
  containerWidth = 332;
  await act(async () => resize());
  await act(async () => [...dom.window.document.querySelectorAll('button')].find(b => b.textContent === 'Lưu ảnh đã che').click());
  assert.equal(outputType, 'image/jpeg');
  assert.equal(saved.type, 'image/jpeg');
  assert.deepEqual(painted.at(-1).rect, [0, 0, 400, 50]);
}));
