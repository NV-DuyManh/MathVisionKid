import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TrainingServicesContext, type TrainingServices } from '@mathvisionkid/training-games';
import { TrainingGameSession } from '../features/training-games/GamePlayer';
import { createTrainingRuntime } from '../features/training-games/runtime';
import { trainingResults } from '../features/training-games/resultStore';

// Native audio I/O is covered separately in trainingNativeAudio.test.ts.
jest.mock('../features/training-games/nativeAudioController', () => ({ NativeAudioController: require('@mathvisionkid/training-games').AudioController }));
jest.mock('expo-router', () => ({ usePreventRemove: jest.fn() }));
jest.mock('react-native-gesture-handler', () => ({ GestureHandlerRootView: require('react-native').View }));
jest.mock('../features/training-games/nativeDiagnostics', () => ({ useTrainingNativeDiagnostics: jest.fn() }));

const A = '99999999-9999-4999-8999-999999999991';
const B = '99999999-9999-4999-8999-999999999992';
const PROFILE = '%40tro_choi_cho_em%3Aprofile';
const settle = async () => { for (let index = 0; index < 20; index++) await Promise.resolve(); };
beforeEach(() => {
  jest.clearAllMocks();
  const rows = new Map<string, string>();
  jest.mocked(AsyncStorage.getItem).mockImplementation(async key => rows.get(key) ?? null);
  jest.mocked(AsyncStorage.setItem).mockImplementation(async (key, value) => { rows.set(key, value); });
});
afterEach(() => jest.restoreAllMocks());

test('settings errors have no fake result retry; result retry cannot clear an unrelated setting failure', async () => {
  const get = jest.mocked(AsyncStorage.getItem).getMockImplementation()!, set = jest.mocked(AsyncStorage.setItem).getMockImplementation()!;
  let profileUnavailable = true, resultsUnavailable = false;
  jest.spyOn(AsyncStorage, 'getItem').mockImplementation(async key => {
    if (profileUnavailable && key.endsWith(PROFILE)) throw Error('profile unavailable');
    return get(key);
  });
  jest.spyOn(AsyncStorage, 'setItem').mockImplementation(async (key, value) => {
    if (resultsUnavailable && key.endsWith(':host-results')) throw Error('results unavailable');
    return set(key, value);
  });
  let services!: TrainingServices;
  function Game() { services = React.useContext(TrainingServicesContext)!; return null; }
  let tree!: TestRenderer.ReactTestRenderer;
  try {
    await act(async () => { tree = TestRenderer.create(<TrainingGameSession studentId={A} gameId="planet-rescue" Game={Game} onExit={jest.fn()} />); });
    const text = () => JSON.stringify(tree.toJSON());
    const retries = () => tree.root.findAll(node => node.props.accessibilityLabel === 'Thử lưu kết quả' && typeof node.props.onPress === 'function');
    expect(text()).toContain('Chưa đọc được cài đặt trò chơi');
    expect(retries()).toHaveLength(0);
    expect(trainingResults.error(A)).toBeNull();
    await act(async () => { services.soundManager.setSoundEnabled(false); await settle(); });
    expect(text()).toContain('Chưa lưu được cài đặt âm thanh');
    expect(retries()).toHaveLength(0);

    resultsUnavailable = true;
    await act(async () => {
      await expect(trainingResults.event(A, { schemaVersion: 1, eventId: 'settings-isolation:event:1', sessionId: 'settings-isolation', studentId: A, gameId: 'planet-rescue', at: new Date().toISOString(), type: 'started' })).rejects.toThrow('results unavailable');
    });
    expect(retries()).toHaveLength(1);
    resultsUnavailable = false;
    await act(async () => { retries()[0].props.onPress(); await settle(); });
    expect(trainingResults.error(A)).toBeNull();
    expect(text()).toContain('Chưa lưu được cài đặt âm thanh');
    expect(retries()).toHaveLength(0);

    profileUnavailable = false;
    await act(async () => { services.soundManager.setSoundEnabled(true); await settle(); });
    expect(text()).not.toContain('Chưa đọc được cài đặt trò chơi');
    expect(text()).not.toContain('Chưa lưu được cài đặt âm thanh');
  } finally { if (tree) act(() => tree.unmount()); }
});

test('rapid sound toggles persist in order so an older write cannot replace the latest choice', async () => {
  const runtime = createTrainingRuntime(B, 'energy-defense', false, undefined, jest.fn());
  await runtime.ready;
  const set = jest.mocked(AsyncStorage.setItem).getMockImplementation()!;
  let finish!: () => void;
  const first = new Promise<void>(resolve => { finish = resolve; });
  const writes = jest.spyOn(AsyncStorage, 'setItem').mockImplementation(async (key, value) => {
    if (key.endsWith(PROFILE) && JSON.parse(value).settings.soundEnabled === false) await first;
    return set(key, value);
  });
  writes.mockClear();
  try {
    runtime.services.soundManager.setSoundEnabled(false);
    runtime.services.soundManager.setSoundEnabled(true);
    await settle();
    expect(writes).toHaveBeenCalledTimes(1);
    expect(JSON.parse(writes.mock.calls[0][1]).settings.soundEnabled).toBe(false);
    finish(); await settle();
    expect(writes).toHaveBeenCalledTimes(2);
    const profile = await runtime.services.profileManager.getOrCreateProfile();
    expect(profile.settings.soundEnabled).toBe(true);
  } finally { finish(); runtime.dispose(); }
});

test('a disposed runtime cannot publish a late setting error into the next student session', async () => {
  const notices = jest.fn();
  const runtime = createTrainingRuntime(A, 'block-island', false, undefined, notices);
  await runtime.ready; notices.mockClear();
  const set = jest.mocked(AsyncStorage.setItem).getMockImplementation()!;
  let fail!: (reason: Error) => void;
  const pending = new Promise<void>((_, reject) => { fail = reject; });
  jest.spyOn(AsyncStorage, 'setItem').mockImplementation(async (key, value) => {
    if (key.includes(A) && key.endsWith(PROFILE)) return pending;
    return set(key, value);
  });
  runtime.services.soundManager.setSoundEnabled(false); await settle(); runtime.dispose();
  const nextNotices = jest.fn();
  const next = createTrainingRuntime(B, 'block-island', false, undefined, nextNotices);
  try {
    await next.ready;
    fail(Error('late obsolete write')); await settle();
    expect(notices).not.toHaveBeenCalled();
    expect(nextNotices.mock.calls.every(([message]) => message === null)).toBe(true);
    expect(trainingResults.error(B)).toBeNull();
  } finally { next.dispose(); }
});
