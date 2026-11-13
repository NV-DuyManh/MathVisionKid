import type { SpeechOptions, Voice } from 'expo-speech';

/** Keep browser speech synchronous with the learner's click and never choose a different language. */
export async function getAvailableVoicesAsync(): Promise<Voice[]> {
  if (typeof window === 'undefined' || !window.speechSynthesis) return [];
  const synth = window.speechSynthesis;
  const inventory = () => synth.getVoices().map(voice => ({ identifier: voice.voiceURI,
    name: voice.name, language: voice.lang, quality: 'Default' as Voice['quality'] }));
  const voices = inventory();
  const hasVietnamese = (items: Voice[]) => items.some(voice => /^vi(?:[-_]|$)/i.test(voice.language));
  if (hasVietnamese(voices) || !synth.addEventListener) return voices;
  // Browsers often populate voices just after the first query. Do not report a missing voice prematurely.
  return new Promise(resolve => {
    const finish = () => { clearTimeout(timer); clearInterval(poll); synth.removeEventListener('voiceschanged', changed); resolve(inventory()); };
    const changed = () => { if (hasVietnamese(inventory())) finish(); };
    const timer = setTimeout(finish, 4000);
    const poll = setInterval(changed, 250);
    synth.addEventListener('voiceschanged', changed); changed();
  });
}

export function speak(text: string, options: SpeechOptions): void {
  if (typeof window === 'undefined' || !window.speechSynthesis || !window.SpeechSynthesisUtterance) throw new Error('Speech unavailable');
  const voice = window.speechSynthesis.getVoices().find(item => item.voiceURI === options.voice && /^vi(?:[-_]|$)/i.test(item.lang));
  if (!voice) throw new Error('Vietnamese voice unavailable');
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = voice; utterance.lang = 'vi-VN'; utterance.rate = options.rate || .9; utterance.pitch = options.pitch || 1;
  utterance.onstart = () => { options.onStart?.(); };
  utterance.onend = () => { options.onDone?.(); };
  utterance.onboundary = event => { options.onBoundary?.call(utterance, event); };
  utterance.onerror = () => { options.onError?.(new Error('Speech playback failed')); };
  window.speechSynthesis.speak(utterance);
}

export async function stop(): Promise<void> {
  if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
}
