import { AppState } from 'react-native';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import { File, Paths } from 'expo-file-system';
import { AudioController } from '@mathvisionkid/training-games';

let fileSequence = 0;

// The packaged controller synthesizes browser audio. Native players accept the
// same short tones as local mono PCM WAVs; each player owns and deletes its file.
function toneWav(frequency: number, type: OscillatorType, duration: number, gain: number) {
  const sampleRate = 22050, samples = Math.ceil(duration * sampleRate);
  const bytes = new Uint8Array(44 + samples * 2), view = new DataView(bytes.buffer);
  const label = (offset: number, text: string) => [...text].forEach((letter, index) => { bytes[offset + index] = letter.charCodeAt(0); });
  label(0, 'RIFF'); view.setUint32(4, bytes.length - 8, true); label(8, 'WAVE');
  label(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  label(36, 'data'); view.setUint32(40, samples * 2, true);
  for (let index = 0; index < samples; index++) {
    const phase = (index * frequency / sampleRate) % 1;
    const wave = type === 'square' ? (phase < .5 ? 1 : -1) : type === 'triangle' ? 1 - 4 * Math.abs(phase - .5)
      : type === 'sawtooth' ? 2 * phase - 1 : Math.sin(phase * Math.PI * 2);
    const envelope = Math.min(1, index / (sampleRate * .006)) * Math.exp(-5 * index / samples);
    view.setInt16(44 + index * 2, Math.round(wave * gain * envelope * 32767), true);
  }
  return bytes;
}

export class NativeAudioController extends AudioController {
  private closed = false;
  private generation = 0;
  private foreground = AppState.currentState !== 'background' && AppState.currentState !== 'inactive';
  private players = new Set<() => void>();
  private tones = new Set<ReturnType<typeof setTimeout>>();
  private preparing: Promise<void> | null = null;
  private appStateSubscription: ReturnType<typeof AppState.addEventListener>;

  constructor(onSoundChange?: (enabled: boolean) => void) {
    super(onSoundChange);
    this.appStateSubscription = AppState.addEventListener('change', state => {
      this.foreground = state === 'active';
      if (!this.foreground) this.stopSounds();
    });
  }
  private canPlay() { return !this.closed && this.foreground && this.isSoundEnabled(); }
  private stopSounds() {
    this.generation++;
    this.tones.forEach(clearTimeout); this.tones.clear();
    [...this.players].forEach(cleanup => cleanup());
  }
  override setSoundEnabled(enabled: boolean, persist = true) {
    if (this.closed) return;
    super.setSoundEnabled(enabled, persist);
    if (!enabled) this.stopSounds();
  }
  override playTone(frequency: number, type: OscillatorType = 'sine', duration = .15, gain = .1) {
    if (!this.canPlay() || ![frequency, duration, gain].every(Number.isFinite) || frequency < 40 || frequency > 5000 || duration <= 0 || gain <= 0) return;
    const generation = this.generation;
    void this.playNative(frequency, type, Math.min(duration, .5), Math.min(gain, .3), generation).catch(() => {});
  }
  private async playNative(frequency: number, type: OscillatorType, duration: number, gain: number, generation: number) {
    // Recording changes the shared audio session. Restore speaker playback before
    // creating a player, and never continue an obsolete mount's pending request.
    this.preparing ??= setAudioModeAsync({ allowsRecording: false, playsInSilentMode: true, shouldPlayInBackground: false,
      shouldRouteThroughEarpiece: false, interruptionMode: 'mixWithOthers' }).finally(() => { this.preparing = null; });
    await this.preparing;
    if (!this.canPlay() || generation !== this.generation) return;
    // ponytail: at most four simultaneous feedback tones; oldest gives way to a
    // new effect rather than accumulating native players during rapid tapping.
    if (this.players.size >= 4) this.players.values().next().value?.();
    const file = new File(Paths.cache, `training-tone-${Date.now()}-${++fileSequence}.wav`);
    let player: ReturnType<typeof createAudioPlayer> | undefined;
    let listener: { remove: () => void } | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let released = false;
    const cleanup = () => {
      if (released) return;
      released = true; this.players.delete(cleanup);
      if (timer) clearTimeout(timer);
      listener?.remove();
      try { player?.pause(); } catch { /* Native player may already have stopped. */ }
      try { player?.remove(); } catch { /* Release remains best effort after an OS interruption. */ }
      try { file.delete(); } catch { /* Cache may already have been purged. */ }
    };
    this.players.add(cleanup);
    try {
      file.create(); file.writeSync(toneWav(frequency, type, duration, gain));
      player = createAudioPlayer({ uri: file.uri }, { keepAudioSessionActive: false, updateInterval: 50 });
      // Completion releases promptly; the watchdog also bounds failed loads.
      timer = setTimeout(cleanup, 2000);
      listener = player.addListener('playbackStatusUpdate', status => { if (status.didJustFinish) cleanup(); });
      if (!released) player.play();
    } catch { cleanup(); }
  }
  private later(callback: () => void, delay: number) {
    const generation = this.generation;
    const timer = setTimeout(() => { this.tones.delete(timer); if (this.canPlay() && generation === this.generation) callback(); }, delay);
    this.tones.add(timer);
  }
  override playCorrect() {
    if (!this.canPlay()) return;
    this.playTone(523.25, 'triangle', .12, .12);
    this.later(() => this.playTone(783.99, 'triangle', .25, .15), 100);
  }
  override playVictory() {
    if (!this.canPlay()) return;
    [523.25, 659.25, 783.99, 1046.5].forEach((frequency, index) => {
      this.later(() => this.playTone(frequency, 'triangle', .22, .15), index * 120);
    });
  }
  override dispose() {
    if (this.closed) return;
    this.closed = true; this.stopSounds(); this.appStateSubscription.remove(); super.dispose();
  }
}
