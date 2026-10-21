import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useRouter } from 'expo-router';
import ProfileScreen from '../app/(tabs)/profile';
import { AuthContext } from '../context/AuthContext';
import { loadLessons } from '../features/tutoring/learningHistory';

jest.mock('expo-router', () => ({ useRouter: jest.fn(), useFocusEffect: (fn: () => void) => require('react').useEffect(fn, [fn]) }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: require('react-native').View }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../features/tutoring/learningHistory', () => ({ loadLessons: jest.fn() }));
const saved = [
  { id: 'first', timestamp: Date.now() - 1000, problemText: 'Bài cộng số bút', workText: '36 + 27 = 63', reflection: '', reviewedSteps: 2 },
  { id: 'second', timestamp: Date.now() - 2000, problemText: 'Bài phân số', workText: '', reflection: 'Các phần bằng nhau', reviewedSteps: 1 },
];
let view: TestRenderer.ReactTestRenderer;
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const press = async (label: string) => { await act(async () => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0].props.onPress()); };
const screen = (id: string) => <AuthContext.Provider value={{ user: { id }, isLoading: false, isAuthenticated: true, login: jest.fn(), logout: jest.fn() }}><ProfileScreen /></AuthContext.Provider>;
beforeEach(() => { jest.clearAllMocks(); (useRouter as jest.Mock).mockReturnValue({ push: jest.fn(), replace: jest.fn() }); (loadLessons as jest.Mock).mockResolvedValue(saved); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('filters real saved work and notes, and opens the selected lesson from its menu', async () => {
  await act(async () => { view = TestRenderer.create(screen('pupil-a')); });
  expect(text()).toContain('Bài cộng số bút'); expect(text()).toContain('Bài phân số');
  await press('Bài làm'); expect(text()).toContain('Bài cộng số bút'); expect(text()).not.toContain('Bài phân số');
  await press('Ghi chú'); expect(text()).not.toContain('Bài cộng số bút'); expect(text()).toContain('Các phần bằng nhau');
  await press('Tùy chọn bài 1'); await press('Mở bài học');
  expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push).toHaveBeenCalledWith({ pathname: '/learning/math-guide', params: {
    problemText: saved[1].problemText, workText: '', lessonId: 'second', reflection: saved[1].reflection,
  } });
});

it('clears the old account list and open menu, and ignores its late history response', async () => {
  let resolve!: (value: unknown) => void;
  (loadLessons as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; })).mockResolvedValueOnce([]);
  await act(async () => { view = TestRenderer.create(screen('pupil-a')); });
  await act(async () => view.update(screen('pupil-b')));
  await act(async () => resolve(saved));
  expect(text()).not.toContain('Bài cộng số bút'); expect(text()).toContain('Bài học hay, mình giữ lại nhé!');
  expect(loadLessons).toHaveBeenLastCalledWith('pupil-b');
});
