import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, AppState } from 'react-native';
import { TaskProgress } from '../components/ui/TaskProgress';

const steps = ['Đề đã xác nhận', 'Chuẩn bị các bước học', 'Mở bài học'];
let view: TestRenderer.ReactTestRenderer;
const progress = () => view.root.find(node => node.props.accessibilityRole === 'progressbar');
const text = () => view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
const render = (activeStep: number, complete = false) => {
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} activeStep={activeStep} complete={complete} />); });
};
beforeEach(() => { jest.useFakeTimers(); jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true); });
afterEach(() => { act(() => view?.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });

it('fills to 100 only after actual readiness and marks the last task complete', () => {
  render(2);
  expect(progress().props.accessibilityValue.now).toBeLessThan(100);
  expect(progress().props['aria-busy']).toBe(true);
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Đang làm' }).length).toBeGreaterThan(0);
  act(() => view.update(<TaskProgress steps={steps} activeStep={2} complete />));
  expect(progress().props.accessibilityValue.now).toBe(100);
  expect(progress().props['aria-busy']).toBe(false);
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Đã xong' }).length).toBeGreaterThan(0);
});

it('creeps smoothly but never invents completed tasks, even during a long wait', () => {
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} activeStep={1} timeoutSeconds={150} />); });
  const values = [progress().props.accessibilityValue.now];
  for (let i = 0; i < 100; i++) { act(() => jest.advanceTimersByTime(1000)); values.push(progress().props.accessibilityValue.now); }
  expect(values.every((value, i) => value >= (values[i - 1] ?? 0) && value <= 85)).toBe(true);
  expect(new Set(values.slice(0, 10)).size).toBeGreaterThan(8);
  expect(values[100]).toBeGreaterThanOrEqual(84);
  expect(progress().props.accessibilityValue.text).toContain('Ước tính');
  expect(view.root.findAllByProps({ accessibilityLabel: 'Mở bài học. Sắp tới' }).length).toBeGreaterThan(0);
});

it('does not calculate its percentage from the timeout', () => {
  act(() => { view = TestRenderer.create(<><TaskProgress steps={steps} timeoutSeconds={45} /><TaskProgress steps={steps} timeoutSeconds={150} /></>); });
  act(() => jest.advanceTimersByTime(9000));
  const bars = view.root.findAll(node => node.props?.accessibilityRole === 'progressbar');
  expect(bars[0].props.accessibilityValue.now).toBe(bars[1].props.accessibilityValue.now);
  expect(text()).toContain('Đã chờ 9s');
});

it.each([-10, NaN, 99])('bounds an invalid active step without implying completion: %s', index => {
  render(index);
  expect(progress().props.accessibilityValue.text).toContain(`Bước ${Number.isFinite(index) && index > 0 ? 3 : 1}/3`);
  expect(progress().props['aria-busy']).toBe(true);
});

it('accepts real milestones without moving backwards or letting the server finish the decoder', () => {
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} percent={45} />); });
  expect(progress().props.accessibilityValue.now).toBe(45);
  act(() => view.update(<TaskProgress steps={steps} percent={20} />));
  expect(progress().props.accessibilityValue.now).toBe(45);
  act(() => view.update(<TaskProgress steps={steps} percent={100} />));
  expect(progress().props.accessibilityValue.now).toBe(99);
  expect(progress().props['aria-busy']).toBe(true);
});

it('freezes the estimate and reports timeout once instead of pretending success', () => {
  const onTimeout = jest.fn();
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} activeStep={1} timeoutSeconds={10} onTimeout={onTimeout} detail="Đã tạo 1/2 đoạn" />); });
  act(() => jest.advanceTimersByTime(4000));
  expect(text()).toContain('Đã chờ 4s'); expect(text()).toContain('Đã tạo 1/2 đoạn');
  act(() => jest.advanceTimersByTime(6000));
  const value = progress().props.accessibilityValue.now;
  act(() => jest.advanceTimersByTime(20000));
  expect(progress().props.accessibilityValue.now).toBe(value);
  expect(onTimeout).toHaveBeenCalledTimes(1);
  expect(text()).toContain('Chờ lâu hơn dự kiến');
  expect(progress().props['aria-busy']).toBe(true);
});

it('pauses visual updates in background, catches up on foreground and removes listeners', () => {
  let change!: (state: string) => void; const remove = jest.fn();
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { change = callback; return { remove }; });
  render(1); act(() => jest.advanceTimersByTime(1000));
  const value = progress().props.accessibilityValue.now;
  act(() => change('background')); act(() => jest.advanceTimersByTime(5000));
  expect(progress().props.accessibilityValue.now).toBe(value);
  act(() => change('active'));
  expect(progress().props.accessibilityValue.now).toBeGreaterThan(value);
  expect(text()).toContain('Đã chờ 6s');
  act(() => view.unmount()); expect(remove).toHaveBeenCalledTimes(1);
});

it('gives the final fill time to finish, then calls the owner once and cancels on close', async () => {
  (AccessibilityInfo.isReduceMotionEnabled as jest.Mock).mockResolvedValue(false);
  const onComplete = jest.fn();
  await act(async () => { view = TestRenderer.create(<TaskProgress steps={steps} onComplete={onComplete} />); });
  await act(async () => view.update(<TaskProgress steps={steps} complete onComplete={onComplete} />));
  expect(progress().props.accessibilityValue.now).toBe(100);
  act(() => jest.advanceTimersByTime(219)); expect(onComplete).not.toHaveBeenCalled();
  act(() => jest.advanceTimersByTime(1)); expect(onComplete).toHaveBeenCalledTimes(1);
  act(() => view.update(<TaskProgress key="next" steps={steps} complete onComplete={onComplete} />));
  act(() => view.unmount()); act(() => jest.advanceTimersByTime(1000));
  expect(onComplete).toHaveBeenCalledTimes(1);
});

it('honors reduced motion and supports a new completion without reusing the old notification', () => {
  const onComplete = jest.fn();
  act(() => { view = TestRenderer.create(<TaskProgress steps={steps} complete onComplete={onComplete} />); });
  act(() => jest.advanceTimersByTime(0)); expect(onComplete).toHaveBeenCalledTimes(1);
  act(() => view.update(<TaskProgress steps={steps} onComplete={onComplete} />));
  act(() => view.update(<TaskProgress steps={steps} complete onComplete={onComplete} />));
  act(() => jest.advanceTimersByTime(0)); expect(onComplete).toHaveBeenCalledTimes(2);
});
