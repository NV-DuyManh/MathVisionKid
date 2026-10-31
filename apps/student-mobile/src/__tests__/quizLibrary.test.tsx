import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthContext } from '../context/AuthContext';
import QuizLibraryScreen from '../app/quiz';
import LessonsScreen from '../app/(tabs)/lessons';
import { quizApi } from '../features/quiz/quizApi';

const mockPush = jest.fn(), mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useFocusEffect: (callback: () => (() => void)) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView', useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) }));
jest.mock('../features/quiz/quizApi', () => ({
  ...jest.requireActual('../features/quiz/quizApi'), quizApi: { list: jest.fn(), count: jest.fn() },
}));

const empty = { items: [], page: 0, totalPages: 0, totalElements: 0 };
const question = { quizId: 'quiz-one', topicName: 'Tìm số còn lại', questionText: 'Có 3/5 số cây là cây táo. Còn lại bao nhiêu cây?', status: 'READY', stars: 0 };
const page = { items: [question], page: 0, totalPages: 1, totalElements: 1 };
let view: TestRenderer.ReactTestRenderer;
const wrapper = (node: React.ReactNode, id = 'student-a') => <AuthContext.Provider value={{ user: { id, role: 'STUDENT' } } as any}>{node}</AuthContext.Provider>;
const button = (name: string) => view.root.findAll(node => node.props.accessibilityLabel === name && node.props.onPress)[0];
const visibleText = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const deferred = () => {
  let resolve!: (value: any) => void;
  const promise = new Promise<any>(done => { resolve = done; });
  return { promise, resolve };
};
beforeEach(() => {
  jest.resetAllMocks();
  (quizApi.count as jest.Mock).mockResolvedValue({ pendingCount: 0, totalStars: 0 });
  (quizApi.list as jest.Mock).mockResolvedValue(empty);
});
afterEach(() => { if (view) act(() => view.unmount()); });

it('opens the compact entry from Lessons and does not start a quiz when browsing the library', async () => {
  await act(async () => { view = TestRenderer.create(wrapper(<LessonsScreen />)); });
  act(() => button('Câu đố của em').props.onPress());
  expect(mockPush).toHaveBeenCalledWith('/quiz');
  await act(async () => view.update(wrapper(<QuizLibraryScreen />)));
  expect(quizApi.list).toHaveBeenCalledWith('PENDING', 0, expect.any(AbortSignal));
  expect(visibleText()).toContain('Chưa có câu đố mới');
  act(() => button('Chọn bài để học').props.onPress());
  expect(mockReplace).toHaveBeenCalledWith('/(tabs)/lessons');
});

it.each(['list-first', 'count-first'])('opens unfinished work on initial entry when only in-progress items remain (%s)', async order => {
  const pending = deferred(), count = deferred();
  (quizApi.list as jest.Mock).mockImplementation(group => group === 'PENDING' ? pending.promise : Promise.resolve({ ...page, items: [{ ...question, status: 'IN_PROGRESS' }] }));
  (quizApi.count as jest.Mock).mockReturnValue(count.promise);
  await act(async () => { view = TestRenderer.create(wrapper(<QuizLibraryScreen />)); });
  await act(async () => order === 'list-first' ? pending.resolve(empty) : count.resolve({ pendingCount: 1, totalStars: 0 }));
  expect(quizApi.list).toHaveBeenCalledTimes(1);
  await act(async () => order === 'list-first' ? count.resolve({ pendingCount: 1, totalStars: 0 }) : pending.resolve(empty));
  expect(button('Đang làm').props.accessibilityState.selected).toBe(true);
  expect(quizApi.list).toHaveBeenCalledWith('IN_PROGRESS', 0, expect.any(AbortSignal));
  act(() => button('Chờ làm').props.onPress());
  await act(async () => {});
  expect(button('Chờ làm').props.accessibilityState.selected).toBe(true);
});

it('keeps an explicit filter selection when a delayed count arrives', async () => {
  const count = deferred();
  (quizApi.count as jest.Mock).mockReturnValue(count.promise);
  await act(async () => { view = TestRenderer.create(wrapper(<QuizLibraryScreen />)); });
  act(() => button('Chờ làm').props.onPress());
  await act(async () => count.resolve({ pendingCount: 1, totalStars: 0 }));
  expect(button('Chờ làm').props.accessibilityState.selected).toBe(true);
  expect(quizApi.list).toHaveBeenCalledTimes(1);
});

it('renders ready questions before a slow count, displays fractions, and opens only the selected question', async () => {
  (quizApi.count as jest.Mock).mockReturnValue(new Promise(() => {}));
  (quizApi.list as jest.Mock).mockImplementation(group => Promise.resolve(group === 'IN_PROGRESS' ? { ...page, items: [{ ...question, status: 'IN_PROGRESS' }] } : empty));
  await act(async () => { view = TestRenderer.create(wrapper(<QuizLibraryScreen />)); });
  await act(async () => button('Đang làm').props.onPress());
  expect(view.root.findAll(node => node.props.testID === 'stacked-fraction' && node.type === 'View')).toHaveLength(1);
  const open = view.root.findAll(node => node.props.accessibilityLabel?.startsWith('Tìm số còn lại.') && node.props.onPress)[0];
  act(() => open.props.onPress());
  expect(mockPush).toHaveBeenCalledWith('/quiz/quiz-one');
});

it('aborts the old account request and never displays its late result', async () => {
  const old = deferred(), next = deferred();
  (quizApi.list as jest.Mock).mockReturnValueOnce(old.promise).mockReturnValue(next.promise);
  await act(async () => { view = TestRenderer.create(wrapper(<QuizLibraryScreen />)); });
  const oldSignal = (quizApi.list as jest.Mock).mock.calls[0][2] as AbortSignal;
  await act(async () => view.update(wrapper(<QuizLibraryScreen />, 'student-b')));
  expect(oldSignal.aborted).toBe(true);
  await act(async () => old.resolve(page));
  expect(visibleText()).not.toContain(question.topicName);
  await act(async () => next.resolve(empty));
  expect(visibleText()).toContain('Chưa có câu đố mới');
});

it('lets a learner retry a failed library request and expand help without starting a quiz', async () => {
  (quizApi.list as jest.Mock).mockRejectedValueOnce(new Error('offline')).mockResolvedValue(empty);
  await act(async () => { view = TestRenderer.create(wrapper(<QuizLibraryScreen />)); });
  expect(button('Thử lại')).toBeDefined();
  await act(async () => button('Thử lại').props.onPress());
  expect(button('Thử lại')).toBeUndefined();
  expect(visibleText()).toContain('Chưa có câu đố mới');
  act(() => button('Câu đố hoạt động thế nào?').props.onPress());
  expect(button('Câu đố hoạt động thế nào?').props.accessibilityState.expanded).toBe(true);
  expect(visibleText()).toContain('Chỉ những dạng bài được hỗ trợ');
  expect(mockPush).not.toHaveBeenCalled();
});
