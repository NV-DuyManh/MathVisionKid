import React from 'react';
import { AppState } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import { QuizVoice, QuizNarrationPreparation } from '../features/quiz/QuizVoice';
import { readNarrationVoice } from '../features/tutoring/narrationVoices';
import { saveNarration } from '../features/tutoring/narrationFile';
import { quizApi } from '../features/quiz/quizApi';

jest.setTimeout(30000);
const mockDispose = jest.fn();
jest.mock('expo-router', () => ({ useFocusEffect: (fn: () => (() => void)) => require('react').useEffect(fn, [fn]) }));
jest.mock('../features/tutoring/DeviceNarration', () => ({ DeviceNarration: 'DeviceNarration' }));
jest.mock('../features/tutoring/AudioPlayback', () => ({ AudioPlayback: 'AudioPlayback' }));
jest.mock('../features/tutoring/narrationFile', () => ({ saveNarration: jest.fn(() => ({ uri: 'file:///quiz-speech.wav', dispose: mockDispose })) }));
jest.mock('../features/tutoring/narrationVoices', () => ({ ...jest.requireActual('../features/tutoring/narrationVoices'),
  readNarrationVoice: jest.fn().mockResolvedValue('vi-VN-HoaiMyNeural'), saveNarrationVoice: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/quiz/quizApi', () => ({ ...jest.requireActual('../features/quiz/quizApi'), quizApi: { audio: jest.fn() } }));
let view: TestRenderer.ReactTestRenderer;
const button = (name: string) => view.root.findAll(n => n.props.accessibilityLabel === name && n.props.onPress)[0];
beforeEach(() => { jest.clearAllMocks(); (readNarrationVoice as jest.Mock).mockResolvedValue('vi-VN-HoaiMyNeural'); });
afterEach(() => { if (view) act(() => view.unmount()); });
it('uses the shared player and requests only the owned Quiz content with the saved voice', async () => {
  (quizApi.audio as jest.Mock).mockResolvedValue(new Uint8Array(50));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Câu hỏi của em']} content="QUESTION"/>); });
  expect(quizApi.audio).toHaveBeenCalledTimes(1);
  expect(quizApi.audio).toHaveBeenCalledWith('quiz-one', 'vi-VN-HoaiMyNeural', expect.any(AbortSignal), 'QUESTION');
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  expect(button('Giọng nam')).toBeDefined(); expect(button('Giọng nữ')).toBeDefined(); expect(button('Giọng có sẵn')).toBeDefined();
});
it('cancels cloud generation on device selection and keeps the same transcript', async () => {
  let finish!: (bytes: Uint8Array) => void;
  (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(resolve => { finish=resolve; }));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Đáp số là 68.']}/>); });
  const signal=(quizApi.audio as jest.Mock).mock.calls[0][2];
  await act(async () => button('Giọng có sẵn').props.onPress());
  expect(signal.aborted).toBe(true);
  expect(view.root.findByType('DeviceNarration' as any).props.paragraphs).toEqual(['Đáp số là 68.']);
  await act(async () => finish(new Uint8Array(50)));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(0);
  expect(mockDispose).toHaveBeenCalledTimes(1);
  expect(quizApi.audio).toHaveBeenCalledTimes(1);
});
it('aborts on navigation and discards late bytes', async () => {
  let finish!: (bytes: Uint8Array) => void;
  (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(resolve => { finish=resolve; }));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Bài một']}/>); });
  const signal=(quizApi.audio as jest.Mock).mock.calls[0][2];
  act(() => view.unmount()); expect(signal.aborted).toBe(true);
  await act(async () => finish(new Uint8Array(50)));
  expect(mockDispose).toHaveBeenCalledTimes(1);
});
it('shows compact retry and local voice options on failure without leaking errors', async () => {
  (quizApi.audio as jest.Mock).mockRejectedValue(new Error('private internal URL'));
  await act(async () => { view = TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Bài một']}/>); });
  expect(button('Tải lại lời giảng')).toBeDefined(); expect(button('Dùng giọng đọc trên thiết bị')).toBeDefined();
  expect(JSON.stringify(view.toJSON())).not.toContain('private internal URL');
});
it('ends an unresponsive Quiz request at 60 seconds and can retry', async () => {
  jest.useFakeTimers();
  try {
    (quizApi.audio as jest.Mock).mockImplementation(() => new Promise(() => {}));
    await act(async () => { view=TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Bài một']}/>); });
    const signal=(quizApi.audio as jest.Mock).mock.calls[0][2];
    await act(async () => { jest.advanceTimersByTime(60000); }); expect(signal.aborted).toBe(true);
    expect(button('Tải lại lời giảng')).toBeDefined();
    (quizApi.audio as jest.Mock).mockResolvedValue(new Uint8Array(50));
    await act(async () => button('Tải lại lời giảng').props.onPress());
    expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  } finally { jest.useRealTimers(); }
});
it('rejects an old challenge response after navigating to another one', async () => {
  let finish!: (bytes: Uint8Array) => void;
  (quizApi.audio as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish=resolve; })).mockResolvedValue(new Uint8Array(50));
  await act(async () => { view=TestRenderer.create(<QuizVoice quizId="quiz-one" paragraphs={['Bài một']}/>); });
  const signal=(quizApi.audio as jest.Mock).mock.calls[0][2];
  await act(async () => view.update(<QuizVoice quizId="quiz-two" paragraphs={['Bài hai']}/>));
  expect(signal.aborted).toBe(true);
  await act(async () => finish(new Uint8Array(50)));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  expect(quizApi.audio).toHaveBeenLastCalledWith('quiz-two','vi-VN-HoaiMyNeural',expect.any(AbortSignal),'SOLUTION');
});

const prepared = (show: boolean, content: 'QUESTION'|'SOLUTION' = 'QUESTION', owner = 'student-a', words = 'Câu hỏi đã được cấp quyền.') =>
  <QuizNarrationPreparation owner={owner} quizId="quiz-one" content={content} paragraphs={[words]}>
    {show ? <QuizVoice quizId="quiz-one" content={content} paragraphs={[words]}/> : null}
  </QuizNarrationPreparation>;

it('warms both voices before opening, then switches and reopens without another request or file write', async () => {
  (quizApi.audio as jest.Mock).mockResolvedValue(new Uint8Array(50));
  await act(async () => { view=TestRenderer.create(prepared(false)); });
  expect(quizApi.audio).toHaveBeenCalledTimes(2);
  expect((quizApi.audio as jest.Mock).mock.calls.map(call=>[call[1],call[3]])).toEqual([
    ['vi-VN-HoaiMyNeural','QUESTION'],['vi-VN-NamMinhNeural','QUESTION'],
  ]);
  await act(async () => view.update(prepared(true)));
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
  await act(async () => button('Giọng nam').props.onPress());
  await act(async () => view.update(prepared(false)));
  await act(async () => view.update(prepared(true)));
  expect(quizApi.audio).toHaveBeenCalledTimes(2);
  expect(saveNarration).toHaveBeenCalledTimes(2);
});

it('joins an unfinished background request and closing the sheet keeps the warm-up alive', async () => {
  const finish: ((bytes: Uint8Array)=>void)[]=[];
  (quizApi.audio as jest.Mock).mockImplementation(()=>new Promise(resolve=>finish.push(resolve)));
  await act(async () => { view=TestRenderer.create(prepared(false)); });
  const signals=(quizApi.audio as jest.Mock).mock.calls.map(call=>call[2]);
  await act(async () => view.update(prepared(true)));
  await act(async () => view.update(prepared(false)));
  expect(quizApi.audio).toHaveBeenCalledTimes(2);
  expect(signals.every(signal=>!signal.aborted)).toBe(true);
  await act(async () => finish.forEach(resolve=>resolve(new Uint8Array(50))));
  await act(async () => view.update(prepared(true)));
  expect(quizApi.audio).toHaveBeenCalledTimes(2);
  expect(view.root.findAllByType('AudioPlayback' as any)).toHaveLength(1);
});

it('does not warm cloud voices when the saved choice is the device', async () => {
  (readNarrationVoice as jest.Mock).mockResolvedValue('device');
  await act(async () => { view=TestRenderer.create(prepared(false)); });
  expect(quizApi.audio).not.toHaveBeenCalled();
  await act(async () => view.update(prepared(true)));
  expect(quizApi.audio).not.toHaveBeenCalled();
  expect(view.root.findByType('DeviceNarration' as any).props.paragraphs).toEqual(['Câu hỏi đã được cấp quyền.']);
});

it('keeps question and published solution warm-ups separate and clears another account assets', async () => {
  (quizApi.audio as jest.Mock).mockResolvedValue(new Uint8Array(50));
  await act(async () => { view=TestRenderer.create(prepared(false)); });
  expect((quizApi.audio as jest.Mock).mock.calls.every(call=>call[3]==='QUESTION')).toBe(true);
  await act(async () => view.update(prepared(false,'SOLUTION')));
  expect((quizApi.audio as jest.Mock).mock.calls.slice(2).every(call=>call[3]==='SOLUTION')).toBe(true);
  expect(quizApi.audio).toHaveBeenCalledTimes(4);
  await act(async () => view.update(prepared(false,'SOLUTION','student-b')));
  expect(quizApi.audio).toHaveBeenCalledTimes(6);
  expect(mockDispose).toHaveBeenCalledTimes(4);
});
