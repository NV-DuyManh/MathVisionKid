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
jest.mock('../features/tutoring/api/TutorService', () => ({
  ...jest.requireActual('../features/tutoring/api/TutorService'),
  TutorService: { inspect: jest.fn(), coach: jest.fn(), startLesson: jest.fn(), answerLesson: jest.fn(), checkDivision: jest.fn() },
}));
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
const render = async (confirmProblem = true) => {
  await act(async () => { view = TestRenderer.create(<MathGuideScreen />); });
  if (confirmProblem && button('Em đã kiểm tra đề bài và các số') && !button('Em đã kiểm tra đề bài và các số').props.disabled)
    act(() => button('Em đã kiểm tra đề bài và các số').props.onPress());
};

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

const division = { dividend: '17843', divisor: '3', quotient: '59947', rows: ['028', '014', '023', '02'] };
const divisionPhoto = () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'WORK', problemText: '', needsProblem: true,
    lines: [{ text: '17843 : 3', box: null, uncertain: true, division }] });
};

it('keeps the division editor and companion text when a photo has one division plus a note', async () => {
  divisionPhoto();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'WORK', problemText: '', needsProblem: true,
    lines: [{ text: '17843 : 3', box: null, uncertain: true, division },
      { text: 'Chữ ghi bên cạnh', box: null, uncertain: false }] });
  await render();
  expect(input('Thương em viết').props.value).toBe('59947');
  expect(readText()).toContain('Chữ ghi bên cạnh');
  act(() => input('Thương em viết').props.onChangeText('5947'));
  expect(input('Thương em viết').props.value).toBe('5947');
  expect(readText()).toContain('Chữ ghi bên cạnh');
});

it('reviews every long-division field before grading and lets the pupil repair a wrong quotient', async () => {
  divisionPhoto(); await render();
  expect(readText()).not.toContain('Cần thêm đề bài');
  expect(input('Thương em viết').props.value).toBe('59947');
  expect(input('Hàng 1').props.value).toBe('028');
  expect(input('Hàng 4 · Số dư cuối').props.value).toBe('02');
  expect(button('Kiểm tra phép chia').props.disabled).toBe(true);
  expect(TutorService.checkDivision).not.toHaveBeenCalled();
  (TutorService.checkDivision as jest.Mock).mockResolvedValue({ status: 'TRY_AGAIN', field: 'quotient', rowIndex: null, message: 'Em xem lại thương ở lượt 3.' });
  act(() => button('Em đã đối chiếu các số với ảnh').props.onPress());
  expect(button('Em đã đối chiếu các số với ảnh').props['aria-checked']).toBe(true);
  await act(async () => { await button('Kiểm tra phép chia').props.onPress(); });
  expect(TutorService.checkDivision).toHaveBeenCalledWith(division, true, expect.anything());
  expect(readText()).toContain('Em xem lại thương ở lượt 3.');
  act(() => input('Thương em viết').props.onChangeText('5947'));
  expect(readText()).not.toContain('Em xem lại thương ở lượt 3.');
  expect(button('Kiểm tra phép chia').props.disabled).toBe(true);
  (TutorService.checkDivision as jest.Mock).mockResolvedValue({ status: 'CORRECT', field: '', rowIndex: null, message: 'Các hàng đã đúng.' });
  act(() => button('Em đã kiểm tra phần vừa sửa').props.onPress());
  await act(async () => { await button('Kiểm tra phép chia').props.onPress(); });
  expect(TutorService.checkDivision).toHaveBeenLastCalledWith({ ...division, quotient: '5947' }, true, expect.anything());
  expect(readText()).toContain('Em làm đúng rồi!');
  expect(TutorService.startLesson).not.toHaveBeenCalled();
});

it('does not apply stale grading after editing a row and preserves inputs through failure', async () => {
  divisionPhoto(); await render();
  let finish!: (value: unknown) => void;
  (TutorService.checkDivision as jest.Mock).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  act(() => button('Em đã đối chiếu các số với ảnh').props.onPress());
  await act(async () => { button('Kiểm tra phép chia').props.onPress(); });
  const signal = (TutorService.checkDivision as jest.Mock).mock.calls[0][2];
  act(() => input('Hàng 1').props.onChangeText('029'));
  expect(signal.aborted).toBe(true);
  await act(async () => { finish({ status: 'CORRECT', field: '', rowIndex: null, message: 'Stale success' }); });
  expect(readText()).not.toContain('Stale success');
  expect(input('Hàng 1').props.value).toBe('029');
  (TutorService.checkDivision as jest.Mock).mockRejectedValue(new Error('connection'));
  act(() => button('Em đã đối chiếu các số với ảnh').props.onPress());
  await act(async () => { button('Kiểm tra phép chia').props.onPress(); });
  expect(readText()).toContain('Các số em đã sửa vẫn được giữ');
  expect(input('Hàng 1').props.value).toBe('029');
});

it('lets pupils add missing rows, blocks unread digits, and restores saved division fields', async () => {
  (useLocalSearchParams as jest.Mock).mockReturnValue({ workText: '87268 : 3\nThương đã viết: 2989\nCác hàng đã viết:\n27\n0026\n008\n01' });
  await render();
  expect(input('Thương em viết').props.value).toBe('2989');
  act(() => button('Thêm hàng bị thiếu').props.onPress());
  expect(input('Hàng 5 · Số dư cuối').props.value).toBe('');
  expect(button('Em đã đối chiếu các số với ảnh').props.disabled).toBe(true);
  act(() => input('Hàng 5 · Số dư cuối').props.onChangeText('[?]'));
  expect(button('Em đã đối chiếu các số với ảnh').props.disabled).toBe(true);
  act(() => input('Hàng 5 · Số dư cuối').props.onChangeText('01'));
  expect(button('Em đã đối chiếu các số với ảnh').props.disabled).toBe(false);
  act(() => button('Xóa hàng 4').props.onPress());
  expect(input('Hàng 4 · Số dư cuối').props.value).toBe('01');
  act(() => button('Thêm hàng sau hàng 1').props.onPress());
  expect(input('Hàng 2').props.value).toBe('');
  expect(input('Hàng 3').props.value).toBe('0026');
  expect(input('Hàng 5 · Số dư cuối').props.value).toBe('01');
  expect(TutorService.inspect).not.toHaveBeenCalled();
});

it('asks for a smaller crop without starting a lesson from an incomplete page', async () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'UNREADABLE', problemText: '', lines: [], needsProblem: false, needsCrop: true });
  await render();
  expect(readText()).toContain('Chọn một vùng nhỏ hơn nhé');
  expect(button('Bắt đầu từng bước')).toBeUndefined();
  act(() => button('Chọn lại vùng bài toán').props.onPress());
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push).toHaveBeenCalledWith('/crop');
  expect(recognitionDraftStore.getDraft()?.privacyImageUri).toBe('file:///masked.jpg');
  expect(TutorService.startLesson).not.toHaveBeenCalled();
});

it('starts meaningful reasoning steps without displaying the answer key', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false }, expect.anything());
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
  act(() => button('Em đã đối chiếu bài làm với ảnh').props.onPress());
  await act(async () => { await button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '90 × 2 : 15 = 12 (cm)', { problemConfirmed: true, workConfirmed: true }, expect.anything());
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
  act(() => button('Em đã đối chiếu bài làm với ảnh').props.onPress());
  await act(async () => { await button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, WORK.lines.map(row => row.text).join('\n'), { problemConfirmed: true, workConfirmed: true }, expect.anything());
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false }, expect.anything());
  expect(readText()).toContain('chưa đọc rõ');
});

it('blocks even confident photo text until the pupil confirms and invalidates confirmation on editing', async () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ ...WORK, kind: 'MIXED', problemText: PROBLEM });
  await render(false);
  expect(button('Cùng hiểu và đối chiếu bài').props.disabled).toBe(true);
  act(() => button('Cùng hiểu và đối chiếu bài').props.onPress());
  expect(TutorService.startLesson).not.toHaveBeenCalled();
  act(() => button('Em đã kiểm tra đề bài và các số').props.onPress());
  await act(async () => { button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false }, expect.anything());
  act(() => button('Chỉnh đề bài').props.onPress());
  act(() => input('Nội dung đề bài').props.onChangeText(PROBLEM.replace('90', '[?]')));
  act(() => button('Dùng nội dung này').props.onPress());
  expect(button('Em đã kiểm tra đề bài và các số').props.disabled).toBe(true);
  expect(button('Cùng hiểu và đối chiếu bài')).toBeUndefined();
});

it('preserves a wrong written value and uses work only after explicit source review', async () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'MIXED', problemText: PROBLEM, needsProblem: false,
    lines: [{ text: '4(3x - 5) + 15 = 11', box: null, uncertain: false }] });
  await render();
  expect(readText()).toContain('4(3x - 5) + 15 = 11');
  act(() => button('Chỉnh chỗ chưa đọc đúng').props.onPress());
  act(() => input('Nội dung bài làm').props.onChangeText('4(2x - 5) + 15 = 11'));
  act(() => button('Dùng nội dung này').props.onPress());
  await act(async () => { button('Cùng hiểu và đối chiếu bài').props.onPress(); });
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '4(2x - 5) + 15 = 11',
    { problemConfirmed: true, workConfirmed: true }, expect.anything());
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
