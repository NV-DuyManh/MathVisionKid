import { setAudioModeAsync, setIsAudioActiveAsync } from 'expo-audio';

/** Recording and playback share the native audio session in Expo Go. */
export async function preparePlaybackSession() {
  await setAudioModeAsync({
    allowsRecording: false,
    playsInSilentMode: true,
    shouldRouteThroughEarpiece: false,
    shouldPlayInBackground: false,
    interruptionMode: 'doNotMix',
  });
  await setIsAudioActiveAsync(true);
}
