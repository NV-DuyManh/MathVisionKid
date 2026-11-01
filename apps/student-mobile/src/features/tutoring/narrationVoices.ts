import { voicePreferences } from './voicePreferences';

export const NARRATION_VOICES = [
  { id: 'vi-VN-NamMinhNeural', name: 'Giọng nam' },
  { id: 'vi-VN-HoaiMyNeural', name: 'Giọng nữ' },
] as const;
export type NarrationVoice = typeof NARRATION_VOICES[number]['id'];
export const VOICE_CHOICES = [...NARRATION_VOICES, { id: 'device', name: 'Giọng có sẵn' }] as const;
export type NarrationChoice = typeof VOICE_CHOICES[number]['id'];
export const DEFAULT_NARRATION_VOICE: NarrationVoice = NARRATION_VOICES[0].id;
const listeners = new Set<(voice: NarrationChoice) => void>();
let selectedVoice: NarrationChoice | null = null;
let loadingVoice: Promise<NarrationChoice> | undefined;
let pendingSave: { voice: NarrationChoice; promise: Promise<void> } | undefined;
export const currentNarrationVoice = () => selectedVoice;
export function subscribeNarrationVoice(listener: (voice: NarrationChoice) => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function isNarrationVoice(value: unknown): value is NarrationVoice {
  return NARRATION_VOICES.some(voice => voice.id === value);
}
export async function readNarrationVoice(): Promise<NarrationChoice> {
  if (selectedVoice) return selectedVoice;
  loadingVoice ??= voicePreferences.get().then(saved => {
    const value = saved ? JSON.parse(saved)?.voiceId : null;
    const restored: NarrationChoice = value === 'device' || isNarrationVoice(value) ? value : DEFAULT_NARRATION_VOICE;
    selectedVoice ??= restored;
    return selectedVoice || DEFAULT_NARRATION_VOICE;
  }).catch(() => { selectedVoice ||= DEFAULT_NARRATION_VOICE; return selectedVoice; });
  return loadingVoice;
}
export function saveNarrationVoice(voiceId: NarrationChoice): Promise<void> {
  selectedVoice = voiceId;
  const promise = (pendingSave?.promise.catch(() => {}) || Promise.resolve()).then(() => voicePreferences.set(JSON.stringify({ voiceId })));
  const next = { voice: voiceId, promise };
  pendingSave = next;
  void promise.then(() => { if (pendingSave === next) pendingSave = undefined; }, () => {});
  listeners.forEach(listener => listener(voiceId));
  return promise;
}
