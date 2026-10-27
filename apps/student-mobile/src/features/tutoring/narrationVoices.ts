import { voicePreferences } from './voicePreferences';

export const NARRATION_VOICES = [
  { id: 'vi-VN-NamMinhNeural', name: 'Nam Minh', description: 'Giọng nam' },
  { id: 'vi-VN-HoaiMyNeural', name: 'Hoài My', description: 'Giọng nữ' },
] as const;
export type NarrationVoice = typeof NARRATION_VOICES[number]['id'];
export const DEFAULT_NARRATION_VOICE: NarrationVoice = NARRATION_VOICES[0].id;
export function isNarrationVoice(value: unknown): value is NarrationVoice {
  return NARRATION_VOICES.some(voice => voice.id === value);
}
export async function readNarrationVoice(): Promise<NarrationVoice> {
  try {
    const saved = await voicePreferences.get();
    const value = saved ? JSON.parse(saved)?.voiceId : null;
    return isNarrationVoice(value) ? value : DEFAULT_NARRATION_VOICE;
  } catch { return DEFAULT_NARRATION_VOICE; }
}
export function saveNarrationVoice(voiceId: NarrationVoice): Promise<void> {
  return voicePreferences.set(JSON.stringify({ voiceId }));
}
