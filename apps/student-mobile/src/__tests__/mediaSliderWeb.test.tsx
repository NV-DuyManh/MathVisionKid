import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import MediaSlider from '../features/tutoring/MediaSlider.web';

it('commits pointer scrubbing once and ignores the late input event emitted after release', () => {
  const change = jest.fn(), complete = jest.fn(); let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MediaSlider value={7} minimumValue={0} maximumValue={100} onValueChange={change} onSlidingComplete={complete} />); });
  const input = view.root.findByType('input');
  act(() => input.props.onPointerDown());
  act(() => input.props.onChange({ currentTarget: { value: '49.25' } }));
  act(() => input.props.onPointerUp({ currentTarget: { value: '49.25' } }));
  act(() => input.props.onChange({ currentTarget: { value: '7' } }));
  expect(change).toHaveBeenCalledTimes(1); expect(change).toHaveBeenCalledWith(49.25);
  expect(complete).toHaveBeenCalledTimes(1); expect(complete).toHaveBeenCalledWith(49.25);
  act(() => view.unmount());
});
