import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo } from 'react-native';
import { AuthContext } from '../context/AuthContext';
import WelcomeScreen from '../app/welcome';
import { completeOnboarding } from '../features/onboarding/onboardingStorage';
import { loadLearningProgress } from '../features/tutoring/learningProgress';

const mockPush = jest.fn(), mockReplace = jest.fn();
jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush, replace: mockReplace }) }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../components/ui/AppIllustration', () => ({ AppIllustration: 'AppIllustration' }));
jest.mock('../features/onboarding/onboardingStorage', () => ({ completeOnboarding: jest.fn(async () => {}) }));
jest.mock('../features/tutoring/learningProgress', () => ({ loadLearningProgress: jest.fn(async () => null) }));
let view: TestRenderer.ReactTestRenderer;
const auth = { user: null, isAuthenticated: false, isLoading: false, login: jest.fn(), logout: jest.fn() };
const wrap = (value: React.ContextType<typeof AuthContext> = auth) => <AuthContext.Provider value={value}><WelcomeScreen /></AuthContext.Provider>;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
beforeEach(() => { jest.clearAllMocks(); jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true); });
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('waits for verified authentication and keeps intentional introduction reopening available', async () => {
  await act(async () => { view = TestRenderer.create(wrap({ ...auth, isLoading: true })); });
  expect(button('Bắt đầu')).toBeUndefined();
  expect(mockReplace).not.toHaveBeenCalled();
  await act(async () => view.update(wrap({ ...auth, isAuthenticated: true })));
  expect(button('Bỏ qua giới thiệu')).toBeDefined();
  await act(async () => button('Bỏ qua giới thiệu').props.onPress());
  expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
});

it('uses compact dots and swiping without arrows or redundant page text', async () => {
  await act(async () => { view = TestRenderer.create(wrap()); });
  expect(button('Trang giới thiệu trước')).toBeUndefined();
  expect(button('Trang giới thiệu tiếp theo')).toBeUndefined();
  expect(button('Tiếp tục học')).toBeDefined();
  const text = view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
  expect(text).not.toMatch(/Trang [123] trên 3/);
  act(() => button('Trang giới thiệu 3').props.onPress());
  expect(button('Trang giới thiệu 3').props['aria-selected']).toBe(true);
  const pager = view.root.findAll(node => node.props.testID === 'welcome-pager' && node.props.onMomentumScrollEnd)[0];
  const layout = view.root.findAll(node => typeof node.props.onLayout === 'function')[0];
  act(() => layout.props.onLayout({ nativeEvent: { layout: { width: 390 } } }));
  act(() => pager.props.onTouchStart());
  act(() => pager.props.onMomentumScrollEnd({ nativeEvent: { contentOffset: { x: 390 } } }));
  expect(button('Trang giới thiệu 2').props['aria-selected']).toBe(true);
});

it.each(['Bắt đầu', 'Bỏ qua giới thiệu', 'Tiếp tục học'])('persists completion and replaces the route once for %s', async label => {
  await act(async () => { view = TestRenderer.create(wrap()); });
  await act(async () => { button(label).props.onPress(); button(label).props.onPress(); });
  expect(completeOnboarding).toHaveBeenCalledTimes(1);
  expect(mockReplace.mock.calls).toEqual([['/login']]);
  expect(mockPush).not.toHaveBeenCalled();
  expect(loadLearningProgress).not.toHaveBeenCalled();
});

it('resumes only a valid draft belonging to the signed-in learner', async () => {
  const saved = { version: 1 as const, at: Date.now(), lessonId: 'draft-lesson', sessionId: 'draft-tutor-session-001',
    revision: 2, stepIndex: 2, problemText: 'Hỏi cả vườn có bao nhiêu cây?', workText: '', attempt: '' };
  jest.mocked(loadLearningProgress).mockResolvedValueOnce(saved);
  await act(async () => { view = TestRenderer.create(wrap({ ...auth, isAuthenticated: true, user: { id: 'own-student' } })); });
  await act(async () => button('Tiếp tục học').props.onPress());
  expect(loadLearningProgress).toHaveBeenCalledWith('own-student');
  expect(mockReplace).toHaveBeenCalledWith({ pathname: '/learning/math-guide', params: {
    problemText: saved.problemText, workText: saved.workText, lessonId: saved.lessonId,
  } });
});

it('opens Home when the signed-in learner has no draft', async () => {
  await act(async () => { view = TestRenderer.create(wrap({ ...auth, isAuthenticated: true, user: { id: 'own-student' } })); });
  await act(async () => button('Tiếp tục học').props.onPress());
  expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
});
