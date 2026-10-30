import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useLocalSearchParams, useRouter } from 'expo-router';
import MathGuideScreen from '../app/learning/math-guide';
import { TutorService } from '../features/tutoring/api/TutorService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { AuthContext } from '../context/AuthContext';
import { StudentWorkReview } from '../features/tutoring/StudentWorkReview';
import { LessonNarration } from '../features/tutoring/LessonNarration';
import { prepareLessonMedia } from '../features/tutoring/narrationApi';
import { quizApi } from '../features/quiz/quizApi';

jest.mock('../features/quiz/quizApi', () => ({ ...jest.requireActual('../features/quiz/quizApi'), quizApi: {
  prepare: jest.fn().mockResolvedValue({ status: 'READY' }),
  fromLearning: jest.fn().mockRejectedValue(new Error('Quiz transport is mocked in screen tests')),
} }));

jest.mock('expo-speech', () => ({ speak: jest.fn(), stop: jest.fn().mockResolvedValue(undefined), getAvailableVoicesAsync: jest.fn().mockResolvedValue([]) }));
// Native image decoding is outside this React renderer; browser export tests load the actual assets.
jest.mock('../components/ui/AppIllustration', () => ({
  AppIllustration: (props: any) => require('react').createElement('Image', props),
  prepareIllustrations: jest.fn().mockResolvedValue(undefined),
}));
jest.mock('expo-audio', () => ({ AudioModule: {}, RecordingPresets: {}, useAudioRecorder: jest.fn(), useAudioRecorderState: jest.fn() }));
// Screen navigation tests must not start speech HTTP requests against a running service.
// The narration/preparation suites exercise the transport and audio lifecycle separately.
jest.mock('../features/tutoring/narrationApi', () => ({
  NARRATION_WAIT_SECONDS: 45, prioritizeNarration: jest.fn().mockResolvedValue(undefined),
  downloadNarration: jest.fn().mockRejectedValue(new Error('Speech transport is mocked in screen tests')),
  prepareLessonMedia: jest.fn().mockResolvedValue(undefined),
  readNarrationProgress: jest.fn().mockRejectedValue(new Error('Speech progress is mocked in screen tests')),
}));

jest.mock('expo-router', () => ({
  useRouter: jest.fn(), useLocalSearchParams: jest.fn(),
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../features/tutoring/api/TutorService', () => ({
  ...jest.requireActual('../features/tutoring/api/TutorService'),
  TutorService: { inspect: jest.fn(), coach: jest.fn(), startLesson: jest.fn(), answerLesson: jest.fn(), lessonPreparation: jest.fn(), checkDivision: jest.fn(), reviewWork: jest.fn() },
}));
jest.mock('../features/recognition/components/RecognitionProgress', () => ({
  RecognitionProgress: ({ title, onCancel, cancelLabel, complete, onComplete }: any) => {
    const React = require('react'); const { View, Text, Pressable } = require('react-native');
    React.useEffect(() => { if (complete) onComplete?.(); }, [complete, onComplete]);
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
const editProblem = () => {
  act(() => button('Chỉnh đề bài').props.onPress());
};
let view: TestRenderer.ReactTestRenderer;

it('collapses only the display after confirmation and keeps the complete source when editing', async () => {
  await render(false);
  expect(button('Xem đầy đủ')).toBeUndefined();
  await act(async () => button('Em đã kiểm tra đề bài và các số').props.onPress());
  expect(button('Xem đầy đủ').props.accessibilityState.expanded).toBe(false);
  act(() => button('Xem đầy đủ').props.onPress());
  expect(button('Thu gọn').props.accessibilityState.expanded).toBe(true);
  act(() => button('Thu gọn').props.onPress());
  editProblem();
  expect(input('Nội dung đề bài').props.value).toBe(PROBLEM);
});

it('opens reading immediately and starts speech preparation before the listening sheet is opened', async () => {
  const reading = { ...LESSON, preparingMath: true, understandingSteps: 3, outline: ['Dữ kiện','Câu hỏi','Đối chiếu'],
    step: { ...LESSON.step, kind: 'UNDERSTAND' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(reading);
  const auth = { user: { id: 'pupil-a' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
  await act(async () => { view = TestRenderer.create(<AuthContext.Provider value={auth}><MathGuideScreen /></AuthContext.Provider>); });
  act(() => button('Em đã kiểm tra đề bài và các số').props.onPress());
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(view.root.findAllByProps({ testID: 'lesson-preparation-screen' })).toHaveLength(0);
  expect(readText()).toContain(reading.step.question);
  expect(readText()).toContain('Em đọc đề trước nhé');
  expect(prepareLessonMedia).toHaveBeenCalledWith({ sessionId: reading.sessionId, revision: 0 }, expect.any(String), expect.anything());
  act(() => button('Xem thêm').props.onPress());
  expect(button('Xem video bài này')).toBeUndefined();
});

it('opens a single fraction at a time only when requested and preserves the active step', async () => {
  (useLocalSearchParams as jest.Mock).mockReturnValue({ problemText: 'Có 1/3 cây táo, 2/5 cây xoài. Hỏi còn lại bao nhiêu phần?' });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(button('Kiểm tra phần em chọn')).toBeUndefined();
  act(() => button('Xem thêm').props.onPress()); act(() => button('Xem hình phân số').props.onPress());
  expect(view.root.findAll(node => node.props.accessibilityRole === 'checkbox' && node.props.onPress)).toHaveLength(3);
  act(() => button('Hình tiếp').props.onPress());
  expect(view.root.findAll(node => node.props.accessibilityRole === 'checkbox' && node.props.onPress)).toHaveLength(5);
  act(() => button('Đóng Cùng nhìn phân số').props.onPress());
  expect(readText()).toContain(LESSON.step.question); expect(TutorService.answerLesson).not.toHaveBeenCalled();
});

it('gives the summary its own transition before showing the first math step', async () => {
  const checked = { kind: 'UNDERSTAND', title: 'Dữ kiện', expression: '', answer: 'Có 12 bút', unit: '', explanation: 'Điều đã biết.' };
  const reading = { ...LESSON, revision: 2, stepIndex: 2, understandingSteps: 3, outline: ['Dữ kiện','Câu hỏi','Đối chiếu',...LESSON.outline],
    completed: [checked, { ...checked, answer: 'Hỏi còn bao nhiêu bút?' }],
    step: { ...LESSON.step, kind: 'UNDERSTAND', choices: ['Đúng', 'Sai'] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(reading);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...reading, revision: 3, stepIndex: 3, status: 'CORRECT',
    completed: [...reading.completed, { ...checked, answer: 'Đúng' }], summary: { givens: ['Có 12 bút', 'Cho 3 bút'], question: 'Hỏi còn bao nhiêu bút?' },
    step: { ...LESSON.step, kind: 'MATH', title: 'Tìm số bút còn lại', question: 'Em tính 12 trừ 3 nhé.', choices: [], expression: '12-3' } });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  await act(async () => button('Đúng').props.onPress());
  expect(readText()).toContain('Cho 3 bút'); expect(readText()).not.toContain('Em tính 12 trừ 3 nhé.');
  act(() => button('Bắt đầu giải').props.onPress());
  expect(readText()).toContain('Em tính 12 trừ 3 nhé.'); expect(readText()).not.toContain('Cho 3 bút');
  expect(TutorService.answerLesson).toHaveBeenCalledTimes(1);
});

it.each(['PREPARING', 'RETRYABLE', 'UNAVAILABLE'])('keeps reading progress and opens math after %s without submitting the third answer again', async status => {
  jest.useFakeTimers();
  try {
    const checked = { kind: 'UNDERSTAND', title: 'Dữ kiện', expression: '', answer: 'Có 12 bút', unit: '', explanation: 'Đọc đề.' };
    const reading = { ...LESSON, preparingMath: true, revision: 2, stepIndex: 2, understandingSteps: 3,
      outline: ['Dữ kiện', 'Câu hỏi', 'Đối chiếu'], completed: [checked, checked],
      step: { ...LESSON.step, kind: 'UNDERSTAND', choices: ['Đúng', 'Sai'] } };
    const pending = { ...reading, revision: 3, stepIndex: 3, completed: [checked, checked, checked], status,
      feedback: 'Phần hiểu đề đã được giữ lại.', step: null };
    const ready = { ...pending, preparingMath: false, status: 'READY', outline: [...reading.outline, ...LESSON.outline],
      step: { ...LESSON.step, kind: 'MATH', question: 'Em tự tính số bút.', choices: [], expression: '12-3' } };
    (TutorService.startLesson as jest.Mock).mockResolvedValue(reading);
    (TutorService.answerLesson as jest.Mock).mockResolvedValue(pending);
    (TutorService.lessonPreparation as jest.Mock).mockResolvedValue(ready);
    await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
    await act(async () => button('Đúng').props.onPress());
    expect(readText()).toContain('Phần hiểu đề đã được giữ lại.');
    expect(readText()).not.toContain('Đây là các bước em đã tự tính');
    expect(quizApi.fromLearning).not.toHaveBeenCalled();
    if (status === 'PREPARING') await act(async () => jest.advanceTimersByTime(500));
    else await act(async () => button('Thử chuẩn bị lại').props.onPress());
    expect(readText()).toContain('Em tự tính số bút.');
    expect(TutorService.answerLesson).toHaveBeenCalledTimes(1);
    expect(TutorService.lessonPreparation).toHaveBeenCalledTimes(1);
  } finally { jest.useRealTimers(); }
});

beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft();
  Object.values(TutorService).forEach(value => { if (jest.isMockFunction(value)) value.mockReset(); });
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

it('prepares Quiz from the confirmed text without waiting to start Tutor and invalidates it when editing', async () => {
  let completePreparation!: (value: unknown) => void;
  (quizApi.prepare as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { completePreparation = resolve; }));
  await render(false); expect(quizApi.prepare).not.toHaveBeenCalled();
  await act(async () => button('Em đã kiểm tra đề bài và các số').props.onPress());
  expect(quizApi.prepare).toHaveBeenCalledWith(expect.any(String), expect.any(Number), PROBLEM, true);
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(TutorService.startLesson).toHaveBeenCalledTimes(1);
  expect(readText()).toContain(LESSON.step.question);
  await act(async () => completePreparation({ status: 'READY' }));
  act(() => button('Chỉnh đề bài').props.onPress());
  expect((quizApi.prepare as jest.Mock).mock.calls.at(-1)!.slice(2)).toEqual(['', false]);
});

it('shows lesson preparation by itself immediately, then replaces it with the ready lesson', async () => {
  let finish!: (value: typeof LESSON) => void;
  (TutorService.startLesson as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  const begin = button('Bắt đầu từng bước').props.onPress;
  act(() => begin());
  expect(view.root.findAllByProps({ testID: 'lesson-preparation-screen' }).length).toBeGreaterThan(0);
  expect(readText()).toContain('Chuẩn bị các bước học');
  expect(readText()).not.toContain(PROBLEM);
  expect(readText()).not.toContain('HỌC CÙNG MATHVISIONKID');
  expect(button('Chụp bài khác')).toBeUndefined();
  expect(button('Mở máy tính bỏ túi')).toBeUndefined();
  expect(button('Dừng chờ')).toBeDefined();
  act(() => begin());
  expect(TutorService.startLesson).toHaveBeenCalledTimes(1);
  await act(async () => finish(LESSON));
  expect(view.root.findAllByProps({ testID: 'lesson-preparation-screen' })).toHaveLength(0);
  expect(readText()).toContain(LESSON.step.question);
});

it('returns from preparation to the confirmed photo, ignores a late response, and allows another attempt', async () => {
  let finish!: (value: typeof LESSON) => void;
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'PROBLEM', problemText: PROBLEM, needsProblem: false, lines: [] });
  (TutorService.startLesson as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  act(() => button('Bắt đầu từng bước').props.onPress());
  const signal = (TutorService.startLesson as jest.Mock).mock.calls[0][3];
  act(() => button('Dừng chờ').props.onPress());
  expect(signal.aborted).toBe(true);
  expect(readText()).toContain(PROBLEM);
  expect(button('Em đã kiểm tra đề bài và các số').props['aria-checked']).toBe(true);
  expect(recognitionDraftStore.getDraft()?.croppedImageUri).toBe('file:///masked-crop.jpg');
  await act(async () => finish(LESSON));
  expect(readText()).not.toContain(LESSON.step.question);
  expect(button('Bắt đầu từng bước').props.disabled).toBe(false);
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).toContain(LESSON.step.question);
  expect(TutorService.startLesson).toHaveBeenCalledTimes(2);
});

it('narrates only the current opened guidance and keeps the learner answer and hidden expression untouched', async () => {
  const current = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '12+5',
    guidance: ['Dữ kiện của bước hiện tại.', 'Vì sao dùng phép cộng ở đây.'] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(current);
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(view.root.findAllByType(LessonNarration)).toHaveLength(0);
  act(() => button('Nghe giảng').props.onPress());
  const narration = view.root.findByType(LessonNarration);
  expect(narration.props.paragraphs).toEqual([current.step.explanation, ...current.step.guidance, current.step.question]);
  expect(narration.props.paragraphs.join(' ')).not.toContain('12+5');
  expect(input('Câu trả lời của em').props.value).toBe('');
  expect(TutorService.answerLesson).not.toHaveBeenCalled();
});

it('asks a small maths response inside a hint without filling the lesson answer', async () => {
  const calculation = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '12+5', question: 'Có tất cả bao nhiêu bút?', guidance: [] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(calculation);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...calculation, status: 'HINT', revision: 1, feedback: 'Gộp hai nhóm bút lại nhé.' });
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  await act(async () => button('Gợi ý cách làm bước này').props.onPress());
  expect(readText()).not.toContain('Dấu + có nghĩa gì?');
  act(() => button('Em muốn hiểu gợi ý rõ hơn').props.onPress());
  expect(readText()).toContain('Dấu + có nghĩa gì?');
  act(() => button('Phép trừ').props.onPress());
  expect(readText()).toContain('Em chọn lại nhé.');
  act(() => button('Phép cộng').props.onPress());
  expect(readText()).toContain('Đúng rồi.');
  expect(input('Câu trả lời của em').props.value).toBe('');
  expect(TutorService.answerLesson).toHaveBeenCalledTimes(1);
});

it('opens and closes the calculator without changing the lesson answer or requesting a hint', async () => {
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  const before = readText();
  act(() => button('Mở máy tính bỏ túi').props.onPress());
  act(() => input('Phép tính').props.onChangeText('17+5'));
  act(() => button('Tính kết quả').props.onPress());
  act(() => button('Đóng máy tính').props.onPress());
  expect(readText()).toBe(before);
  expect(TutorService.startLesson).toHaveBeenCalledTimes(1);
  expect(TutorService.answerLesson).not.toHaveBeenCalled();
});

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

it('shows photo reading by itself, keeps the photo on cancel, and ignores the cancelled result', async () => {
  photo();
  let finish!: (value: object) => void;
  (TutorService.inspect as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  expect(view.root.findAllByProps({ testID: 'lesson-reading-screen' }).length).toBeGreaterThan(0);
  expect(readText()).toContain('Mình đang đọc bài của em');
  expect(readText()).not.toContain('HỌC CÙNG MATHVISIONKID');
  expect(button('Mở máy tính bỏ túi')).toBeUndefined();
  expect(button('Chụp bài khác')).toBeUndefined();
  const signal = (TutorService.inspect as jest.Mock).mock.calls[0][2];
  act(() => button('Dừng chờ, giữ ảnh').props.onPress());
  expect(signal.aborted).toBe(true);
  expect(recognitionDraftStore.getDraft()?.croppedImageUri).toBe('file:///masked-crop.jpg');
  expect(view.root.findAllByProps({ testID: 'lesson-reading-screen' })).toHaveLength(0);
  await act(async () => finish({ kind: 'PROBLEM', problemText: 'Cancelled reading', needsProblem: false, lines: [] }));
  expect(readText()).not.toContain('Cancelled reading');
  expect(button('Đọc lại ảnh')).toBeDefined();
  await act(async () => button('Đọc lại ảnh').props.onPress());
  expect(TutorService.inspect).toHaveBeenCalledTimes(2);
  expect(readText()).toContain('Cần thêm đề bài');
});

it('keeps source-bound work lines through adding the original problem photo', async () => {
  photo();
  const lines = WORK.lines.map((line, index) => ({ ...line, box: [50, 50 + index * 200, 950, 150 + index * 200] }));
  (TutorService.inspect as jest.Mock).mockResolvedValue({ ...WORK, lines });
  await render();
  act(() => button('Chụp thêm đề bài').props.onPress());
  const context = recognitionDraftStore.getDraft()!.lessonContext!;
  expect(context.workLines).toEqual(lines);
  act(() => view.unmount());
  photo();
  recognitionDraftStore.updateDraft({ lessonContext: context, croppedImageUri: 'file:///problem-masked-crop.jpg' });
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'PROBLEM', problemText: PROBLEM, needsProblem: false, lines: [] });
  await render();
  const review = view.root.findByType(StudentWorkReview);
  expect(review.props.lines).toEqual(lines);
  expect(review.props.imageUri).toBe('file:///masked-crop.jpg');
  expect(review.props.photoCurrent).toBe(true);
  expect(review.props.enabled).toBe(false);
  act(() => button('Em đã đối chiếu bài làm với ảnh').props.onPress());
  expect(view.root.findByType(StudentWorkReview).props.enabled).toBe(true);
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
  act(() => view.root.findByType(StudentWorkReview).props.onReviewReady());
  expect(button('Xem lại đề và bài làm')).toBeDefined();
  expect(button('Em đã kiểm tra đề bài và các số')).toBeUndefined();
  act(() => button('Xem lại đề và bài làm').props.onPress());
  expect(button('Em đã kiểm tra đề bài và các số')).toBeDefined();
});

it('invalidates image regions and confirmation when a learner revises a written line', async () => {
  photo();
  const lines = WORK.lines.map((line, index) => ({ ...line, box: [50, 50 + index * 200, 950, 150 + index * 200] }));
  (TutorService.inspect as jest.Mock).mockResolvedValue({ ...WORK, kind: 'MIXED', problemText: PROBLEM, lines });
  await render();
  act(() => button('Em đã đối chiếu bài làm với ảnh').props.onPress());
  const revised = '90 × 2 : 15 = 13 (cm)';
  act(() => view.root.findByType(StudentWorkReview).props.onReviseWork(revised));
  const review = view.root.findByType(StudentWorkReview);
  expect(review.props.enabled).toBe(false);
  expect(review.props.workText).toBe(revised);
  expect(review.props.photoCurrent).toBe(false);
  expect(review.props.lines).toEqual([{ text: revised, box: null, uncertain: false }]);
  expect(review.props.imageUri).toBe('file:///masked-crop.jpg');
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
});

it('allows a pupil to photograph work during a lesson while keeping its confirmed original problem', async () => {
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  act(() => button('Xem thêm').props.onPress());
  act(() => button('Chụp bài em đã làm để nhận xét').props.onPress());
  const context = recognitionDraftStore.getDraft()!.lessonContext!;
  expect(context.purpose).toBe('ADD_WORK');
  expect(context.problemText).toBe(PROBLEM);
  expect(context.problemConfirmed).toBe(true);
});

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

it('reveals division hints progressively without auto-filling and resets them on repair', async () => {
  divisionPhoto(); await render();
  const hints = ['Ở lượt 3, thử nhân 3 với một chữ số.', 'Chọn tích không lớn hơn 14.'];
  (TutorService.checkDivision as jest.Mock).mockResolvedValue({ status: 'TRY_AGAIN', field: 'quotient', rowIndex: null,
    message: 'Em xem lại lượt 3.', hints });
  act(() => button('Em đã đối chiếu các số với ảnh').props.onPress());
  await act(async () => { await button('Kiểm tra phép chia').props.onPress(); });
  expect(readText()).not.toContain(hints[0]);
  act(() => button('Gợi ý sửa bước này').props.onPress());
  expect(readText()).toContain(hints[0]);
  expect(readText()).not.toContain(hints[1]);
  act(() => button('Gợi ý rõ hơn').props.onPress());
  expect(readText()).toContain(hints[1]);
  expect(button('Gợi ý rõ hơn')).toBeUndefined();
  expect(TutorService.checkDivision).toHaveBeenCalledTimes(1);
  expect(input('Thương em viết').props.value).toBe('59947');
  expect(input('Hàng 1').props.value).toBe('028');
  act(() => input('Thương em viết').props.onChangeText('5947'));
  expect(readText()).not.toContain(hints[0]);
  expect(readText()).not.toContain(hints[1]);
  expect(button('Kiểm tra phép chia').props.disabled).toBe(true);
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false, guidedUnderstanding: true, startWithReading: true }, expect.anything());
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

it('keeps the full confirmed source behind a collapsed reference and expands without leaving the lesson', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(readText()).toContain(PROBLEM);
  expect(button('Mở đề bài').props.accessibilityState.expanded).toBe(false);
  expect(view.root.findAllByProps({ testID: 'lesson-problem-content' })).toHaveLength(0);
  act(() => button('Mở đề bài').props.onPress());
  const toggle = button('Thu gọn đề bài');
  expect(toggle.props.accessibilityState.expanded).toBe(true);
  expect(view.root.findAllByProps({ nativeID: toggle.props['aria-controls'] }).length).toBeGreaterThan(0);
  act(() => toggle.props.onPress());
  expect(view.root.findAllByProps({ testID: 'lesson-problem-content' })).toHaveLength(0);
  expect(button('Mở đề bài').props.accessibilityState.expanded).toBe(false);
  act(() => button('Mở đề bài').props.onPress());
  expect(view.root.findAllByProps({ testID: 'lesson-problem-content' }).length).toBeGreaterThan(0);
  expect(readText()).toContain('Em tìm gì trước?');
  expect(TutorService.startLesson).toHaveBeenCalledTimes(1);
  expect(TutorService.answerLesson).not.toHaveBeenCalled();
  editProblem();
  expect(input('Nội dung đề bài').props.value).toBe(PROBLEM);
  expect(view.root.findAllByProps({ testID: 'lesson-problem-reference' })).toHaveLength(0);
});

it('removes duplicated question and calculator entries from more tools while retaining the header calculator', async () => {
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  act(() => button('Xem thêm').props.onPress());
  expect(button('Xem lại đề bài')).toBeUndefined();
  expect(button('Máy tính')).toBeUndefined();
  expect(button('Xem video bài này')).toBeUndefined();
  expect(button('Lưu bài để học tiếp')).toBeDefined();
  act(() => button('Đóng Em cần gì thêm?').props.onPress());
  expect(button('Mở máy tính bỏ túi')).toBeDefined();
  expect(button('Mở đề bài')).toBeDefined();
});

it('uses a short numeric input and unit only after the server advances', async () => {
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...LESSON, status: 'CORRECT', stepIndex: 1, revision: 1,
    completed: [{ title: LESSON.step.title, expression: '', answer: 'Chiều cao', unit: '', explanation: LESSON.step.explanation }],
    step: { ...LESSON.step, title: 'Tìm chiều cao', question: 'Em tính chiều cao?', choices: [], expression: '90 × 2 ÷ 15', unit: 'cm' } });
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(button('Mở đề bài')).toBeDefined();
  await act(async () => { await button('Chiều cao').props.onPress(); });
  expect(readText()).not.toContain('Em tính chiều cao?');
  act(() => button('Tiếp tục bước tiếp theo').props.onPress());
  expect(button('Mở đề bài')).toBeDefined();
  expect(readText()).not.toContain('90 × 2 ÷ 15');
  expect(readText()).not.toContain('138');
  expect(input('Câu trả lời của em').props.keyboardType).toBe('decimal-pad');
});

it('reveals the operation only through help and pauses on a checked classroom solution before the next step', async () => {
  const first = { ...LESSON, outline: ['Tìm phần hai nhóm', 'Tìm phần còn lại'], step: { ...LESSON.step,
    title: 'Tìm phần hai nhóm', solutionSentence: 'Phân số chỉ số cây táo và xoài là:',
    explanation: 'Cần biết phần hai nhóm để tìm phần còn lại.', question: 'Hai nhóm chiếm mấy phần?',
    choices: [], expression: '1/3 + 2/5', unit: 'số cây' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(first);
  (TutorService.answerLesson as jest.Mock).mockResolvedValueOnce({ ...first, status: 'HINT', feedback: 'Đổi về các phần cùng cỡ.' })
    .mockResolvedValueOnce({ ...first, revision: 1, stepIndex: 1, status: 'CORRECT', feedback: 'Đã đúng.',
      completed: [{ ...first.step, answer: '11/15', calculationDetails: ['5/15 + 6/15 = 11/15'] }],
      step: { ...first.step, title: 'Tìm phần còn lại', question: 'Còn lại mấy phần?', expression: '1 − 11/15' } });
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).toContain(first.step.explanation);
  expect(readText()).not.toContain('1/3 + 2/5');
  expect(input('Tử số câu trả lời')).toBeDefined();
  act(() => input('Tử số câu trả lời').props.onChangeText('11'));
  act(() => input('Mẫu số câu trả lời').props.onChangeText('15'));
  await act(async () => button('Gợi ý cách làm bước này').props.onPress());
  expect(input('Tử số câu trả lời').props.value).toBe('11');
  expect(input('Mẫu số câu trả lời').props.value).toBe('15');
  expect(view.root.findAllByProps({ accessibilityLabel: '1 phần 3 + 2 phần 5 = ?' }).length).toBeGreaterThan(0);
  await act(async () => button('Kiểm tra bước này').props.onPress());
  expect(readText()).toContain('Viết vào bài giải');
  expect(readText()).not.toContain('Còn lại mấy phần?');
  const calls = (TutorService.answerLesson as jest.Mock).mock.calls.length;
  act(() => button('Tiếp tục bước tiếp theo').props.onPress());
  expect(readText()).toContain('Còn lại mấy phần?');
  expect(readText()).not.toContain('Viết vào bài giải');
  expect(TutorService.answerLesson).toHaveBeenCalledTimes(calls);
});

it('opens the richer explanation on demand without changing the pupil answer', async () => {
  const items = ['Hiểu các nhóm cây trong đề.', 'Chia lại thành các phần bằng nhau.', 'Cộng số phần của hai nhóm.'];
  const first = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '12+5', guidance: items } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(first);
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).not.toContain(items[0]);
  act(() => input('Câu trả lời của em').props.onChangeText('22'));
  act(() => button('Nghe giảng').props.onPress());
  act(() => button('Đọc lời giảng chi tiết').props.onPress());
  items.forEach(item => expect(readText()).toContain(item));
  act(() => button('Đóng Nghe giảng').props.onPress());
  expect(input('Câu trả lời của em').props.value).toBe('22');
  expect(readText()).not.toContain(items[0]);
  expect(TutorService.answerLesson).not.toHaveBeenCalled();
});

it('assembles checked solution sentences and an answer only after all steps are complete', async () => {
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...LESSON, status: 'COMPLETE', step: null, stepIndex: 1,
    conclusion: 'Đáp số: 60 cây.', completed: [{ title: 'Tìm cả vườn', solutionSentence: 'Số cây trong vườn là:',
      expression: '16 ÷ (4/15)', answer: '60', unit: 'cây', explanation: 'Tìm một phần rồi gộp cả vườn.', calculationDetails: [] }] });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).not.toContain('Đáp số');
  await act(async () => button('Chiều cao').props.onPress());
  expect(readText()).toContain('Bài giải');
  expect(readText()).toContain('Số cây trong vườn là:');
  expect(readText()).toContain('Đáp số: 60 cây.');
  expect(readText()).not.toContain('Nhìn lại cách giải');
  expect(button('Nghe giảng')).toBeDefined();
});

it('never uploads before privacy review', async () => {
  photo(false); await render();
  expect(TutorService.inspect).not.toHaveBeenCalled();
  act(() => button('Kiểm tra thông tin cá nhân trên ảnh').props.onPress());
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.replace).toHaveBeenCalledWith('/privacy');
});

it('offers progressive help for a concept step without clearing the pupil answer', async () => {
  (TutorService.answerLesson as jest.Mock).mockResolvedValueOnce({ ...LESSON, status: 'HINT', feedback: 'Tìm chiều cao trong hình.' })
    .mockResolvedValueOnce({ ...LESSON, status: 'HINT', feedback: 'Kẻ đường vuông góc với đáy.' });
  await render();
  await act(async () => { button('Bắt đầu từng bước').props.onPress(); });
  await act(async () => { button('Gợi ý cách làm bước này').props.onPress(); });
  expect(TutorService.answerLesson).toHaveBeenCalledWith(LESSON, '', true, expect.anything());
  await act(async () => { button('Gợi ý rõ hơn').props.onPress(); });
  expect(readText()).toContain('Kẻ đường vuông góc');
  expect(readText()).toContain('Em tìm gì trước?');
});

it('allows numerator and denominator input, keeps fraction source, and clears stale wrong feedback on editing', async () => {
  const fraction = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '1 − 1/3 − 2/5', unit: 'phần' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(fraction);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...fraction, status: 'TRY_AGAIN', feedback: 'Em kiểm tra lại nhé.' });
  await render();
  await act(async () => { button('Bắt đầu từng bước').props.onPress(); });
  act(() => button('Nhập kết quả phân số').props.onPress());
  act(() => input('Tử số câu trả lời').props.onChangeText('4'));
  expect(button('Kiểm tra bước này').props.disabled).toBe(true);
  act(() => input('Mẫu số câu trả lời').props.onChangeText('15'));
  await act(async () => { button('Kiểm tra bước này').props.onPress(); });
  expect(TutorService.answerLesson).toHaveBeenCalledWith(fraction, '4/15', false, expect.anything());
  expect(readText()).toContain('Em kiểm tra lại nhé.');
  act(() => input('Tử số câu trả lời').props.onChangeText('8'));
  expect(readText()).not.toContain('Em kiểm tra lại nhé.');
  expect(input('Mẫu số câu trả lời').props.value).toBe('15');
});

it.each([['1 ÷ 3', '1', '3'], ['1 − 5', '-4', '1']])('accepts an exact signed fraction for an ordinary calculation: %s', async (expression, numerator, denominator) => {
  const lesson = { ...LESSON, step: { ...LESSON.step, choices: [], expression, unit: '' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(lesson);
  await render();
  await act(async () => { button('Bắt đầu từng bước').props.onPress(); });
  act(() => button('Nhập kết quả phân số').props.onPress());
  act(() => input('Tử số câu trả lời').props.onChangeText(numerator));
  act(() => input('Mẫu số câu trả lời').props.onChangeText('0'));
  expect(button('Kiểm tra bước này').props.disabled).toBe(true);
  act(() => input('Mẫu số câu trả lời').props.onChangeText(denominator));
  await act(async () => { button('Kiểm tra bước này').props.onPress(); });
  expect(TutorService.answerLesson).toHaveBeenCalledWith(lesson, `${numerator}/${denominator}`, false, expect.anything());
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '90 × 2 : 15 = 12 (cm)', { problemConfirmed: true, workConfirmed: true, guidedUnderstanding: true, startWithReading: true }, expect.anything());
  act(() => button('Xem thêm').props.onPress());
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, WORK.lines.map(row => row.text).join('\n'), { problemConfirmed: true, workConfirmed: true, guidedUnderstanding: true, startWithReading: true }, expect.anything());
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false, guidedUnderstanding: true, startWithReading: true }, expect.anything());
  act(() => button('Xem thêm').props.onPress());
  act(() => button('Xem bài em đã viết').props.onPress());
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
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false, guidedUnderstanding: true, startWithReading: true }, expect.anything());
  editProblem();
  act(() => input('Nội dung đề bài').props.onChangeText(PROBLEM.replace('90', '[?]')));
  act(() => button('Dùng nội dung này').props.onPress());
  expect(button('Em đã kiểm tra đề bài và các số').props.disabled).toBe(true);
  expect(button('Cùng hiểu và đối chiếu bài')).toBeUndefined();
});

it('keeps a disputed original question for editing and cannot start until the pupil repairs it', async () => {
  photo();
  (TutorService.inspect as jest.Mock).mockResolvedValue({ kind: 'PROBLEM', problemText: '[?] ' + PROBLEM, needsProblem: false, lines: [] });
  await render(false);
  expect(readText()).not.toContain('Cần thêm đề bài');
  expect(button('Em đã kiểm tra đề bài và các số').props.disabled).toBe(true);
  expect(TutorService.startLesson).not.toHaveBeenCalled();
  editProblem();
  expect(input('Nội dung đề bài').props.value).toBe('[?] ' + PROBLEM);
  act(() => input('Nội dung đề bài').props.onChangeText(PROBLEM));
  act(() => button('Dùng nội dung này').props.onPress());
  expect(button('Em đã kiểm tra đề bài và các số').props['aria-checked']).toBe(true);
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(TutorService.startLesson).toHaveBeenCalledWith(PROBLEM, '', { problemConfirmed: true, workConfirmed: false, guidedUnderstanding: true, startWithReading: true }, expect.anything());
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
    { problemConfirmed: true, workConfirmed: true, guidedUnderstanding: true, startWithReading: true }, expect.anything());
});

it('shows the explanation before the pupil answers, rather than a generic extra hint', async () => {
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(readText()).toContain('Cần hai đáy và chiều cao.');
  expect(readText()).toContain(LESSON.step.question);
  expect(readText()).not.toContain('HỌC CÙNG MATHVISIONKID');
});

it('distinguishes lesson generation failure from a network error and offers a concrete retry', async () => {
  (TutorService.startLesson as jest.Mock).mockRejectedValue({ response: { status: 503, data: { message: 'provider secret' } } });
  await render();
  await act(async () => { await button('Bắt đầu từng bước').props.onPress(); });
  expect(readText()).toContain('chưa chuẩn bị được hướng dẫn');
  expect(readText()).not.toContain('Chưa kết nối được');
  expect(readText()).not.toContain('provider secret');
  expect(view.root.findAllByProps({ testID: 'lesson-preparation-screen' })).toHaveLength(0);
  expect(readText()).toContain(PROBLEM);
  expect(button('Bắt đầu lại bài học')).toBeDefined();
  expect(button('Nhận một gợi ý để bắt đầu')).toBeUndefined();
});

it('offers source comprehension choices and fraction exploration without advancing the server lesson locally', async () => {
  const problem = 'Một tấm vải dùng 1/3 để may áo, dùng 1/4 để may túi. Hỏi còn lại bao nhiêu phần tấm vải?';
  const fact = 'Một tấm vải dùng 1/3 để may áo';
  const question = 'Hỏi còn lại bao nhiêu phần tấm vải?';
  (useLocalSearchParams as jest.Mock).mockReturnValue({ problemText: problem });
  const comprehension = { ...LESSON, understandingSteps: 3, outline: ['Dữ kiện', 'Câu hỏi', 'Đúng hay sai', ...LESSON.outline],
    step: { ...LESSON.step, kind: 'UNDERSTAND', question: 'Câu nào là điều đề đã cho biết?', choices: [question, fact] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(comprehension);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...comprehension, status: 'TRY_AGAIN', feedback: 'Em đọc lại điều đã biết nhé.' });
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).toContain('Hiểu đề trước khi tính');
  expect(input('Câu trả lời của em')).toBeUndefined();
  expect(view.root.findAll(node => node.props.accessibilityRole === 'checkbox' && node.props.onPress)).toHaveLength(0);
  expect(button('Kiểm tra phần em chọn')).toBeUndefined();
  expect(readText()).not.toContain('Cùng nhìn phân số');
  expect(TutorService.answerLesson).not.toHaveBeenCalled();
  await act(async () => button(question).props.onPress());
  expect(readText()).toContain('Em đọc lại điều đã biết nhé.');
  expect(TutorService.answerLesson).toHaveBeenCalledWith(comprehension, question, false, expect.anything());
  expect(readText()).not.toContain('Bài giải');
  editProblem();
  expect(readText()).not.toContain('Cùng nhìn phân số');
  expect(button(fact)).toBeUndefined();
});

it('reviews comprehension as understanding and keeps it out of the written arithmetic solution', async () => {
  const completed = { kind: 'UNDERSTAND', title: 'Dữ kiện', expression: '', answer: 'Có 8 cm', unit: '', explanation: 'Đây là điều đã biết.' };
  const initial = { ...LESSON, understandingSteps: 3, step: { ...LESSON.step, kind: 'UNDERSTAND' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(initial);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...initial, revision: 1, stepIndex: 1, completed: [completed], status: 'CORRECT' });
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  await act(async () => button('Chiều cao').props.onPress());
  expect(readText()).toContain('Em đã hiểu điều này');
  expect(readText()).not.toContain('Viết vào bài giải');
  expect(button('Tiếp tục bước tiếp theo')).toBeDefined();
});

it('aborts an old-source request and ignores its late response after navigation changes the problem', async () => {
  let finish!: (value: typeof LESSON) => void;
  (TutorService.startLesson as jest.Mock).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  const signal = (TutorService.startLesson as jest.Mock).mock.calls[0][3];
  const next = 'Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?';
  (useLocalSearchParams as jest.Mock).mockReturnValue({ problemText: next });
  await act(async () => view.update(<MathGuideScreen />));
  expect(signal.aborted).toBe(true);
  expect(readText()).toContain(next);
  expect(button('Em đã kiểm tra đề bài và các số').props['aria-checked']).toBe(false);
  await act(async () => finish(LESSON));
  expect(readText()).not.toContain('Em tìm gì trước?');
  expect(button('Bắt đầu từng bước').props.disabled).toBe(true);
});

it('discards lesson progress and answers when the active pupil changes', async () => {
  const auth = (id: string) => ({ user: { id }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() });
  const screen = (id: string) => <AuthContext.Provider value={auth(id)}><MathGuideScreen /></AuthContext.Provider>;
  await act(async () => { view = TestRenderer.create(screen('pupil-a')); });
  act(() => button('Em đã kiểm tra đề bài và các số').props.onPress());
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).toContain('Em tìm gì trước?');
  await act(async () => view.update(screen('pupil-b')));
  expect(readText()).not.toContain('Em tìm gì trước?');
  expect(button('Em đã kiểm tra đề bài và các số').props['aria-checked']).toBe(false);
  expect(button('Bắt đầu từng bước').props.disabled).toBe(true);
});

it('does not re-adopt a prior pupil photo draft or its late OCR response for another pupil', async () => {
  photo();
  let finish!: (value: object) => void;
  (TutorService.inspect as jest.Mock).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const auth = (id: string) => ({ user: { id }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() });
  const screen = (id: string) => <AuthContext.Provider value={auth(id)}><MathGuideScreen /></AuthContext.Provider>;
  await act(async () => { view = TestRenderer.create(screen('pupil-a')); });
  expect(TutorService.inspect).toHaveBeenCalledTimes(1);
  const signal = (TutorService.inspect as jest.Mock).mock.calls[0][2];
  await act(async () => view.update(screen('pupil-b')));
  expect(signal.aborted).toBe(true);
  expect(recognitionDraftStore.getDraft()).toBeNull();
  await act(async () => finish({ kind: 'PROBLEM', problemText: 'Private old pupil problem', lines: [], needsProblem: false }));
  expect(readText()).not.toContain('Private old pupil problem');
  expect(TutorService.inspect).toHaveBeenCalledTimes(1);
  expect(button('Bắt đầu từng bước')).toBeUndefined();
});

it('guides summary choices, then shows the grouped source only after both reading answers are checked', async () => {
  const fact = 'Có 12 bút đỏ';
  const question = 'Hỏi có tất cả bao nhiêu bút?';
  const first = { ...LESSON, understandingSteps: 3, outline: ['Dữ kiện', 'Câu hỏi', 'Đối chiếu', ...LESSON.outline],
    step: { ...LESSON.step, kind: 'UNDERSTAND', question: 'Câu nào là điều đã biết?', choices: [fact, question] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(first);
  await render();
  await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(readText()).not.toContain('Em tập tóm tắt đề');
  expect(readText()).not.toContain('Bản tóm tắt từ đề');
  const checked = { kind: 'UNDERSTAND', title: 'Dữ kiện', expression: '', answer: fact, unit: '', explanation: 'Điều đã biết.' };
  (TutorService.answerLesson as jest.Mock).mockResolvedValueOnce({ ...first, stepIndex: 1, revision: 1, status: 'CORRECT',
    completed: [checked], step: { ...first.step, question: 'Đề hỏi gì?', choices: [fact, question] } });
  await act(async () => button(fact).props.onPress());
  expect(readText()).toContain('Em đã hiểu điều này');
  expect(readText()).not.toContain('Bản tóm tắt từ đề');
  act(() => button('Tiếp tục bước tiếp theo').props.onPress());
  (TutorService.answerLesson as jest.Mock).mockResolvedValueOnce({ ...first, stepIndex: 2, revision: 2, status: 'CORRECT',
    completed: [checked, { ...checked, title: 'Câu hỏi', answer: question }],
    step: { ...first.step, choices: ['Đúng', 'Sai'] }, summary: { givens: [fact, 'thêm 5 bút xanh'], question } });
  await act(async () => button(question).props.onPress());
  expect(readText()).not.toContain('thêm 5 bút xanh');
  act(() => button('Xem thêm').props.onPress());
  act(() => button('Xem lại tóm tắt đề').props.onPress());
  expect(readText()).toContain('thêm 5 bút xanh');
  act(() => button('Đóng Tóm tắt đề').props.onPress());
  expect(TutorService.answerLesson).toHaveBeenCalledTimes(2);
  editProblem();
  expect(readText()).not.toContain('Bản tóm tắt từ đề');
});

it('keeps opened hints visible after a wrong attempt and avoids requesting the same deep help indefinitely', async () => {
  const calculation = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '12+5' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(calculation);
  (TutorService.answerLesson as jest.Mock).mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Gộp hai nhóm, giữ cùng một đơn vị.' })
    .mockResolvedValueOnce({ ...calculation, status: 'TRY_AGAIN', feedback: 'Em kiểm tra phép cộng nhé.' })
    .mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Đếm tiếp từ nhóm đã có.' })
    .mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Đếm tiếp từ nhóm đã có.' });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  await act(async () => button('Gợi ý cách làm bước này').props.onPress());
  act(() => input('Câu trả lời của em').props.onChangeText('18'));
  await act(async () => button('Kiểm tra bước này').props.onPress());
  expect(readText()).toContain('Gộp hai nhóm, giữ cùng một đơn vị.');
  expect(readText()).toContain('Em kiểm tra phép cộng nhé.');
  await act(async () => button('Gợi ý rõ hơn').props.onPress());
  expect(readText()).toContain('Đếm tiếp từ nhóm đã có.');
  await act(async () => button('Gợi ý rõ hơn').props.onPress());
  expect(button('Đã mở đủ gợi ý bước này').props.disabled).toBe(true);
  act(() => button('Đã mở đủ gợi ý bước này').props.onPress());
  expect(TutorService.answerLesson).toHaveBeenCalledTimes(4);
  expect(input('Câu trả lời của em').props.value).toBe('18');
});

it('keeps guidance for reading choices free of instructions to calculate', async () => {
  const reading = { ...LESSON, understandingSteps: 3, step: { ...LESSON.step, kind: 'UNDERSTAND', guidance: ['Đọc lại đề.', 'Tìm câu hỏi.'] } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(reading);
  (TutorService.answerLesson as jest.Mock).mockResolvedValue({ ...reading, status: 'HINT', feedback: 'Tách điều đã biết với câu hỏi.' });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  expect(button('Xem ý tiếp theo')).toBeUndefined();
  expect(readText()).toContain(reading.step.question);
  expect(readText()).not.toContain('Em thử tự tính');
  await act(async () => button('Gợi ý cách làm bước này').props.onPress());
  expect(readText()).not.toContain('Ở bước hiểu đề, em cần làm gì?');
  act(() => button('Em muốn hiểu gợi ý rõ hơn').props.onPress());
  expect(readText()).toContain('Ở bước hiểu đề, em cần làm gì?');
});

it('allows a third distinct hint and clears old help only when the server advances', async () => {
  const calculation = { ...LESSON, step: { ...LESSON.step, choices: [], expression: '12+5' } };
  (TutorService.startLesson as jest.Mock).mockResolvedValue(calculation);
  (TutorService.answerLesson as jest.Mock)
    .mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Gộp hai nhóm.' })
    .mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Đếm tiếp từng chiếc bút.' })
    .mockResolvedValueOnce({ ...calculation, status: 'HINT', feedback: 'Viết phép cộng rồi kiểm tra số bút.' })
    .mockResolvedValueOnce({ ...calculation, revision: 1, stepIndex: 1, status: 'CORRECT', completed: [{ ...calculation.step, answer: '17' }] });
  await render(); await act(async () => button('Bắt đầu từng bước').props.onPress());
  await act(async () => button('Gợi ý cách làm bước này').props.onPress());
  await act(async () => button('Gợi ý rõ hơn').props.onPress());
  await act(async () => button('Gợi ý rõ hơn').props.onPress());
  expect(readText()).toContain('Viết phép cộng rồi kiểm tra số bút.');
  expect(button('Gợi ý rõ hơn').props.disabled).toBe(false);
  act(() => input('Câu trả lời của em').props.onChangeText('17'));
  await act(async () => button('Kiểm tra bước này').props.onPress());
  act(() => button('Tiếp tục bước tiếp theo').props.onPress());
  expect(readText()).not.toContain('Viết phép cộng rồi kiểm tra số bút.');
  expect(button('Gợi ý cách làm bước này')).toBeDefined();
});
