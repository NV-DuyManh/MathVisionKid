import apiClient from '../services/api/apiClient';
import { quizApi } from '../features/quiz/quizApi';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { post: jest.fn(), get: jest.fn() } }));
beforeEach(() => { jest.clearAllMocks(); jest.useFakeTimers(); });
afterEach(() => jest.useRealTimers());

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
