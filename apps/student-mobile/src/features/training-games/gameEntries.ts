/* eslint-disable @typescript-eslint/no-require-imports -- Native needs deferred synchronous Metro requires; web retains dynamic imports. */
import type { ComponentType } from 'react';
import type { TrainingGameId } from '@mathvisionkid/training-games';

type GameModule = { default: ComponentType<{ onExit: () => void }> };
// Native keeps entries in the existing bundle/module cache. Require is deferred
// until Play: it does not register async Metro chunks or request an HMR reload.
const entries: Record<TrainingGameId, () => GameModule> = {
  'race-to-finish': () => require('@mathvisionkid/training-games/race-to-finish'),
  'terrain-racing': () => require('@mathvisionkid/training-games/terrain-racing'),
  'energy-defense': () => require('@mathvisionkid/training-games/energy-defense'),
  'planet-rescue': () => require('@mathvisionkid/training-games/planet-rescue'),
  'block-island': () => require('@mathvisionkid/training-games/block-island'),
};
export function loadTrainingGame(gameId: TrainingGameId): Promise<GameModule> {
  return Promise.resolve().then(entries[gameId]);
}
