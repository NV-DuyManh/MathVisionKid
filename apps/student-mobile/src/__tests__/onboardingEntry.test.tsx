import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext } from '../context/AuthContext';
import IndexRoute from '../app/index';
import PortalRoute from '../app/portal';
import { completeOnboarding, ONBOARDING_COMPLETED_KEY } from '../features/onboarding/onboardingStorage';

const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('expo-router', () => {
  const router = { push: (...args: unknown[]) => mockPush(...args), replace: (...args: unknown[]) => mockReplace(...args) };
  return {
    useRouter: () => router,
    useFocusEffect: (callback: () => () => void) => require('react').useEffect(callback, [callback]),
  };
});
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('expo-linear-gradient', () => ({ LinearGradient: 'LinearGradient' }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Ionicons' }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../components/ui/BrandLockup', () => ({ BrandLockup: () => null }));
let view: TestRenderer.ReactTestRenderer;
const auth = { user: null, isAuthenticated: false, isLoading: false, login: jest.fn(), logout: jest.fn() };
const mount = async (value = auth, Route = IndexRoute) => act(async () => {
  view = TestRenderer.create(<AuthContext.Provider value={value}><Route /></AuthContext.Provider>);
});
const loginCtas = () => view.root.findAll(
  (node) => node.props.accessibilityLabel === 'Đăng nhập để bắt đầu' && typeof node.props.onPress === 'function'
);
const pressLoginCta = async () => {
  const [btn] = loginCtas();
  await act(async () => btn.props.onPress());
};
beforeEach(async () => { jest.clearAllMocks(); await AsyncStorage.removeItem(ONBOARDING_COMPLETED_KEY); });
afterEach(() => { act(() => view?.unmount()); });

it('opens introduction on first launch and bypasses it on a later launch after completion', async () => {
  await mount();
  await pressLoginCta();
  expect(mockPush).toHaveBeenLastCalledWith('/welcome');
  act(() => view.unmount());
  await completeOnboarding();
  await mount();
  await pressLoginCta();
  expect(mockPush).toHaveBeenLastCalledWith('/login');
});

it.each([
  ['/', IndexRoute],
  ['/portal', PortalRoute],
])('%s waits for auth and sends a verified learner directly home', async (_path, Route) => {
  await mount({ ...auth, isLoading: true }, Route);
  expect(loginCtas()).toHaveLength(0);
  expect(mockPush).not.toHaveBeenCalled();
  expect(mockReplace).not.toHaveBeenCalled();

  await act(async () => view.update(
    <AuthContext.Provider value={{ ...auth, isAuthenticated: true }}><Route /></AuthContext.Provider>
  ));
  expect(loginCtas()).toHaveLength(0);
  expect(mockReplace.mock.calls).toEqual([['/(tabs)']]);
});

it('shows the guest CTAs on /portal after auth finishes without a session', async () => {
  await mount({ ...auth, isLoading: true }, PortalRoute);
  expect(loginCtas()).toHaveLength(0);
  await act(async () => view.update(
    <AuthContext.Provider value={auth}><PortalRoute /></AuthContext.Provider>
  ));
  expect(loginCtas()[0]).toBeDefined();
  expect(mockReplace).not.toHaveBeenCalled();
});
