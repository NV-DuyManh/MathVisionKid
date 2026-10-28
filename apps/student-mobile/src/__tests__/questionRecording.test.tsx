import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState, Platform } from 'react-native';
import { QuestionRecording } from '../features/tutoring/QuestionRecording';
import { AudioPlayback } from '../features/tutoring/AudioPlayback';
import { MediaTimeline } from '../features/tutoring/MediaTimeline';
import { TaskProgress } from '../components/ui/TaskProgress';
import { setAudioModeAsync, setIsAudioActiveAsync } from 'expo-audio';

let mockNativePlaying: boolean | undefined;
const mockPlayer = { get playing() { return mockNativePlaying ?? mockStatus.playing; }, currentTime: 2, get currentStatus() { return mockStatus; }, muted: true, volume: 0, play: jest.fn(), pause: jest.fn(), seekTo: jest.fn().mockResolvedValue(undefined), setPlaybackRate: jest.fn() };
const mockNavigation = { addListener: jest.fn((_event: string, _callback: () => void) => jest.fn()) };
let mockStatus = { isLoaded: true, playing: false, duration: 60, currentTime: 2, didJustFinish: false, error: null as string | null };
jest.mock('expo-audio', () => ({ useAudioPlayer: () => mockPlayer, useAudioPlayerStatus: () => mockStatus,
  setAudioModeAsync: jest.fn().mockResolvedValue(undefined), setIsAudioActiveAsync: jest.fn().mockResolvedValue(undefined) }));
jest.mock('expo-router', () => ({ useNavigation: () => mockNavigation }));
jest.mock('../features/tutoring/MediaTimeline', () => ({ MediaTimeline: () => null }));
let view: TestRenderer.ReactTestRenderer, state: (next: string) => void;
const controls = () => view.root.findByType(MediaTimeline).props;
const render = async () => { await act(async () => { view = TestRenderer.create(<QuestionRecording uri="file:///own-question.m4a" durationMillis={60000} />); }); };
beforeEach(() => {
  jest.replaceProperty(Platform, 'OS', 'android');
  jest.clearAllMocks(); mockPlayer.seekTo.mockReset().mockResolvedValue(undefined);
  (setAudioModeAsync as jest.Mock).mockReset().mockResolvedValue(undefined);
  (setIsAudioActiveAsync as jest.Mock).mockReset().mockResolvedValue(undefined);
  mockPlayer.currentTime = 2; mockPlayer.muted = true; mockPlayer.volume = 0;
  mockNativePlaying = undefined;
  mockStatus = { isLoaded: true, playing: false, duration: 60, currentTime: 2, didJustFinish: false, error: null };
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { state = callback; return { remove: jest.fn() }; });
});
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });

it('does not autoplay and seeks to an arbitrary second without starting paused audio', async () => {
  await render(); expect(mockPlayer.play).not.toHaveBeenCalled();
  await act(async () => controls().onSeek(23.75));
  expect(mockPlayer.seekTo).toHaveBeenLastCalledWith(23.75); expect(mockPlayer.play).not.toHaveBeenCalled();
  await act(async () => controls().onSeek(200)); expect(mockPlayer.seekTo).toHaveBeenLastCalledWith(60);
});

it('resumes from the dragged position only if playback was active before scrubbing', async () => {
  mockStatus.playing = true; await render();
  act(() => controls().onScrubStart()); expect(mockPlayer.pause).toHaveBeenCalledTimes(1);
  mockStatus.playing = false; await act(async () => view.update(<QuestionRecording uri="file:///own-question.m4a" durationMillis={60000} />));
  await act(async () => controls().onSeek(31.25));
  expect(mockPlayer.seekTo).toHaveBeenLastCalledWith(31.25); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
});

it('replays completed audio and pauses on background and blur', async () => {
  mockStatus.currentTime = 60; mockStatus.didJustFinish = true;
  await render(); await act(async () => controls().onToggle());
  expect(mockPlayer.seekTo).toHaveBeenLastCalledWith(0); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  act(() => state('background')); act(() => mockNavigation.addListener.mock.calls[0][1]());
  expect(mockPlayer.pause).toHaveBeenCalledTimes(2);
});

it('does not resume a delayed seek after the question has closed', async () => {
  let finish!: () => void; mockStatus.playing = true;
  mockPlayer.seekTo.mockImplementationOnce(() => new Promise<void>(resolve => { finish = resolve; }));
  await render(); act(() => controls().onSeek(22)); act(() => view.unmount()); await act(async () => finish());
  expect(mockPlayer.play).not.toHaveBeenCalled();
});

it('does not restart audio if the pause reached the player before its rendered status updated', async () => {
  mockStatus.playing = true; mockNativePlaying = false; await render();
  act(() => controls().onScrubStart()); await act(async () => controls().onSeek(28.5));
  expect(mockPlayer.seekTo).toHaveBeenLastCalledWith(28.5); expect(mockPlayer.play).not.toHaveBeenCalled();
});

it('reports decoding errors to the narration owner so the file can be downloaded again', async () => {
  const onError = jest.fn(); mockStatus.error = 'private decoder details';
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///speech.wav" title="Nghe giảng" onError={onError} />); });
  expect(onError).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ')).not.toContain('private decoder details');
});

it('keeps the final audio stage busy until the decoder is loaded and never autoplays it', async () => {
  mockStatus.isLoaded = false;
  const steps = ['Giọng đã chọn', 'Tải âm thanh', 'Mở lời giảng'];
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///speech.wav" title="Nghe giảng" preparationSteps={steps} />); });
  expect(view.root.findByType(TaskProgress).props.activeStep).toBe(2);
  expect(view.root.find(node => node.props.accessibilityRole === 'progressbar').props['aria-busy']).toBe(true);
  expect(mockPlayer.play).not.toHaveBeenCalled();
  mockStatus.isLoaded = true;
  await act(async () => view.update(<AudioPlayback uri="file:///speech.wav" title="Nghe giảng" preparationSteps={steps} />));
  expect(view.root.findByType(TaskProgress).props.complete).toBe(true);
  act(() => view.root.findByType(TaskProgress).props.onComplete());
  expect(view.root.findAllByType(TaskProgress)).toHaveLength(0);
  expect(mockPlayer.play).not.toHaveBeenCalled();
});

it('leaves a stalled decoder after twelve seconds instead of waiting forever', async () => {
  jest.useFakeTimers(); mockStatus.isLoaded = false;
  const onError = jest.fn();
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///stalled.wav" title="Nghe giảng" onError={onError} />); });
  act(() => jest.advanceTimersByTime(12000));
  expect(onError).toHaveBeenCalledTimes(1);
  expect(controls().loading).toBe(false);
  expect(controls().disabled).toBe(true);
  mockStatus.isLoaded = true;
  await act(async () => view.update(<AudioPlayback uri="file:///stalled.wav" title="Nghe giảng" onError={onError} />));
  expect(controls().disabled).toBe(false);
});

it('keeps the previous rate and gives a readable notice if the device rejects a speed change', async () => {
  mockPlayer.setPlaybackRate.mockImplementationOnce(() => { throw new Error('unsupported'); });
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///speech.wav" title="Nghe giảng" />); });
  act(() => controls().onRate(.8));
  expect(controls().rate).toBe(1);
  expect(view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ')).toContain('Chưa đổi được tốc độ');
});

it.each([true, false])('restores native playback before playing a recording=%s or narration', async question => {
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///sound.wav" title="Âm thanh" question={question} />); });
  await act(async () => controls().onToggle());
  expect(setAudioModeAsync).toHaveBeenCalledWith(expect.objectContaining({ allowsRecording: false, playsInSilentMode: true, shouldRouteThroughEarpiece: false, interruptionMode: 'doNotMix' }));
  expect(setIsAudioActiveAsync).toHaveBeenCalledWith(true);
  expect((setIsAudioActiveAsync as jest.Mock).mock.invocationCallOrder[0]).toBeLessThan(mockPlayer.play.mock.invocationCallOrder[0]);
  expect(mockPlayer.muted).toBe(false); expect(mockPlayer.volume).toBe(1);
});

it('keeps Play retryable when native audio setup fails without exposing native details', async () => {
  (setAudioModeAsync as jest.Mock).mockRejectedValueOnce(new Error('private native details'));
  await render(); await act(async () => controls().onToggle());
  expect(mockPlayer.play).not.toHaveBeenCalled();
  const message = view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
  expect(message).toContain('Chưa phát được'); expect(message).not.toContain('private native');
  await act(async () => controls().onToggle()); expect(mockPlayer.play).toHaveBeenCalledTimes(1);
});

it.each(['background', 'close'])('ignores delayed audio setup after %s', async reason => {
  let ready!: () => void;
  (setAudioModeAsync as jest.Mock).mockImplementationOnce(() => new Promise<void>(resolve => { ready = resolve; }));
  await render(); act(() => { void controls().onToggle(); });
  act(() => reason === 'close' ? view.unmount() : state('background'));
  await act(async () => ready()); expect(mockPlayer.play).not.toHaveBeenCalled();
});

it('reports a silent no-start instead of leaving Play without feedback, and allows retry', async () => {
  jest.useFakeTimers(); await render(); await act(async () => controls().onToggle());
  act(() => jest.advanceTimersByTime(6000));
  expect(mockPlayer.pause).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ')).toContain('bấm phát để thử lại');
  await act(async () => controls().onToggle()); mockPlayer.currentTime = 3;
  act(() => jest.advanceTimersByTime(6000)); expect(mockPlayer.pause).toHaveBeenCalledTimes(1);
});

it('clears the no-start check when the pupil pauses or closes playback', async () => {
  jest.useFakeTimers(); await render(); await act(async () => controls().onToggle());
  mockNativePlaying = true;
  await act(async () => controls().onToggle());
  act(() => jest.advanceTimersByTime(6000)); expect(mockPlayer.pause).toHaveBeenCalledTimes(1);
  mockNativePlaying = false;
  await act(async () => controls().onToggle()); act(() => view.unmount());
  act(() => jest.advanceTimersByTime(6000)); expect(mockPlayer.pause).toHaveBeenCalledTimes(1);
});
