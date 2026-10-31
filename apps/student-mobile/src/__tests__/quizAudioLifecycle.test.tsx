import React from 'react';
import { AppState } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import { AudioPlayback } from '../features/tutoring/AudioPlayback';

const mockStatus: any = { isLoaded: true, duration: 10, currentTime: 0, playing: false };
const mockPlayer: any = { pause: jest.fn(), play: jest.fn(), seekTo: jest.fn().mockResolvedValue(undefined),
  currentTime: 0, playing: false, currentStatus: mockStatus };
const mockNavigation = { addListener: jest.fn(() => jest.fn()) };
jest.mock('expo-router', () => ({ useNavigation: () => mockNavigation }));
jest.mock('expo-audio', () => ({ useAudioPlayer: () => mockPlayer, useAudioPlayerStatus: () => mockStatus }));
jest.mock('../features/tutoring/playbackSession', () => ({ preparePlaybackSession: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/tutoring/MediaTimeline', () => ({ MediaTimeline: 'MediaTimeline' }));
let view: TestRenderer.ReactTestRenderer;
beforeEach(() => { jest.useFakeTimers(); jest.clearAllMocks(); Object.assign(mockStatus, { isLoaded: true, error: undefined, playing: false }); });
afterEach(() => { act(() => view?.unmount()); jest.useRealTimers(); });

it('reports a native loader that never resolves within twelve seconds', async () => {
  mockStatus.isLoaded = false;
  const error = jest.fn();
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///quiz.wav" title="Cách giải" onError={error} />); });
  act(() => jest.advanceTimersByTime(12000));
  expect(error).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByType('MediaTimeline' as any)).toHaveLength(0);
});

it('reports expired/404 audio instead of keeping player loading', async () => {
  mockStatus.error = 'HTTP 404'; mockStatus.isLoaded = false;
  const error = jest.fn();
  await act(async () => { view = TestRenderer.create(<AudioPlayback uri="https://audio.invalid/expired" title="Cách giải" onError={error} />); });
  expect(error).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByType('MediaTimeline' as any)).toHaveLength(0);
});

it('prepares native playback, pauses on blur/background, and ignores a late play after leaving', async () => {
  let background: (state: string) => void = () => {};
  const listener = jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => {
    background = callback; return { remove: jest.fn() };
  });
  try {
    const ready = jest.fn();
    await act(async () => { view = TestRenderer.create(<AudioPlayback uri="file:///quiz.wav" title="Cách giải" onReady={ready} />); });
    expect(ready).toHaveBeenCalled();
    await act(async () => view.root.findByType('MediaTimeline' as any).props.onToggle());
    expect(mockPlayer.play).toHaveBeenCalledTimes(1);
    act(() => background('background'));
    expect(mockPlayer.pause).toHaveBeenCalled();
    const blur = mockNavigation.addListener.mock.calls.find((call: any[]) => call[0] === 'blur') as any;
    act(() => blur[1]());
    expect(mockPlayer.pause).toHaveBeenCalledTimes(2);
    act(() => jest.advanceTimersByTime(6000));
    expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  } finally { listener.mockRestore(); }
});
