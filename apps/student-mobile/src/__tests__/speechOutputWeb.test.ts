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
  jest.useRealTimers();
  if (savedSynth) Object.defineProperty(window, 'speechSynthesis', savedSynth); else delete (window as any).speechSynthesis;
  if (savedUtterance) Object.defineProperty(window, 'SpeechSynthesisUtterance', savedUtterance); else delete (window as any).SpeechSynthesisUtterance;
});

it('returns an empty inventory immediately rather than hanging on missing voices', async () => {
  synth.getVoices.mockReturnValue([]);
  await expect(getAvailableVoicesAsync()).resolves.toEqual([]);
});

it('waits briefly for the first browser voice inventory and removes its listener', async () => {
  jest.useFakeTimers(); let changed!:()=>void;
  const browserSynth={...synth,addEventListener:jest.fn((_,callback)=>{changed=callback;}),removeEventListener:jest.fn()};
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:browserSynth});
  synth.getVoices.mockReturnValue([]);
  const voices=getAvailableVoicesAsync(); synth.getVoices.mockReturnValue([vi]);changed();
  await expect(voices).resolves.toEqual([expect.objectContaining({identifier:vi.voiceURI})]);
  expect(browserSynth.removeEventListener).toHaveBeenCalledWith('voiceschanged',changed);
  expect(jest.getTimerCount()).toBe(0);expect(synth.speak).not.toHaveBeenCalled();
});

it('bounds an empty browser inventory wait even when no event arrives', async () => {
  jest.useFakeTimers();
  const browserSynth={...synth,addEventListener:jest.fn(),removeEventListener:jest.fn()};
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:browserSynth});
  synth.getVoices.mockReturnValue([]);const voices=getAvailableVoicesAsync();
  jest.advanceTimersByTime(4000);await expect(voices).resolves.toEqual([]);
  expect(browserSynth.removeEventListener).toHaveBeenCalled();expect(jest.getTimerCount()).toBe(0);
});

it('waits for Vietnamese even when other languages arrive first and polls without an event', async () => {
  jest.useFakeTimers();
  const browserSynth={...synth,addEventListener:jest.fn(),removeEventListener:jest.fn()};
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:browserSynth});
  synth.getVoices.mockReturnValue([english]);
  const voices=getAvailableVoicesAsync();
  jest.advanceTimersByTime(1500);
  synth.getVoices.mockReturnValue([english,vi]);
  jest.advanceTimersByTime(250);
  await expect(voices).resolves.toEqual(expect.arrayContaining([expect.objectContaining({identifier:vi.voiceURI})]));
  expect(jest.getTimerCount()).toBe(0);
});

it('speaks synchronously using the selected Vietnamese voice and forwards lifecycle events', () => {
  const onDone = jest.fn(), onError = jest.fn(), onBoundary = jest.fn();
  speak('Em đọc lại đề nhé.', { voice: vi.voiceURI, rate: .75, onDone, onError, onBoundary });
  expect(synth.speak).toHaveBeenCalledTimes(1);
  const utterance = synth.speak.mock.calls[0][0];
  expect(utterance.voice).toEqual(vi); expect(utterance.lang).toBe('vi-VN'); expect(utterance.rate).toBe(.75);
  utterance.onend(); expect(onDone).toHaveBeenCalledTimes(1);
  utterance.onerror(); expect(onError).toHaveBeenCalledWith(expect.any(Error));
  utterance.onboundary({charIndex:6,charLength:3}); expect(onBoundary).toHaveBeenCalledWith({charIndex:6,charLength:3});
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
