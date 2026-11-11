import { readFileSync } from 'node:fs';
import { transpileModule, ModuleKind } from 'typescript';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';

function service(responses) {
  const calls = [];
  const api = Object.fromEntries(['get', 'post'].map(method => [method, async (url, data) => {
    calls.push({ method, url, data });
    if (!(url in responses)) throw new Error('Unexpected endpoint');
    const response = responses[url];
    if (response instanceof Error) throw response;
    return { data: response };
  }]));
  const source = transpileModule(readFileSync(new URL('../src/services/api/SpringTeacherService.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(source, { exports, require: id => id === './apiClient' ? api : { AuthTokenStore: { setTokens() {} } } });
  return { service: exports.SpringTeacherService, calls };
}

test('dashboard maps the backend DTO counts and retains actual recent batches', async () => {
  const recentBatches = [{ batchId: 'b', assignmentTitle: 'Phép cộng', totalCount: 7, processedCount: 4, reviewRequiredCount: 2, status: 'PARTIAL' }];
  const { service: api, calls } = service({
    '/teacher/dashboard': { todayTotal: 7, processedCount: 4, reviewRequiredCount: 2, recentBatches },
  });
  const result = await api.getDashboard();
  assert.equal(result.totalToday, 7);
  assert.equal(result.completed, 4);
  assert.equal(result.reviewRequired, 2);
  assert.equal(result.recentBatches, recentBatches);
  assert.equal(calls[0].url, '/teacher/dashboard');
});

test('dashboard preserves genuine zero counts from the backend', async () => {
  const { service: api } = service({
    '/teacher/dashboard': { todayTotal: 0, processedCount: 0, reviewRequiredCount: 0, recentBatches: [] },
  });
  const result = await api.getDashboard();
  assert.equal(result.totalToday, 0);
  assert.equal(result.completed, 0);
  assert.equal(result.reviewRequired, 0);
  assert.equal(result.recentBatches.length, 0);
});

test('missing or malformed dashboard data never becomes fabricated zero statistics', async () => {
  const valid = { todayTotal: 7, processedCount: 4, reviewRequiredCount: 2, recentBatches: [] };
  for (const response of [null, {}, { metrics: { totalToday: 7, completed: 4, reviewRequired: 2 }, recentBatches: [] },
    { ...valid, todayTotal: undefined }, { ...valid, todayTotal: '7' }, { ...valid, processedCount: -1 },
    { ...valid, reviewRequiredCount: NaN }, { ...valid, recentBatches: null }]) {
    const { service: api } = service({ '/teacher/dashboard': response });
    await assert.rejects(api.getDashboard());
  }
});

test('dashboard API failures remain errors for the page to display', async () => {
  const failure = new Error('Dashboard offline');
  const { service: api } = service({ '/teacher/dashboard': failure });
  await assert.rejects(api.getDashboard(), failure);
});

test('review summary preserves confidence, evidence and backend grade scale in a single request', async () => {
  const { service: api, calls } = service({
    '/teacher/batches/b/review-summary': [{ submissionId: 's', maxScore: 10, gradeProposal: { suggestedScore: 75, maxScore: 100 },
      confidenceBundle: { recognition: .92, diagnosis: 0 }, evidence: { rule: 'Sai ở hàng đơn vị' } }],
  });
  const [detail] = await api.getReviewQueue('b');
  assert.equal(detail.submissionId, 's');
  assert.equal(detail.suggestedScore, 8);
  assert.equal(detail.recognitionConfidence, 92);
  assert.equal(detail.diagnosisConfidence, 0);
  assert.equal(detail.evidence.rule, 'Sai ở hàng đơn vị');
  assert.deepEqual(calls.map(call => call.url), ['/teacher/batches/b/review-summary']);
});

test('missing and malformed analysis never produces a fabricated score or verdict', async () => {
  for (const detail of [{}, { maxScore: 10, gradeProposal: { suggestedScore: 101, maxScore: 100 }, confidenceBundle: { recognition: 92 } }]) {
    const { service: api } = service({ '/teacher/submissions/s': detail });
    const result = await api.getSubmissionDetail('s');
    assert.equal(result.suggestedScore, undefined);
    assert.equal(result.recognitionConfidence, undefined);
    assert.equal(result.decision, 'UNCERTAIN');
  }
});

test('review evidence preserves reported error descriptions, positions and recognized text', async () => {
  const { service: api } = service({ '/teacher/submissions/s': {
    evidence: { items: [null, { columnIndex: 0 }, {
      description: 'Phép cộng hàng chục không khớp.', placeValue: 'Hàng chục', observedText: '0', columnIndex: 1,
    }, { description: 'Bố cục phép tính chưa hoàn chỉnh.', placeValue: null, observedText: ' ' }] },
  } });
  const { evidence } = await api.getSubmissionDetail('s');
  assert.equal(evidence.rule, 'Phép cộng hàng chục không khớp.');
  assert.equal(evidence.position, 'Hàng chục');
  assert.deepEqual(JSON.parse(JSON.stringify(evidence.items)), [
    { description: 'Phép cộng hàng chục không khớp.', placeValue: 'Hàng chục', observedText: '0' },
    { description: 'Bố cục phép tính chưa hoàn chỉnh.' },
  ]);
});

test('empty evidence stays absent and legacy review text remains available', async () => {
  const { service: api } = service({
    '/teacher/submissions/empty': { evidence: { items: [] } },
    '/teacher/submissions/legacy': { evidence: { rule: 'Ảnh quá mờ', position: 'Toàn bộ ảnh' } },
  });
  assert.equal((await api.getSubmissionDetail('empty')).evidence, undefined);
  const { evidence } = await api.getSubmissionDetail('legacy');
  assert.equal(evidence.rule, 'Ảnh quá mờ');
  assert.equal(evidence.position, 'Toàn bộ ảnh');
});

test('zero proposal remains zero', async () => {
  const { service: api } = service({
    '/teacher/submissions/s': { maxScore: 10, gradeProposal: { suggestedScore: 0, maxScore: 100 } },
  });
  assert.equal((await api.getSubmissionDetail('s')).suggestedScore, 0);
});

test('approve and override acknowledge the POST independently of a failed detail read', async () => {
  for (const action of ['approve', 'override']) {
    const failure = new Error('Detail temporarily unavailable');
    const { service: api, calls } = service({
      [`/teacher/submissions/s/${action}`]: '',
      '/teacher/submissions/s': failure,
    });
    const result = action === 'approve' ? await api.approveSubmission('s') : await api.overrideSubmission('s', 4, 'Reviewed');
    assert.equal(result, undefined);
    assert.deepEqual(calls.map(({ method, url }) => [method, url]), [['post', `/teacher/submissions/s/${action}`]]);
    await assert.rejects(api.getSubmissionDetail('s'), failure);
  }
});

test('manual grading submits only an affirmative image legibility attestation', async () => {
  const { service: api, calls } = service({ '/teacher/submissions/s/override': '' });
  await api.overrideSubmission('s', 0, 'Đã đối chiếu ảnh.', true);
  await api.overrideSubmission('s', 8, 'Đã kiểm tra kết quả.');
  await api.overrideSubmission('s', 8, 'Đã kiểm tra kết quả.', false);
  assert.equal(calls[0].data.imageLegible, true);
  assert.equal(Object.hasOwn(calls[1].data, 'imageLegible'), false);
  assert.equal(Object.hasOwn(calls[2].data, 'imageLegible'), false);
});

test('roster belongs to the selected assignment, preserving real user IDs', async () => {
  const { service: api, calls } = service({
    '/teacher/assignments/a': { classId: 'second-class' },
    '/teacher/classes/second-class': { students: [{ userId: 'real-id', displayName: 'Actual student' }] },
  });
  const roster = await api.getAssignmentRoster('a');
  assert.equal(roster[0].id, 'real-id');
  assert.equal(roster[0].name, 'Actual student');
  assert.equal(calls.length, 2);
});

test('API failure remains an error instead of silently returning a sample roster', async () => {
  const { service: api } = service({ '/teacher/assignments/a': new Error('Offline') });
  await assert.rejects(api.getAssignmentRoster('a'), /Offline/);
});
