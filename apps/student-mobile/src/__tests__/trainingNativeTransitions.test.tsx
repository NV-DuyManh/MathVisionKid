import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StatusBar } from 'expo-status-bar';
import { TRAINING_GAME_IDS, TrainingServicesContext, type TrainingGameId, type TrainingServices } from '@mathvisionkid/training-games';
import { GamePlayer } from '../features/training-games/GamePlayer';
import { trainingResults } from '../features/training-games/resultStore';
import { trainingScreenOptions } from '../features/training-games/presentation';
import { createTrainingRuntime } from '../features/training-games/runtime';

// Native audio I/O is covered separately in trainingNativeAudio.test.ts.
jest.mock('../features/training-games/nativeAudioController', () => ({ NativeAudioController: require('@mathvisionkid/training-games').AudioController }));
jest.mock('expo-router', () => ({ usePreventRemove: jest.fn() }));
jest.mock('react-native-gesture-handler', () => ({ GestureHandlerRootView: require('react-native').View }));
jest.mock('@mathvisionkid/training-games/race-to-finish', () => mockEntry('race-to-finish'));
jest.mock('@mathvisionkid/training-games/terrain-racing', () => mockEntry('terrain-racing'));
jest.mock('@mathvisionkid/training-games/energy-defense', () => mockEntry('energy-defense'));
jest.mock('@mathvisionkid/training-games/planet-rescue', () => mockEntry('planet-rescue'));
jest.mock('@mathvisionkid/training-games/block-island', () => mockEntry('block-island'));

const mockInitializations = new Map<TrainingGameId, number>();
const mockServices = new Map<TrainingGameId, TrainingServices>();
function mockEntry(gameId: TrainingGameId) {
  mockInitializations.set(gameId, (mockInitializations.get(gameId) ?? 0) + 1);
  function Entry({ onExit }: { onExit: () => void }) {
    const services = React.useContext(TrainingServicesContext)!;
    React.useLayoutEffect(() => {
      mockServices.set(gameId, services);
      services.setStatusBarHidden?.(true);
      services.bridge.observe({ attemptId: 'native-sequence', started: true, paused: false, mode: 'fixture', skillsPracticed: [] });
    }, [services]);
    return React.createElement('NativeEntry', { gameId, onExit });
  }
  return { __esModule: true, default: Entry };
}

const order: TrainingGameId[] = ['race-to-finish', 'terrain-racing', 'energy-defense', 'planet-rescue', 'block-island'];
const studentId = '88888888-8888-4888-8888-888888888888';
test.each([false, true])('native entry selection, three cycles, once-only exit and obsolete callbacks (trial=%s)', async trial => {
  let obsolete: TrainingServices | undefined;
  const save = jest.spyOn(trainingResults, 'save');
  for (let cycle = 0; cycle < 3; cycle++) for (const gameId of order) {
    const onExit = jest.fn(); let tree!: TestRenderer.ReactTestRenderer;
    await act(async () => { tree = TestRenderer.create(<GamePlayer studentId={trial ? 'development-trial:8001' : studentId} trial={trial} gameId={gameId} onExit={onExit} />); });
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 20)); });
    const entry = tree.root.find(node => node.type === ('NativeEntry' as React.ElementType));
    expect(entry.props.gameId).toBe(gameId); expect(tree.root.findByType(StatusBar).props.hidden).toBe(true);
    act(() => { obsolete?.setStatusBarHidden?.(false); obsolete?.bridge.observe({ attemptId: 'late', started: true, paused: false, mode: 'fixture', status: 'won', skillsPracticed: [] }); });
    expect(tree.root.findByType(StatusBar).props.hidden).toBe(true);
    const exit = entry.props.onExit;
    act(() => { exit(); exit(); }); expect(onExit).toHaveBeenCalledTimes(1);
    const changedExit = jest.fn();
    act(() => tree.update(<GamePlayer studentId={trial ? 'development-trial:8001' : studentId} trial={trial} gameId={gameId} onExit={changedExit} />));
    expect(changedExit).not.toHaveBeenCalled(); expect(tree.root.findAllByType(StatusBar)).toHaveLength(0);
    obsolete = mockServices.get(gameId);
    act(() => tree.unmount()); act(() => exit()); expect(onExit).toHaveBeenCalledTimes(1);
  }
  for (const id of TRAINING_GAME_IDS) expect(mockInitializations.get(id)).toBe(1);
  if (trial) expect(save).not.toHaveBeenCalled();
  else {
    await trainingResults.retry(studentId);
    for (const id of TRAINING_GAME_IDS) {
      const results = await trainingResults.history(studentId, id);
      expect(results).toHaveLength(3); expect(results.every(row => row.status === 'abandoned')).toBe(true);
    }
  }
  save.mockRestore();
});

test('Race owns landscape while other games keep their policy; native stack never owns status bar', () => {
  expect(trainingScreenOptions('race-to-finish').orientation).toBe('landscape');
  expect(trainingScreenOptions('terrain-racing').orientation).toBe('portrait');
  expect(trainingScreenOptions('energy-defense').orientation).toBe('portrait');
  for (const id of ['planet-rescue', 'block-island'] as const) expect(trainingScreenOptions(id).orientation).toBe('default');
  for (const id of TRAINING_GAME_IDS) expect(Object.keys(trainingScreenOptions(id)).some(key => key.startsWith('statusBar'))).toBe(false);
});

test('disposed runtime refuses late presentation and Back registrations', async () => {
  const presentation = jest.fn(), back = jest.fn();
  const runtime = createTrainingRuntime('development-trial:8002', 'energy-defense', true, presentation);
  await runtime.ready; runtime.services.setStatusBarHidden?.(true); expect(presentation).toHaveBeenCalledWith(true);
  runtime.dispose(); runtime.services.setStatusBarHidden?.(false); runtime.services.registerBack(back);
  expect(presentation).toHaveBeenCalledTimes(1); expect(runtime.requestBack()).toBe(false); expect(back).not.toHaveBeenCalled();
});
