import type { TrainingGameId } from '@mathvisionkid/training-games';

/** Development-only allowlisted fields: never log users, IDs, tokens or errors. */
export function trainingTrace(event: 'catalog-access' | 'play-press' | 'route' | 'runtime-ready' | 'runtime-disposed' | 'game-mounted' | 'game-unmounted' | 'game-error', fields: {
  gameId?: TrainingGameId;
  mode: 'student' | 'trial' | 'blocked';
  loading?: boolean;
  authenticated?: boolean;
}) {
  if (__DEV__) console.info('[training-games]', event, fields);
}
