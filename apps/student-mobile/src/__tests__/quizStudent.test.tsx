import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthContext } from '../context/AuthContext';
import { QuizInvitation } from '../features/quiz/QuizInvitation';
import { QuizShortcut } from '../features/quiz/QuizShortcut';
import QuizScreen from '../app/quiz/[quizId]';
import { quizApi } from '../features/quiz/quizApi';
import { NarrationPreparation } from '../features/tutoring/NarrationPreparation';
import { QuizNarrationPreparation } from '../features/quiz/QuizVoice';

jest.setTimeout(30000);

const mockPush = jest.fn(), mockReplace = jest.fn();
jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush, replace: mockReplace }), useLocalSearchParams: () => ({ quizId: 'quiz-one' }),
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

it.each(['LESSON','WORK_REVIEW'] as const)('hides unavailable %s suggestions without a placeholder or failure card', async sourceType => {
  (quizApi.fromLearning as jest.Mock).mockRejectedValue({response:{data:{error:{code:'QUIZ_UNSUPPORTED',message:'No verified quiz'}}}});
  await act(async () => {view=TestRenderer.create(<QuizInvitation sourceType={sourceType} sourceId="no-quiz"/>);});
  expect(view.toJSON()).toBeNull();
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
