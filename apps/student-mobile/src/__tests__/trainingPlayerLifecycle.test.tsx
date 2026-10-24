import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { TrainingGameSession } from '../features/training-games/GamePlayer';
import { trainingResults } from '../features/training-games/resultStore';
import { TrainingServicesContext } from '@mathvisionkid/training-games';
import { createTrainingRuntime } from '../features/training-games/runtime';

// Native audio I/O is covered separately in trainingNativeAudio.test.ts.
jest.mock('../features/training-games/nativeAudioController', () => ({ NativeAudioController: require('@mathvisionkid/training-games').AudioController }));
jest.mock('expo-router', () => ({ usePreventRemove: jest.fn() }));
jest.mock('react-native-gesture-handler', () => ({ GestureHandlerRootView: require('react-native').View }));
function TestGame() {
  const services = React.useContext(TrainingServicesContext);
  React.useLayoutEffect(() => { services!.bridge.observe({ attemptId: 'strict-lifecycle', started: true, paused: false, mode: 'easy', status: 'won', score: 1, skillsPracticed: ['Phân số'] }); }, [services]);
  return null;
}
test('StrictMode effect replay keeps the active runtime usable and stores completion once', async () => {
  const studentId = '33333333-3333-4333-8333-333333333333';
  let renderer: TestRenderer.ReactTestRenderer;
  await act(async () => { renderer = TestRenderer.create(<React.StrictMode><TrainingGameSession studentId={studentId} gameId="planet-rescue" onExit={jest.fn()} Game={TestGame} /></React.StrictMode>); });
  await act(async () => { await new Promise(resolve => setTimeout(resolve, 30)); });
  await trainingResults.retry(studentId);
  const results = await trainingResults.history(studentId, 'planet-rescue');
  expect(results).toHaveLength(1); expect(results[0].status).toBe('won'); expect(results[0].correctCount).toBeUndefined();
  act(() => renderer!.unmount());
  await trainingResults.retry(studentId); expect(await trainingResults.history(studentId, 'planet-rescue')).toHaveLength(1);
});
test('rapid reopen keeps one question-history writer per UUID/game and never shares A with B', async () => {
  const a = '44444444-4444-4444-8444-444444444444', b = '55555555-5555-4555-8555-555555555555';
  const first = createTrainingRuntime(a, 'race-to-finish');
  await first.services.questionHistory.ready;
  first.services.questionHistory.remember('race:medium', 'a-question'); first.dispose();
  const again = createTrainingRuntime(a, 'race-to-finish'), other = createTrainingRuntime(b, 'race-to-finish');
  expect(again.services.questionHistory).toBe(first.services.questionHistory);
  expect(other.services.questionHistory).not.toBe(first.services.questionHistory);
  await other.services.questionHistory.ready;
  expect(again.services.questionHistory.has('race:medium', 'a-question')).toBe(true);
  expect(other.services.questionHistory.has('race:medium', 'a-question')).toBe(false);
  await again.services.questionHistory.flush();
  again.dispose(); other.dispose(); await Promise.all([first.ready, again.ready, other.ready]);
});
