import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { usePreventRemove } from 'expo-router';
import { TrainingGameSession } from '../features/training-games/GamePlayer';
import { TRAINING_GAME_IDS } from '@mathvisionkid/training-games';

jest.mock('expo-router', () => ({ usePreventRemove: jest.fn() }));
jest.mock('react-native-gesture-handler', () => ({ GestureHandlerRootView: require('react-native').View }));
// This preset runs CommonJS without dynamic-import VM support. Exercise host
// commit/exit with its component injection seam; real lazy entry selection and
// real start buttons are covered by browser E2E for all five games.

let tree: TestRenderer.ReactTestRenderer;
afterEach(() => { if (tree) act(() => tree.unmount()); jest.clearAllMocks(); });
test.each(TRAINING_GAME_IDS)('host commits the %s game component and its exit callback', async gameId => {
  const exit = jest.fn();
  const Entry = (props: { onExit: () => void }) => React.createElement('GameStart', { ...props, gameId });
  await act(async () => { tree = TestRenderer.create(<TrainingGameSession studentId="77777777-7777-4777-8777-777777777777" gameId={gameId} onExit={exit} Game={Entry} />); });
  await act(async () => { await new Promise(resolve => setTimeout(resolve, 30)); });
  const entry = tree.root.find(node => node.type === ('GameStart' as React.ElementType));
  expect(entry.props.gameId).toBe(gameId);
  expect(jest.mocked(usePreventRemove)).toHaveBeenCalledWith(gameId !== 'race-to-finish', expect.any(Function));
  act(() => entry.props.onExit()); expect(exit).toHaveBeenCalledTimes(1);
  expect(tree.root.findAll(node => node.type === ('GameStart' as React.ElementType))).toHaveLength(0);
});
