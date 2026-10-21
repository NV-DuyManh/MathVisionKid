const KEY = 'mathvision.lesson-voice';
export const voicePreferences = {
  async get(): Promise<string | null> { return typeof window === 'undefined' ? null : window.localStorage.getItem(KEY); },
  async set(value: string): Promise<void> { if (typeof window !== 'undefined') window.localStorage.setItem(KEY, value); },
};
