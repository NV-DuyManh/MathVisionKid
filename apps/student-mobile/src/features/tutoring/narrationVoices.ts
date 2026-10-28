import { voicePreferences } from './voicePreferences';

export const NARRATION_VOICES = [
  { id: 'vi-VN-NamMinhNeural', name: 'Nam Minh', description: 'Giọng nam' },
  { id: 'vi-VN-HoaiMyNeural', name: 'Hoài My', description: 'Giọng nữ' },
] as const;
export type NarrationVoice = typeof NARRATION_VOICES[number]['id'];
export const DEFAULT_NARRATION_VOICE: NarrationVoice = NARRATION_VOICES[0].id;
const listeners = new Set<(voice: NarrationVoice) => void>();
let pendingSave: { voice: NarrationVoice; promise: Promise<void> } | undefined;
const pendingVoice = () => pendingSave?.voice;
export function subscribeNarrationVoice(listener: (voice: NarrationVoice) => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function isNarrationVoice(value: unknown): value is NarrationVoice {
  return NARRATION_VOICES.some(voice => voice.id === value);
}
export async function readNarrationVoice(): Promise<NarrationVoice> {
  if (pendingSave) return pendingSave.voice;
  try {
    const saved = await voicePreferences.get();
    const value = saved ? JSON.parse(saved)?.voiceId : null;
    return pendingVoice() || (isNarrationVoice(value) ? value : DEFAULT_NARRATION_VOICE);
  } catch { return pendingVoice() || DEFAULT_NARRATION_VOICE; }
}
export function saveNarrationVoice(voiceId: NarrationVoice): Promise<void> {
  const promise = (pendingSave?.promise.catch(() => {}) || Promise.resolve()).then(() => voicePreferences.set(JSON.stringify({ voiceId })));
  const next = { voice: voiceId, promise };
  pendingSave = next;
  void promise.then(() => { if (pendingSave === next) pendingSave = undefined; }, () => {});
  listeners.forEach(listener => listener(voiceId));
  return promise;
}
