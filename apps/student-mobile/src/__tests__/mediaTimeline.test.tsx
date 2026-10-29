import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import Slider from '../features/tutoring/MediaSlider';
import { MediaTimeline } from '../features/tutoring/MediaTimeline';
import { StyleSheet } from 'react-native';
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

it('keeps replay, skip and speed controls named, bounded and visibly focused',()=>{
  const seek=jest.fn(),restart=jest.fn(),rate=jest.fn();let view!:TestRenderer.ReactTestRenderer;
  act(()=>{view=TestRenderer.create(<MediaTimeline title="Nghe giảng" duration={12} currentTime={7} playing={false} onSeek={seek} onScrubStart={()=>{}} onToggle={()=>{}} onRestart={restart} rate={1} onRate={rate}/>);});
  const button=(label:string)=>view.root.findAll(node=>node.props.accessibilityLabel===label&&node.props.onPress)[0];
  act(()=>button('Lùi 10 giây').props.onPress());expect(seek).toHaveBeenLastCalledWith(0);
  act(()=>button('Tiến 10 giây').props.onPress());expect(seek).toHaveBeenLastCalledWith(12);
  act(()=>button('Nghe lại từ đầu').props.onPress());expect(restart).toHaveBeenCalledTimes(1);
  act(()=>button('Tốc độ 1 lần. Bấm để đổi tốc độ').props.onPress());expect(rate).toHaveBeenCalledWith(.8);
  act(()=>button('Phát lời giảng').props.onFocus());
  const control=button('Phát lời giảng');
  expect(StyleSheet.flatten(control.props.style({pressed:false})).outlineWidth).toBe(2);
  act(()=>control.props.onPointerDown());
  expect(StyleSheet.flatten(button('Phát lời giảng').props.style({pressed:false})).outlineWidth).toBeUndefined();
  act(()=>view.unmount());
});
