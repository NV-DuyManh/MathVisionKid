import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState } from 'react-native';
import { NarrationPreparation, NarrationCacheContext, useNarrationPreparation } from '../features/tutoring/NarrationPreparation';
import { downloadNarration, prepareLessonMedia } from '../features/tutoring/narrationApi';
import { readNarrationVoice, saveNarrationVoice } from '../features/tutoring/narrationVoices';
import { downloadPreparedNarration, type NarrationCache } from '../features/tutoring/narrationCache';
import type { NarrationSource } from '../features/tutoring/narrationApi';
jest.mock('expo-router', () => ({ useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]) }));
jest.mock('../features/tutoring/narrationFile', () => ({ saveNarration: jest.fn(() => ({ uri: 'file:///warm.wav', dispose: jest.fn() })) }));
jest.mock('../features/tutoring/narrationApi', () => ({ NARRATION_WAIT_SECONDS: 45, prioritizeNarration: jest.fn().mockResolvedValue(undefined), downloadNarration: jest.fn(), prepareLessonMedia: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/tutoring/narrationVoices', () => ({ ...jest.requireActual('../features/tutoring/narrationVoices'), readNarrationVoice: jest.fn() }));
jest.mock('../features/tutoring/voicePreferences', () => ({ voicePreferences: { get: jest.fn(), set: jest.fn().mockResolvedValue(undefined) } }));
const source = { sessionId: 'owned-narration-preparation-123', revision: 1 }, parts = ['Dữ kiện đã mở.', 'Câu hỏi bước này.'];
const bytes = new Uint8Array(50);
let view: TestRenderer.ReactTestRenderer, state: (next: string) => void, cache: NarrationCache;
function Reader({ current = source, paragraphs = parts }: { current?: NarrationSource | null; paragraphs?: string[] }) {
  cache = React.useContext(NarrationCacheContext)!;
  useNarrationPreparation(current, paragraphs);
  return null;
}
const screen = (current: NarrationSource | null = source, key = 'owner-a', paragraphs = parts) => <NarrationPreparation key={key}><Reader current={current} paragraphs={paragraphs} /></NarrationPreparation>;
beforeEach(() => {
  jest.clearAllMocks(); (downloadNarration as jest.Mock).mockReset().mockResolvedValue(bytes);
  (readNarrationVoice as jest.Mock).mockResolvedValue('vi-VN-HoaiMyNeural');
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { state = callback; return { remove: jest.fn() }; });
});
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); });

it('prepares the chosen local file without starting a competing unselected-voice job', async () => {
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await act(async () => { view = TestRenderer.create(screen()); });
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(prepareLessonMedia).toHaveBeenCalledWith(source, 'vi-VN-HoaiMyNeural', expect.any(AbortSignal));
  expect((prepareLessonMedia as jest.Mock).mock.calls[0][0]).not.toHaveProperty('paragraphs');
  expect(downloadNarration).toHaveBeenLastCalledWith({ ...source, prefetch: true }, parts, expect.any(AbortSignal), 'vi-VN-HoaiMyNeural', expect.any(Function));
  const pressed = downloadPreparedNarration(cache, source, parts, new AbortController().signal, 'vi-VN-HoaiMyNeural');
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  await act(async () => finish(bytes)); await pressed;
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  await downloadPreparedNarration(cache, source, parts, new AbortController().signal, 'vi-VN-NamMinhNeural');
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('does not generate audio before an owned issued lesson exists or for empty text', async () => {
  await act(async () => { view = TestRenderer.create(screen(null)); });
  expect(downloadNarration).not.toHaveBeenCalled();
  await act(async () => view.update(screen(source, 'owner-a', [])));
  expect(downloadNarration).not.toHaveBeenCalled();
});

it('cancels old-step work, rejects late output and prepares exactly the new revision', async () => {
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await act(async () => { view = TestRenderer.create(screen()); });
  const oldSignal = (downloadNarration as jest.Mock).mock.calls[0][2];
  await act(async () => view.update(screen({ ...source, revision: 2 }, 'owner-a', ['Bước mới đã mở.'])));
  expect(oldSignal.aborted).toBe(true);
  await act(async () => finish(bytes));
  expect((downloadNarration as jest.Mock).mock.calls.map(call => call[0].revision)).toEqual([1, 2]);
  expect((downloadNarration as jest.Mock).mock.calls[1][1]).toEqual(['Bước mới đã mở.']);
});

it('stops unfinished prefetch on background and restarts when reading resumes', async () => {
  (downloadNarration as jest.Mock).mockImplementation(() => new Promise(() => {}));
  await act(async () => { view = TestRenderer.create(screen()); });
  const signal = (downloadNarration as jest.Mock).mock.calls[0][2];
  act(() => state('background')); expect(signal.aborted).toBe(true);
  await act(async () => state('active'));
  expect(downloadNarration).toHaveBeenCalledTimes(2);
  const nextSignal = (downloadNarration as jest.Mock).mock.calls[1][2];
  act(() => view.unmount()); expect(nextSignal.aborted).toBe(true);
});

it('a failed warm-up stays silent and an explicit request can still succeed', async () => {
  (downloadNarration as jest.Mock).mockRejectedValueOnce(new Error('Provider down'));
  await act(async () => { view = TestRenderer.create(screen()); });
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  await expect(downloadPreparedNarration(cache, source, parts, new AbortController().signal, 'vi-VN-HoaiMyNeural')).resolves.toBe(bytes);
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('does not share the previous pupil cache or invent and prefetch future answers', async () => {
  await act(async () => { view = TestRenderer.create(screen()); });
  const oldCache = cache;
  await act(async () => view.update(screen(source, 'owner-b')));
  expect(cache).not.toBe(oldCache);
  expect(downloadNarration).toHaveBeenCalledTimes(2);
  expect((downloadNarration as jest.Mock).mock.calls.every(call => JSON.stringify(call[1]) === JSON.stringify(parts))).toBe(true);
});

it('changing voice immediately updates the whole-lesson priority and ignores the old warm-up', async () => {
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await act(async () => { view = TestRenderer.create(screen()); });
  const oldSignal = (downloadNarration as jest.Mock).mock.calls[0][2];
  await act(async () => { await saveNarrationVoice('vi-VN-NamMinhNeural'); });
  expect(oldSignal.aborted).toBe(true);
  expect(prepareLessonMedia).toHaveBeenLastCalledWith(source, 'vi-VN-NamMinhNeural', expect.any(AbortSignal));
  expect((downloadNarration as jest.Mock).mock.calls.map(call => call[3])).toEqual(['vi-VN-HoaiMyNeural', 'vi-VN-NamMinhNeural']);
  const before = (downloadNarration as jest.Mock).mock.calls.length;
  await act(async () => { finish(bytes); });
  expect(downloadNarration).toHaveBeenCalledTimes(before);
});

it('remembers a voice change while backgrounded and removes its subscription on unmount', async () => {
  await act(async () => { view = TestRenderer.create(screen()); });
  act(() => state('background'));
  const before = (prepareLessonMedia as jest.Mock).mock.calls.length;
  await act(async () => { await saveNarrationVoice('vi-VN-NamMinhNeural'); });
  expect(prepareLessonMedia).toHaveBeenCalledTimes(before);
  await act(async () => { state('active'); });
  expect(prepareLessonMedia).toHaveBeenLastCalledWith(source, 'vi-VN-NamMinhNeural', expect.any(AbortSignal));
  act(() => view.unmount());
  const after = (prepareLessonMedia as jest.Mock).mock.calls.length;
  await act(async () => { await saveNarrationVoice('vi-VN-HoaiMyNeural'); });
  expect(prepareLessonMedia).toHaveBeenCalledTimes(after);
});
