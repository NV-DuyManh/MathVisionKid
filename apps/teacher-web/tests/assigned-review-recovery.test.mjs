import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { transpileModule, ModuleKind, JsxEmit } from 'typescript';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as queryRuntime from '@tanstack/react-query';

const require = createRequire(import.meta.url);
const conflict = () => Object.assign(new Error('Changed'), { isAxiosError: true, response: { status: 409 } });
const initial = { studentName: 'Synthetic student', prompt: '2 + 2', status: 'AWAITING_REVIEW', maxScore: 10, imageVersion: 1 };

async function screen(run) {
  const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/' });
  const old = { window: globalThis.window, document: globalThis.document, IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT };
  const browserCrypto = { getRandomValues: bytes => globalThis.crypto.getRandomValues(bytes) };
  Object.defineProperty(dom.window, 'crypto', { value: browserCrypto });
  Object.assign(globalThis, { window: dom.window, document: dom.window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const root = createRoot(dom.window.document.getElementById('root'));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const block = ({ children }) => React.createElement('div', null, children);
  const controls = {};
  const mui = {
    Dialog: ({ children, open }) => open ? React.createElement('div', { role: 'dialog' }, children) : null,
    DialogTitle: block, DialogContent: block, DialogActions: block, Typography: block, Box: block, Card: block, Skeleton: block,
    Alert: ({ children, action }) => React.createElement('div', { role: 'alert' }, children, action),
    Button: ({ children, onClick, disabled }) => React.createElement('button', { onClick, disabled }, children),
    FormControlLabel: ({ label, control }) => React.createElement('label', null, label, control),
    Checkbox: ({ checked, onChange }) => React.createElement('input', { type: 'checkbox', checked, onChange: e => onChange(e, e.target.checked) }),
    TextField: props => { const { id, label, value, onChange, onBlur, error, helperText, select, children } = props; controls[label] = props; return React.createElement('label', null, label,
      React.createElement(select ? 'select' : 'input', { id, value, onChange, onBlur, 'aria-label': label,
        'aria-invalid': Boolean(error), 'aria-describedby': helperText && id ? `${id}-helper-text` : undefined }, select ? children : undefined),
      helperText && React.createElement('span', { id: id ? `${id}-helper-text` : undefined }, helperText)); },
    MenuItem: ({ value, children }) => React.createElement('option', { value }, children),
  };
  let api = { get: async () => ({ data: initial }), post: async () => ({}) };
  const imports = { '@mui/material': mui, '@tanstack/react-query': queryRuntime,
    '../services/api/apiClient': { __esModule: true, default: { get: (...args) => api.get(...args), post: (...args) => api.post(...args) } } };
  const helperExports = {};
  const helperSource = transpileModule(readFileSync(new URL('../src/services/api/newCreationRequestId.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS },
  }).outputText;
  vm.runInNewContext(helperSource, { exports: helperExports, window: dom.window });
  imports['../services/api/newCreationRequestId'] = helperExports;
  const source = transpileModule(readFileSync(new URL('../src/pages/AssignedReviewDialog.tsx', import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, AbortController, crypto: browserCrypto,
    URL: { createObjectURL: () => 'blob:synthetic', revokeObjectURL: () => {} },
    require: id => imports[id] ?? require(id) });
  const Component = exports.default;
  const loadPanel = (extraImports) => {
    const panelExports = {};
    const compiled = transpileModule(readFileSync(new URL('../src/pages/ClassAssignmentsPanel.tsx', import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.ReactJSX, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(compiled, { exports: panelExports, crypto: browserCrypto,
      require: id => extraImports[id] ?? imports[id] ?? require(id) });
    return panelExports.ClassAssignmentsPanel;
  };
  const settle = async () => { await act(async () => { await new Promise(resolve => setTimeout(resolve, 25)); }); };
  const render = async (props, Target = Component) => {
    await act(async () => root.render(React.createElement(QueryClientProvider, { client }, React.createElement(Target, props))));
    await settle(); await settle();
  };
  const button = text => [...dom.window.document.querySelectorAll('button')].find(el => el.textContent === text);
  const click = async text => { assert.ok(button(text), `Missing button: ${text}`); await act(async () => button(text).click()); await settle(); };
  const fill = async (label, value) => {
    const input = dom.window.document.querySelector(`[aria-label="${label}"]`);
    assert.ok(input, label);
    await act(async () => controls[label].onChange({ target: { value } }));
  };
  const loadImage = async () => { await act(async () => dom.window.document.querySelector('img').dispatchEvent(new dom.window.Event('load'))); };
  const check = async () => { await act(async () => dom.window.document.querySelectorAll('input[type="checkbox"]').forEach(el => el.click())); };
  const loadClassPage = extraImports => {
    const pageExports = {};
    const compiled = transpileModule(readFileSync(new URL('../src/pages/ClassDetailPage.tsx', import.meta.url), 'utf8'), {
      compilerOptions: { module: ModuleKind.CommonJS, jsx: JsxEmit.ReactJSX, esModuleInterop: true },
    }).outputText;
    vm.runInNewContext(compiled, { exports: pageExports,
      require: id => extraImports[id] ?? imports[id] ?? require(id) });
    return pageExports.default;
  };
  try { await run({ dom, render, settle, click, fill, check, loadImage, button, loadPanel, loadClassPage, client, mui, api: value => { api = value; } }); }
  finally { await act(async () => root.unmount()); client.clear(); Object.assign(globalThis, old); dom.window.close(); }
}

test('cached class navigation isolates the assignment editor, preview and recipient queue', () => screen(async ui => {
  ui.client.setQueryDefaults(['teacher-class'], { gcTime: Infinity, staleTime: Infinity });
  ui.api({ get: async () => ({ data: [] }), post: async () => ({}) });
  let currentClass = 'A';
  const classes = {
    A: { name: 'Class A', studentCount: 1, students: [{ id: 'studentA', name: 'Student A' }] },
    B: { name: 'Class B', studentCount: 1, students: [{ id: 'studentB', name: 'Student B' }] },
  };
  const assignment = { assignmentId: 'draftA', classId: 'A', title: 'Saved draft A', prompt: 'Only class A', status: 'DRAFT', maxScore: 10 };
  const published = { ...assignment, assignmentId: 'publishedA', title: 'Published A', status: 'PUBLISHED', recipientCount: 1 };
  const writes = [];
  let completeOldSave;
  let deferOldSave = false;
  const service = {
    getClassDetail: async id => classes[id],
    listClassAssignments: async id => id === 'A' ? [assignment, published] : [],
    saveAssignmentDraft: async body => {
      writes.push(body);
      if (deferOldSave && body.classId === 'A') return new Promise(resolve => { completeOldSave = resolve; });
      return {};
    },
  };
  const panel = ui.loadPanel({
    '../services/api/ServiceLocator': { AppTeacherService: service },
    '../types': { MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION', VERTICAL_SUBTRACTION: 'VERTICAL_SUBTRACTION' } },
    './AssignedReviewDialog': { __esModule: true, default: () => null },
  });
  const block = ({ children, title }) => React.createElement('div', null, title, children);
  const Page = ui.loadClassPage({
    'react-router-dom': { useParams: () => ({ id: currentClass }), Link: block },
    '@mui/material': { ...ui.mui, List: block, ListItem: block, ListItemText: block,
      Tab: ({ label, onClick }) => React.createElement('button', { onClick }, label),
      Tabs: ({ children, onChange }) => React.createElement('div', null,
        React.Children.map(children, (child, index) => React.cloneElement(child, { onClick: () => onChange(null, index) }))),
    },
    '../components/common/PageHeader': { PageHeader: block },
    './ClassroomFoundation': { ClassroomSettings: () => null },
    './ClassAssignmentsPanel': { ClassAssignmentsPanel: panel },
    '../services/api/ServiceLocator': { AppTeacherService: service },
  });
  for (const id of ['A', 'B']) ui.client.setQueryData(['teacher-class', id], classes[id]);
  const go = async id => { currentClass = id; await ui.render({}, Page); };
  for (const action of ['Tạo bài tập', 'Sửa bản nháp', 'Xem trước', 'Bài nộp của lớp']) {
    await go('A');
    await ui.click('Bài tập');
    await ui.click(action);
    if (action === 'Tạo bài tập') {
      await ui.fill('Tên bài tập', 'Unsaved A');
      await ui.fill('Đề toán', 'Private draft A');
    }
    assert.ok(ui.dom.window.document.querySelector('[role=dialog]'), `Missing A dialog for ${action}`);
    await go('B');
    assert.match(ui.dom.window.document.body.textContent, /Class B/);
    assert.equal(Boolean(ui.dom.window.document.querySelector('[role=dialog]')), false, `A ${action} leaked into cached class B`);
  }
  await go('A');
  await ui.click('Bài tập');
  await ui.click('Tạo bài tập');
  await ui.fill('Tên bài tập', 'Save A in flight');
  await ui.fill('Đề toán', 'Only A');
  deferOldSave = true;
  await ui.click('Lưu bản nháp');
  assert.equal(typeof completeOldSave, 'function');
  await go('B');
  await ui.click('Bài tập');
  await ui.click('Tạo bài tập');
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Tên bài tập"]').value, '');
  await ui.fill('Tên bài tập', 'New B');
  await ui.fill('Đề toán', 'Only class B');
  await act(async () => completeOldSave({}));
  await ui.settle();
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Tên bài tập"]').value, 'New B', 'Late A save closed or replaced the B editor');
  await ui.click('Lưu bản nháp');
  assert.equal(writes.length, 2);
  assert.equal(writes[0].classId, 'A');
  assert.equal(writes[1].classId, 'B');
  assert.equal(writes[1].title, 'New B');
  assert.equal(writes[1].assignmentId, undefined);
}));

test('image conflict reloads current metadata and the new image without closing review', () => screen(async ui => {
  let current = 1;
  const images = [];
  ui.api({ get: async (url, config) => {
    if (url.endsWith('/image')) { images.push(config.params.imageVersion); if (config.params.imageVersion === 1) throw conflict(); return { data: {} }; }
    const value = current; current = 2;
    return { data: { ...initial, imageVersion: value } };
  }, post: async () => ({}) });
  await ui.render({ id: 'first', onClose() {}, onSaved() {} });
  await ui.click('Tải phiên bản mới');
  assert.match(ui.dom.window.document.body.textContent, /Phiên bản ảnh 2/);
  assert.deepEqual(images, [1, 2]);
  assert.equal(ui.button('Chấm và trả').disabled, true);
}));

test('missing old image returns 404 and generic retry fetches metadata before requesting version 2', () => screen(async ui => {
  let detailReads = 0;
  const requests = [];
  ui.api({ get: async (url, config) => {
    if (url.endsWith('/image')) {
      requests.push(`image:${config.params.imageVersion}`);
      if (config.params.imageVersion === 1) {
        throw Object.assign(new Error('Not found'), { isAxiosError: true, response: { status: 404 } });
      }
      return { data: {} };
    }
    requests.push('detail');
    return { data: { ...initial, imageVersion: ++detailReads === 1 ? 1 : 2 } };
  }, post: async () => ({}) });
  await ui.render({ id: 'first', onClose() {}, onSaved() {} });
  assert.match(ui.dom.window.document.body.textContent, /Chưa tải được ảnh bài làm/);
  assert.equal(ui.button('Tải phiên bản mới'), undefined);
  await ui.click('Tải lại ảnh');
  assert.deepEqual(requests, ['detail', 'image:1', 'detail', 'image:2']);
  assert.match(ui.dom.window.document.body.textContent, /Phiên bản ảnh 2/);
  assert.equal(ui.button('Chấm và trả').disabled, true);
}));

test('grade conflict discards old confirmations and grade before reloading version 2', () => screen(async ui => {
  let current = 1;
  ui.api({ get: async url => ({ data: url.endsWith('/image') ? {} : { ...initial, imageVersion: current } }),
    post: async () => { current = 2; throw conflict(); } });
  await ui.render({ id: 'first', onClose() {}, onSaved() {} });
  await ui.loadImage(); await ui.check(); await ui.fill('Điểm (0–10)', '8'); await ui.fill('Nhận xét', 'Old image feedback');
  assert.equal(ui.button('Chấm và trả').disabled, false);
  await ui.click('Chấm và trả');
  await ui.click('Tải phiên bản mới');
  assert.match(ui.dom.window.document.body.textContent, /Phiên bản ảnh 2/);
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Điểm (0–10)"]').value, '');
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Nhận xét"]').value, '');
  assert.ok([...ui.dom.window.document.querySelectorAll('input[type="checkbox"]')].every(el => !el.checked));
  await ui.loadImage();
  assert.equal(ui.button('Chấm và trả').disabled, true);
}));

test('late grade success from a closed review cannot save or close another review', () => screen(async ui => {
  let finish;
  let saves = 0;
  ui.api({ get: async url => ({ data: url.endsWith('/image') ? {} : initial }),
    post: () => new Promise(resolve => { finish = resolve; }) });
  await ui.render({ id: 'first', onClose() {}, onSaved() { saves++; } });
  await ui.loadImage(); await ui.check(); await ui.fill('Điểm (0–10)', '8'); await ui.click('Chấm và trả');
  await ui.render({ id: 'second', onClose() {}, onSaved() { saves++; } });
  await act(async () => finish({})); await ui.settle();
  assert.equal(saves, 0);
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Điểm (0–10)"]').value, '');
}));

test('saving keeps review available for next pending work and Back preserves the queue filter', () => screen(async ui => {
  let saved = false;
  ui.api({ get: async () => ({ data: [
    { studentId: 'one', studentName: 'One', submissionId: 'first', status: saved ? 'GRADE_RELEASED' : 'AWAITING_REVIEW' },
    { studentId: 'two', studentName: 'Two', submissionId: 'second', status: 'AWAITING_REVIEW' },
  ] }) });
  const Panel = ui.loadPanel({
    '../types': { MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION' } },
    '../services/api/ServiceLocator': { AppTeacherService: { listClassAssignments: async () => [
      { assignmentId: 'assignment', title: 'Synthetic', status: 'PUBLISHED', recipientCount: 2 },
    ] } },
    './AssignedReviewDialog': { __esModule: true, default: props => React.createElement('div', null, `Review ${props.id}`,
      React.createElement('button', { onClick: () => { saved = true; props.onSaved('release-grade'); } }, 'Save'),
      props.onNext && React.createElement('button', { onClick: props.onNext }, 'Next'),
      React.createElement('button', { onClick: props.onClose }, 'Back')) },
  });
  await ui.render({ classId: 'class', studentCount: 2 }, Panel);
  await ui.click('Bài nộp của lớp');
  await ui.fill('Trạng thái bài nộp', 'AWAITING_REVIEW');
  await ui.click('Mở bài làm');
  await ui.click('Save');
  assert.match(ui.dom.window.document.body.textContent, /Review first/);
  await ui.click('Next');
  assert.match(ui.dom.window.document.body.textContent, /Review second/);
  await ui.click('Back');
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Trạng thái bài nộp"]').value, 'AWAITING_REVIEW');
  assert.equal([...ui.dom.window.document.querySelectorAll('button')].filter(el => el.textContent === 'Mở bài làm').length, 1);
}));

test('Next skips completed reviews while the queue refresh is delayed', () => screen(async ui => {
  const queue = ['first', 'second', 'third'].map(id => ({ studentId: id, studentName: id,
    submissionId: id, status: 'AWAITING_REVIEW' }));
  let reads = 0;
  ui.api({ get: async (_, { signal }) => ++reads === 1 ? { data: queue } : new Promise((_, reject) => {
    signal.addEventListener('abort', () => reject(new Error('Cancelled')), { once: true });
  }) });
  const Panel = ui.loadPanel({
    '../types': { MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION' } },
    '../services/api/ServiceLocator': { AppTeacherService: { listClassAssignments: async () => [
      { assignmentId: 'assignment', title: 'Synthetic', status: 'PUBLISHED', recipientCount: 3 },
    ] } },
    './AssignedReviewDialog': { __esModule: true, default: props => React.createElement('div', null, `Review ${props.id}`,
      React.createElement('button', { onClick: () => props.onSaved('release-grade') }, 'Save'),
      props.onNext && React.createElement('button', { onClick: props.onNext }, 'Next'),
      React.createElement('button', { onClick: props.onClose }, 'Back')) },
  });
  await ui.render({ classId: 'class', studentCount: 3 }, Panel);
  await ui.click('Bài nộp của lớp');
  await ui.fill('Trạng thái bài nộp', 'AWAITING_REVIEW');
  await ui.click('Mở bài làm');
  await ui.click('Save');
  await ui.click('Next');
  assert.match(ui.dom.window.document.body.textContent, /Review second/);
  await ui.click('Save');
  await ui.click('Next');
  assert.match(ui.dom.window.document.body.textContent, /Review third/);
  await ui.click('Back');
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Trạng thái bài nộp"]').value, 'AWAITING_REVIEW');
}));

test('a publish response failure is announced inside the dialog without claiming the draft was unchanged', () => screen(async ui => {
  const Panel = ui.loadPanel({
    '../types': { MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION' } },
    '../services/api/ServiceLocator': { AppTeacherService: {
      listClassAssignments: async () => [{ assignmentId: 'assignment', title: 'Synthetic', status: 'DRAFT' }],
      publishAssignment: async () => { throw new Error('Synthetic response lost'); },
    } },
    './AssignedReviewDialog': { __esModule: true, default: () => null },
  });
  await ui.render({ classId: 'class', studentCount: 2 }, Panel);
  await ui.click('Giao bài');
  await ui.click('Xác nhận giao');
  const alert = ui.dom.window.document.querySelector('[role="dialog"] [role="alert"]');
  assert.match(alert?.textContent ?? '', /Chưa xác nhận được kết quả giao bài/);
  assert.equal(ui.button('Xác nhận giao').disabled, false);
}));

test('successful zero grade hides editable assessment and exposes the explicit next action', () => screen(async ui => {
  let released = false;
  let saves = 0;
  let next = 0;
  let submitted;
  ui.api({ get: async url => ({ data: url.endsWith('/image') ? {} : { ...initial, status: released ? 'GRADE_RELEASED' : 'AWAITING_REVIEW' } }),
    post: async (_url, body) => { submitted = body; released = true; return {}; } });
  await ui.render({ id: 'first', onClose() {}, onSaved() { saves++; }, onNext() { next++; } });
  await ui.loadImage(); await ui.check(); await ui.fill('Điểm (0–10)', '0');
  await ui.click('Chấm và trả');
  assert.equal(submitted.score, 0);
  assert.equal(saves, 1);
  assert.equal(ui.dom.window.document.querySelector('[aria-label="Điểm (0–10)"]'), null);
  await ui.click('Mở bài tiếp theo');
  assert.equal(next, 1);
}));

test('score explains blank, decimal and out-of-range values through associated feedback and accepts zero', () => screen(async ui => {
  ui.api({ get: async url => ({ data: url.endsWith('/image') ? {} : initial }), post: async () => ({}) });
  await ui.render({ id: 'first', onClose() {}, onSaved() {} });
  await ui.loadImage(); await ui.check();
  const input = () => ui.dom.window.document.querySelector('[aria-label="Điểm (0–10)"]');
  for (const value of ['', '1.5', '-1', '11']) {
    await ui.fill('Điểm (0–10)', value);
    await act(async () => input().dispatchEvent(new ui.dom.window.FocusEvent('focusout', { bubbles: true })));
    assert.equal(input().getAttribute('aria-invalid'), 'true', `Invalid score ${value}`);
    const feedback = ui.dom.window.document.getElementById(input().getAttribute('aria-describedby'));
    assert.match(feedback?.textContent ?? '', /Nhập điểm nguyên từ 0 đến 10/);
    assert.equal(ui.button('Chấm và trả').disabled, true);
  }
  await ui.fill('Điểm (0–10)', '0');
  assert.equal(input().getAttribute('aria-invalid'), 'false');
  assert.equal(ui.button('Chấm và trả').disabled, false);
}));

test('LAN HTTP without randomUUID can create and edit drafts and release a grade with valid request IDs', () => screen(async ui => {
  const drafts = [];
  const Panel = ui.loadPanel({
    '../types': { MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION' } },
    '../services/api/ServiceLocator': { AppTeacherService: {
      listClassAssignments: async () => [{ assignmentId: 'assignment', title: 'Synthetic', prompt: '2 + 2',
        mathType: 'VERTICAL_ADDITION', maxScore: 10, status: 'DRAFT' }],
      saveAssignmentDraft: async draft => { drafts.push(draft); },
    } },
    './AssignedReviewDialog': { __esModule: true, default: () => null },
  });
  await ui.render({ classId: 'class', studentCount: 2 }, Panel);
  await ui.click('Tạo bài tập');
  await ui.fill('Tên bài tập', 'New synthetic');
  await ui.fill('Đề toán', '3 + 3');
  await ui.click('Lưu bản nháp');
  await ui.click('Sửa bản nháp');
  await ui.fill('Tên bài tập', 'Edited synthetic');
  await ui.click('Lưu bản nháp');
  let submitted;
  ui.api({ get: async url => ({ data: url.endsWith('/image') ? {} : initial }),
    post: async (_, body) => { submitted = body; return {}; } });
  await ui.render({ id: 'first', onClose() {}, onSaved() {} });
  await ui.loadImage(); await ui.check(); await ui.fill('Điểm (0–10)', '0');
  await ui.fill('Nhận xét', 'Synthetic feedback');
  await ui.click('Chấm và trả');
  const ids = [...drafts.map(draft => draft.creationRequestId), submitted.requestId];
  assert.equal(ids.length, 3);
  assert.equal(new Set(ids).size, 3);
  for (const id of ids) assert.match(id, /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  assert.equal(submitted.score, 0);
}));
