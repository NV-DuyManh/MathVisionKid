import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import type { SpeechOptions, Voice } from 'expo-speech';
import { getSpeechAudio } from './speechCache';
import { DEFAULT_SPEECH_RATE, SPEECH_RATES } from './speechPreferences';
import { saveSpeechAudio } from './speechAudioFile';

const voices: Voice[] = [
  { identifier: 'vi-VN-NamMinhNeural', name: 'Nam Minh', language: 'vi-VN', quality: 'Enhanced' as Voice['quality'] },
  { identifier: 'vi-VN-HoaiMyNeural', name: 'Hoài My', language: 'vi-VN', quality: 'Enhanced' as Voice['quality'] },
];
type Playback = {
  controller: AbortController; options: SpeechOptions;
  player?: ReturnType<typeof createAudioPlayer>; file?: ReturnType<typeof saveSpeechAudio>;
  subscription?: { remove: () => void }; timeout?: ReturnType<typeof setTimeout>;
};
let current: Playback | undefined;

function release(playback: Playback) {
  playback.controller.abort();
  clearTimeout(playback.timeout);
  playback.subscription?.remove();
  try { playback.player?.pause(); } catch { /* Player already released. */ }
  try { playback.player?.remove(); } catch { /* Player already released. */ }
  playback.file?.dispose();
}

export async function getAvailableVoicesAsync(): Promise<Voice[]> { return [...voices]; }

export async function stop(): Promise<void> {
  const previous = current; current = undefined;
  if (previous) { release(previous); previous.options.onStopped?.(); }
}

export function speak(text: string, options: SpeechOptions = {}): void {
  void stop();
  const playback: Playback = { controller: new AbortController(), options };
  current = playback;
  const fail = () => {
    if (current !== playback) return;
    current = undefined; release(playback);
    options.onError?.(new Error('Chưa phát được lời giảng tiếng Việt.'));
  };
  void (async () => {
    try {
      const bytes = await getSpeechAudio(text, options.voice || voices[0].identifier, playback.controller.signal);
      if (current !== playback) return;
      await setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true, shouldRouteThroughEarpiece: false });
      if (current !== playback) return;
      playback.file = saveSpeechAudio(bytes);
      const player = createAudioPlayer(playback.file.uri, { updateInterval: 250 });
      playback.player = player;
      const rate = SPEECH_RATES.some(item => item.value === options.rate) ? options.rate! : DEFAULT_SPEECH_RATE;
      player.shouldCorrectPitch = true;
      player.setPlaybackRate(rate, 'high');
      let started = false;
      playback.subscription = player.addListener('playbackStatusUpdate', status => {
        if (current !== playback) return;
        if (status.error) { fail(); return; }
        if (status.playing && !started) { started = true; clearTimeout(playback.timeout); options.onStart?.(); }
        if (status.didJustFinish) {
          current = undefined; release(playback); options.onDone?.();
        }
      });
      playback.timeout = setTimeout(fail, 15000);
      player.play();
    } catch { fail(); }
  })();
}
