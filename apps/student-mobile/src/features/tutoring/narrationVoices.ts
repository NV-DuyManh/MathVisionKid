import { voicePreferences } from './voicePreferences';

export const NARRATION_VOICES = [
  { id: 'vi-VN-NamMinhNeural', name: 'Giọng nam' },
  { id: 'vi-VN-HoaiMyNeural', name: 'Giọng nữ' },
] as const;
export type NarrationVoice = typeof NARRATION_VOICES[number]['id'];
export const DEFAULT_NARRATION_VOICE: NarrationVoice = NARRATION_VOICES[0].id;
const listeners = new Set<(voice: NarrationVoice) => void>();
let selectedVoice: NarrationVoice | null = null;
let loadingVoice: Promise<NarrationVoice> | undefined;
let pendingSave: { voice: NarrationVoice; promise: Promise<void> } | undefined;
export const currentNarrationVoice = () => selectedVoice;
export function subscribeNarrationVoice(listener: (voice: NarrationVoice) => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function isNarrationVoice(value: unknown): value is NarrationVoice {
  return NARRATION_VOICES.some(voice => voice.id === value);
}
export async function readNarrationVoice(): Promise<NarrationVoice> {
  if (selectedVoice) return selectedVoice;
  loadingVoice ??= voicePreferences.get().then(saved => {
    const value = saved ? JSON.parse(saved)?.voiceId : null;
    selectedVoice ??= isNarrationVoice(value) ? value : DEFAULT_NARRATION_VOICE;
    return selectedVoice;
  }).catch(() => selectedVoice ||= DEFAULT_NARRATION_VOICE);
  return loadingVoice;
}
export function saveNarrationVoice(voiceId: NarrationVoice): Promise<void> {
  selectedVoice = voiceId;
  const promise = (pendingSave?.promise.catch(() => {}) || Promise.resolve()).then(() => voicePreferences.set(JSON.stringify({ voiceId })));
  const next = { voice: voiceId, promise };
  pendingSave = next;
  void promise.then(() => { if (pendingSave === next) pendingSave = undefined; }, () => {});
  listeners.forEach(listener => listener(voiceId));
  return promise;
}
