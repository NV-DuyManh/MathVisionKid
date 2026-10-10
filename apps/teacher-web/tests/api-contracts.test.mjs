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

test('review IDs resolve to actual details, confidence percentages and backend grade scale', async () => {
  const { service: api } = service({
    '/teacher/batches/b/review': ['s'],
    '/teacher/submissions/s': { submissionId: 's', maxScore: 10, gradeProposal: { suggestedScore: 75, maxScore: 100 },
      confidenceBundle: { recognition: .92, diagnosis: 0 }, validation: { diagnosisState: 'VALID', isValid: true } },
  });
  const [detail] = await api.getReviewQueue('b');
  assert.equal(detail.submissionId, 's');
  assert.equal(detail.suggestedScore, 8);
  assert.equal(detail.recognitionConfidence, 92);
  assert.equal(detail.diagnosisConfidence, 0);
  assert.equal(detail.decision, 'VALID');
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

test('zero score remains zero and approve/override refresh after an empty HTTP response', async () => {
  for (const action of ['approve', 'override']) {
    const { service: api, calls } = service({
      [`/teacher/submissions/s/${action}`]: '',
      '/teacher/submissions/s': { maxScore: 10, gradeProposal: { suggestedScore: 0, maxScore: 100 } },
    });
    const result = action === 'approve' ? await api.approveSubmission('s') : await api.overrideSubmission('s', 4, 'Reviewed');
    assert.equal(result.suggestedScore, 0);
    assert.deepEqual(calls.map(call => call.method), ['post', 'get']);
  }
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
