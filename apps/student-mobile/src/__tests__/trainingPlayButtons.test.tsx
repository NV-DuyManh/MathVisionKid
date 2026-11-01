import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { ScrollView, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import GamesScreen from '../app/games';
import { AuthContext } from '../context/AuthContext';
import { TRAINING_CATALOG } from '../features/training-games/catalog';

jest.mock('expo-router', () => ({
  useRouter: jest.fn(), Redirect: 'Redirect',
  useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));

const UUID = '11111111-1111-4111-8111-111111111111';
const auth = { user: { userId: UUID, role: 'STUDENT' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
const push = jest.fn(), dismissTo = jest.fn();
let tree: TestRenderer.ReactTestRenderer;
const update = async (value: React.ComponentProps<typeof AuthContext.Provider>['value']) => {
  await act(async () => {
    const element = <AuthContext.Provider value={value}><GamesScreen /></AuthContext.Provider>;
    if (tree) tree.update(element); else tree = TestRenderer.create(element);
  });
};
const button = (id: string) => tree.root.findAll(node => node.props.testID === `training-play-${id}` && typeof node.props.onPress === 'function')[0];
const text = () => JSON.stringify(tree.toJSON());
beforeEach(() => { jest.clearAllMocks(); jest.mocked(useRouter).mockReturnValue({ push, dismissTo } as ReturnType<typeof useRouter>); });
afterEach(() => { if (tree) act(() => tree.unmount()); tree = undefined as unknown as TestRenderer.ReactTestRenderer; });

test.each(TRAINING_CATALOG)('authenticated UUID: touching $id navigates to its allowlisted route', async game => {
  await update(auth);
  const play = button(game.id);
  expect(play.props.disabled).toBe(false);
  expect(play.props.accessibilityState.disabled).toBe(false);
  act(() => play.props.onPress());
  expect(push).toHaveBeenCalledTimes(1);
  expect(push).toHaveBeenCalledWith({ pathname: '/games/[gameId]', params: { gameId: game.id } });
});

test('auth loading does not expose controls; finishing restore enables the real student buttons', async () => {
  await update({ ...auth, isLoading: true }); expect(tree.toJSON()).toBeNull(); expect(push).not.toHaveBeenCalled();
  await update(auth); expect(button('planet-rescue').props.disabled).toBe(false);
  act(() => button('planet-rescue').props.onPress()); expect(push).toHaveBeenCalledTimes(1);
});

test('invalid profile gives an explicit reason and a truthful blocked button label', async () => {
  await update({ ...auth, user: { role: 'STUDENT', userId: 'missing-uuid' } });
  expect(text()).toContain('Vui lòng đăng nhập bằng tài khoản học sinh để lưu kết quả.');
  expect(text()).not.toContain('Chơi ngay');
  for (const game of TRAINING_CATALOG) expect(button(game.id).props.disabled).toBe(true);
  expect(push).not.toHaveBeenCalled();
});

test('development mock has five working trial buttons, explicitly separate from student achievements', async () => {
  await update({ ...auth, user: { role: 'STUDENT', userId: 'mock_student_fixture' } });
  expect(text()).toContain('Chơi thử không lưu thành tích');
  for (const game of TRAINING_CATALOG) {
    const play = button(game.id); expect(play.props.disabled).toBe(false);
    act(() => play.props.onPress());
    expect(push).toHaveBeenLastCalledWith({ pathname: '/games/[gameId]', params: { gameId: game.id, playMode: 'trial' } });
  }
});

test('native touch structure: ordinary Pressable targets outside decorative artwork, no responder capture', async () => {
  await update(auth);
  const scroll = tree.root.findByType(ScrollView);
  expect(scroll.props.onStartShouldSetResponderCapture).toBeUndefined();
  expect(scroll.props.onMoveShouldSetResponderCapture).toBeUndefined();
  for (const game of TRAINING_CATALOG) {
    const play = button(game.id);
    const style = StyleSheet.flatten(play.props.style({ pressed: false }));
    expect(style.minHeight).toBeGreaterThanOrEqual(48);
    expect(style.position).not.toBe('absolute');
    for (let parent = play.parent; parent; parent = parent.parent) {
      expect(parent.props.pointerEvents).not.toBe('none');
      expect(parent.props.pointerEvents).not.toBe('box-only');
      expect(parent.props.onStartShouldSetResponderCapture).toBeUndefined();
    }
  }
});

test('catalog Back dismisses to the existing profile tab', async () => {
  await update(auth);
  const back = tree.root.findAll(node => node.props.accessibilityLabel === 'Quay lại tab Của em' && typeof node.props.onPress === 'function')[0];
  act(() => back.props.onPress());
  expect(dismissTo).toHaveBeenCalledWith('/(tabs)/profile'); expect(push).not.toHaveBeenCalled();
});

test('production mock account has explicit blocked feedback and cannot navigate into trial', async () => {
  const development = __DEV__;
  try {
    Object.defineProperty(global, '__DEV__', { value: false, writable: true, configurable: true });
    await update({ ...auth, user: { userId: 'mock_student_fixture', role: 'STUDENT' } });
    expect(text()).not.toContain('Chơi thử'); expect(text()).toContain('Đăng nhập để chơi');
    for (const game of TRAINING_CATALOG) expect(button(game.id).props.disabled).toBe(true);
    expect(push).not.toHaveBeenCalled();
  } finally { Object.defineProperty(global, '__DEV__', { value: development, writable: true, configurable: true }); }
});
