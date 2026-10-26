import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AccessibilityInfo, Animated } from 'react-native';
import { RecognitionProgress } from '../features/recognition/components/RecognitionProgress';

const steps = ['Chuẩn bị các bước học', 'Chuẩn bị lời giảng', 'Sẵn sàng học'];
let view: TestRenderer.ReactTestRenderer;
let loop: jest.SpyInstance;
const progress = () => view.root.findAll(node => node.props.accessibilityRole === 'progressbar')[0];
const stage = (label: string) => view.root.findAll(node => typeof node.type === 'string' && node.props.accessibilityLabel === label);
const render = async (props = {}) => {
  await act(async () => { view = TestRenderer.create(<RecognitionProgress title="Chuẩn bị bài học" description="Mình chuẩn bị từng phần cho em." {...props} />); });
};

beforeEach(() => {
  jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
  jest.spyOn(AccessibilityInfo, 'addEventListener').mockReturnValue({ remove: jest.fn() } as any);
  loop = jest.spyOn(Animated, 'loop');
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('advances only with reported stages and keeps the current stage separate from completed work', async () => {
  await render({ steps, activeStep: 0 });
  expect(progress().props.accessibilityValue).toEqual(expect.objectContaining({ min: 0, max: 3, now: 0 }));
  expect(stage('Chuẩn bị các bước học. Đang làm')).toHaveLength(1);
  expect(stage('Chuẩn bị lời giảng. Sắp tới')).toHaveLength(1);
  await act(async () => view.update(<RecognitionProgress title="Chuẩn bị bài học" description="Đang chuẩn bị lời đọc." steps={steps} activeStep={1} />));
  expect(progress().props.accessibilityValue.now).toBe(1);
  expect(stage('Chuẩn bị các bước học. Đã xong')).toHaveLength(1);
  expect(stage('Chuẩn bị lời giảng. Đang làm')).toHaveLength(1);
  expect(loop).not.toHaveBeenCalled();
});

it('marks the ready state complete and retains cancellation and the supplied image', async () => {
  const onCancel = jest.fn();
  await render({ steps, activeStep: 2, onCancel, cancelLabel: 'Dừng chuẩn bị', imageUri: 'file:///private/question.png' });
  expect(progress().props.accessibilityState.busy).toBe(false);
  expect(progress().props.accessibilityValue).toEqual(expect.objectContaining({ now: 3, max: 3 }));
  expect(view.root.findAll(node => typeof node.type === 'string' && node.props.accessibilityLabel?.endsWith('. Đã xong'))).toHaveLength(3);
  const cancel = view.root.findAll(node => node.props.accessibilityLabel === 'Dừng chuẩn bị' && node.props.onPress)[0];
  act(() => cancel.props.onPress()); expect(onCancel).toHaveBeenCalledTimes(1);
  expect(view.root.findAll(node => node.props.source?.uri === 'file:///private/question.png').length).toBeGreaterThan(0);
  expect(loop).not.toHaveBeenCalled();
});

it('shows audio finished before the lesson without claiming the pending lesson is complete', async () => {
  await render({ steps, activeStep: 0, completedSteps: [1, 1, -1, 8] });
  expect(progress().props.accessibilityValue).toEqual(expect.objectContaining({ now: 1, max: 3 }));
  expect(progress().props.accessibilityValue.text).toContain('Đã xong 1/3 phần');
  expect(stage('Chuẩn bị các bước học. Đang làm')).toHaveLength(1);
  expect(stage('Chuẩn bị lời giảng. Đã xong')).toHaveLength(1);
  expect(stage('Sẵn sàng học. Sắp tới')).toHaveLength(1);
  await act(async () => view.update(<RecognitionProgress title="Chuẩn bị bài học" description="Đang chuẩn bị lời đọc." steps={steps} activeStep={1} completedSteps={[0]} />));
  expect(stage('Chuẩn bị các bước học. Đã xong')).toHaveLength(1);
  expect(stage('Chuẩn bị lời giảng. Đang làm')).toHaveLength(1);
  expect(progress().props.accessibilityValue.now).toBe(1);
  expect(loop).not.toHaveBeenCalled();
});

it('never marks a completed active index as current and still completes all stages when ready', async () => {
  await render({ steps, activeStep: 1, completedSteps: [1] });
  expect(stage('Chuẩn bị lời giảng. Đã xong')).toHaveLength(1);
  expect(stage('Chuẩn bị lời giảng. Đang làm')).toHaveLength(0);
  expect(progress().props.accessibilityValue.text).toContain('Đang chuẩn bị các phần còn lại');
  await act(async () => view.update(<RecognitionProgress title="Chuẩn bị bài học" description="Sẵn sàng." steps={steps} activeStep={2} completedSteps={[1]} />));
  expect(progress().props.accessibilityValue.now).toBe(3);
  expect(progress().props.accessibilityState.busy).toBe(false);
  expect(view.root.findAll(node => typeof node.type === 'string' && node.props.accessibilityLabel?.endsWith('. Đã xong'))).toHaveLength(3);
});

it('keeps unreported work indeterminate and stops its old sweep when stages become available', async () => {
  const stop = jest.fn(); loop.mockReturnValue({ start: jest.fn(), stop });
  await render();
  expect(progress().props.accessibilityValue).toBeUndefined();
  expect(loop).toHaveBeenCalledTimes(1);
  await act(async () => view.update(<RecognitionProgress title="Chuẩn bị bài học" description="Đang soạn bài." steps={steps} activeStep={0} />));
  expect(stop).toHaveBeenCalledTimes(1);
  expect(loop).toHaveBeenCalledTimes(1);
  expect(progress().props.accessibilityValue.now).toBe(0);
});
