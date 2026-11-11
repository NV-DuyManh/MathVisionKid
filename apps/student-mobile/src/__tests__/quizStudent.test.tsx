import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthContext } from '../context/AuthContext';
import { QuizAfterLearningButton, QuizInvitation } from '../features/quiz/QuizInvitation';
import { QuizShortcut } from '../features/quiz/QuizShortcut';
import QuizScreen from '../app/quiz/[quizId]';
import QuizFromLearningScreen from '../app/quiz/from-learning';
import { quizApi } from '../features/quiz/quizApi';
import { NarrationPreparation } from '../features/tutoring/NarrationPreparation';
import { QuizNarrationPreparation } from '../features/quiz/QuizVoice';

jest.setTimeout(30000);

const mockPush = jest.fn(), mockReplace = jest.fn();
const mockParams = { quizId: 'quiz-one', sourceType: 'LESSON', sourceId: 'lesson-purchase' };
jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush, replace: mockReplace }), useLocalSearchParams: () => mockParams,
  useFocusEffect: (fn: () => (() => void)) => require('react').useEffect(fn, [fn]) }));
jest.mock('../features/quiz/QuizHelp', () => ({ QuizHelp: 'QuizHelp' }));
jest.mock('../features/quiz/QuizVoice', () => ({ QuizVoice: 'QuizVoice', QuizNarrationPreparation: ({children}: any) => children }));
jest.mock('../features/quiz/quizApi', () => ({ ...jest.requireActual('../features/quiz/quizApi'), quizApi: {
  fromLearning: jest.fn(), defer: jest.fn(), count: jest.fn(), get: jest.fn(), start: jest.fn(), submit: jest.fn(), reveal: jest.fn(), replay: jest.fn(), activity: jest.fn(),
} }));
const ready: any = { quizId: 'quiz-one', topicName: 'Tìm tổng khi biết phần còn lại', gradeLevel: 4, status: 'READY', unit: 'quyển sách',
  answerFormat: 'INTEGER', questionText: 'Câu đố đã sẵn sàng.', attempts: [], elapsedMillis: 0, stars: 0, wrongAttempts: 0, startedAt: '2026-10-31T10:00:00Z' };
let view: TestRenderer.ReactTestRenderer;
const wrapper = (node: React.ReactNode, id = 'student-a') => <AuthContext.Provider value={{ user: { id, role: 'STUDENT' } } as any}>{node}</AuthContext.Provider>;
const button = (name: string) => view.root.findAll(n => n.props.accessibilityLabel === name && n.props.onPress)[0];
const text = () => view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
beforeEach(() => {
  jest.clearAllMocks(); (quizApi.count as jest.Mock).mockResolvedValue({ pendingCount: 2, totalStars: 0 });
  (quizApi.get as jest.Mock).mockResolvedValue(ready);
  (quizApi.activity as jest.Mock).mockImplementation(async (_id, run, active) => ({ ...ready, status:'IN_PROGRESS', startedAt:run, elapsedMillis:15000, timerRunning:active }));
  (quizApi.fromLearning as jest.Mock).mockResolvedValue({ offered: true, quiz: ready });
});
afterEach(() => { if (view) act(() => view.unmount()); });
it('submits the selected ordinal for a verified sequence rather than parsing the sequence as a number', async () => {
  const sequence = { ...ready, status: 'IN_PROGRESS', answerFormat: 'CHOICE', unit: '',
    questionText: 'Chọn dãy tăng dần.\nA. 1,25; 0,98; 3,56\nB. 0,98; 1,25; 3,56' };
  (quizApi.get as jest.Mock).mockResolvedValue(sequence);
  (quizApi.submit as jest.Mock).mockResolvedValue({ quiz: { ...sequence, wrongAttempts: 1 }, attempt: { correct: false } });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  act(() => button('B. 0,98; 1,25; 3,56').props.onPress());
  await act(async () => button('Hoàn thành').props.onPress());
  expect(quizApi.submit).toHaveBeenCalledWith('quiz-one', expect.any(String), '2', expect.any(AbortSignal));
  expect(button('B. 0,98; 1,25; 3,56').props.accessibilityState.checked).toBe(true);
  act(() => button('A. 1,25; 0,98; 3,56').props.onPress());
  expect(button('A. 1,25; 0,98; 3,56').props.accessibilityState.checked).toBe(true);
});
it('offers a Quiz from the completed review source and sends only its server reference', async () => {
  await act(async () => { view = TestRenderer.create(<QuizInvitation sourceType="WORK_REVIEW" sourceId="review-source" />); });
  expect(quizApi.fromLearning).toHaveBeenCalledWith('WORK_REVIEW', 'review-source', expect.any(AbortSignal));
  expect(button('Làm ngay')).toBeDefined();
  (quizApi.defer as jest.Mock).mockResolvedValue({ ...ready, status: 'DEFERRED' });
  await act(async () => button('Để khi khác').props.onPress());
  expect(quizApi.defer).toHaveBeenCalledWith('quiz-one', expect.any(AbortSignal));
  expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
});
it('does not repeat a persisted invitation or pretend unsupported generation succeeded', async () => {
  (quizApi.fromLearning as jest.Mock).mockResolvedValue({ offered: false, quiz: ready });
  await act(async () => { view = TestRenderer.create(<QuizInvitation sourceType="LESSON" sourceId="lesson-one" />); });
  expect(quizApi.fromLearning).toHaveBeenCalledWith('LESSON', 'lesson-one', expect.any(AbortSignal));
  expect(button('Làm ngay')).toBeUndefined();
  expect(button('Làm Quiz')).toBeDefined();
  expect(button('Để khi khác')).toBeDefined();
});
it('invitation adapts to in-progress and completed quiz states', async () => {
  (quizApi.fromLearning as jest.Mock).mockResolvedValue({ offered: false, quiz: { ...ready, status: 'IN_PROGRESS' } });
  await act(async () => { view = TestRenderer.create(<QuizInvitation sourceType="LESSON" sourceId="lesson-two" />); });
  expect(button('Tiếp tục làm')).toBeDefined();
  expect(button('Để khi khác')).toBeDefined();

  (quizApi.fromLearning as jest.Mock).mockResolvedValue({ offered: false, quiz: { ...ready, status: 'COMPLETED', stars: 2 } });
  await act(async () => { view = TestRenderer.create(<QuizInvitation sourceType="LESSON" sourceId="lesson-three" />); });
  expect(button('Làm lại')).toBeDefined();
  expect(button('Xem kết quả')).toBeDefined();
});
it('badge comes from the server and immediately clears old-account data on account change', async () => {
  await act(async () => { view = TestRenderer.create(wrapper(<QuizShortcut />)); });
  expect(button('Câu đố của em, 2 câu chưa hoàn thành')).toBeDefined();
  let resolve: (value: any) => void = () => {};
  (quizApi.count as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => view.update(wrapper(<QuizShortcut />, 'student-b')));
  expect(button('Câu đố của em, 2 câu chưa hoàn thành')).toBeUndefined();
  await act(async () => resolve({ pendingCount: 0, totalStars: 0 }));
  expect(button('Câu đố của em')).toBeDefined();
});
it('keeps the solution locked, prevents double submit and reuses the same request key after network ambiguity', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'IN_PROGRESS', questionText: 'Đề mới đã xác minh.' });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(button('Cách giải')).toBeUndefined();
  const input = view.root.findAll(n => n.props.onChangeText && n.props.accessibilityLabel === 'Đáp án của em, quyển sách')[0];
  act(() => input.props.onChangeText('48'));
  let reject: (error: Error) => void = () => {};
  (quizApi.submit as jest.Mock).mockImplementation(() => new Promise((_, fail) => { reject = fail; }));
  act(() => { button('Hoàn thành').props.onPress(); button('Hoàn thành').props.onPress(); });
  expect(quizApi.submit).toHaveBeenCalledTimes(1);
  const key = (quizApi.submit as jest.Mock).mock.calls[0][1];
  await act(async () => reject(new Error('network')));
  (quizApi.submit as jest.Mock).mockResolvedValue({ quiz: { ...ready, status: 'IN_PROGRESS', wrongAttempts: 1 }, attempt: { correct: false } });
  await act(async () => button('Hoàn thành').props.onPress());
  expect((quizApi.submit as jest.Mock).mock.calls[1][1]).toBe(key);
  expect(text()).toContain('Chưa đúng rồi'); expect(button('Cách giải')).toBeUndefined();
});
it('shows solution only after the backend reveal and makes a completed Quiz read only', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'IN_PROGRESS', wrongAttempts: 2, canRevealSolution: true });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(text()).not.toContain('Đáp án đã công bố');
  (quizApi.reveal as jest.Mock).mockResolvedValue({ ...ready, status: 'IN_PROGRESS', wrongAttempts: 2, solutionViewed: true, explanationText: 'Đáp án đã công bố' });
  act(() => button('Xem thêm').props.onPress());
  await act(async () => button('Xem cách giải').props.onPress());
  expect(text()).toContain('Đáp án đã công bố');
  act(() => view.unmount());
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', stars: 0, completedWithSolution: true, explanationText: 'Đáp án đã công bố' });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(button('Hoàn thành')).toBeUndefined(); expect(button('Về trang chủ')).toBeDefined();
});
it('uses the latest completed state when retrying an old wrong attempt after another device completed the Quiz', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'IN_PROGRESS' });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  const input = view.root.findAll(n => n.props.onChangeText && n.props.accessibilityLabel === 'Đáp án của em, quyển sách')[0];
  act(() => input.props.onChangeText('999'));
  (quizApi.submit as jest.Mock).mockResolvedValue({ quiz: { ...ready, status: 'COMPLETED', stars: 3 }, attempt: { correct: false } });
  await act(async () => button('Hoàn thành').props.onPress());
  expect(button('Về trang chủ')).toBeDefined();
  expect(text()).not.toContain('Chưa đúng rồi');
  expect(button('Hoàn thành')).toBeUndefined();
});

it('explains zero stars for practice while preserving the all-time record', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', replayMode: 'PRACTICE', stars: 3,
    attempts: [{ number: 1, correct: true, stars: 3 }, { number: 2, correct: true, stars: 0, mode: 'PRACTICE' }] });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(text()).toContain('Em đã ôn lại bài cũ. Thành tích của em được giữ nguyên.');
  expect(view.root.findAll(n => n.props.accessibilityLabel === '0 sao')).toHaveLength(0);
  expect(text()).not.toContain('Em nhận được 3 sao');
});
it('shows the current two-star result separately from the three-star record', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', replayMode: 'CHALLENGE', stars: 3,
    attempts: [{ number: 1, correct: true, stars: 3 }, { number: 2, correct: true, stars: 2 }] });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(text()).toContain('Lượt này: 2 sao · Kỷ lục: 3 sao');
});
it('shows exactly one assisted star even when an earlier record is three stars', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', stars: 3, completedWithSolution: true,
    attempts: [{ number: 1, correct: true, stars: 3 }, { number: 2, correct: true, stars: 1, solutionViewed: true }] });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  expect(text()).toContain('Lượt này: 1 sao · Kỷ lục: 3 sao');
  expect(view.root.findAll(n => n.props.accessibilityLabel === '1 sao').length).toBeGreaterThan(0);
});

it('uses a monotonic display clock and does not jump when the phone clock changes', async () => {
  jest.useFakeTimers();
  try {
    (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'IN_PROGRESS', elapsedMillis: 15000 });
    await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
    act(() => jest.advanceTimersByTime(1000));
    expect(text()).toContain('0:16');
    jest.setSystemTime(Date.now() + 48 * 60 * 60 * 1000);
    act(() => jest.advanceTimersByTime(1000));
    expect(text()).toContain('0:17');
    expect(text()).not.toContain('2407:');
  } finally { jest.useRealTimers(); }
});

it('keeps the reported long completed duration truthful and frozen with explicit hours', async () => {
  jest.useFakeTimers();
  try {
    (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', stars: 1, elapsedMillis: 144472719 });
    await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
    expect(text()).toContain('40:07:52');
    act(() => jest.advanceTimersByTime(60000));
    expect(text()).toContain('40:07:52');
    expect(view.root.findAll(n=>n.props.accessibilityLabel === 'Thời gian làm bài 40:07:52').length).toBeGreaterThan(0);
  } finally { jest.useRealTimers(); }
});

it('opens a separate Quiz page and retries a transient connection error', async () => {
  (quizApi.fromLearning as jest.Mock)
    .mockRejectedValueOnce(new Error('Connection interrupted'))
    .mockResolvedValueOnce({ offered: true, quiz: ready });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizFromLearningScreen />)); });
  expect(text()).toContain('Quiz sau bài học');
  expect(button('Về trang chủ')).toBeDefined();
  expect(button('Làm ngay')).toBeUndefined();
  await act(async () => button('Thử lại Quiz').props.onPress());
  expect(quizApi.fromLearning).toHaveBeenLastCalledWith('LESSON', 'lesson-purchase', expect.any(AbortSignal));
  expect(text()).toContain('cùng dạng toán');
  act(() => button('Làm ngay').props.onPress());
  expect(mockPush).toHaveBeenCalledWith('/quiz/quiz-one');
});
it('explains that an unsupported lesson has no verified Quiz of the same type', async () => {
  (quizApi.fromLearning as jest.Mock).mockRejectedValue({ response: { data: { error: {
    code: 'QUIZ_UNSUPPORTED', message: 'Sao chưa có câu luyện tập cùng dạng đã kiểm tra cho bài này.',
  } } } });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizFromLearningScreen />)); });
  expect(text()).toContain('Chưa có Quiz cùng dạng');
  expect(button('Thử lại Quiz')).toBeUndefined();
  expect(button('Làm ngay')).toBeUndefined();
});
it('does not offer a Quiz when the server says no verified Quiz is available', async () => {
  (quizApi.fromLearning as jest.Mock).mockRejectedValue({ response: { data: { error: { code: 'QUIZ_UNSUPPORTED' } } } });
  await act(async () => { view = TestRenderer.create(<QuizAfterLearningButton sourceType="LESSON" sourceId="lesson-purchase" />); });
  expect(quizApi.fromLearning).toHaveBeenCalledWith('LESSON', 'lesson-purchase', expect.any(AbortSignal));
  expect(button('Thử sức với Quiz')).toBeUndefined();
  expect(button('Thử lại Quiz')).toBeUndefined();
  expect(mockPush).not.toHaveBeenCalled();
});
it('waits for a verified Quiz and opens its existing page without generating it again', async () => {
  let resolve: (value: any) => void = () => {};
  (quizApi.fromLearning as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(wrapper(<QuizAfterLearningButton sourceType="LESSON" sourceId="lesson-purchase" />)); });
  expect(text()).toContain('Đang chuẩn bị Quiz…');
  expect(button('Thử sức với Quiz')).toBeUndefined();
  expect(mockPush).not.toHaveBeenCalled();
  await act(async () => resolve({ offered: true, quiz: ready }));
  expect(text()).not.toContain('Đang chuẩn bị Quiz…');
  act(() => button('Thử sức với Quiz').props.onPress());
  expect(mockPush).toHaveBeenCalledWith('/quiz/quiz-one');
  expect(quizApi.fromLearning).toHaveBeenCalledTimes(1);
});
it('recovers a connection failure on the lesson page before offering navigation', async () => {
  (quizApi.fromLearning as jest.Mock).mockRejectedValueOnce(new Error('Connection interrupted'))
    .mockResolvedValueOnce({ offered: true, quiz: ready });
  await act(async () => { view = TestRenderer.create(<QuizAfterLearningButton sourceType="WORK_REVIEW" sourceId="review-source" />); });
  expect(button('Thử sức với Quiz')).toBeUndefined();
  expect(text()).toContain('Bài học của em đã hoàn thành.');
  await act(async () => button('Thử lại Quiz').props.onPress());
  act(() => button('Thử sức với Quiz').props.onPress());
  expect(mockPush).toHaveBeenCalledWith('/quiz/quiz-one');
});
it.each([
  ['IN_PROGRESS', '', 'Tiếp tục Quiz'],
  ['COMPLETED', '', 'Xem kết quả Quiz'],
  ['READY', 'CHECKED_SOURCE_REVIEW', 'Ôn lại bài vừa học'],
])('describes the available %s Quiz truthfully', async (status, topicCode, label) => {
  (quizApi.fromLearning as jest.Mock).mockResolvedValue({ offered: false, quiz: { ...ready, status, topicCode } });
  await act(async () => { view = TestRenderer.create(<QuizAfterLearningButton sourceType="LESSON" sourceId="lesson-purchase" />); });
  expect(button(label)).toBeDefined();
  expect(button('Thử sức với Quiz')).toBeUndefined();
});
it('discards late readiness and old Quiz ids when the source or account changes', async () => {
  let finishOld: (value: any) => void = () => {};
  (quizApi.fromLearning as jest.Mock).mockImplementationOnce(() => new Promise(done => { finishOld = done; }));
  await act(async () => { view = TestRenderer.create(wrapper(<QuizAfterLearningButton sourceType="LESSON" sourceId="old-source" />)); });
  const oldSignal = (quizApi.fromLearning as jest.Mock).mock.calls[0][2];
  (quizApi.fromLearning as jest.Mock).mockRejectedValue({ response: { data: { error: { code: 'QUIZ_UNSUPPORTED' } } } });
  await act(async () => view.update(wrapper(<QuizAfterLearningButton sourceType="LESSON" sourceId="new-source" />,'student-b')));
  expect(oldSignal.aborted).toBe(true);
  await act(async () => finishOld({ offered: true, quiz: ready }));
  expect(button('Thử sức với Quiz')).toBeUndefined();
  expect(mockPush).not.toHaveBeenCalled();
});
it.each([
  ['UNIT_PRICE_FIND_CASH', 'đồng', 'Long đang có bao nhiêu tiền?\nA. 48 000 đồng\nB. 66 000 đồng\nC. 81 000 đồng\nD. 96 000 đồng', 'B. 66 000 đồng', '66000'],
  ['FRACTION_FIND_CLASS_COMPLEMENT', 'học sinh', 'Lớp có bao nhiêu học sinh nam?\nA. 15 học sinh\nB. 18 học sinh\nC. 27 học sinh\nD. 20 học sinh', 'B. 18 học sinh', '18'],
  ['CHECKED_LESSON_VARIANT', '', 'Tính phân số\nA. 3/2\nB. 5/2\nC. 7/2\nD. 9/2', 'B. 5/2', '5/2'],
])('submits the selected answer from %s for server grading', async (topicCode, unit, questionText, selectedLabel, value) => {
  const quiz = { ...ready, topicCode, status: 'IN_PROGRESS', unit, questionText };
  (quizApi.get as jest.Mock).mockResolvedValue(quiz);
  (quizApi.activity as jest.Mock).mockResolvedValue(quiz);
  (quizApi.submit as jest.Mock).mockResolvedValue({ quiz: { ...quiz, wrongAttempts: 1 }, attempt: { correct: false } });
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  act(() => button(selectedLabel).props.onPress());
  expect(button(selectedLabel).props.accessibilityState.checked).toBe(true);
  expect(quizApi.submit).not.toHaveBeenCalled();
  await act(async () => button('Hoàn thành').props.onPress());
  expect(quizApi.submit).toHaveBeenCalledWith('quiz-one', expect.any(String), value, expect.any(AbortSignal));
  expect(button(selectedLabel).props.accessibilityState.checked).toBe(true);
});
it('keeps one work area and opens audio/questions in the same sheets as lessons', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({...ready,status:'IN_PROGRESS'});
  await act(async()=>{view=TestRenderer.create(wrapper(<QuizScreen/>));});
  expect(view.root.findAllByType('QuizVoice' as any)).toHaveLength(0);
  act(()=>button('Nghe giảng').props.onPress());
  expect(view.root.findByType('QuizVoice' as any).props.content).toBe('QUESTION');
  expect(view.root.findByType('QuizVoice' as any).props.paragraphs).toEqual([ready.questionText]);
  act(()=>button('Đóng Nghe giảng').props.onPress());
  act(()=>button('Hỏi bài').props.onPress());
  expect(view.root.findByType('QuizHelp' as any)).toBeDefined();
  const replyPreparation=view.root.findByType(NarrationPreparation);
  expect(replyPreparation.props.owner).toBe('student-a');
  expect(replyPreparation.props.download).toBeUndefined(); // Replies use the tutor endpoint, never the Quiz script loader.
});

it('does not prefetch the placeholder or an unopened Quiz question',async()=>{
  (quizApi.get as jest.Mock).mockResolvedValue({...ready,startedAt:null});
  await act(async()=>{view=TestRenderer.create(wrapper(<QuizScreen/>));});
  expect(view.root.findByType(QuizNarrationPreparation).props.paragraphs).toEqual([]);
});

it('acknowledges challenge preparation immediately, preserves the result and keeps safe tools usable', async () => {
  const completed = { ...ready, status: 'COMPLETED', stars: 3, explanationText: 'Cách giải bài cũ.' };
  (quizApi.get as jest.Mock).mockResolvedValue(completed);
  let resolve!: (value: any) => void;
  (quizApi.replay as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  act(() => { button('Thử thách nâng sao').props.onPress(); button('Thử thách nâng sao').props.onPress(); });
  expect(quizApi.replay).toHaveBeenCalledTimes(1);
  expect(text()).toContain('Đang chuẩn bị câu mới…');
  expect(text()).toContain('Sao đang tạo câu mới cùng dạng');
  expect(text()).toContain('Em đã hoàn thành rồi!');
  expect(button('Thử thách nâng sao').props.accessibilityState.busy).toBe(true);
  expect(button('Về trang chủ').props.accessibilityState.busy).toBe(false);
  act(() => button('Nghe giảng').props.onPress());
  expect(view.root.findByType('QuizVoice' as any).props.paragraphs).toEqual(['Cách giải bài cũ.']);
  act(() => button('Đóng Nghe giảng').props.onPress());
  act(() => button('Hỏi bài').props.onPress());
  // Read-only tools work; a second mutation cannot target a run being replaced.
  expect(view.root.findAllByType('QuizHelp' as any)).toHaveLength(0);
  expect(text()).toContain('Sao đang hoàn tất thao tác vừa rồi');
  await act(async () => resolve({ ...ready, status: 'IN_PROGRESS', questionText: 'Câu mới đã kiểm tra.' }));
  expect(text()).toContain('Câu mới đã kiểm tra.');
  expect(text()).not.toContain('Sao đang tạo câu mới cùng dạng');
  expect(view.root.findAllByType('QuizHelp' as any)).toHaveLength(0);
  expect(button('Hoàn thành')).toBeDefined();
});

it('clears the preparation indicator on failure and aborts a late replay when leaving', async () => {
  (quizApi.get as jest.Mock).mockResolvedValue({ ...ready, status: 'COMPLETED', stars: 3 });
  (quizApi.replay as jest.Mock).mockRejectedValueOnce(new Error('network'));
  await act(async () => { view = TestRenderer.create(wrapper(<QuizScreen />)); });
  await act(async () => button('Thử thách nâng sao').props.onPress());
  expect(button('Thử thách nâng sao').props.accessibilityState.busy).toBe(false);
  expect(text()).toContain('Em đã hoàn thành rồi!');
  let resolve!: (value: any) => void;
  (quizApi.replay as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  act(() => button('Thử thách nâng sao').props.onPress());
  const signal = (quizApi.replay as jest.Mock).mock.calls[1][2];
  act(() => view.unmount());
  expect(signal.aborted).toBe(true);
  await act(async () => resolve({ ...ready, status: 'IN_PROGRESS' }));
  expect(mockReplace).not.toHaveBeenCalled();
});
