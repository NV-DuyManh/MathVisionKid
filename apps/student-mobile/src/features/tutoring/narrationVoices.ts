import { voicePreferences } from './voicePreferences';

export const NARRATION_VOICES = [
  { id: 'vi-VN-NamMinhNeural', name: 'Giọng nam' },
  { id: 'vi-VN-HoaiMyNeural', name: 'Giọng nữ' },
] as const;
export type NarrationVoice = typeof NARRATION_VOICES[number]['id'];
export const VOICE_CHOICES = [{ id: 'device', name: 'Giọng thiết bị' }, ...NARRATION_VOICES] as const;
export type NarrationChoice = typeof VOICE_CHOICES[number]['id'];
export const DEFAULT_NARRATION_VOICE: NarrationVoice = NARRATION_VOICES[0].id;
const DEFAULT_NARRATION_CHOICE: NarrationChoice = 'device';
const listeners = new Set<(voice: NarrationChoice) => void>();
let selectedVoice: NarrationChoice | null = null;
let lastOnlineVoice: NarrationVoice = DEFAULT_NARRATION_VOICE;
let loadingVoice: Promise<NarrationChoice> | undefined;
let pendingSave: { voice: NarrationChoice; promise: Promise<void> } | undefined;
export const currentNarrationVoice = () => selectedVoice;
export const currentOnlineNarrationVoice = () => lastOnlineVoice;
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
    if (selectedVoice) return selectedVoice;
    const preference = saved ? JSON.parse(saved) : null;
    const value = preference?.voiceId;
    const restored: NarrationChoice = value === 'device' || isNarrationVoice(value) ? value : DEFAULT_NARRATION_CHOICE;
    selectedVoice = restored;
    if (isNarrationVoice(value)) lastOnlineVoice = value;
    else if (value === 'device' && isNarrationVoice(preference?.onlineVoiceId)) lastOnlineVoice = preference.onlineVoiceId;
    return restored;
  }).catch(() => (selectedVoice ??= DEFAULT_NARRATION_CHOICE));
  return loadingVoice;
}
export function saveNarrationVoice(voiceId: NarrationChoice): Promise<void> {
  selectedVoice = voiceId;
  if (isNarrationVoice(voiceId)) lastOnlineVoice = voiceId;
  const preference = JSON.stringify({
    voiceId,
    ...(voiceId === 'device' && lastOnlineVoice !== DEFAULT_NARRATION_VOICE ? { onlineVoiceId: lastOnlineVoice } : {}),
  });
  const promise = (pendingSave?.promise.catch(() => {}) || Promise.resolve()).then(() => voicePreferences.set(preference));
  const next = { voice: voiceId, promise };
  pendingSave = next;
  void promise.then(() => { if (pendingSave === next) pendingSave = undefined; }, () => {});
  listeners.forEach(listener => listener(voiceId));
  return promise;
}
