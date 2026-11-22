import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState, Text } from 'react-native';
import apiClient from '../services/api/apiClient';
import { StudentGameTimeGate } from '../features/student-profile/StudentGameTimeGate';

jest.mock('../services/api/apiClient', () => ({ post: jest.fn() }));
jest.mock('../services/auth/tokenStorage', () => ({
  tokenStorage: { getSessionId: jest.fn().mockResolvedValue('session-a') },
}));
jest.mock('../features/student-profile/studentUsage', () => ({
  createUsageConnectionId: () => '11b090af-84bb-41bf-a80e-bbc7937bfe67',
}));
jest.mock('../features/student-profile/StudentDailyLimit', () => ({
  StudentGameAccess: require('react').createContext(true),
  VerifyStudentGameAccess: require('react').createContext(async () => true),
}));
jest.mock('../features/student-profile/StudentPauseScreen', () => ({
  StudentPauseScreen: ({ reason }: { reason: string }) =>
    require('react').createElement(require('react-native').Text, null, reason),
}));

let tree: TestRenderer.ReactTestRenderer;
const initialAppState = AppState.currentState;
beforeEach(() => {
  AppState.currentState = 'active';
  jest.useFakeTimers();
  jest.mocked(apiClient.post).mockReset();
});
afterEach(async () => {
  await act(async () => tree.unmount());
  AppState.currentState = initialAppState;
  jest.useRealTimers();
});

it('mounts only after an authenticated lease and removes the game when its duration expires', async () => {
  jest.mocked(apiClient.post).mockResolvedValue({
    data: { leaseMillis: 800, remainingMillis: 800, gameLimitReached: false },
  });
  await act(async () => {
    tree = TestRenderer.create(<StudentGameTimeGate onLeave={jest.fn()}>
      <Text testID="actual-game">Game</Text>
    </StudentGameTimeGate>);
  });
  expect(apiClient.post).toHaveBeenCalledWith('/student/app-usage/game-heartbeat',
    { connectionId: '11b090af-84bb-41bf-a80e-bbc7937bfe67', active: true },
    expect.objectContaining({ _identity: 'session-a' }));
  expect(tree.root.findByProps({ testID: 'actual-game' })).toBeTruthy();
  act(() => { jest.advanceTimersByTime(801); });
  expect(tree.root.findAllByProps({ testID: 'actual-game' })).toHaveLength(0);
  expect(tree.root.findAllByType(Text).some(node => node.props.children === 'game-limit')).toBe(true);
});

it('never mounts a game on a failed server check', async () => {
  jest.mocked(apiClient.post).mockRejectedValue(new Error('offline'));
  await act(async () => {
    tree = TestRenderer.create(<StudentGameTimeGate onLeave={jest.fn()}>
      <Text testID="actual-game">Game</Text>
    </StudentGameTimeGate>);
  });
  expect(tree.root.findAllByProps({ testID: 'actual-game' })).toHaveLength(0);
  expect(tree.root.findAllByType(Text).some(node => node.props.children === 'connection')).toBe(true);
});
