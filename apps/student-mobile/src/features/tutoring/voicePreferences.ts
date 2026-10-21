import * as SecureStore from 'expo-secure-store';

const KEY = 'mathvision.lesson-voice';
export const voicePreferences = {
  get: () => SecureStore.getItemAsync(KEY),
  set: (value: string) => SecureStore.setItemAsync(KEY, value),
};
