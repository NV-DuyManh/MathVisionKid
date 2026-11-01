import { useMemo, useRef } from 'react';
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder, useAudioRecorderState } from 'expo-audio';
import { preparePlaybackSession } from './playbackSession';

/** Expo Go owns the native recorder; stop never leaves a recording audio session. */
export function useQuestionRecorder() {
  const finished = useRef<(() => void) | null>(null);
  const generation = useRef(0);
  const native = useAudioRecorder(RecordingPresets.HIGH_QUALITY, status => { if (status.isFinished) finished.current?.(); });
  const state = useAudioRecorderState(native);
  const recorder = useMemo(() => ({
    async prepare() {
      const id = ++generation.current;
      const permission = await AudioModule.requestRecordingPermissionsAsync();
      if (!permission.granted) throw new Error('Microphone permission required');
      if (id !== generation.current) throw new Error('Recording canceled');
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true, shouldRouteThroughEarpiece: false, interruptionMode: 'doNotMix' });
      await native.prepareToRecordAsync();
      if (id !== generation.current) { await native.stop().catch(() => {}); throw new Error('Recording canceled'); }
    },
    start(onFinish: () => void) { finished.current = onFinish; native.record({ forDuration: 30 }); },
    async stop(): Promise<string | null> {
      generation.current++;
      finished.current = null;
      try { await native.stop(); } catch { /* The native time limit may have already stopped it. */ }
      // Playback retries configuration itself if restoring the session fails here.
      await preparePlaybackSession().catch(() => {});
      try { return native.uri; } catch { return null; }
    },
  }), [native]);
  return { recorder, durationMillis: state.durationMillis };
}
