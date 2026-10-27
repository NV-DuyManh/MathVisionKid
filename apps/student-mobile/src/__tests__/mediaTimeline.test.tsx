import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import Slider from '../features/tutoring/MediaSlider';
import { MediaTimeline } from '../features/tutoring/MediaTimeline';
jest.mock('../features/tutoring/MediaSlider', () => 'Slider');

it('shows a dragged time and commits an arbitrary position only when the slider is released', () => {
  const seek = jest.fn(), start = jest.fn(); let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MediaTimeline title="Nghe giảng" duration={100} currentTime={7} playing={false} onSeek={seek} onScrubStart={start} onToggle={() => {}} />); });
  const slider = () => view.root.findByType(Slider);
  act(() => { slider().props.onSlidingStart(); slider().props.onValueChange(49.25); });
  expect(start).toHaveBeenCalledTimes(1); expect(seek).not.toHaveBeenCalled();
  expect(slider().props.accessibilityValue.now).toBe(49.25);
  act(() => slider().props.onSlidingComplete(49.25)); expect(seek).toHaveBeenCalledWith(49.25);
  act(() => view.unmount());
});
