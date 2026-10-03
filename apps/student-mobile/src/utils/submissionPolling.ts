import { SubmissionResult, SubmissionService, SubmissionStatus } from '../types';

export const SUBMISSION_POLL_LIMIT = 45;
export const SUBMISSION_POLL_INTERVAL = 2000;

function waitForPoll(signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => { clearTimeout(timer); signal.removeEventListener('abort', abort); reject(new Error('Aborted')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, SUBMISSION_POLL_INTERVAL);
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
  });
}

/** Sequential, bounded requests; cancelling the screen cancels both its wait and HTTP request. */
export async function pollSubmission(initial: SubmissionResult, service: SubmissionService, signal: AbortSignal, scenarioHint?: string): Promise<SubmissionResult> {
  let result = initial;
  for (let count = 0; result.status === SubmissionStatus.PROCESSING && count < SUBMISSION_POLL_LIMIT; count++) {
    await waitForPoll(signal);
    result = await service.getSubmission(initial.id, scenarioHint, signal);
    if (signal.aborted) throw new Error('Aborted');
  }
  if (result.status === SubmissionStatus.PROCESSING) throw new Error('SUBMISSION_PENDING');
  return result;
}
