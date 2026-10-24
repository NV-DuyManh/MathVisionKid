import { useEffect } from 'react';
import { AppState, Dimensions, Platform } from 'react-native';
import Constants from 'expo-constants';
import { requireOptionalNativeModule } from 'expo';
import type { TrainingGameId } from '@mathvisionkid/training-games';
import { trainingScreenOptions } from './presentation';

/** Native-only development diagnostics; contains no identity, token or profile. */
export function useTrainingNativeDiagnostics(gameId: TrainingGameId, trial: boolean) {
  useEffect(() => {
    if (!__DEV__ || Platform.OS === 'web') return;
    let active = true;
    // Read once while the focused runtime is alive; cleanup must not initialize
    // a native module while Expo Go is tearing its JS runtime down.
    let assetModuleAvailable = false;
    try { assetModuleAvailable = !!requireOptionalNativeModule('ExpoAsset'); } catch { /* diagnostics only */ }
    const log = (phase: 'focus' | 'resize' | 'app-state' | 'blur', state?: string) => {
      const window = Dimensions.get('window');
      console.info('[training-native]', { phase, gameId, mode: trial ? 'trial' : 'student',
        platform: Platform.OS, osVersion: String(Platform.Version), expoGoVersion: Constants.expoVersion,
        assetModuleAvailable, requestedOrientation: trainingScreenOptions(gameId).orientation,
        windowOrientation: window.width > window.height ? 'landscape' : 'portrait', width: window.width, height: window.height, state });
    };
    log('focus');
    const dimensions = Dimensions.addEventListener('change', () => { if (active) log('resize'); });
    const app = AppState.addEventListener('change', state => { if (active) log('app-state', state); });
    return () => { active = false; dimensions.remove(); app.remove(); log('blur'); };
  }, [gameId, trial]);
}
