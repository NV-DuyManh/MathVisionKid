import { getAvailableVoicesAsync, speak, stop } from '../features/tutoring/speechOutput.web';

const vi = { voiceURI: 'vietnamese', lang: 'vi-VN', name: 'Giọng Việt' };
const english = { voiceURI: 'english', lang: 'en-US', name: 'English' };
const savedSynth = Object.getOwnPropertyDescriptor(window, 'speechSynthesis');
const savedUtterance = Object.getOwnPropertyDescriptor(window, 'SpeechSynthesisUtterance');
let synth: { getVoices: jest.Mock; speak: jest.Mock; cancel: jest.Mock };
beforeEach(() => {
  synth = { getVoices: jest.fn().mockReturnValue([english, vi]), speak: jest.fn(), cancel: jest.fn() };
  Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: synth });
  Object.defineProperty(window, 'SpeechSynthesisUtterance', { configurable: true, value: class { text: string; constructor(text: string) { this.text = text; } } });
});
afterEach(() => {
  if (savedSynth) Object.defineProperty(window, 'speechSynthesis', savedSynth); else delete (window as any).speechSynthesis;
  if (savedUtterance) Object.defineProperty(window, 'SpeechSynthesisUtterance', savedUtterance); else delete (window as any).SpeechSynthesisUtterance;
});

it('returns an empty inventory immediately rather than hanging on missing voices', async () => {
  synth.getVoices.mockReturnValue([]);
  await expect(getAvailableVoicesAsync()).resolves.toEqual([]);
});

it('speaks synchronously using the selected Vietnamese voice and forwards lifecycle events', () => {
  const onDone = jest.fn(), onError = jest.fn();
  speak('Em đọc lại đề nhé.', { voice: vi.voiceURI, rate: .75, onDone, onError });
  expect(synth.speak).toHaveBeenCalledTimes(1);
  const utterance = synth.speak.mock.calls[0][0];
  expect(utterance.voice).toEqual(vi); expect(utterance.lang).toBe('vi-VN'); expect(utterance.rate).toBe(.75);
  utterance.onend(); expect(onDone).toHaveBeenCalledTimes(1);
  utterance.onerror(); expect(onError).toHaveBeenCalledWith(expect.any(Error));
});

it('does not silently read Vietnamese with an English voice when the chosen voice disappears', () => {
  synth.getVoices.mockReturnValue([english]);
  expect(() => speak('Em đọc lại đề nhé.', { voice: vi.voiceURI })).toThrow('Vietnamese voice unavailable');
  expect(() => speak('Em đọc lại đề nhé.', { voice: english.voiceURI })).toThrow('Vietnamese voice unavailable');
  expect(synth.speak).not.toHaveBeenCalled();
});

it('cancels immediately on stop and remains usable when speech is unsupported', async () => {
  const promise = stop(); expect(synth.cancel).toHaveBeenCalledTimes(1); await promise;
  Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: undefined });
  await expect(getAvailableVoicesAsync()).resolves.toEqual([]);
  await expect(stop()).resolves.toBeUndefined();
  expect(() => speak('Em đọc nhé.', { voice: vi.voiceURI })).toThrow('Speech unavailable');
});
