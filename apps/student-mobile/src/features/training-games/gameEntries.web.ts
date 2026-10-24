import type { TrainingGameId } from '@mathvisionkid/training-games';

// Web retains independent chunks and the existing /study base-path handling.
const entries = {
  'race-to-finish': () => import('@mathvisionkid/training-games/race-to-finish'),
  'terrain-racing': () => import('@mathvisionkid/training-games/terrain-racing'),
  'energy-defense': () => import('@mathvisionkid/training-games/energy-defense'),
  'planet-rescue': () => import('@mathvisionkid/training-games/planet-rescue'),
  'block-island': () => import('@mathvisionkid/training-games/block-island'),
};
export function loadTrainingGame(gameId: TrainingGameId) { return entries[gameId](); }
