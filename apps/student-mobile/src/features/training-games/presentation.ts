import type { TrainingGameId } from '@mathvisionkid/training-games';

// Matches the standalone route: only Race is landscape; Terrain/Energy portrait.
// No statusBar* options: RN Screens' iOS controller API conflicts with Expo Go's
// global React Native StatusBar configuration (UIViewControllerBased... = NO).
export function trainingScreenOptions(gameId: TrainingGameId) {
  return { headerShown: false, gestureEnabled: false,
    orientation: gameId === 'race-to-finish' ? 'landscape' as const
      : gameId === 'terrain-racing' || gameId === 'energy-defense' ? 'portrait' as const : 'default' as const };
}
export function trainingStatusBarHidden(gameId: TrainingGameId) {
  return gameId === 'race-to-finish' || gameId === 'terrain-racing';
}
