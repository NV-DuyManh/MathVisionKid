import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState } from 'react-native';
import { LessonQuestion } from '../features/tutoring/LessonQuestion';
import { TutorService } from '../features/tutoring/api/TutorService';
import { LessonNarration } from '../features/tutoring/LessonNarration';
import { AudioModule, setAudioModeAsync, setIsAudioActiveAsync } from 'expo-audio';

const mockRecorder = { uri: 'file:///cache/owned-question.m4a', prepareToRecordAsync: jest.fn(), record: jest.fn(), stop: jest.fn() };
const mockDelete = jest.fn();
jest.mock('expo-audio', () => ({ AudioModule: { requestRecordingPermissionsAsync: jest.fn() }, RecordingPresets: { HIGH_QUALITY: {} },
  setAudioModeAsync: jest.fn().mockResolvedValue(undefined), setIsAudioActiveAsync: jest.fn().mockResolvedValue(undefined), useAudioRecorder: () => mockRecorder, useAudioRecorderState: () => ({ durationMillis: 2000 }) }));
jest.mock('expo-file-system', () => ({ File: jest.fn().mockImplementation(() => ({ delete: mockDelete })) }));
jest.mock('../features/tutoring/LessonNarration', () => ({ LessonNarration: () => null }));
jest.mock('../features/tutoring/QuestionRecording', () => ({ QuestionRecording: () => null }));
jest.mock('../features/tutoring/api/TutorService', () => ({ TutorService: { transcribeQuestion: jest.fn(), askLesson: jest.fn() } }));
let view: TestRenderer.ReactTestRenderer;
const press = async (label: string) => { await act(async () => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0].props.onPress()); };
const input = () => view.root.findAll(node => node.props.accessibilityLabel === 'Câu hỏi của em' && node.props.onChangeText)[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const render = async () => { await act(async () => { view = TestRenderer.create(<LessonQuestion sessionId="conversation-session-123456" revision={3} stepIndex={1} scope="pupil-a:session:3" />); }); };
beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(AppState, 'addEventListener').mockImplementation(() => ({ remove: jest.fn() }));
  mockRecorder.prepareToRecordAsync.mockResolvedValue(undefined); mockRecorder.stop.mockResolvedValue(undefined);
  (AudioModule.requestRecordingPermissionsAsync as jest.Mock).mockResolvedValue({ granted: true });
  (TutorService.transcribeQuestion as jest.Mock).mockReset().mockResolvedValue('Vì sao phải quy đồng?');
  (TutorService.askLesson as jest.Mock).mockReset().mockResolvedValue({ answer: 'Các phần phải bằng nhau.',
    spokenExplanation: 'Em tưởng tượng chia lại các miếng bánh để chúng cùng kích thước rồi mới gộp.', followUp: 'Các phần cần có đặc điểm gì?', guarded: false });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('opens the microphone in one tap, keeps the recording for replay, and sends only the confirmed transcript', async () => {
  await render(); await press('Ghi âm câu hỏi');
  expect(text()).not.toContain('Đồng ý và ghi âm');
  expect(mockRecorder.record).toHaveBeenCalledWith({ forDuration: 30 });
  await press('Nói xong');
  expect(setAudioModeAsync).toHaveBeenLastCalledWith(expect.objectContaining({ allowsRecording: false, playsInSilentMode: true, shouldRouteThroughEarpiece: false }));
  expect(setIsAudioActiveAsync).toHaveBeenCalledWith(true);
  const { QuestionRecording } = require('../features/tutoring/QuestionRecording');
  expect(view.root.findByType(QuestionRecording).props.uri).toBe(mockRecorder.uri);
  expect(mockDelete).not.toHaveBeenCalled();
  expect(input().props.value).toBe('Vì sao phải quy đồng?');
  expect(TutorService.askLesson).not.toHaveBeenCalled();
  act(() => input().props.onChangeText('Vì sao các phần phải bằng nhau?'));
  await press('Gửi câu hỏi');
  expect(TutorService.askLesson).toHaveBeenCalledWith({ sessionId: 'conversation-session-123456', revision: 3, stepIndex: 1,
    question: 'Vì sao các phần phải bằng nhau?' }, expect.anything());
  expect(text()).toContain('Các phần phải bằng nhau.');
  expect(view.root.findByType(LessonNarration).props.paragraphs[0]).toContain('các miếng bánh');
});

it('retains the local recording after a transcription failure and releases it when the question closes', async () => {
  (TutorService.transcribeQuestion as jest.Mock).mockRejectedValue(new Error('private provider error'));
  await render(); await press('Ghi âm câu hỏi'); await press('Nói xong');
  const { QuestionRecording } = require('../features/tutoring/QuestionRecording');
  expect(view.root.findByType(QuestionRecording).props.uri).toBe(mockRecorder.uri);
  expect(text()).toContain('Chưa nghe rõ lúc này');
  expect(text()).not.toContain('private provider error');
  expect(mockDelete).not.toHaveBeenCalled();
  await act(async () => view.unmount());
  expect(mockDelete).toHaveBeenCalled();
});

it('clears the old question and recording when the pupil or opened step changes', async () => {
  await render(); await press('Ghi âm câu hỏi'); await press('Nói xong');
  await act(async () => view.update(<LessonQuestion sessionId="new-session" revision={0} stepIndex={0} scope="pupil-b" />));
  expect(input().props.value).toBe('');
  const { QuestionRecording } = require('../features/tutoring/QuestionRecording');
  expect(view.root.findAllByType(QuestionRecording)).toHaveLength(0);
  expect(mockDelete).toHaveBeenCalled();
});

it('keeps typed questions usable when microphone permission is denied', async () => {
  (AudioModule.requestRecordingPermissionsAsync as jest.Mock).mockResolvedValue({ granted: false });
  await render(); await press('Ghi âm câu hỏi');
  expect(text()).toContain('Chưa dùng được mic'); expect(mockRecorder.record).not.toHaveBeenCalled();
  act(() => input().props.onChangeText('Em chưa hiểu bước này.')); await press('Gửi câu hỏi');
  expect(TutorService.askLesson).toHaveBeenCalledTimes(1);
});

it('aborts an in-flight question on dismiss and ignores the late response', async () => {
  let finish!: (value: any) => void;
  (TutorService.askLesson as jest.Mock).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await render(); act(() => input().props.onChangeText('Vì sao phải quy đồng?')); await press('Gửi câu hỏi');
  const signal = (TutorService.askLesson as jest.Mock).mock.calls[0][1];
  act(() => view.unmount()); expect(signal.aborted).toBe(true);
  await act(async () => finish({ answer: 'Late reply' }));
});

it('stops recording when the app leaves the foreground', async () => {
  let listener!: (state: string) => void;
  const spy = jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { listener = callback; return { remove: jest.fn() }; });
  await render(); await press('Ghi âm câu hỏi');
  await act(async () => listener('background'));
  expect(mockRecorder.stop).toHaveBeenCalledTimes(1);
  expect(TutorService.transcribeQuestion).not.toHaveBeenCalled();
  spy.mockRestore();
});

it('waits for recorder cleanup before offering another recording after cancellation', async () => {
  await render(); await press('Ghi âm câu hỏi');
  let stopped!: () => void;
  mockRecorder.stop.mockImplementationOnce(() => new Promise<void>(resolve => { stopped = resolve; }));
  await press('Hủy ghi âm');
  const microphone = view.root.findAll(node => node.props.accessibilityLabel === 'Ghi âm câu hỏi' && node.props.onPress);
  await act(async () => stopped());
  expect(microphone).toHaveLength(0);
  expect(input()).toBeDefined();
  expect(TutorService.transcribeQuestion).not.toHaveBeenCalled();
});
