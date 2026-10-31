import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { QuizVoice } from '../features/quiz/QuizVoice';
import { quizApi } from '../features/quiz/quizApi';

jest.setTimeout(30000);
const mockDispose = jest.fn();
jest.mock('expo-router', () => ({ useFocusEffect: (fn: () => (() => void)) => require('react').useEffect(fn, [fn]) }));
jest.mock('../features/tutoring/AudioPlayback', () => ({ AudioPlayback: 'AudioPlayback' }));
jest.mock('../features/tutoring/narrationFile', () => ({ saveNarration: () => ({ uri: 'file:///quiz-speech.wav', dispose: mockDispose }) }));
jest.mock('../features/tutoring/narrationVoices', () => ({ ...jest.requireActual('../features/tutoring/narrationVoices'),
  readNarrationVoice: jest.fn().mockResolvedValue('vi-VN-HoaiMyNeural'), saveNarrationVoice: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/quiz/quizApi', () => ({ ...jest.requireActual('../features/quiz/quizApi'), quizApi: { audio: jest.fn() } }));
let view: TestRenderer.ReactTestRenderer;
const button = (name: string) => view.root.findAll(n => n.props.accessibilityLabel === name && n.props.onPress)[0];
beforeEach(() => { jest.clearAllMocks(); });
afterEach(() => { if (view) act(() => view.unmount()); });
it('never auto-requests speech, preserves the selected voice and deduplicates rapid taps', async () => {
  let resolve: (bytes: Uint8Array) => void = () => {};
  (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
  expect(quizApi.audio).not.toHaveBeenCalled();
  act(() => { button('Nghe cách giải').props.onPress(); button('Nghe cách giải').props.onPress(); });
  expect(quizApi.audio).toHaveBeenCalledTimes(1);
  expect(quizApi.audio).toHaveBeenCalledWith('quiz-one', 'vi-VN-HoaiMyNeural', expect.any(AbortSignal));
  await act(async () => resolve(new Uint8Array([1, 2, 3])));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  expect(view.root.findByType('AudioPlayback' as any).props.uri).toBe('file:///quiz-speech.wav');
  expect(quizApi.audio).toHaveBeenCalledTimes(1);
  act(() => view.unmount()); expect(mockDispose).toHaveBeenCalledTimes(1);
});
it('aborts pending speech on navigation/account unmount and ignores its late bytes', async () => {
  let resolve: (bytes: Uint8Array) => void = () => {};
  (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
  act(() => button('Nghe cách giải').props.onPress());
  const signal = (quizApi.audio as jest.Mock).mock.calls[0][2];
  act(() => view.unmount()); expect(signal.aborted).toBe(true);
  await act(async () => resolve(new Uint8Array([1, 2, 3])));
  expect(mockDispose).not.toHaveBeenCalled();
});
it('speech failure keeps a retry and a readable text fallback without exposing internal errors', async () => {
  (quizApi.audio as jest.Mock).mockRejectedValue(new Error('private speech engine URL'));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
  await act(async () => button('Nghe cách giải').props.onPress());
  expect(button('Thử tải giọng đọc lại')).toBeDefined();
  const words = view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
  expect(words).toContain('Em vẫn đọc được phần chữ'); expect(words).not.toContain('private speech engine URL');
});

it('ends an unresponsive request at its overall deadline and allows retry', async () => {
  jest.useFakeTimers();
  try {
    (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(() => {}));
    await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
    act(() => button('Nghe cách giải').props.onPress());
    const signal = (quizApi.audio as jest.Mock).mock.calls[0][2];
    await act(async () => { jest.advanceTimersByTime(45000); });
    expect(signal.aborted).toBe(true);
    expect(button('Thử tải giọng đọc lại')).toBeDefined();
    (quizApi.audio as jest.Mock).mockResolvedValue(new Uint8Array([1, 2, 3]));
    await act(async () => button('Thử tải giọng đọc lại').props.onPress());
    expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  } finally { jest.useRealTimers(); }
});

it('switches voice during generation, rejects old bytes and recovers from player failure', async () => {
  let first: (bytes: Uint8Array) => void = () => {};
  (quizApi.audio as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { first = resolve; }))
    .mockResolvedValue(new Uint8Array([4, 5, 6]));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
  act(() => button('Nghe cách giải').props.onPress());
  const signal = (quizApi.audio as jest.Mock).mock.calls[0][2];
  await act(async () => button('Giọng nam').props.onPress());
  expect(signal.aborted).toBe(true);
  await act(async () => button('Nghe cách giải').props.onPress());
  expect(quizApi.audio).toHaveBeenLastCalledWith('quiz-one', 'vi-VN-NamMinhNeural', expect.any(AbortSignal));
  await act(async () => first(new Uint8Array([1, 2, 3])));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  act(() => view.root.findByType('AudioPlayback' as any).props.onError());
  expect(mockDispose).toHaveBeenCalledTimes(1);
  expect(button('Thử tải giọng đọc lại')).toBeDefined();
});

it('changing challenge cancels generation before another challenge can play', async () => {
  let first: (bytes: Uint8Array) => void = () => {};
  (quizApi.audio as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { first = resolve; }))
    .mockResolvedValue(new Uint8Array([4, 5, 6]));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" />); });
  act(() => button('Nghe cách giải').props.onPress());
  const signal = (quizApi.audio as jest.Mock).mock.calls[0][2];
  await act(async () => view.update(<QuizVoice quizId="quiz-two" />));
  expect(signal.aborted).toBe(true);
  await act(async () => first(new Uint8Array([1, 2, 3])));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(0);
  await act(async () => button('Nghe cách giải').props.onPress());
  expect(quizApi.audio).toHaveBeenLastCalledWith('quiz-two', expect.any(String), expect.any(AbortSignal));
});
