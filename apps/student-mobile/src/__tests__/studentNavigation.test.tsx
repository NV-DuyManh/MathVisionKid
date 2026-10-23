import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useRouter } from 'expo-router';
import SplashScreen from '../app/index';
import LessonsScreen from '../app/(tabs)/lessons';
import AchievementsScreen from '../app/(tabs)/achievements';
import ProfileScreen from '../app/(tabs)/profile';
import GamesScreen from '../app/games';
import { AuthContext } from '../context/AuthContext';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { recognitionAnalyticsStore } from '../features/recognition/analytics/recognitionAnalyticsStore';
import { getProblemsByGrade } from '../data/primaryMathCurriculum';

jest.mock('expo-router', () => ({
  useRouter: jest.fn(),
  Redirect: ({ href }: { href: string }) => require('react').createElement('Redirect', { href }),
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: 'SafeAreaView',
  useSafeAreaInsets: () => ({ top: 0, bottom: 20 }),
}));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../features/recognition/analytics/recognitionAnalyticsStore', () => ({
  recognitionAnalyticsStore: { init: jest.fn(async () => {}), getSessions: jest.fn(() => []) },
}));

const text = (renderer: TestRenderer.ReactTestRenderer) => renderer.root.findAllByType('Text' as any)
  .map(node => String(node.props.children)).join(' ');
const press = (renderer: TestRenderer.ReactTestRenderer, label: string) => renderer.root
  .findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0].props.onPress();

describe('Student navigation and real saved activity', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn(), replace: jest.fn(), dismissTo: jest.fn() });
    (recognitionAnalyticsStore.getSessions as jest.Mock).mockReturnValue([]);
    recognitionDraftStore.clearDraft();
  });

  it('waits for restored auth, then opens the right destination immediately', () => {
    const auth = { user: null, isAuthenticated: false, isLoading: true, login: jest.fn(), logout: jest.fn() };
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<AuthContext.Provider value={auth}><SplashScreen /></AuthContext.Provider>); });
    const router = (useRouter as jest.Mock).mock.results.at(-1)!.value;
    expect(router.replace).not.toHaveBeenCalled();
    act(() => renderer!.update(<AuthContext.Provider value={{ ...auth, isLoading: false, isAuthenticated: true }}><SplashScreen /></AuthContext.Provider>));
    expect(router.replace).toHaveBeenCalledWith('/(tabs)');
    act(() => renderer!.update(<AuthContext.Provider value={{ ...auth, isLoading: false }}><SplashScreen /></AuthContext.Provider>));
    expect(router.replace).toHaveBeenLastCalledWith('/login');
    act(() => renderer!.unmount());
  });

  it('selects a different grade, expands its real guidance and starts a clean learning capture', () => {
    recognitionDraftStore.setDraft({ uri: 'file:///old.png', rawUri: 'file:///old.png', width: 100, height: 100, filename: 'old.png', mimeType: 'image/png', mode: 'ARITHMETIC' });
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<LessonsScreen />); });
    act(() => press(renderer!, 'Chọn Lớp 5'));
    const problem = getProblemsByGrade(5)[0];
    expect(text(renderer!)).toContain(problem.title);
    expect(text(renderer!)).not.toContain(getProblemsByGrade(1)[0].title);
    act(() => press(renderer!, `Mở bài: ${problem.title}`));
    act(() => press(renderer!, `Xem gợi ý: ${problem.title}`));
    expect(text(renderer!)).toContain(problem.guidance);
    expect(text(renderer!)).not.toContain('Bài giải tham khảo');
    expect(text(renderer!)).not.toContain(problem.sampleSolution.finalAnswer);
    act(() => press(renderer!, `Học từng bước: ${problem.title}`));
    expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push)
      .toHaveBeenCalledWith({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } });
    act(() => press(renderer!, `Chụp lời giải: ${problem.title}`));
    expect(recognitionDraftStore.getDraft()).toBeNull();
    expect((useRouter as jest.Mock).mock.results.at(-1)!.value.push)
      .toHaveBeenCalledWith({ pathname: '/camera', params: { mode: 'MATH_TUTOR', problemText: problem.problemText } });
    act(() => renderer!.unmount());
  });

  it('shows only real saved activity, excluding samples, benchmarks and future records', async () => {
    (recognitionAnalyticsStore.getSessions as jest.Mock).mockReturnValue([
      { sessionId: 'saved-1', timestamp: Date.now() - 1000, confirmedLines: 3 },
      { sessionId: 'sample', timestamp: Date.now() - 1000, confirmedLines: 20, isSampleData: true },
      { sessionId: 'session_benchmark_1', timestamp: Date.now() - 1000, confirmedLines: 20 },
      { sessionId: 'future', timestamp: Date.now() + 86400000, confirmedLines: 20 },
    ]);
    let renderer: TestRenderer.ReactTestRenderer;
    await act(async () => { renderer = TestRenderer.create(<AchievementsScreen />); });
    expect(text(renderer!)).toContain('Ngày liên tiếp');
    expect(text(renderer!)).toContain('Em đã ghi lại 1 bài học.');
    const values = renderer!.root.findAllByType('Text' as any).map(node => node.props.children).flat();
    expect(values).toContain(1);
    expect(values).toContain(3);
    expect(values).not.toContain(20);
    act(() => renderer!.unmount());
  });

  it('opens games from the profile and returns to that tab with only a header on the games screen', async () => {
    const auth = { user: null, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
    let renderer: TestRenderer.ReactTestRenderer;
    await act(async () => {
      renderer = TestRenderer.create(<AuthContext.Provider value={auth}><ProfileScreen /></AuthContext.Provider>);
    });
    const router = (useRouter as jest.Mock).mock.results.at(-1)!.value;
    const gameEntries = renderer!.root.findAll(node =>
      node.props.accessibilityLabel === 'Trò chơi rèn luyện cho em' && typeof node.props.onPress === 'function');
    expect(gameEntries).toHaveLength(1);
    expect(gameEntries[0].props.accessibilityRole).toBe('button');
    act(() => press(renderer!, 'Trò chơi rèn luyện cho em'));
    expect(router.push).toHaveBeenCalledWith('/games');
    act(() => renderer!.update(<AuthContext.Provider value={auth}><GamesScreen /></AuthContext.Provider>));
    const screen = renderer!.toJSON() as TestRenderer.ReactTestRendererJSON;
    expect(screen.children).toHaveLength(1);
    act(() => press(renderer!, 'Quay lại tab Của em'));
    expect(router.dismissTo).toHaveBeenCalledWith('/(tabs)/profile');
    act(() => renderer!.unmount());
  });

  it('guards direct games entry while restoring auth, when signed out and when the session expires', () => {
    const auth = { user: null, isAuthenticated: false, isLoading: true, login: jest.fn(), logout: jest.fn() };
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => {
      renderer = TestRenderer.create(<AuthContext.Provider value={auth}><GamesScreen /></AuthContext.Provider>);
    });
    expect(renderer!.toJSON()).toBeNull();
    act(() => renderer!.update(<AuthContext.Provider value={{ ...auth, isLoading: false }}><GamesScreen /></AuthContext.Provider>));
    expect(renderer!.root.findByType('Redirect' as any).props.href).toBe('/login');
    act(() => renderer!.update(<AuthContext.Provider value={{ ...auth, isLoading: false, isAuthenticated: true }}><GamesScreen /></AuthContext.Provider>));
    expect(renderer!.root.findAllByType('Redirect' as any)).toHaveLength(0);
    act(() => renderer!.update(<AuthContext.Provider value={{ ...auth, isLoading: false }}><GamesScreen /></AuthContext.Provider>));
    expect(renderer!.root.findByType('Redirect' as any).props.href).toBe('/login');
    act(() => renderer!.update(<GamesScreen />));
    expect(renderer!.root.findByType('Redirect' as any).props.href).toBe('/login');
    act(() => renderer!.unmount());
  });
});
