import { getAvailableVoicesAsync, speak, stop } from '../features/tutoring/speechOutput.web';
import { createAudioPlayer, setAudioModeAsync } from 'expo-audio';
import { TutorService } from '../features/tutoring/api/TutorService';
import { saveSpeechAudio } from '../features/tutoring/speechAudioFile';
import { clearSpeechCache, getSpeechAudio } from '../features/tutoring/speechCache';

jest.mock('expo-audio', () => ({ createAudioPlayer: jest.fn(), setAudioModeAsync: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/tutoring/api/TutorService', () => ({ TutorService: { synthesizeSpeech: jest.fn() } }));
jest.mock('../features/tutoring/speechAudioFile', () => ({ saveSpeechAudio: jest.fn() }));
const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
let update: (status: any) => void;
let player: { play: jest.Mock; pause: jest.Mock; remove: jest.Mock; addListener: jest.Mock; setPlaybackRate: jest.Mock; shouldCorrectPitch: boolean };
let unsubscribe: jest.Mock, dispose: jest.Mock;
beforeEach(() => {
  jest.clearAllMocks(); unsubscribe = jest.fn(); dispose = jest.fn();
  clearSpeechCache();
  player = { play: jest.fn(), pause: jest.fn(), remove: jest.fn(), setPlaybackRate: jest.fn(), shouldCorrectPitch: false,
    addListener: jest.fn((_, callback) => { update = callback; return { remove: unsubscribe }; }) };
  (createAudioPlayer as jest.Mock).mockReturnValue(player);
  (saveSpeechAudio as jest.Mock).mockReturnValue({ uri: 'blob:private-narration', dispose });
  (TutorService.synthesizeSpeech as jest.Mock).mockReset().mockResolvedValue(new Uint8Array(128));
});
afterEach(async () => { await stop(); clearSpeechCache(); jest.useRealTimers(); });

it('uses Nam Minh by default and plays the downloaded Vietnamese audio without a device TTS fallback', async () => {
  const voices = await getAvailableVoicesAsync();
  expect(voices.map(v => v.identifier)).toEqual(['vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural']);
  const onDone = jest.fn(), onStart = jest.fn();
  speak('Chao em.', { onDone, onStart }); await flush();
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledWith('Chao em.', 'vi-VN-NamMinhNeural', 1, expect.anything());
  expect(player.setPlaybackRate).toHaveBeenCalledWith(1.15, 'high');
  expect(player.shouldCorrectPitch).toBe(true);
  expect(setAudioModeAsync).toHaveBeenCalledWith(expect.objectContaining({ allowsRecording: false, playsInSilentMode: true }));
  expect(player.play).toHaveBeenCalledTimes(1); expect(onDone).not.toHaveBeenCalled();
  update({ playing: true }); expect(onStart).toHaveBeenCalledTimes(1);
  update({ didJustFinish: true }); expect(onDone).toHaveBeenCalledTimes(1);
  update({ didJustFinish: true }); expect(onDone).toHaveBeenCalledTimes(1);
  expect(dispose).toHaveBeenCalledTimes(1); expect(unsubscribe).toHaveBeenCalledTimes(1);
});

it('stops waiting for shared audio and never plays a late result after stop', async () => {
  let resolve!: (value: Uint8Array) => void;
  (TutorService.synthesizeSpeech as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  const onDone = jest.fn(); speak('Chao em.', { onDone });
  await flush(); await stop();
  resolve(new Uint8Array(128)); await flush();
  expect(createAudioPlayer).not.toHaveBeenCalled(); expect(saveSpeechAudio).not.toHaveBeenCalled(); expect(onDone).not.toHaveBeenCalled();
});

it('releases playback and reports a safe error without choosing another language', async () => {
  const onError = jest.fn(), onDone = jest.fn();
  speak('Chao em.', { voice: 'vi-VN-HoaiMyNeural', rate: 1, onError, onDone }); await flush();
  update({ error: 'private-provider-details' });
  expect(onError).toHaveBeenCalledTimes(1); expect(String(onError.mock.calls[0][0])).not.toContain('private-provider-details');
  expect(player.pause).toHaveBeenCalledTimes(1); expect(player.remove).toHaveBeenCalledTimes(1); expect(dispose).toHaveBeenCalledTimes(1);
  update({ didJustFinish: true }); expect(onDone).not.toHaveBeenCalled();
});

it('reuses prepared audio at all three playback speeds without another synthesis request', async () => {
  await getSpeechAudio('Chao em.', 'vi-VN-NamMinhNeural');
  for (const rate of [1, 1.15, 1.3]) {
    speak('Chao em.', { rate }); await flush();
    expect(player.setPlaybackRate).toHaveBeenLastCalledWith(rate, 'high');
    await stop();
  }
  expect(TutorService.synthesizeSpeech).toHaveBeenCalledTimes(1);
});

it('reports a download failure and a player that never starts', async () => {
  jest.useFakeTimers(); const onError = jest.fn();
  (TutorService.synthesizeSpeech as jest.Mock).mockRejectedValueOnce(new Error('private response'));
  speak('Chao em.', { onError }); await flush();
  expect(onError).toHaveBeenCalledTimes(1); expect(createAudioPlayer).not.toHaveBeenCalled();
  speak('Chao em.', { onError }); await flush(); jest.advanceTimersByTime(15000);
  expect(onError).toHaveBeenCalledTimes(2); expect(dispose).toHaveBeenCalledTimes(1);
});
