import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

export const ONBOARDING_COMPLETED_KEY = 'mathvision_onboarding_completed_v1';

export async function hasCompletedOnboarding() {
  try {
    return (Platform.OS === 'web' && typeof window !== 'undefined'
      ? window.localStorage.getItem(ONBOARDING_COMPLETED_KEY)
      : await AsyncStorage.getItem(ONBOARDING_COMPLETED_KEY)) === 'true';
  } catch { return false; }
}

export async function completeOnboarding() {
  try {
    if (Platform.OS === 'web' && typeof window !== 'undefined') window.localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
    else await AsyncStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
  } catch { /* Navigation stays available when optional device storage is unavailable. */ }
}
