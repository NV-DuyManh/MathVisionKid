import { clearSpeechCache, getSpeechAudio, prefetchLessonOpening, prefetchNarration, setSpeechOwner, warmSpeechSegments } from '../features/tutoring/speechCache';
import { TutorService } from '../features/tutoring/api/TutorService';
import { readSpeechPreferences } from '../features/tutoring/speechPreferences';

jest.mock('../features/tutoring/api/TutorService', () => ({ TutorService: { synthesizeSpeech: jest.fn() } }));
jest.mock('../features/tutoring/speechPreferences', () => ({ readSpeechPreferences: jest.fn() }));
const VOICE = 'vi-VN-NamMinhNeural';
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
beforeEach(() => {
  clearSpeechCache(); setSpeechOwner('pupil-a'); jest.clearAllMocks();
  (TutorService.synthesizeSpeech as jest.Mock).mockReset().mockResolvedValue(new Uint8Array(128));
  (readSpeechPreferences as jest.Mock).mockResolvedValue({ voiceId: VOICE, rate: 1.15 });
});
afterEach(() => { clearSpeechCache(); jest.useRealTimers(); });

it('deduplicates pending and completed audio while separating voice selections', async () => {
  const [one, two] = await Promise.all([getSpeechAudio('Chào em.', VOICE), getSpeechAudio('Chào em.', VOICE)]);
  expect(one).toBe(two); await getSpeechAudio('Chào em.', VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
  await getSpeechAudio('Chào em.', 'vi-VN-HoaiMyNeural');
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(2);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledWith('Chào em.', VOICE, 1, expect.anything());
});

it('speculatively prepares only the safe reading opening before a lesson is available', async () => {
  await prefetchLessonOpening();
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
  const text = (TutorService.synthesizeSpeech as jest.Mock).mock.calls[0][0];
  expect(text.startsWith('Đọc lại nguyên đề.')).toBe(true);
  expect(text.length).toBeLessThanOrEqual(160);
  await getSpeechAudio(text, VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
});

it('warms subsequent clips before playback and never synthesizes beyond its look-ahead', async () => {
  await warmSpeechSegments(['Đoạn một.', 'Đoạn hai.', 'Đoạn ba.', 'Đoạn bốn.', 'Đoạn năm.'], VOICE); await flush();
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(4);
  await getSpeechAudio('Đoạn hai.', VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(4);
});

it('starts preparing the second clip while the opening is still downloading', async () => {
  let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const first = warmSpeechSegments(['Đoạn một.', 'Đoạn hai.'], VOICE); await flush();
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(2);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledWith('Đoạn hai.', VOICE, 1, expect.anything());
  resolve(new Uint8Array(128)); await first;
});

it('uses the saved voice while preparing narration without changing the shared synthesis pace', async () => {
  (readSpeechPreferences as jest.Mock).mockResolvedValue({ voiceId: 'vi-VN-HoaiMyNeural', rate: 1.3 });
  expect(await prefetchNarration(['Em đọc đề.', 'Rồi tìm điều cần biết.'])).toBe(true);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledWith('Em đọc đề. Rồi tìm điều cần biết.', 'vi-VN-HoaiMyNeural', 1, expect.anything());
});

it('aborts old account requests and prevents late audio from entering another account cache', async () => {
  let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const previous = getSpeechAudio('Riêng tư.', VOICE); const rejected = expect(previous).rejects.toThrow('canceled'); await flush();
  const signal = (TutorService.synthesizeSpeech as jest.Mock).mock.calls[0][3];
  setSpeechOwner('pupil-b'); expect(signal.aborted).toBe(true);
  resolve(new Uint8Array(128)); await rejected;
  await getSpeechAudio('Riêng tư.', VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(2);
});

it('keeps a newer cached retry when an invalidated old request finishes late', async () => {
  let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const previous = getSpeechAudio('Chào em.', VOICE); const rejected = expect(previous).rejects.toThrow(); await flush();
  clearSpeechCache(); await getSpeechAudio('Chào em.', VOICE);
  resolve(new Uint8Array(128)); await rejected;
  await getSpeechAudio('Chào em.', VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(2);
});

it('can stop waiting without disrupting shared preparation or playing anything', async () => {
  let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const controller = new AbortController();
  const pending = getSpeechAudio('Chào em.', VOICE, controller.signal); const rejected = expect(pending).rejects.toThrow(); await flush();
  controller.abort(); await rejected;
  const next = getSpeechAudio('Chào em.', VOICE); resolve(new Uint8Array(128)); await next;
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
});

it('treats audio failures as optional and allows a later retry', async () => {
  (TutorService.synthesizeSpeech as jest.Mock).mockRejectedValueOnce(new Error('provider unavailable'));
  expect(await prefetchNarration(['Chào em.'])).toBe(false);
  expect(await prefetchNarration(['Chào em.'])).toBe(true);
});

it('does not start synthesis when preparation is canceled while preferences are loading', async () => {
  let resolve!: (value: { voiceId: string; rate: number }) => void;
  (readSpeechPreferences as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const controller = new AbortController();
  const prepared = prefetchNarration(['Chào em.'], controller.signal);
  const rejected = expect(prepared).rejects.toThrow('canceled');
  controller.abort(); resolve({ voiceId: VOICE, rate: 1.15 }); await rejected;
  expect(TutorService.synthesizeSpeech).not.toHaveBeenCalled();
});

it('limits the preparation wait while the first clip continues warming', async () => {
  jest.useFakeTimers(); let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  const prepared = prefetchNarration(['Chào em.']); await flush();
  jest.advanceTimersByTime(4000); expect(await prepared).toBe(false);
  resolve(new Uint8Array(128)); await flush(); await getSpeechAudio('Chào em.', VOICE);
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
});
