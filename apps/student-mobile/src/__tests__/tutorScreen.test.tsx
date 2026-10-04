import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useLocalSearchParams, useRouter } from 'expo-router';
import MathGuideScreen from '../app/learning/math-guide';
import { TutorService } from '../features/tutoring/api/TutorService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

jest.mock('expo-router', () => ({
  useRouter: jest.fn(), useLocalSearchParams: jest.fn(),
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../features/tutoring/api/TutorService', () => ({ TutorService: { inspect: jest.fn(), coach: jest.fn(), startLesson: jest.fn(), answerLesson: jest.fn() } }));
jest.mock('../features/recognition/components/RecognitionProgress', () => ({
  RecognitionProgress: ({ title, onCancel, cancelLabel }: any) => {
    const React = require('react'); const { View, Text, Pressable } = require('react-native');
    return React.createElement(View, {}, React.createElement(Text, {}, title),
      React.createElement(Pressable, { accessibilityLabel: cancelLabel, onPress: onCancel }, React.createElement(Text, {}, cancelLabel)));
  },
}));
const PROBLEM = 'Cho hình thang ABCD có AB = 8 cm, CD = 15 cm. Diện tích tam giác ACD là 90 cm². Tính diện tích hình thang.';
const WORK = { kind: 'WORK', problemText: '', needsProblem: true, lines: [
  { text: 'Bài giải:', box: null, uncertain: false },
  { text: '90 × 2 : 15 = 12 (cm)', box: null, uncertain: false },
  { text: '(15 + 8) × 12 : 2 = 138 (cm²)', box: null, uncertain: false },
] };
const LESSON = { sessionId: 'abcdefghijklmnopqrstuv', revision: 0, topic: 'Hình thang', goal: 'Tìm chiều cao rồi tính diện tích.',
  outline: ['Tìm điều còn thiếu', 'Tìm chiều cao', 'Tính diện tích'], stepIndex: 0, completed: [], status: 'READY', feedback: '',
  step: { title: 'Tìm điều còn thiếu', explanation: 'Cần hai đáy và chiều cao.', question: 'Em tìm gì trước?', choices: ['Chiều cao', 'Chu vi'], expression: '', unit: '', workExcerpt: '' } };
const readText = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const input = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onChangeText === 'function')[0];
let view: TestRenderer.ReactTestRenderer;

beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft();
  (useLocalSearchParams as jest.Mock).mockReturnValue({ problemText: PROBLEM });
  (useRouter as jest.Mock).mockReturnValue({ push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => true });
  (TutorService.inspect as jest.Mock).mockResolvedValue(WORK);
  (TutorService.startLesson as jest.Mock).mockResolvedValue(LESSON);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...LESSON, status: 'TRY_AGAIN', feedback: 'Em thử chọn lại nhé.' });
});
afterEach(() => { if (view) act(() => view.unmount()); });
const render = async () => { await act(async () => { view = TestRenderer.create(<MathGuideScreen />); }); };

it('returns home when a lesson is opened without navigation history', async () => {
  const replace = jest.fn();
  (useRouter as jest.Mock).mockReturnValue({ replace, back: jest.fn(), canGoBack: () => false });
  await render();
  act(() => button('Quay lại').props.onPress());
  expect(replace).toHaveBeenCalledWith('/');
});
const photo = (privacyConfirmed = true) => {
  (useLocalSearchParams as jest.Mock).mockReturnValue({});
  recognitionDraftStore.setDraft({ rawUri: 'file:///original.jpg', uri: 'file:///masked-crop.jpg', croppedImageUri: 'file:///masked-crop.jpg',
    privacyImageUri: 'file:///masked.jpg', privacyConfirmed, mode: 'MATH_TUTOR', width: 500, height: 300, filename: 'photo.jpg', mimeType: 'image/jpeg' });
};

it('starts meaningful reasoning steps without displaying the answer key', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', expect.anything());
  expect(readText()).toContain('Em tìm gì trước?');
  expect(readText()).not.toContain('138');
  expect(button('Xem bước tiếp')).toBeUndefined();
});

it('keeps a wrong response at the same reasoning step', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  await act(async () => { await button('Chu vi').props.onPress(); });
  expect(TutorService.answerLesson).toHaveBeenCalledWith(LESSON, 'Chu vi', false, expect.anything());
  expect(readText()).toContain('Em thử chọn lại nhé.');
  expect(readText()).toContain('Em tìm gì trước?');
});

it('opens and collapses the problem while keeping the current lesson step', async () => {
  await render();
  expect(button('Xem lại đề bài')).toBeUndefined();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(button('Xem lại đề bài').props['aria-expanded']).toBe(false);
  expect(readText()).not.toContain(PROBLEM);
  act(() => button('Xem lại đề bài').props.onPress());
  expect(button('Xem lại đề bài').props['aria-expanded']).toBe(true);
  expect(readText()).toContain(PROBLEM);
  act(() => button('Xem lại đề bài').props.onPress());
  expect(readText()).not.toContain(PROBLEM);
  expect(readText()).toContain('Em tìm gì trước?');
  expect(TutorService.startLesson).toHaveBeenCalledTimes(1);
  act(() => button('Chỉnh đề bài').props.onPress());
  expect(input('Nội dung đề bài').props.value).toBe(PROBLEM);
});

it('uses a short numeric input and unit only after the server advances', async () => {
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...LESSON, stepIndex: 1, revision: 1, completed: [{}],
    step: { ...LESSON.step, title: 'Tìm chiều cao', question: 'Em tính chiều cao?', choices: [], expression: '90 × 2 ÷ 15', unit: 'cm' } });
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  await act(async () => { await button('Chiều cao').props.onPress(); });
  expect(readText()).toContain('90 × 2 ÷ 15');
  expect(readText()).not.toContain('138');
  expect(input('Câu trả lời của em').props.keyboardType).toBe('decimal-pad');
});

it('never uploads before privacy review', async () => {
  photo(false); await render();
  expect(TutorService.inspect).not.toHaveBeenCalled();
  act(() => button('Kiểm tra thông tin cá nhân trên ảnh').props.onPress());
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.replace).toHaveBeenCalledWith('/privacy');
});

it('requires a problem and preserves the work when taking its companion photo', async () => {
  photo(); await render();
  expect(button('Cùng hiểu và đối chiếu bài')).toBeUndefined();
  act(() => button('Chụp thêm đề bài').props.onPress());
  const context = recognitionDraftStore.getDraft()?.lessonContext;
  expect(context?.purpose).toBe('ADD_PROBLEM');
  expect(context?.workText).toContain('90 × 2 : 15');
  expect(context?.workImageUri).toBe('file:///masked-crop.jpg');
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push).toHaveBeenCalledWith({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } });
});

it('combines the second privacy-approved problem photo with the first work', async () => {
  photo();
  recognitionDraftStore.updateDraft({ lessonContext: { purpose: 'ADD_PROBLEM', problemText: '', workText: '90 × 2 : 15 = 12 (cm)',
    workImageUri: 'file:///previous-masked.jpg', lessonId: 'lesson_existing', uncertainWork: false } });
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'PROBLEM', problemText: PROBLEM, lines: [], needsProblem: false });
  await render();
  expect(readText()).toContain(PROBLEM);
  await act(async () => { await button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '90 × 2 : 15 = 12 (cm)', expect.anything());
  act(() => button('Xem bài em đã viết').props.onPress());
  expect(view.root.findAll(node => node.props.accessibilityLabel === 'Ảnh bài em đã làm')[0].props.source.uri).toBe('file:///previous-masked.jpg');
});

it('does not treat another work photo as the missing original problem', async () => {
  photo();
  recognitionDraftStore.updateDraft({ lessonContext: { purpose: 'ADD_PROBLEM', problemText: '', workText: '90 × 2 : 15 = 12 (cm)',
    lessonId: 'lesson_existing', uncertainWork: false } });
  await render();
  expect(readText()).toContain('Ảnh này chưa có đề bài');
  expect(button('Cùng hiểu và đối chiếu bài')).toBeUndefined();
});

it('allows a manually supplied original question without losing work', async () => {
  photo(); await render();
  act(() => button('Nhập đề bài').props.onPress());
  act(() => input('Nội dung đề bài').props.onChangeText(PROBLEM));
  act(() => button('Dùng nội dung này').props.onPress());
  await act(async () => { await button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, WORK.lines.map(row => row.text).join('\n'), expect.anything());
});

it('offers recropping for several exercises', async () => {
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'MULTIPLE', problemText: '', lines: [], needsProblem: false });
  photo(); await render();
  expect(readText()).toContain('Mỗi lần một bài nhé');
  act(() => button('Chọn lại vùng bài toán').props.onPress());
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push).toHaveBeenCalledWith('/crop');
});

it('shows a retry without exposing service errors', async () => {
  (TutorService.inspect as jest.Mock).mockRejectedValue({ response: { status: 503, data: { message: 'provider secret' } } });
  photo(); await render();
  expect(readText()).toContain('Bài của em vẫn ở đây');
  expect(readText()).not.toContain('provider secret');
  expect(button('Đọc lại ảnh')).toBeDefined();
});

it('does not use uncertain work as a basis for comparing a method', async () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ ...WORK, kind: 'MIXED', problemText: PROBLEM,
    lines: WORK.lines.map(row => ({ ...row, uncertain: true })) });
  await render();
  await act(async () => { await button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', expect.anything());
  expect(readText()).toContain('chưa đọc rõ');
});

it('shows the explanation before the pupil answers, rather than a generic extra hint', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(readText()).toContain('Cần hai đáy và chiều cao.');
  expect(readText()).toContain(LESSON.goal);
});

it('distinguishes lesson generation failure from a network error and offers a concrete retry', async () => {
  (TutorService.startLesson as jest.Mock).mockRejectedValue({ response: { status: 503, data: { message: 'provider secret' } } });
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(readText()).toContain('chưa chuẩn bị được hướng dẫn');
  expect(readText()).not.toContain('Chưa kết nối được');
  expect(readText()).not.toContain('provider secret');
  expect(button('Bắt đầu lại bài học')).toBeDefined();
  expect(button('Nhận một gợi ý để bắt đầu')).toBeUndefined();
});
