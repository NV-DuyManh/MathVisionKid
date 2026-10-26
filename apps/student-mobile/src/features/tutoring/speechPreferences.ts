import { voicePreferences } from './voicePreferences';

export const DEFAULT_SPEECH_RATE = 1.15;
export const DEFAULT_SPEECH_VOICE = 'vi-VN-NamMinhNeural';
export const SPEECH_RATES = [
  { value: 1, label: 'Chậm' },
  { value: DEFAULT_SPEECH_RATE, label: 'Vừa' },
  { value: 1.3, label: 'Nhanh' },
] as const;

export async function readSpeechPreferences(): Promise<{ voiceId: string; rate: number }> {
  const defaults = { voiceId: DEFAULT_SPEECH_VOICE, rate: DEFAULT_SPEECH_RATE };
  try {
    const value = await voicePreferences.get();
    if (!value) return defaults;
    const saved = JSON.parse(value);
    const legacyRates = new Map([[.75, 1], [.9, 1.15], [1.05, 1.3]]);
    const rate = legacyRates.get(saved?.rate) ?? saved?.rate;
    return {
      voiceId: [DEFAULT_SPEECH_VOICE, 'vi-VN-HoaiMyNeural'].includes(saved?.voiceId) ? saved.voiceId : defaults.voiceId,
      rate: SPEECH_RATES.some(option => option.value === rate) ? rate : defaults.rate,
    };
  } catch { return defaults; }
}
