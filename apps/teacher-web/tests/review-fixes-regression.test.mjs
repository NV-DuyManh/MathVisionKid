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
  vm.runInNewContext(source, {
    exports,
    window: globalThis.window,
    document: globalThis.document,
    setTimeout: globalThis.setTimeout,
    clearTimeout: globalThis.clearTimeout,
    ...globals,
    require: id => imports[id] ?? require(id)
  });
  return exports.default;
}

async function screen(run) {
  const dom = new JSDOM('<div id="root"></div>', { url: 'http://localhost/' });
  const previous = {
    window: globalThis.window,
    document: globalThis.document,
    IS_REACT_ACT_ENVIRONMENT: globalThis.IS_REACT_ACT_ENVIRONMENT
  };
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
    if (name === 'Select' || name === 'TextField') return props => {
      controls[props.label || props.placeholder] = props;
      return React.createElement('div', null, props.label, props.children);
    };
    if (name === 'Box') return ({ children, component, ...p }) => React.createElement(component || 'div', p, children);
    return block;
  };
  const mui = new Proxy({}, { get: (target, name) => target[name] ??= makeMui(name) });
  let path;
  function Path() { const location = useLocation(); React.useEffect(() => { path = location; }, [location]); return null; }
  const render = async (Component, props = {}, entry = '/') => {
    await act(async () => root.render(React.createElement(QueryClientProvider, { client },
      React.createElement(MemoryRouter, { initialEntries: [entry] }, React.createElement(Path), React.createElement(Component, props)))));
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 50)); });
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 50)); });
  };
  const imports = {
    '../config/runtime': { notebookPreview: false },
    '../services/api/AuthTokenStore': { AuthTokenStore: { getSessionId: () => 'test-session' } },
    '@tanstack/react-query': queryRuntime,
    'react-router-dom': routerRuntime,
    '@mui/material': mui,
    '@mui/icons-material': new Proxy({}, { get: () => () => null }),
    '../components/common/PageHeader': { PageHeader: block },
    '../components/common/EmptyState': { EmptyState: block },
    '../components/common/StatusChip': { StatusChip: block },
    './SubmissionRetake': { SubmissionRetake: block },
  };
  try { await run({ dom, root, render, imports, controls, path: () => path }); }
  finally { await act(async () => root.unmount()); client.clear(); Object.assign(globalThis, previous); dom.window.close(); }
}

// ---------------------------------------------------------
// R2: SpringTeacherService upload progress
// ---------------------------------------------------------
test('R2: SpringTeacherService wires onUploadProgress and handles valid/zero/missing total', async () => {
  let capturedConfig = null;
  const mockApi = {
    post: async (url, data, config) => {
      capturedConfig = config;
      return { data: {} };
    }
  };

  const serviceSource = transpileModule(
    readFileSync(new URL('../src/services/api/SpringTeacherService.ts', import.meta.url), 'utf8'),
    { compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true } }
  ).outputText;
  const serviceExports = {};
  vm.runInNewContext(serviceSource, {
    exports: serviceExports,
    FormData,
    require: id => id === './apiClient' ? mockApi : { AuthTokenStore: { setTokens() {} } }
  });

  const progressValues = [];
  const fakeFile = new File(['fake content'], 'test.jpg', { type: 'image/jpeg' });
  await serviceExports.SpringTeacherService.uploadImages('batch-123', [fakeFile], [], percent => {
    progressValues.push(percent);
  });

  assert.ok(capturedConfig, 'apiClient.post was called with config');
  assert.equal(typeof capturedConfig.onUploadProgress, 'function', 'onUploadProgress handler was provided');

  // Test progress events:
  // 1. Valid total
  capturedConfig.onUploadProgress({ loaded: 25, total: 100 });
  capturedConfig.onUploadProgress({ loaded: 100, total: 100 });
  // 2. Zero total (should be ignored, not emit NaN or Infinity)
  capturedConfig.onUploadProgress({ loaded: 0, total: 0 });
  // 3. Missing total (should be ignored)
  capturedConfig.onUploadProgress({ loaded: 50 });

  assert.deepEqual(progressValues, [25, 100]);
});

// ---------------------------------------------------------
// R3: ReviewQueuePage displays denominator matching assignment/submission scale
// ---------------------------------------------------------
test('R3: ReviewQueuePage displays denominator matching assignment/submission scale (10, 100, 0, undefined)', async () => {
  await screen(async ({ dom, render, imports }) => {
    const Component = load('pages/ReviewQueuePage', {
      ...imports,
      'react-router-dom': { ...routerRuntime, useParams: () => ({ id: 'batch-test' }) },
      '../services/api/AuthTokenStore': { AuthTokenStore: { getSessionId: () => 'test-session' } },
      '../services/api/ServiceLocator': {
        AppTeacherService: {
          getBatchStatus: async () => ({ status: 'COMPLETED', totalCount: 4, processedCount: 4, pendingReviewCount: 4, finalizedCount: 0, failedCount: 0 }),
          getReviewQueue: async () => [
            { submissionId: 's1', studentName: 'Pupil 100', maxScore: 100, suggestedScore: 80, status: 'PROPOSED_GRADE' },
            { submissionId: 's2', studentName: 'Pupil 10', maxScore: 10, suggestedScore: 8, status: 'PROPOSED_GRADE' },
            { submissionId: 's3', studentName: 'Pupil Zero', maxScore: 10, suggestedScore: 0, status: 'PROPOSED_GRADE' },
            { submissionId: 's4', studentName: 'Pupil Unchecked', maxScore: 10, suggestedScore: undefined, status: 'PROPOSED_GRADE' },
          ]
        }
      }
    });

    await render(Component);
    const text = dom.window.document.body.textContent;
    assert.ok(text.includes('80 / 100 điểm'), 'Sub 1 with maxScore 100 must show 80 / 100 điểm');
    assert.ok(!text.includes('80 / 10 điểm'), 'Must not display 80 / 10 điểm');
    assert.ok(text.includes('8 / 10 điểm'), 'Sub 2 with maxScore 10 must show 8 / 10 điểm');
    assert.ok(text.includes('0 / 10 điểm'), 'Sub 3 with zero score must show 0 / 10 điểm');
    assert.ok(text.includes('Chưa chấm'), 'Sub 4 without score proposal must show Chưa chấm');
  });
});

test('SCRUM-111: ReviewQueuePage filters by status, searches by student name, and handles queue count', async () => {
  await screen(async ({ dom, render, imports, controls }) => {
    const Component = load('pages/ReviewQueuePage', {
      ...imports,
      'react-router-dom': { ...routerRuntime, useParams: () => ({ id: 'batch-filter-test' }) },
      '../services/api/AuthTokenStore': { AuthTokenStore: { getSessionId: () => 'test-session' } },
      '../services/api/ServiceLocator': {
        AppTeacherService: {
          getBatchStatus: async () => ({ status: 'COMPLETED', totalCount: 3, processedCount: 3, pendingReviewCount: 3, finalizedCount: 0, failedCount: 0 }),
          getReviewQueue: async () => [
            { submissionId: 'sub-b', studentName: 'Tran Thi Binh', maxScore: 10, suggestedScore: 7, status: 'PROPOSED_GRADE', recognitionConfidence: 95 },
            { submissionId: 'sub-a', studentName: 'Nguyen Van An', maxScore: 10, suggestedScore: 9, status: 'REVIEW_REQUIRED', recognitionConfidence: 60 },
            { submissionId: 'sub-c', studentName: 'Le Van Cuong', maxScore: 10, suggestedScore: 5, status: 'NEEDS_CONFIRMATION', recognitionConfidence: 80 },
          ]
        }
      }
    });

    await render(Component);

    const getRenderedStudentOrder = () => {
      const text = dom.window.document.body.textContent;
      const students = ['Nguyen Van An', 'Tran Thi Binh', 'Le Van Cuong'];
      return students
        .map(name => ({ name, pos: text.indexOf(name) }))
        .filter(x => x.pos !== -1)
        .sort((a, b) => a.pos - b.pos)
        .map(x => x.name);
    };

    // Initial: shows all 3 in fixture order (Binh -> An -> Cuong), distinct from any sort mode
    assert.ok(dom.window.document.body.textContent.includes('Hiển thị 3 / 3 bài'));
    assert.deepEqual(getRenderedStudentOrder(), ['Tran Thi Binh', 'Nguyen Van An', 'Le Van Cuong']);

    // Filter by status: REVIEW_REQUIRED
    await act(async () => controls['Trạng thái'].onChange({ target: { value: 'REVIEW_REQUIRED' } }));
    assert.ok(dom.window.document.body.textContent.includes('Hiển thị 1 / 3 bài'));
    assert.deepEqual(getRenderedStudentOrder(), ['Nguyen Van An']);
    assert.ok(!dom.window.document.body.textContent.includes('Tran Thi Binh'));
    assert.ok(!dom.window.document.body.textContent.includes('Le Van Cuong'));

    // Reset status filter to ALL
    await act(async () => controls['Trạng thái'].onChange({ target: { value: 'ALL' } }));
    assert.ok(dom.window.document.body.textContent.includes('Hiển thị 3 / 3 bài'));
    assert.deepEqual(getRenderedStudentOrder(), ['Tran Thi Binh', 'Nguyen Van An', 'Le Van Cuong']);

    // Search by student name: "Binh"
    await act(async () => controls['Tên học sinh'].onChange({ target: { value: 'Binh' } }));
    assert.ok(dom.window.document.body.textContent.includes('Hiển thị 1 / 3 bài'));
    assert.deepEqual(getRenderedStudentOrder(), ['Tran Thi Binh']);
    assert.ok(!dom.window.document.body.textContent.includes('Nguyen Van An'));
    assert.ok(!dom.window.document.body.textContent.includes('Le Van Cuong'));

    // Reset search to empty string
    await act(async () => controls['Tên học sinh'].onChange({ target: { value: '' } }));
    assert.ok(dom.window.document.body.textContent.includes('Hiển thị 3 / 3 bài'));
    assert.deepEqual(getRenderedStudentOrder(), ['Tran Thi Binh', 'Nguyen Van An', 'Le Van Cuong']);

    // Sort by SCORE_ASC (lowest to highest score: Cuong(5) -> Binh(7) -> An(9))
    await act(async () => controls['Sắp xếp theo'].onChange({ target: { value: 'SCORE_ASC' } }));
    assert.equal(controls['Sắp xếp theo'].value, 'SCORE_ASC');
    assert.deepEqual(getRenderedStudentOrder(), ['Le Van Cuong', 'Tran Thi Binh', 'Nguyen Van An']);

    // Sort by SCORE_DESC (highest to lowest score: An(9) -> Binh(7) -> Cuong(5))
    await act(async () => controls['Sắp xếp theo'].onChange({ target: { value: 'SCORE_DESC' } }));
    assert.equal(controls['Sắp xếp theo'].value, 'SCORE_DESC');
    assert.deepEqual(getRenderedStudentOrder(), ['Nguyen Van An', 'Tran Thi Binh', 'Le Van Cuong']);

    // Sort by CONFIDENCE_ASC (lowest to highest confidence: An(60) -> Cuong(80) -> Binh(95))
    await act(async () => controls['Sắp xếp theo'].onChange({ target: { value: 'CONFIDENCE_ASC' } }));
    assert.equal(controls['Sắp xếp theo'].value, 'CONFIDENCE_ASC');
    assert.deepEqual(getRenderedStudentOrder(), ['Nguyen Van An', 'Le Van Cuong', 'Tran Thi Binh']);
  });
});

// ---------------------------------------------------------
// R4: BatchCreatePage file overflow feedback
// ---------------------------------------------------------
test('R4: BatchCreatePage alerts when files exceed 30 limit, keeps selected files without silent drop', async () => {
  await screen(async ({ dom, render, imports }) => {
    const Component = load('pages/BatchCreatePage', {
      ...imports,
      './PrivacyEditorModal': () => null,
      '../services/api/newCreationRequestId': { newCreationRequestId: () => '173f718e-2c21-4a98-8c0e-f01337cabaf1' },
      '../services/api/AuthTokenStore': { AuthTokenStore: { getSessionId: () => null } },
      '../hooks/useUploadDraftGuard': { useUploadDraftGuard: () => ({ confirmation: null, allowNextNavigation() {} }) },
      '../services/api/ServiceLocator': {
        AppTeacherService: {
          getAssignments: async () => [{ assignmentId: 'a1', title: 'Test Bài tập' }],
          getAssignmentRoster: async () => [{ id: 'stu1', name: 'Student 1' }],
        }
      }
    }, {
      URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} }
    });

    await render(Component, {}, '/batches/create?assignmentId=a1');
    const fileInput = dom.window.document.querySelector('input[type=file]');

    // Selecting 31 files at once into empty batch
    const files31 = Array.from({ length: 31 }, (_, i) => ({
      name: `img-${i}.jpg`,
      type: 'image/jpeg',
      size: 1000
    }));

    Object.defineProperty(fileInput, 'files', { configurable: true, value: files31 });
    await act(async () => fileInput.dispatchEvent(new dom.window.Event('change', { bubbles: true })));

    const alerts = [...dom.window.document.querySelectorAll('[role=alert]')].map(x => x.textContent);
    assert.equal(dom.window.document.querySelectorAll('img').length, 30, 'Should retain 30 files in state');
    assert.ok(alerts.length > 0, 'Must show overflow alert');
    assert.match(alerts[0], /Bỏ qua 1 ảnh do vượt quá giới hạn 30 ảnh/, 'Alert must specify overflow count');
  });
});

// ---------------------------------------------------------
// R5: AssignmentCreatePage maxScore preserves editing value and rejects decimals/exponents
// ---------------------------------------------------------
test('R5: AssignmentCreatePage preserves decimal/exponent strings and validates integer range on submit', async () => {
  await screen(async ({ dom, render, imports, controls }) => {
    let createdAssignmentScore = null;
    const Component = load('pages/AssignmentCreatePage', {
      ...imports,
      '../components/layout/AuthContext': { useAuth: () => ({ user: null }) },
      '../services/api/newCreationRequestId': { newCreationRequestId: () => '173f718e-2c21-4a98-8c0e-f01337cabaf1' },
      '../services/api/ServiceLocator': {
        AppTeacherService: {
          getClasses: async () => [{ classId: 'c1', name: '4A', studentCount: 25 }],
          createAssignment: async (classId, title, mathType, maxScore) => {
            createdAssignmentScore = maxScore;
            return { assignmentId: 'assign-created', title, maxScore };
          }
        }
      },
      '../types': {
        MathType: { VERTICAL_ADDITION: 'VERTICAL_ADDITION', VERTICAL_SUBTRACTION: 'VERTICAL_SUBTRACTION' }
      }
    });

    await render(Component);

    // 1. Enter decimal "1.5" - must NOT be truncated to 1
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '1.5' } }));
    assert.equal(controls['Thang điểm tối đa'].value, '1.5', 'Preserves decimal input string');

    // Attempt submit with decimal
    await act(async () => controls['Tên bài tập'].onChange({ target: { value: 'Bài toán cộng' } }));
    const submitBtn = [...dom.window.document.querySelectorAll('button')].find(b => b.textContent?.includes('Tạo bài tập'));
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, null, 'Submit must be blocked for decimal');
    let alerts = [...dom.window.document.querySelectorAll('[role=alert]')].map(x => x.textContent);
    assert.match(alerts[0], /phải là số nguyên/, 'Shows integer validation error for decimal');

    // 2. Enter exponent "1e2" - must NOT be truncated to 1
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '1e2' } }));
    assert.equal(controls['Thang điểm tối đa'].value, '1e2', 'Preserves exponent input string');
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, null, 'Submit must be blocked for exponent');

    // 3. Enter empty string - must NOT automatically revert to 10
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '' } }));
    assert.equal(controls['Thang điểm tối đa'].value, '', 'Preserves empty input');
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, null, 'Submit must be blocked for empty score');

    // 4. Enter out-of-range "0"
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '0' } }));
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, null, 'Submit must be blocked for 0');

    // 5. Enter out-of-range "101"
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '101' } }));
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, null, 'Submit must be blocked for 101');

    // 6. Enter valid integer "100" - must succeed
    await act(async () => controls['Thang điểm tối đa'].onChange({ target: { value: '100' } }));
    await act(async () => submitBtn.click());
    assert.equal(createdAssignmentScore, 100, 'Submits integer 100 successfully');
  });
});

test('SubmissionReviewPage blocks approve and override buttons when submission image is not ready', async () => {
  await screen(async ({ dom, render, imports }) => {
    const mockService = {
      getSubmissionDetail: async () => ({
        submissionId: 'sub-1',
        studentName: 'An kiểm thử',
        status: 'PROPOSED_GRADE',
        maxScore: 100,
        suggestedScore: 80,
        gradeProposal: { suggestedScore: 80, maxScore: 100 },
        imageUrl: '/api/v1/teacher/submissions/sub-1/image',
      }),
      approveSubmission: async () => {},
      overrideSubmission: async () => {},
    };

    imports['react-router-dom'] = { ...routerRuntime, useParams: () => ({ id: 'sub-1' }) };
    imports['../services/api/ServiceLocator'] = { AppTeacherService: mockService };
    imports['../components/common/SubmissionImage'] = {
      SubmissionImage: ({ onStatusChange }) => {
        React.useEffect(() => {
          onStatusChange?.({ ready: false, reason: 'Ảnh bài làm không tải được hoặc không hợp lệ.' });
        }, [onStatusChange]);
        return React.createElement('div', { 'data-testid': 'mock-image' }, 'Mock Image Loading');
      }
    };

    const Page = load('pages/SubmissionReviewPage', imports);
    await render(Page, {}, '/submissions/sub-1');

    const alerts = [...dom.window.document.querySelectorAll('[role=alert], [role=status]')].map(el => el.textContent);
    assert.ok(alerts.some(t => t.includes('Chưa thể duyệt hoặc điều chỉnh điểm')),
      'Alert explains grading is blocked until image is loaded');

    const approveBtn = [...dom.window.document.querySelectorAll('button')].find(b => b.textContent?.includes('Duyệt điểm'));
    assert.equal(approveBtn, undefined, 'Approve button must not be active when image is not ready');
  });
});

test('SubmissionReviewPage shows actual evidence and omits ungrounded warnings for a valid result', async () => {
  for (const detail of [
    { decision: 'VALID' },
    {
      decision: 'INVALID', evidence: {
        rule: 'Phép cộng hàng chục không khớp.', position: 'Hàng chục', items: [
          { description: 'Phép cộng hàng chục không khớp.', placeValue: 'Hàng chục', observedText: '0' },
          { description: 'Bố cục phép tính chưa hoàn chỉnh.' },
        ],
      },
    },
  ]) {
    await screen(async ({ dom, render, imports }) => {
      imports['react-router-dom'] = { ...routerRuntime, useParams: () => ({ id: 'sub-1' }) };
      imports['../services/api/ServiceLocator'] = { AppTeacherService: {
        getSubmissionDetail: async () => ({ ...detail, studentName: 'An kiểm thử', status: 'PROPOSED_GRADE' }),
      } };
      imports['../components/common/SubmissionImage'] = { SubmissionImage: () => null };
      await render(load('pages/SubmissionReviewPage', imports), {}, '/submissions/sub-1');

      const body = dom.window.document.body.textContent;
      assert.doesNotMatch(body, /Quy tắc tính toán hoặc nét chữ/);
      if (detail.decision === 'VALID') {
        assert.match(body, /Hợp lệ theo quy tắc/);
        assert.doesNotMatch(body, /Dấu hiệu cần xem xét|Phát hiện lỗi/);
      } else {
        const evidenceItems = [...dom.window.document.querySelectorAll('li')].map(item => item.textContent);
        assert.match(evidenceItems[0], /Phép cộng hàng chục không khớp.*Hàng chục.*Ký tự nhận diện.*0/);
        assert.equal(evidenceItems[1], 'Bố cục phép tính chưa hoàn chỉnh.');
      }
    });
  }
});

// ---------------------------------------------------------
// SubmissionImage: Retry, Zoom/Scroll, and Accessible Modal
// ---------------------------------------------------------
test('SubmissionImage: retry on broken image clears error and restores ready state on valid image', async () => {
  await screen(async ({ dom, render, imports }) => {
    let callCount = 0;
    const mockApiClient = {
      get: async () => {
        callCount++;
        if (callCount === 1) {
          return { data: new Blob([]) };
        }
        return { data: new Blob(['valid-image-bytes'], { type: 'image/jpeg' }) };
      }
    };

    const statuses = [];
    const Component = load('components/common/SubmissionImage', {
      ...imports,
      '../../services/api/apiClient': mockApiClient,
      '../../config/runtime': { useMocks: false },
    }, {
      URL: {
        createObjectURL: () => 'blob:mock-image-url',
        revokeObjectURL: () => {},
      }
    });

    await render(Component, {
      id: 'sub-retry-test',
      studentName: 'Học sinh kiểm thử',
      onStatusChange: status => statuses.push(status),
    });

    let alert = dom.window.document.querySelector('[role=alert]');
    assert.ok(alert, 'Must display error alert on 0-byte image');
    assert.match(alert.textContent, /Tệp ảnh rỗng/, 'Explains empty file');
    assert.equal(statuses[statuses.length - 1].ready, false);

    const retryBtn = [...dom.window.document.querySelectorAll('button')].find(b => b.textContent?.includes('Thử lại'));
    assert.ok(retryBtn, 'Retry button is present');
    await act(async () => retryBtn.click());
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 60)); });
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 60)); });

    const img = dom.window.document.querySelector('img');
    assert.ok(img, 'Valid image element is rendered on successful retry');

    Object.defineProperty(img, 'naturalWidth', { value: 640, configurable: true });
    Object.defineProperty(img, 'naturalHeight', { value: 480, configurable: true });
    await act(async () => {
      img.dispatchEvent(new dom.window.Event('load'));
    });

    assert.equal(dom.window.document.querySelector('[role=alert]'), null, 'Error alert removed after successful decode');
    assert.equal(statuses[statuses.length - 1].ready, true, 'Status is marked ready for grading');
  });
});

test('SubmissionImage: zoom level scales rendered layout and rotation swaps bounding dimensions', async () => {
  await screen(async ({ dom, render, imports }) => {
    const Component = load('components/common/SubmissionImage', {
      ...imports,
      '../../services/api/apiClient': {
        get: async () => ({ data: new Blob(['valid-image-bytes'], { type: 'image/jpeg' }) })
      },
      '../../config/runtime': { useMocks: false },
    }, {
      URL: { createObjectURL: () => 'blob:mock-zoom', revokeObjectURL: () => {} }
    });

    await render(Component, { id: 'sub-zoom-test', studentName: 'Test Zoom' });

    const img = dom.window.document.querySelector('img');
    assert.ok(img, 'Image must be rendered');
    Object.defineProperty(img, 'naturalWidth', { value: 640, configurable: true });
    Object.defineProperty(img, 'naturalHeight', { value: 480, configurable: true });
    await act(async () => { img.dispatchEvent(new dom.window.Event('load')); });

    assert.equal(dom.window.document.body.textContent.includes('125%'), false);

    const rotateAtFit = dom.window.document.querySelector('button[aria-label="Xoay ảnh 90 độ"]');
    await act(async () => rotateAtFit.click());
    assert.equal(img.parentElement.style.width, '480px', 'Rotation reserves its full width at 100%');
    assert.equal(img.parentElement.style.height, '640px', 'Rotation reserves its full height at 100%');
    await act(async () => dom.window.document.querySelector('button[aria-label="Đặt lại kích thước"]').click());

    const zoomInBtn = dom.window.document.querySelector('button[aria-label="Phóng to ảnh"]');
    assert.ok(zoomInBtn, 'Zoom in button exists');
    await act(async () => zoomInBtn.click());

    assert.ok(dom.window.document.body.textContent.includes('125%'), 'Displays 125% badge');
    assert.equal(img.style.width, '800px');
    assert.equal(img.style.height, '600px');

    const rotateBtn = dom.window.document.querySelector('button[aria-label="Xoay ảnh 90 độ"]');
    assert.ok(rotateBtn, 'Rotate button exists');
    await act(async () => rotateBtn.click());

    const boxContainer = img.parentElement;
    assert.equal(boxContainer.style.width, '600px', 'Rotated bounding box width swaps to 600px');
    assert.equal(boxContainer.style.height, '800px', 'Rotated bounding box height swaps to 800px');
    assert.match(img.style.transform, /rotate\(90deg\)/, 'Image has 90deg transform');

    const resetBtn = dom.window.document.querySelector('button[aria-label="Đặt lại kích thước"]');
    await act(async () => resetBtn.click());
    assert.equal(dom.window.document.body.textContent.includes('125%'), false, 'Reset removes zoom badge');
  });
});

test('SubmissionImage: fullscreen modal traps focus, handles Escape key, and restores focus to trigger button', async () => {
  await screen(async ({ dom, render, imports }) => {
    const Component = load('components/common/SubmissionImage', {
      ...imports,
      '../../services/api/apiClient': {
        get: async () => ({ data: new Blob(['valid-image-bytes'], { type: 'image/jpeg' }) })
      },
      '../../config/runtime': { useMocks: false },
    }, {
      URL: { createObjectURL: () => 'blob:mock-modal', revokeObjectURL: () => {} }
    });

    await render(Component, { id: 'sub-modal-test', studentName: 'Test Modal' });
    const img = dom.window.document.querySelector('img');
    Object.defineProperty(img, 'naturalWidth', { value: 640, configurable: true });
    Object.defineProperty(img, 'naturalHeight', { value: 480, configurable: true });
    await act(async () => { img.dispatchEvent(new dom.window.Event('load')); });

    const fullscreenBtn = dom.window.document.querySelector('button[aria-label="Xem chi tiết toàn màn hình"]');
    assert.ok(fullscreenBtn, 'Fullscreen trigger button exists');

    fullscreenBtn.focus();
    await act(async () => fullscreenBtn.click());
    await act(async () => { await new Promise(r => setTimeout(r, 60)); });

    const dialog = dom.window.document.querySelector('[role=dialog][aria-modal=true]');
    assert.ok(dialog, 'Fullscreen dialog is open with aria-modal="true"');
    assert.equal(dom.window.document.body.style.overflow, 'hidden', 'Locks body scroll');

    await act(async () => {
      dom.window.dispatchEvent(new dom.window.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    await act(async () => { await new Promise(r => setTimeout(r, 20)); });

    assert.equal(dom.window.document.querySelector('[role=dialog]'), null, 'Escape closes dialog');
    assert.equal(dom.window.document.body.style.overflow, '', 'Restores body overflow');
    assert.equal(dom.window.document.activeElement, fullscreenBtn, 'Returns focus to triggering button');
  });
});
