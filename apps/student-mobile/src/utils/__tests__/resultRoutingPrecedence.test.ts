import { resolveResultRoute } from '../resultRouting';
import { SubmissionStatus, Decision } from '../../types';

describe('CORE-MVP Result Routing Precedence Regression Tests', () => {
  test('AI OUT_OF_SCOPE with Spring REVIEW_REQUIRED status and OUT_OF_SCOPE reasonCode must route to /results/out-of-scope', () => {
    // Exact payload returned by Spring Boot when AI flags OUT_OF_SCOPE:
    // status is REVIEW_REQUIRED, but reasonCode is 'OUT_OF_SCOPE'
    const payload = {
      id: 'sub-out-of-scope-1',
      status: SubmissionStatus.REVIEW_REQUIRED,
      reasonCode: 'OUT_OF_SCOPE',
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/out-of-scope');
  });

  test('Direct OUT_OF_SCOPE status routes to /results/out-of-scope', () => {
    const payload = {
      id: 'sub-out-of-scope-2',
      status: SubmissionStatus.OUT_OF_SCOPE,
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/out-of-scope');
  });

  test('REVIEW_REQUIRED with other reasonCodes routes to /results/review-required', () => {
    const payload = {
      id: 'sub-review-1',
      status: SubmissionStatus.REVIEW_REQUIRED,
      reasonCode: 'INVALID_LAYOUT',
      diagnostics: { reasonCode: 'INVALID_LAYOUT' },
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/review-required');
    expect(target.params?.reasonCode).toBe('INVALID_LAYOUT');
  });

  test('Quality failures take precedence and route to /results/quality-failure', () => {
    const payload = {
      id: 'sub-qual-1',
      status: SubmissionStatus.NEEDS_RETAKE,
      imageQualityIssue: 'BLUR' as any,
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/quality-failure');
    expect(target.params?.issue).toBe('BLUR');
  });

  test('Token ambiguity routes to /results/token-confirmation', () => {
    const payload = {
      id: 'sub-ambig-1',
      status: SubmissionStatus.NEEDS_CONFIRMATION,
      jobId: 'job-1',
      recognizedExercise: { tokens: [{ tokenId: 'token-3', value: '3', ambiguity: true }] },
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/token-confirmation');
    expect(target.params?.submissionId).toBe('sub-ambig-1');
  });

  test('FEEDBACK_READY with VALID decision routes to /results/correct', () => {
    const payload = {
      id: 'sub-valid-1',
      status: SubmissionStatus.FEEDBACK_READY,
      validation: { decision: Decision.VALID },
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/correct');
  });

  test('FEEDBACK_READY with INVALID decision routes to /results/error-hint', () => {
    const payload = {
      id: 'sub-invalid-1',
      status: SubmissionStatus.FEEDBACK_READY,
      validation: { decision: Decision.INVALID },
    };

    const target = resolveResultRoute(payload);
    expect(target.pathname).toBe('/results/error-hint');
  });
});

test.each([
  { isValid: true, diagnosisState: 'VALID' },
])('canonical valid response routes to correct', validation => {
  expect(resolveResultRoute({ status: SubmissionStatus.FEEDBACK_READY, validation }).pathname).toBe('/results/correct');
});

test('canonical invalid response routes to error, including immediately returned feedback', () => {
  expect(resolveResultRoute({ status: SubmissionStatus.FEEDBACK_READY, validation: { isValid: false, diagnosisState: 'INVALID' } }).pathname).toBe('/results/error-hint');
});

test.each([
  undefined, { decision: Decision.UNCERTAIN }, { isValid: false, diagnosisState: 'UNCERTAIN' },
  { isValid: true, diagnosisState: 'INVALID' }, { isValid: false, diagnosisState: 'VALID' },
])('missing or conflicting evidence never claims correct or incorrect', validation => {
  expect(resolveResultRoute({ status: SubmissionStatus.FEEDBACK_READY, validation }).pathname).toBe('/results/review-required');
});

test('confirmation requires actual token identity and the current job', () => {
  expect(resolveResultRoute({ status: SubmissionStatus.NEEDS_CONFIRMATION, ambiguousToken: { value: '7' } }).pathname).toBe('/results/review-required');
});

test('unfinished or unknown status cannot produce a grading result', () => {
  expect(resolveResultRoute({ id: 'real', status: SubmissionStatus.PROCESSING, validation: { decision: Decision.VALID } }).pathname).toBe('/processing');
  expect(resolveResultRoute({}).pathname).toBe('/results/review-required');
});

test('result links contain identity rather than copied result or diagnostics', () => {
  const target = resolveResultRoute({ id: 'real', status: SubmissionStatus.FEEDBACK_READY,
    diagnostics: { modelProvenance: { modelName: 'internal' } },
    validation: { isValid: true, diagnosisState: 'VALID' } });
  expect(target.params).toEqual({ id: 'real', submissionId: 'real' });
});
