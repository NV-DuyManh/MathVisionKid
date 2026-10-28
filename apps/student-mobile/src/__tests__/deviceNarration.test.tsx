import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { DeviceNarration } from '../features/tutoring/DeviceNarration';
import { AppButton } from '../components/ui/AppButton';
import { getAvailableVoicesAsync, speak, stop } from '../features/tutoring/speechOutput';
jest.mock('../features/tutoring/speechOutput', () => ({ getAvailableVoicesAsync: jest.fn(), speak: jest.fn(), stop: jest.fn().mockResolvedValue(undefined) }));
jest.mock('../features/tutoring/playbackSession', () => ({ preparePlaybackSession: jest.fn().mockResolvedValue(undefined) }));
const mockNavigation = { addListener: jest.fn(() => jest.fn()) };
jest.mock('expo-router', () => ({ useNavigation: () => mockNavigation }));
let view: TestRenderer.ReactTestRenderer;
beforeEach(() => {
  jest.clearAllMocks();
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ identifier: 'vi-test', language: 'vi-VN', name: 'Vietnamese', quality: 'Default' }]);
});
afterEach(() => { act(() => view?.unmount()); jest.useRealTimers(); });
const render = async (onFinished = jest.fn()) => {
  await act(async () => { view = TestRenderer.create(<DeviceNarration paragraphs={['Em cộng 1/3 với 2/5.']} onFinished={onFinished} />); });
};
it('uses a Vietnamese device voice only on a click and stops on close', async () => {
  const done = jest.fn(); await render(done);
  expect(speak).not.toHaveBeenCalled();
  await act(async () => view.root.findByType(AppButton).props.onPress());
  expect(speak).toHaveBeenCalledWith(expect.stringContaining('1 phần 3'), expect.objectContaining({ voice: 'vi-test' }));
  const callbacks = (speak as jest.Mock).mock.calls[0][1];
  act(() => callbacks.onStart()); act(() => callbacks.onDone()); expect(done).toHaveBeenCalledTimes(1);
  act(() => view.unmount()); expect(stop).toHaveBeenCalled();
});
it('does not substitute English when the device has no Vietnamese voice', async () => {
  (getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ identifier: 'en', language: 'en-US', name: 'English' }]);
  await render(); expect(view.root.findAllByType(AppButton)).toHaveLength(0); expect(speak).not.toHaveBeenCalled();
});
it('reports a device engine that never starts instead of hanging', async () => {
  jest.useFakeTimers(); await render();
  await act(async () => view.root.findByType(AppButton).props.onPress());
  act(() => jest.advanceTimersByTime(8000));
  const words = view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
  expect(words).toContain('Giọng thiết bị chưa phát được'); expect(stop).toHaveBeenCalled();
});
