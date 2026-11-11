import apiClient from '../services/api/apiClient';
import { quizApi } from '../features/quiz/quizApi';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { post: jest.fn(), get: jest.fn() } }));
beforeEach(() => { jest.clearAllMocks(); jest.useFakeTimers(); });
afterEach(() => jest.useRealTimers());

it('allows the checked variant budget without retrying an ambiguous replay mutation', async () => {
  const failure = new Error('connection interrupted');
  (apiClient.post as jest.Mock).mockRejectedValue(failure);
  const abort = new AbortController();
  await expect(quizApi.replay('quiz-id', 'CHALLENGE', abort.signal)).rejects.toBe(failure);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
  expect(apiClient.post).toHaveBeenCalledWith('/student/quizzes/quiz-id/replay', { mode: 'CHALLENGE' }, { signal: abort.signal, timeout: 35000 });
  (apiClient.post as jest.Mock).mockResolvedValue({ data: {} });
  await quizApi.replay('quiz-id', 'PRACTICE', abort.signal);
  expect(apiClient.post).toHaveBeenLastCalledWith('/student/quizzes/quiz-id/replay', { mode: 'PRACTICE' }, { signal: abort.signal, timeout: 20000 });
});

it('persists the entire confirmed text including score decoration and whitespace', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { status: 'GENERATING' } });
  const original='  Vườn có 1/3 số cây là cây táo.\nHỏi tổng số cây? (2 điểm)  ';
  await quizApi.prepare('workflow', 3, original, true);
  expect(apiClient.post).toHaveBeenCalledWith('/student/quizzes/prepare', {
    workflowKey: 'workflow', revision: 3, confirmedProblemText: original, problemConfirmed: true,
  }, expect.anything());
});

it('waits for a genuine generation-in-progress response and publishes the real ready result', async () => {
  const ready={ offered: true, quiz: { quizId: 'published' } };
  (apiClient.post as jest.Mock).mockRejectedValueOnce({ response: { status: 409, data: { error: { code: 'QUIZ_GENERATING' } } } })
    .mockResolvedValueOnce({ data: ready });
  const response=quizApi.fromLearning('LESSON', 'real-completed-source');
  await jest.advanceTimersByTimeAsync(500);
  expect(await response).toEqual(ready);
  expect(apiClient.post).toHaveBeenCalledTimes(2);
});

it('preserves authentication, rate-limit and provider failures instead of reporting unsupported', async () => {
  for (const status of [401,403,404,422,429,500,503]) {
    const error={ response: { status, data: { error: { code: status===503?'QUIZ_PROVIDER_UNAVAILABLE':'REQUEST_FAILED' } } } };
    (apiClient.post as jest.Mock).mockRejectedValueOnce(error);
    await expect(quizApi.fromLearning('LESSON', 'source')).rejects.toBe(error);
  }
  expect(apiClient.post).toHaveBeenCalledTimes(7);
});

it('keeps a still-running checked preparation alive past the old short retry window', async () => {
  const pending = { response: { status: 409, data: { error: { code: 'QUIZ_GENERATING' } } } };
  const ready = { offered: true, quiz: { quizId: 'prepared-in-background' } };
  let requests = 0;
  (apiClient.post as jest.Mock).mockImplementation(async () => {
    if (++requests <= 10) throw pending;
    return { data: ready };
  });
  const response = quizApi.fromLearning('LESSON', 'completed-source');
  await jest.advanceTimersByTimeAsync(5000);
  expect(await response).toEqual(ready);
});

it('stops polling at its deadline instead of waiting indefinitely', async () => {
  (apiClient.post as jest.Mock).mockRejectedValue({ response: { status: 409, data: { error: { code: 'QUIZ_GENERATING' } } } });
  const response = quizApi.fromLearning('LESSON', 'completed-source');
  const assertion = expect(response).rejects.toThrow('hết thời gian');
  await jest.advanceTimersByTimeAsync(60000);
  await assertion;
});
