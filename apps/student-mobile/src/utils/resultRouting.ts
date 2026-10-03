import { Decision, SubmissionStatus, SubmissionResult, RecognizedToken } from '../types';

export interface RouteTarget { pathname: string; params?: Record<string, string> }

/** A completed job is not itself evidence that the student's calculation is correct. */
export function getArithmeticDecision(result: Partial<SubmissionResult>): Decision {
  const validation = result.validation;
  const diagnosis = validation?.diagnosisState;
  if (diagnosis) {
    if (diagnosis === 'VALID' && validation?.isValid === true) return Decision.VALID;
    if (diagnosis === 'INVALID' && validation?.isValid === false) return Decision.INVALID;
    return Decision.UNCERTAIN;
  }
  // Older server responses used the explicit decision enum.
  return validation?.decision === Decision.VALID && validation.isValid !== false ? Decision.VALID
    : validation?.decision === Decision.INVALID && validation.isValid !== true ? Decision.INVALID : Decision.UNCERTAIN;
}

export function getUncertainTokens(result: Partial<SubmissionResult>): RecognizedToken[] {
  return (result.recognizedExercise?.tokens || []).filter(token => token.tokenId &&
    (token.ambiguity === true || result.uncertainTokenIds?.includes(token.tokenId)));
}

export function resolveResultRoute(result: Partial<SubmissionResult>, originalUri?: string): RouteTarget {
  const params: Record<string, string> = {
    submissionId: result.id || '', id: result.id || '',
  };
  if (result.status === SubmissionStatus.NEEDS_RETAKE || result.status === SubmissionStatus.CROP_REQUIRED) {
    return { pathname: '/results/quality-failure', params: { ...params, issue: result.imageQualityIssue || '', originalUri: originalUri || '' } };
  }
  if (result.status === SubmissionStatus.OUT_OF_SCOPE || result.reasonCode === 'OUT_OF_SCOPE' || result.validation?.diagnosisState === 'OUT_OF_SCOPE') {
    return { pathname: '/results/out-of-scope', params };
  }
  if (result.status === SubmissionStatus.PROCESSING) return { pathname: '/processing', params };
  if (result.status === SubmissionStatus.NEEDS_CONFIRMATION && result.jobId && getUncertainTokens(result).length) {
    return { pathname: '/results/token-confirmation', params };
  }
  if (result.status === SubmissionStatus.FEEDBACK_READY) {
    const decision = getArithmeticDecision(result);
    if (decision === Decision.VALID) return { pathname: '/results/correct', params };
    if (decision === Decision.INVALID) return { pathname: '/results/error-hint', params };
  }
  return { pathname: '/results/review-required', params: { ...params, reasonCode: result.reasonCode || 'RESULT_UNCERTAIN' } };
}

export function parseSubmissionResult(data?: string | string[]): SubmissionResult | null {
  try {
    const result = JSON.parse(Array.isArray(data) ? data[0] : data || 'null');
    return result && typeof result.id === 'string' && typeof result.status === 'string' ? result : null;
  } catch { return null; }
}
