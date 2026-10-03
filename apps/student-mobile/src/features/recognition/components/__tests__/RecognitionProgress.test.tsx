import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, Animated } from 'react-native';
import { RecognitionProgress } from '../RecognitionProgress';

test('long recognition keeps the real image, honest bar and cancellation without a stopwatch', async () => {
  jest.useFakeTimers();
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
  const loop = jest.spyOn(Animated, 'loop');
  const timer = jest.spyOn(global, 'setInterval');
  const cancel = jest.fn();
  let renderer!: TestRenderer.ReactTestRenderer;
  try {
    await act(async () => { renderer = TestRenderer.create(<RecognitionProgress title="Đang tìm các dòng chữ" description="Đang đọc ảnh" imageUri="file:///selected-page.png" onCancel={cancel} cancelLabel="Quay lại kiểm tra" />); });
    const progress = renderer.root.find(node => node.props.accessibilityRole === 'progressbar');
    expect(progress.props.accessibilityState.busy).toBe(true);
    expect(progress.props.accessibilityValue).toBeUndefined();
    expect(renderer.root.findAllByType('ActivityIndicator' as any)).toHaveLength(0);
    expect(loop).not.toHaveBeenCalled();
    expect(renderer.root.findAllByType('Image' as any).some(node => node.props.source?.uri === 'file:///selected-page.png')).toBe(true);
    act(() => { jest.advanceTimersByTime(26000); });
    const text = renderer.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(timer).not.toHaveBeenCalled();
    expect(text).not.toMatch(/Đã chờ|giây|26|phút/);
    expect(text).not.toContain('%');
    const button = renderer.root.find(node => node.props.accessibilityRole === 'button');
    expect(button.props.accessibilityLabel).toBe('Quay lại kiểm tra');
    act(() => { button.props.onPress(); });
    expect(cancel).toHaveBeenCalledTimes(1);
  } finally {
    act(() => renderer?.unmount());
    jest.clearAllTimers();
    jest.useRealTimers();
    jest.restoreAllMocks();
  }
});
