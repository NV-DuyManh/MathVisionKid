import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { TaskProgress } from '../components/ui/TaskProgress';

const steps = ['Đề đã xác nhận', 'Chuẩn bị các bước học', 'Mở bài học'];
let view: TestRenderer.ReactTestRenderer;
const progress = () => view.root.find(node => node.props.accessibilityRole === 'progressbar');
const render = (activeStep: number, complete = false) => {
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} activeStep={activeStep} complete={complete} />); });
};
afterEach(() => { act(() => view?.unmount()); jest.useRealTimers(); });

it('does not call the last stage complete until its work finishes', () => {
  render(2);
  expect(progress().props.accessibilityValue).toEqual({ min: 0, max: 3, now: 2, text: 'Bước 3/3 · Mở bài học' });
  expect(progress().props['aria-busy']).toBe(true);
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Đang làm' }).length).toBeGreaterThan(0);
  act(() => view.update(<TaskProgress steps={steps} activeStep={2} complete />));
  expect(progress().props.accessibilityValue.now).toBe(3);
  expect(progress().props['aria-busy']).toBe(false);
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Đã xong' }).length).toBeGreaterThan(0);
});

it('never advances tasks just because the request is taking time', () => {
  jest.useFakeTimers(); render(1);
  act(() => jest.advanceTimersByTime(90000));
  expect(progress().props.accessibilityValue.now).toBe(1);
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Sắp tới' }).length).toBeGreaterThan(0);
});

it.each([-10, NaN, 99])('bounds an invalid active step without implying completion: %s', index => {
  render(index);
  expect(progress().props.accessibilityValue.now).toBe(Number.isFinite(index) && index > 0 ? 2 : 0);
  expect(progress().props['aria-busy']).toBe(true);
});
