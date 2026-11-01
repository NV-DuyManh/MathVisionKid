import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, Animated } from 'react-native';
import { CorrectAnswerFeedback } from '../features/tutoring/CorrectAnswerFeedback';

afterEach(() => jest.restoreAllMocks());

it.each([true, false])('respects reduced motion (%s) while retaining the success and manual-continue instruction', async reduced => {
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(reduced);
  const start = jest.fn(), stop = jest.fn();
  const animation = jest.spyOn(Animated, 'timing').mockReturnValue({ start, stop, reset: jest.fn() });
  let view!: TestRenderer.ReactTestRenderer;
  await act(async () => { view = TestRenderer.create(<CorrectAnswerFeedback message="Em làm đúng rồi!" />); });
  expect(JSON.stringify(view.toJSON())).toContain('rồi bấm tiếp tục nhé.');
  if (reduced) {
    expect(animation).not.toHaveBeenCalled();
    expect(view.root.findAllByProps({ testID: 'correct-answer-celebration' })).toHaveLength(0);
  } else {
    expect(animation).toHaveBeenCalledTimes(1);
    expect(animation.mock.calls[0][1].duration).toBe(900);
    expect(start).toHaveBeenCalledTimes(1);
  }
  act(() => view.unmount());
});
