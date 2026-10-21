import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState } from 'react-native';
import { LessonVideo } from '../features/tutoring/LessonVideo';
const mockPlayers: any[] = [];
let mockBlur: () => void;
const mockNavigation = { addListener: jest.fn((_event, callback) => { mockBlur = callback; return jest.fn(); }) };
jest.mock('expo-video', () => ({ useVideoPlayer: (_source: unknown, setup: (player: any) => void) => {
  const React = require('react');
  const [player] = React.useState(() => {
    const item = { released: false, play: jest.fn(), pause: jest.fn(() => { if(item.released) throw new Error('Native player already released'); }), seekBy: jest.fn(), currentTime: 0, loop: false };
    setup(item); mockPlayers.push(item); return item;
  });
  React.useEffect(() => () => { player.released = true; }, [player]);
  return player;
}, VideoView: 'VideoView' }));
jest.mock('expo', () => ({ useEvent: () => ({ isPlaying: false, status: 'readyToPlay' }) }));
jest.mock('expo-router', () => ({ useNavigation: () => mockNavigation, useFocusEffect: (fn: () => void) => require('react').useEffect(fn, [fn]) }));
let view: TestRenderer.ReactTestRenderer, changeState: (state: string) => void;
const button = (label: string) => view.root.findAll(n => n.props.accessibilityLabel === label && n.props.onPress)[0];
beforeEach(() => { jest.clearAllMocks(); mockPlayers.length = 0; jest.spyOn(AppState, 'addEventListener').mockImplementation((_, fn: any) => { changeState = fn; return { remove: jest.fn() }; }); });
afterEach(() => { if(view) act(() => view.unmount()); jest.restoreAllMocks(); });
it('loads a local, captioned clip without autoplay and pauses on background', () => {
  act(() => { view = TestRenderer.create(<LessonVideo reading={false} />); });
  const mockPlayer = mockPlayers[0];
  expect(mockPlayer.play).not.toHaveBeenCalled();
  act(() => button('Phát video minh họa').props.onPress());
  expect(mockPlayer.play).toHaveBeenCalledTimes(1);
  act(() => changeState('background'));
  expect(mockPlayer.pause).toHaveBeenCalled();
  act(() => button('Xem lại từ đầu').props.onPress());
  expect(mockPlayer.currentTime).toBe(0);
  expect(mockPlayer.play).toHaveBeenCalledTimes(1);
});
it('offers only the reading example while learning to understand a problem', () => {
  act(() => { view = TestRenderer.create(<LessonVideo reading />); });
  expect(button('Vì sao cùng kích thước?')).toBeUndefined();
  expect(view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ')).toContain('Tóm tắt đề, chưa cần tính');
});

it('leaves unmount disposal to the SDK without pausing an already released native player', () => {
  act(() => { view = TestRenderer.create(<LessonVideo reading={false} />); });
  const mockPlayer = mockPlayers[0];
  mockPlayer.pause.mockClear();
  act(() => view.unmount());
  expect(mockPlayer.pause).not.toHaveBeenCalled();
  expect(mockPlayer.released).toBe(true);
});

it('releases the old clip when switching and pauses the new clip on route blur', () => {
  act(() => { view = TestRenderer.create(<LessonVideo reading={false} />); });
  act(() => button('Vì sao cùng kích thước?').props.onPress());
  expect(mockPlayers[0].released).toBe(true);
  expect(mockPlayers[0].pause).not.toHaveBeenCalled();
  act(() => mockBlur());
  expect(mockPlayers[1].pause).toHaveBeenCalledTimes(1);
});
