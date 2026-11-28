import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState, Text } from 'react-native';
import apiClient from '../services/api/apiClient';
import { tokenStorage } from '../services/auth/tokenStorage';
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
  jest.mocked(tokenStorage.getSessionId).mockReset().mockResolvedValue('session-a');
});
afterEach(async () => {
  await act(async () => tree.unmount());
  AppState.currentState = initialAppState;
  jest.useRealTimers();
});

async function mountGame() {
  await act(async () => {
    tree = TestRenderer.create(<StudentGameTimeGate onLeave={jest.fn()}>
      <Text testID="actual-game">Game</Text>
    </StudentGameTimeGate>);
  });
}

function expectGameToBeReady() {
  expect(tree.root.findByProps({ testID: 'actual-game' })).toBeTruthy();
}

function expectGameToBePaused() {
  expect(tree.root.findAllByProps({ testID: 'actual-game' })).toHaveLength(0);
  expect(tree.root.findAllByType(Text).some(node => node.props.children === 'connection')).toBe(true);
}

async function advanceLeaseClock(millis: number) {
  await act(async () => { await jest.advanceTimersByTimeAsync(millis); });
}

const temporaryFailure = { response: { status: 503 } };
const grantedLease = { data: { leaseMillis: 10_000, remainingMillis: null, gameLimitReached: false } };

it('stops at the original cutoff after repeated 503 renewals', async () => {
  const post = jest.mocked(apiClient.post);
  post.mockResolvedValueOnce(grantedLease).mockRejectedValueOnce(temporaryFailure)
    .mockRejectedValueOnce(temporaryFailure).mockResolvedValue(grantedLease);
  await mountGame();

  await advanceLeaseClock(4_000);
  expectGameToBeReady();
  await advanceLeaseClock(4_000);
  expectGameToBeReady();
  await advanceLeaseClock(1_999);
  expectGameToBeReady();
  await advanceLeaseClock(1);
  expectGameToBePaused();
  await advanceLeaseClock(4_000);
  expectGameToBePaused();
  expect(post.mock.calls.map(([, body]) => body)).toEqual([
    expect.objectContaining({ active: true }), expect.objectContaining({ active: true }),
    expect.objectContaining({ active: true }), expect.objectContaining({ active: false }),
  ]);
});

it.each([2_999, 3_001])('honors cutoff when a renewal returns 503 after %i ms', async delay => {
  const post = jest.mocked(apiClient.post);
  const lease = { data: { leaseMillis: 7_000, remainingMillis: null, gameLimitReached: false } };
  post.mockResolvedValueOnce(lease)
    .mockImplementationOnce(() => new Promise((_, reject) => setTimeout(() => reject(temporaryFailure), delay)))
    .mockResolvedValue(lease);
  await mountGame();

  await advanceLeaseClock(6_999);
  expectGameToBeReady();
  await advanceLeaseClock(1);
  expectGameToBePaused();
  await advanceLeaseClock(1);
  expectGameToBePaused();
  expect(post).toHaveBeenLastCalledWith('/student/app-usage/game-heartbeat',
    expect.objectContaining({ active: false }), expect.objectContaining({ _identity: 'session-a' }));
});

it.each([401, 403])('pauses on a final HTTP %i denial during a valid lease', async status => {
  jest.mocked(apiClient.post).mockResolvedValueOnce(grantedLease)
    .mockRejectedValueOnce({ response: { status } }).mockResolvedValue(grantedLease);
  await mountGame();
  expectGameToBeReady();

  await advanceLeaseClock(4_000);
  expectGameToBePaused();
});

it('pauses when the renewal request times out during a valid lease', async () => {
  const timeout = Object.assign(new Error('timeout of 3500ms exceeded'), { code: 'ECONNABORTED' });
  jest.mocked(apiClient.post).mockResolvedValueOnce(grantedLease)
    .mockImplementationOnce((_url, _body, config) => new Promise((_, reject) => {
      setTimeout(() => reject(timeout), config?.timeout);
    }))
    .mockResolvedValue(grantedLease);
  await mountGame();

  await advanceLeaseClock(7_499);
  expectGameToBeReady();
  await advanceLeaseClock(1);
  expectGameToBePaused();
});

it('pauses when a 503 arrives after the client has invalidated the session', async () => {
  jest.mocked(apiClient.post).mockResolvedValueOnce(grantedLease).mockImplementationOnce(async () => {
    // Native auth clears its identity before propagating a failed token refresh.
    jest.mocked(tokenStorage.getSessionId).mockResolvedValue('session-b');
    throw temporaryFailure;
  });
  await mountGame();
  expectGameToBeReady();

  await advanceLeaseClock(4_000);
  expectGameToBePaused();
});

it('mounts only after an authenticated lease and removes the game when its duration expires', async () => {
  jest.mocked(apiClient.post).mockResolvedValue({
    data: { leaseMillis: 800, remainingMillis: 800, gameLimitReached: false },
  });
  await mountGame();
  expect(apiClient.post).toHaveBeenCalledWith('/student/app-usage/game-heartbeat',
    { connectionId: '11b090af-84bb-41bf-a80e-bbc7937bfe67', active: true },
    expect.objectContaining({ _identity: 'session-a' }));
  expectGameToBeReady();
  act(() => { jest.advanceTimersByTime(801); });
  expect(tree.root.findAllByProps({ testID: 'actual-game' })).toHaveLength(0);
  expect(tree.root.findAllByType(Text).some(node => node.props.children === 'game-limit')).toBe(true);
});

it('never mounts a game on a failed server check', async () => {
  jest.mocked(apiClient.post).mockRejectedValue(new Error('offline'));
  await mountGame();
  expectGameToBePaused();
});
