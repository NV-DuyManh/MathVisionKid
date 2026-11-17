import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext } from '../context/AuthContext';
import SplashScreen from '../app/index';
import { completeOnboarding, ONBOARDING_COMPLETED_KEY } from '../features/onboarding/onboardingStorage';

const mockReplace = jest.fn();
jest.mock('expo-router', () => ({ useRouter: () => ({ replace: mockReplace }) }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../components/ui/BrandLockup', () => ({ BrandLockup: () => null }));
let view: TestRenderer.ReactTestRenderer;
const auth = { user: null, isAuthenticated: false, isLoading: false, login: jest.fn(), logout: jest.fn() };
const mount = async (value = auth) => act(async () => { view = TestRenderer.create(<AuthContext.Provider value={value}><SplashScreen /></AuthContext.Provider>); });
beforeEach(async () => { jest.clearAllMocks(); await AsyncStorage.removeItem(ONBOARDING_COMPLETED_KEY); });
afterEach(() => { act(() => view?.unmount()); });

it('opens introduction on first launch and bypasses it on a later launch after completion', async () => {
  await mount();
  expect(mockReplace).toHaveBeenLastCalledWith('/welcome');
  act(() => view.unmount());
  await completeOnboarding();
  await mount();
  expect(mockReplace).toHaveBeenLastCalledWith('/login');
});

it('waits for auth and sends an authenticated learner directly home regardless of onboarding storage', async () => {
  await mount({ ...auth, isLoading: true });
  expect(mockReplace).not.toHaveBeenCalled();
  await act(async () => view.update(<AuthContext.Provider value={{ ...auth, isAuthenticated: true }}><SplashScreen /></AuthContext.Provider>));
  expect(mockReplace.mock.calls).toEqual([['/(tabs)']]);
});
