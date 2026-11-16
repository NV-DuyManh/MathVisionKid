import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthContext } from '../context/AuthContext';
import WelcomeScreen from '../app/welcome';

const mockPush = jest.fn(), mockReplace = jest.fn();
jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush, replace: mockReplace }) }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../components/ui/AppIllustration', () => ({ AppIllustration: 'AppIllustration' }));

let view: TestRenderer.ReactTestRenderer;
const auth = { user: null, isAuthenticated: false, isLoading: false, login: jest.fn(), logout: jest.fn() };
const wrap = (value = auth) => <AuthContext.Provider value={value}><WelcomeScreen /></AuthContext.Provider>;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
beforeEach(() => { jest.clearAllMocks(); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('waits for restored authentication and returns signed-in learners to their home', () => {
  act(() => { view = TestRenderer.create(wrap({ ...auth, isLoading: true })); });
  expect(button('Bắt đầu')).toBeUndefined();
  expect(mockReplace).not.toHaveBeenCalled();
  act(() => view.update(wrap({ ...auth, isAuthenticated: true })));
  expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
  expect(view.toJSON()).toBeNull();
});

it('supports previous, next and direct card selection with accessible selected states', () => {
  act(() => { view = TestRenderer.create(wrap()); });
  expect(button('Trang giới thiệu trước').props.disabled).toBe(true);
  expect(button('Trang giới thiệu 1').props.accessibilityState.selected).toBe(true);
  act(() => button('Trang giới thiệu tiếp theo').props.onPress());
  expect(button('Trang giới thiệu 2').props.accessibilityState.selected).toBe(true);
  expect(button('Trang giới thiệu 2').props['aria-selected']).toBe(true);
  expect(button('Trang giới thiệu 1').props['aria-selected']).toBe(false);
  act(() => button('Trang giới thiệu 3').props.onPress());
  expect(button('Trang giới thiệu tiếp theo').props.disabled).toBe(true);
  act(() => button('Trang giới thiệu trước').props.onPress());
  expect(button('Trang giới thiệu 2').props.accessibilityState.selected).toBe(true);
});

it('updates the active card after a horizontal swipe and preserves it when the width changes', () => {
  act(() => { view = TestRenderer.create(wrap()); });
  const layout = view.root.findAll(node => typeof node.props.onLayout === 'function')[0];
  act(() => layout.props.onLayout({ nativeEvent: { layout: { width: 390 } } }));
  const pager = view.root.findAll(node => node.props.testID === 'welcome-pager' && node.props.onMomentumScrollEnd)[0];
  expect(pager.props.horizontal).toBe(true);
  expect(pager.props.pagingEnabled).toBe(true);
  act(() => pager.props.onMomentumScrollEnd({ nativeEvent: { contentOffset: { x: 780 } } }));
  expect(button('Trang giới thiệu 3').props.accessibilityState.selected).toBe(true);
  act(() => layout.props.onLayout({ nativeEvent: { layout: { width: 780 } } }));
  expect(button('Trang giới thiệu 3').props.accessibilityState.selected).toBe(true);
});

it('opens the existing account screen from either welcome action', () => {
  act(() => { view = TestRenderer.create(wrap()); });
  act(() => button('Bắt đầu').props.onPress());
  act(() => button('Tiếp tục học').props.onPress());
  expect(mockPush.mock.calls).toEqual([['/login'], ['/login']]);
});
