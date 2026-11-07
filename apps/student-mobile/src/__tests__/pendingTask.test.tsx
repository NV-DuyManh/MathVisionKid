import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, ActivityIndicator, Animated, AppState, StyleSheet } from 'react-native';
import { AppButton } from '../components/ui/AppButton';
import { PendingTask } from '../components/ui/PendingTask';
import { COLORS } from '../constants/theme';

let view: TestRenderer.ReactTestRenderer;
beforeEach(() => { jest.useFakeTimers(); jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true); });
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });

it('shows the actual pending action with an active indicator while preventing duplicate clicks', async () => {
  const press = jest.fn();
  await act(async () => { view = TestRenderer.create(<AppButton title="Thử thách nâng sao" loadingTitle="Đang chuẩn bị câu mới…" onPress={press} disabled loading />); });
  const control = view.root.find(n => n.props.accessibilityRole === 'button');
  expect(control.props.accessibilityLabel).toBe('Thử thách nâng sao');
  expect(control.props.accessibilityState).toEqual({ disabled: true, busy: true });
  expect(StyleSheet.flatten(control.props.style).backgroundColor).toBe(COLORS.primary);
  expect(view.root.findAllByType(ActivityIndicator)).toHaveLength(1);
  expect(view.root.findAllByType('Text' as any).some(n => n.props.children === 'Đang chuẩn bị câu mới…')).toBe(true);
  expect(press).not.toHaveBeenCalled();
  act(() => view.update(<AppButton title="Thử thách nâng sao" onPress={press} />));
  expect(view.root.findAllByType(ActivityIndicator)).toHaveLength(0);
  expect(view.root.find(n => n.props.accessibilityRole === 'button').props.accessibilityState.busy).toBe(false);
});

it('reports elapsed waiting without inventing a percentage and stops timers on close', async () => {
  const interval = jest.spyOn(global, 'setInterval'), clear = jest.spyOn(global, 'clearInterval');
  await act(async () => { view = TestRenderer.create(<PendingTask title="Đang tạo câu mới" detail="Em có thể xem bài cũ." />); });
  act(() => jest.advanceTimersByTime(5000));
  expect(view.root.findAllByProps({ accessibilityLabel: 'Đã chờ 5 giây' }).length).toBeGreaterThan(0);
  const progress = view.root.find(n => n.props.accessibilityRole === 'progressbar');
  expect(progress.props.accessibilityState.busy).toBe(true);
  expect(progress.props.accessibilityValue).toBeUndefined();
  act(() => view.unmount());
  expect(clear).toHaveBeenCalledWith(interval.mock.results[0].value);
});

it('runs the lightweight animation only when visible and motion is allowed', async () => {
  (AccessibilityInfo.isReduceMotionEnabled as jest.Mock).mockResolvedValue(false);
  const listeners: ((state: string) => void)[] = [];
  const change = (state: string) => listeners.forEach(listener => listener(state));
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, listener: any) => { listeners.push(listener); return { remove: jest.fn() }; });
  const start = jest.fn(), stop = jest.fn();
  const interval = jest.spyOn(global, 'setInterval'), clear = jest.spyOn(global, 'clearInterval');
  const loop = jest.spyOn(Animated, 'loop').mockReturnValue({ start, stop, reset: jest.fn() } as any);
  await act(async () => { view = TestRenderer.create(<PendingTask title="Đang tạo" detail="Đang kiểm tra" />); });
  act(() => view.root.find(n => !!n.props.onLayout).props.onLayout({ nativeEvent: { layout: { width: 320 } } }));
  expect(loop).toHaveBeenCalledTimes(1); expect(start).toHaveBeenCalledTimes(1);
  act(() => change('background'));
  expect(stop).toHaveBeenCalledTimes(1);
  expect(clear).toHaveBeenCalledWith(interval.mock.results[0].value);
  act(() => change('active'));
  expect(start).toHaveBeenCalledTimes(2);
  act(() => view.unmount());
  expect(stop).toHaveBeenCalledTimes(2);
});
