import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState } from 'react-native';
import { LessonNarration } from '../features/tutoring/LessonNarration';
import { AudioPlayback } from '../features/tutoring/AudioPlayback';
import { downloadNarration, readNarrationProgress } from '../features/tutoring/narrationApi';
import { saveNarration } from '../features/tutoring/narrationFile';
import { voicePreferences } from '../features/tutoring/voicePreferences';
import { TaskProgress } from '../components/ui/TaskProgress';
import { NarrationCacheContext } from '../features/tutoring/NarrationPreparation';
import { createNarrationCache } from '../features/tutoring/narrationCache';

jest.mock('../features/tutoring/AudioPlayback', () => ({ AudioPlayback: () => null }));
jest.mock('../features/tutoring/MediaTimeline', () => ({ MediaTimeline: () => null }));
jest.mock('../features/tutoring/narrationApi', () => ({ NARRATION_WAIT_SECONDS: 45, prioritizeNarration: jest.fn().mockResolvedValue(undefined), downloadNarration: jest.fn(), readNarrationProgress: jest.fn().mockRejectedValue(new Error('No status')) }));
jest.mock('../features/tutoring/DeviceNarration', () => ({ DeviceNarration: () => null }));
jest.mock('../features/tutoring/narrationFile', () => ({ saveNarration: jest.fn() }));
jest.mock('../features/tutoring/voicePreferences', () => ({ voicePreferences: { get: jest.fn(), set: jest.fn() } }));
const source = { sessionId: 'owned-narration-session-123', revision: 2 };
const paragraphs = ['Em chia các phần bằng nhau.', 'Mình gộp các phần cùng kích thước.'];
let view: TestRenderer.ReactTestRenderer;
const dispose = jest.fn();
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const render = async (overrides = {}) => { await act(async () => { view = TestRenderer.create(<LessonNarration scope="owner:step" source={source} paragraphs={paragraphs} {...overrides} />); }); };
beforeEach(() => {
  jest.clearAllMocks(); (downloadNarration as jest.Mock).mockReset().mockResolvedValue(new Uint8Array(50));
  (voicePreferences.get as jest.Mock).mockResolvedValue(null);
  (voicePreferences.set as jest.Mock).mockResolvedValue(undefined);
  (saveNarration as jest.Mock).mockReturnValue({ uri: 'file:///private-speech.wav', dispose });
});
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });

it('loads the owned WAV once and keeps long written narration collapsed until requested', async () => {
  const onFinished = jest.fn(); await render({ onFinished });
  expect(downloadNarration).toHaveBeenCalledWith(source, paragraphs, expect.any(AbortSignal), 'vi-VN-NamMinhNeural', expect.any(Function));
  expect(view.root.findByType(AudioPlayback).props.uri).toBe('file:///private-speech.wav');
  expect(onFinished).not.toHaveBeenCalled(); expect(text()).not.toContain(paragraphs[1]);
  act(() => button('Đọc lời giảng chi tiết').props.onPress()); expect(text()).toContain(paragraphs[1]);
  expect(button('Đọc lời giảng chi tiết').props['aria-expanded']).toBe(true);
});

it('releases its private file on close and does not publish a file after an aborted source', async () => {
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); const signal = (downloadNarration as jest.Mock).mock.calls[0][2];
  await act(async () => view.update(<LessonNarration scope="other-owner" source={source} paragraphs={['Bài khác.']} />));
  expect(signal.aborted).toBe(true);
  await act(async () => finish(new Uint8Array(50)));
  expect(saveNarration).toHaveBeenCalledTimes(1);
  act(() => view.unmount()); expect(dispose).toHaveBeenCalledTimes(1);
});

it('keeps the transcript usable and retries a failed audio download without showing provider details', async () => {
  (downloadNarration as jest.Mock).mockRejectedValueOnce(new Error('localhost private provider'));
  await render(); expect(text()).not.toContain('localhost'); expect(button('Tải lại lời giảng')).toBeDefined();
  act(() => button('Đọc lời giảng chi tiết').props.onPress()); expect(text()).toContain(paragraphs[0]);
  await act(async () => button('Tải lại lời giảng').props.onPress());
  expect(view.root.findByType(AudioPlayback)).toBeDefined(); expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('cancels an unfinished download on background and does not autoplay when returning', async () => {
  let change!: (state: string) => void;
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { change = callback; return { remove: jest.fn() }; });
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); act(() => change('background'));
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(true);
  await act(async () => finish(new Uint8Array(50))); expect(saveNarration).not.toHaveBeenCalled();
  expect(button('Tải lại lời giảng')).toBeDefined();
});

it('does not fetch narration while disabled', async () => { await render({ disabled: true }); expect(downloadNarration).not.toHaveBeenCalled(); });

it('keeps one progress bar through synthesis, downloading and actual decoder readiness', async () => {
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  expect(view.root.findByType(TaskProgress).props.activeStep).toBe(1);
  expect(view.root.findAllByType(AudioPlayback)).toHaveLength(0);
  await act(async () => finish(new Uint8Array(50)));
  expect(view.root.findByType(TaskProgress).props.activeStep).toBe(2);
  expect(view.root.findByType(TaskProgress).props.complete).toBe(false);
  act(() => view.root.findByType(AudioPlayback).props.onReady());
  expect(view.root.findByType(TaskProgress).props.complete).toBe(true);
  act(() => view.root.findByType(TaskProgress).props.onComplete());
  expect(view.root.findAllByType(TaskProgress)).toHaveLength(0);
});

it('can recover if the downloaded audio fails to decode instead of leaving a broken player', async () => {
  await render();
  act(() => view.root.findByType(AudioPlayback).props.onError());
  expect(button('Tải lại lời giảng')).toBeDefined();
  await act(async () => button('Tải lại lời giảng').props.onPress());
  expect(dispose).toHaveBeenCalledTimes(1);
  expect(downloadNarration).toHaveBeenCalledTimes(2);
  expect(view.root.findByType(AudioPlayback)).toBeDefined();
});

it('clears the old decoded file and completion state before a manually chosen backup is created', async () => {
  await render();
  act(() => view.root.findByType(AudioPlayback).props.onReady());
  act(() => view.root.findByType(TaskProgress).props.onComplete());
  act(() => view.root.findByType(AudioPlayback).props.onError());
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(() => {}));
  await act(async () => button('Dùng giọng dự phòng (âm sắc khác)').props.onPress());
  expect(view.root.findAllByType(AudioPlayback)).toHaveLength(0);
  expect(view.root.findByType(TaskProgress).props.complete).toBe(false);
  expect(downloadNarration).toHaveBeenLastCalledWith({ ...source, useFallback: true }, paragraphs, expect.any(AbortSignal), 'vi-VN-NamMinhNeural', expect.any(Function));
});

it('offers exactly two named voices and replaces the current file without autoplay on switching', async () => {
  await render();
  expect(view.root.findAll(node => node.props.accessibilityRole === 'radio' && node.props.onPress)).toHaveLength(2);
  expect(button('Nam Minh, giọng nam').props.accessibilityState.checked).toBe(true);
  const firstSignal = (downloadNarration as jest.Mock).mock.calls[0][2];
  await act(async () => button('Hoài My, giọng nữ').props.onPress());
  expect(dispose).toHaveBeenCalledTimes(1); expect(firstSignal.aborted).toBe(true);
  expect(downloadNarration).toHaveBeenLastCalledWith(source, paragraphs, expect.any(AbortSignal), 'vi-VN-HoaiMyNeural', expect.any(Function));
  expect(voicePreferences.set).toHaveBeenCalledWith(JSON.stringify({ voiceId: 'vi-VN-HoaiMyNeural' }));
  expect(button('Hoài My, giọng nữ').props.accessibilityState.checked).toBe(true);
  await act(async () => button('Hoài My, giọng nữ').props.onPress());
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('loads the saved female voice before downloading and ignores late audio from the previous voice', async () => {
  (voicePreferences.get as jest.Mock).mockResolvedValue(JSON.stringify({ voiceId: 'vi-VN-HoaiMyNeural' }));
  let finish!: (value: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(downloadNarration).toHaveBeenLastCalledWith(source, paragraphs, expect.any(AbortSignal), 'vi-VN-HoaiMyNeural', expect.any(Function));
  await act(async () => button('Nam Minh, giọng nam').props.onPress());
  await act(async () => finish(new Uint8Array(50)));
  expect(saveNarration).toHaveBeenCalledTimes(1);
  expect(button('Nam Minh, giọng nam').props.accessibilityState.checked).toBe(true);
});

it.each(['{"voiceId":"en-US-EmmaMultilingualNeural"}', 'broken-json'])('recovers safely from an unsupported saved voice: %s', async saved => {
  (voicePreferences.get as jest.Mock).mockResolvedValue(saved);
  await render();
  expect(downloadNarration).toHaveBeenLastCalledWith(source, paragraphs, expect.any(AbortSignal), 'vi-VN-NamMinhNeural', expect.any(Function));
});

it('uses fallback only after an explicit click and identifies its different voice', async () => {
  (downloadNarration as jest.Mock).mockRejectedValueOnce(new Error('provider unavailable'));
  await render();
  expect((downloadNarration as jest.Mock).mock.calls[0][0].useFallback).toBeUndefined();
  await act(async () => button('Dùng giọng dự phòng (âm sắc khác)').props.onPress());
  expect((downloadNarration as jest.Mock).mock.calls[1][0].useFallback).toBe(true);
  expect(text()).toContain('Đang dùng giọng Việt dự phòng');
  expect(view.root.findByType(AudioPlayback)).toBeDefined();
  await act(async () => button('Nam Minh, giọng nam').props.onPress());
  expect((downloadNarration as jest.Mock).mock.calls[2][0].useFallback).toBeUndefined();
});

it('keeps emergency voices out of the normal preparation view and offers them only after an error', async () => {
  let fail!: (error: Error) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise((_resolve, reject) => { fail = reject; }));
  await render();
  expect(button('Dùng giọng đọc trên thiết bị')).toBeUndefined();
  expect(button('Dùng giọng dự phòng (âm sắc khác)')).toBeUndefined();
  await act(async () => fail(new Error('Unavailable')));
  expect(button('Dùng giọng đọc trên thiết bị')).toBeDefined();
  expect(button('Dùng giọng dự phòng (âm sắc khác)')).toBeDefined();
});

it('observes the pending warm download without creating another progress polling loop', async () => {
  jest.useFakeTimers();
  const cache = createNarrationCache();
  let finish!: (bytes: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const warm = cache.acquire(source, paragraphs, 'vi-VN-NamMinhNeural', true);
  const update = (downloadNarration as jest.Mock).mock.calls[0][4];
  update({ phase: 'synthesizing', percent: 45, elapsedMs: 1200, completedChunks: 1, totalChunks: 2, mode: 'online' });
  await act(async () => { view = TestRenderer.create(<NarrationCacheContext.Provider value={cache}><LessonNarration scope="owner:step" source={source} paragraphs={paragraphs} /></NarrationCacheContext.Provider>); });
  expect(view.root.findByType(TaskProgress).props.percent).toBe(45);
  await act(async () => { jest.advanceTimersByTime(3000); });
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(readNarrationProgress).not.toHaveBeenCalled();
  act(() => update({ phase: 'synthesizing', percent: 80, elapsedMs: 4000, completedChunks: 2, totalChunks: 2, mode: 'online' }));
  expect(view.root.findByType(TaskProgress).props.percent).toBe(80);
  await act(async () => { finish(new Uint8Array(50)); });
  expect(view.root.findByType(AudioPlayback)).toBeDefined();
  expect(readNarrationProgress).not.toHaveBeenCalled();
  warm.release(); cache.clear();
});

it('opens and replays the prepared local file with no status request, download or file write', async () => {
  const cache = createNarrationCache();
  const warm = cache.acquire(source, paragraphs, 'vi-VN-NamMinhNeural', true);
  await warm.promise; warm.release();
  const screen = () => <NarrationCacheContext.Provider value={cache}><LessonNarration scope="owner:step" source={source} paragraphs={paragraphs} /></NarrationCacheContext.Provider>;
  await act(async () => { view = TestRenderer.create(screen()); });
  expect(view.root.findByType(AudioPlayback).props.uri).toBe('file:///private-speech.wav');
  act(() => view.unmount());
  await act(async () => { view = TestRenderer.create(screen()); });
  expect(view.root.findByType(AudioPlayback).props.uri).toBe('file:///private-speech.wav');
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(saveNarration).toHaveBeenCalledTimes(1);
  expect(readNarrationProgress).not.toHaveBeenCalled();
  cache.clear();
});
