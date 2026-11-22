import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState, Text } from 'react-native';
import { AuthContext } from '../context/AuthContext';
import { StudentDailyLimit } from '../features/student-profile/StudentDailyLimit';
import { readParentControlStatus } from '../features/student-profile/parentControlApi';
import apiClient from '../services/api/apiClient';

let mockPath = '/';
jest.mock('expo-router', () => ({ usePathname: () => mockPath, useRouter: () => ({ push: jest.fn() }) }));
jest.mock('../services/api/apiClient', () => ({ post: jest.fn().mockResolvedValue({}) }));
jest.mock('../services/auth/tokenStorage', () => ({ tokenStorage: { getSessionId: jest.fn().mockResolvedValue('session') } }));
jest.mock('../features/student-profile/parentControlApi', () => ({ readParentControlStatus: jest.fn() }));
jest.mock('../features/student-profile/ParentModePreview', () => ({ ParentProfilePinDialog: () => null }));
jest.mock('../features/student-profile/StudentPauseScreen', () => ({ StudentPauseScreen: () => null }));

let tree: TestRenderer.ReactTestRenderer | undefined;
const initialAppState = AppState.currentState;
afterEach(async () => {
  if (tree) await act(async () => tree?.unmount());
  tree = undefined;
  AppState.currentState = initialAppState;
  mockPath = '/';
  jest.useRealTimers();
});

it('stops usage while the daily limit is reached and in parent mode, then resumes when allowed', async () => {
  jest.useFakeTimers();
  AppState.currentState = 'active';
  jest.mocked(apiClient.post).mockClear();
  const status = jest.mocked(readParentControlStatus);
  status.mockResolvedValue({ pinConfigured: true, dailyLimitReached: false, activityVerified: true });
  const auth = { isAuthenticated: true, user: { id: 'student', role: 'STUDENT', active: true } } as any;
  const render = () => <AuthContext.Provider value={auth}><StudentDailyLimit><Text>Student</Text></StudentDailyLimit></AuthContext.Provider>;
  await act(async () => { tree = TestRenderer.create(render()); });
  expect(jest.mocked(apiClient.post).mock.calls.some(([, body]) => body.active === true)).toBe(true);
  status.mockResolvedValue({ pinConfigured: true, dailyLimitReached: true, activityVerified: true });
  await act(async () => { jest.advanceTimersByTime(5000); });
  expect(jest.mocked(apiClient.post).mock.calls.some(([, body]) => body.active === false)).toBe(true);
  jest.mocked(apiClient.post).mockClear();
  await act(async () => { jest.advanceTimersByTime(20000); });
  expect(apiClient.post).not.toHaveBeenCalled();
  mockPath = '/parent-mode';
  status.mockResolvedValue({ pinConfigured: true, dailyLimitReached: false, activityVerified: false });
  await act(async () => { tree!.update(render()); });
  await act(async () => { jest.advanceTimersByTime(10000); });
  expect(apiClient.post).not.toHaveBeenCalled();
  mockPath = '/';
  await act(async () => { tree!.update(render()); });
  expect(jest.mocked(apiClient.post).mock.calls.some(([, body]) => body.active === true)).toBe(true);
});

it('does not count time while the learner is reviewing privacy before approval', async () => {
  jest.useFakeTimers();
  jest.mocked(apiClient.post).mockClear();
  AppState.currentState = 'active';
  mockPath = '/privacy';
  const status = jest.mocked(readParentControlStatus);
  status.mockResolvedValue({ pinConfigured: false, dailyLimitReached: false, activityVerified: true });
  const auth = { isAuthenticated: true, user: { id: 'student', role: 'STUDENT', active: true } } as any;
  await act(async () => {
    tree = TestRenderer.create(<AuthContext.Provider value={auth}><StudentDailyLimit><Text>Privacy</Text></StudentDailyLimit></AuthContext.Provider>);
  });
  await act(async () => { jest.advanceTimersByTime(20000); });
  expect(apiClient.post).not.toHaveBeenCalled();
});
