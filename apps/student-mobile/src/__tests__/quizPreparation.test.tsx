import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useQuizPreparation } from '../features/quiz/useQuizPreparation';
import { quizApi } from '../features/quiz/quizApi';

jest.mock('../features/quiz/quizApi', () => ({ quizApi: { prepare: jest.fn() } }));
let view: TestRenderer.ReactTestRenderer, state: ReturnType<typeof useQuizPreparation>;
function Screen({ text, confirmed }: { text: string; confirmed: boolean }) {
  state = useQuizPreparation('11111111-1111-4111-8111-111111111111', text, confirmed);
  return null;
}
beforeEach(() => { jest.clearAllMocks(); (quizApi.prepare as jest.Mock).mockResolvedValue({ status: 'READY' }); });
afterEach(() => { if (view) act(() => view.unmount()); });
it('only sends confirmed text, independently of starting or completing a lesson', async () => {
  await act(async () => { view = TestRenderer.create(<Screen text="Đề OCR chưa xác nhận" confirmed={false} />); });
  expect(quizApi.prepare).not.toHaveBeenCalled();
  await act(async () => view.update(<Screen text="Đề đã được em sửa và xác nhận" confirmed />));
  expect(quizApi.prepare).toHaveBeenCalledWith(expect.any(String), expect.any(Number), 'Đề đã được em sửa và xác nhận', true);
  expect(state.state).toBe('READY');
});
it('invalidates old text on edit and ignores an older preparation response', async () => {
  let resolveOld: (value: unknown) => void = () => {};
  (quizApi.prepare as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }));
  await act(async () => { view = TestRenderer.create(<Screen text="Đề cũ đã xác nhận" confirmed />); });
  expect(state.state).toBe('PREPARING');
  (quizApi.prepare as jest.Mock).mockResolvedValueOnce({ status: 'INVALIDATED' });
  await act(async () => view.update(<Screen text="Đang sửa đề mới" confirmed={false} />));
  const calls = (quizApi.prepare as jest.Mock).mock.calls;
  expect(calls[1].slice(2)).toEqual(['', false]); expect(calls[1][1]).toBeGreaterThan(calls[0][1]);
  await act(async () => resolveOld({ status: 'READY' })); expect(state.state).toBe('IDLE');
});
it('keeps technical failure distinct and supports an explicit bounded retry', async () => {
  (quizApi.prepare as jest.Mock).mockRejectedValueOnce(new Error('offline'));
  await act(async () => { view = TestRenderer.create(<Screen text="Đề đã xác nhận" confirmed />); });
  expect(state.state).toBe('FAILED');
  await act(async () => state.retry()); expect(state.state).toBe('READY'); expect(quizApi.prepare).toHaveBeenCalledTimes(2);
});
it('never sends ambiguous digit text before confirmation', async () => {
  await act(async () => { view = TestRenderer.create(<Screen text="Có [?] cây" confirmed />); });
  expect(quizApi.prepare).not.toHaveBeenCalled();
});
