import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, Animated } from 'react-native';
import { RecognitionProgress } from '../RecognitionProgress';

test('long recognition has an honest horizontal bar, elapsed time and a usable way back', async () => {
  jest.useFakeTimers();
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
  const loop = jest.spyOn(Animated, 'loop');
  const clearTimer = jest.spyOn(global, 'clearInterval');
  const cancel = jest.fn();
  let renderer!: TestRenderer.ReactTestRenderer;
  try {
    await act(async () => { renderer = TestRenderer.create(<RecognitionProgress title="Đang tìm các dòng chữ" description="Đang đọc ảnh" onCancel={cancel} />); });
    const progress = renderer.root.find(node => node.props.accessibilityRole === 'progressbar');
    expect(progress.props.accessibilityState.busy).toBe(true);
    expect(progress.props.accessibilityValue).toBeUndefined();
    expect(renderer.root.findAllByType('ActivityIndicator' as any)).toHaveLength(0);
    expect(loop).not.toHaveBeenCalled();
    act(() => { jest.advanceTimersByTime(26000); });
    const text = renderer.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(text).toContain('26');
    expect(text).toContain('Ảnh nhiều dòng');
    expect(text).not.toContain('%');
    act(() => { renderer.root.find(node => node.props.accessibilityRole === 'button').props.onPress(); });
    expect(cancel).toHaveBeenCalledTimes(1);
  } finally {
    act(() => renderer?.unmount());
    expect(clearTimer).toHaveBeenCalled();
    jest.clearAllTimers();
    jest.useRealTimers();
    jest.restoreAllMocks();
  }
});
