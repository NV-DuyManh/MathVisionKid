import React from 'react';
import { act, create, ReactTestRenderer } from 'react-test-renderer';
import AssignedSubmission from '../AssignedSubmission.web';
import apiClient from '../../../services/api/apiClient';
import { exportCropImage } from '../../../utils/cropRotation.web';

jest.mock('../../../services/api/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() } }));
jest.mock('../../../utils/cropRotation.web', () => ({ exportCropImage: jest.fn() }));
let mockRouteFocused = true;
jest.mock('expo-router', () => ({ useFocusEffect: (callback: () => void) => {
  const React = require('react');
  React.useEffect(() => mockRouteFocused ? callback() : undefined, [callback, mockRouteFocused]);
} }));

const waiting = { imageVersion: 1, status: 'AWAITING_REVIEW', score: null, feedback: null };
let tree: ReactTestRenderer;
const listeners = new Map<string, () => void>();
const originalDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
const originalWindow = Object.getOwnPropertyDescriptor(globalThis, 'window');

beforeEach(() => {
  jest.useFakeTimers();
  listeners.clear();
  mockRouteFocused = true;
  const events = { addEventListener: (name: string, fn: () => void) => listeners.set(name, fn),
    removeEventListener: (name: string) => listeners.delete(name) };
  Object.defineProperty(globalThis, 'window', { configurable: true, value: { ...events, setTimeout, clearTimeout } });
  Object.defineProperty(globalThis, 'document', { configurable: true, value: { ...events, visibilityState: 'visible' } });
  (apiClient.get as jest.Mock).mockReset().mockResolvedValue({ data: waiting });
  (apiClient.post as jest.Mock).mockReset().mockResolvedValue({});
});
afterEach(async () => {
  if (tree) await act(async () => tree.unmount());
  jest.useRealTimers();
  if (originalDocument) Object.defineProperty(globalThis, 'document', originalDocument);
  else Reflect.deleteProperty(globalThis, 'document');
  if (originalWindow) Object.defineProperty(globalThis, 'window', originalWindow);
  else Reflect.deleteProperty(globalThis, 'window');
});

test('waiting Student receives retake and released grade without reloading, then stops polling', async () => {
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { ...waiting, status: 'RETAKE_REQUESTED', retakeInstruction: 'Chụp rõ phần cuối nhé' } });
  await act(async () => { jest.advanceTimersByTime(5000); });
  expect(JSON.stringify(tree.toJSON())).toContain('Chụp rõ phần cuối nhé');
  (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { ...waiting, status: 'GRADE_RELEASED', score: 8, feedback: 'Làm tốt' } });
  await act(async () => { listeners.get('focus')?.(); });
  expect(JSON.stringify(tree.toJSON())).toContain('Làm tốt');
  const calls = (apiClient.get as jest.Mock).mock.calls.length;
  await act(async () => { jest.advanceTimersByTime(120000); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls);
});

test('focus events coalesce while a status request is in flight; leaving cancels it', async () => {
  let resolve!: (value: unknown) => void;
  (apiClient.get as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  await act(async () => { listeners.get('focus')?.(); listeners.get('visibilitychange')?.(); });
  expect(apiClient.get).toHaveBeenCalledTimes(1);
  const signal = (apiClient.get as jest.Mock).mock.calls[0][1].signal;
  await act(async () => tree.unmount());
  expect(signal.aborted).toBe(true);
  await act(async () => { resolve({ data: waiting }); jest.advanceTimersByTime(120000); });
  expect(apiClient.get).toHaveBeenCalledTimes(1);
});

test('hidden tabs pause polling and the bounded polling window resumes on focus', async () => {
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
  await act(async () => { listeners.get('visibilitychange')?.(); jest.advanceTimersByTime(120000); });
  expect(apiClient.get).toHaveBeenCalledTimes(1);
  Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' });
  await act(async () => { listeners.get('visibilitychange')?.(); });
  for (let i = 0; i < 20; i++) await act(async () => { jest.advanceTimersByTime(60000); });
  expect(JSON.stringify(tree.toJSON())).toContain('Em có thể bấm Cập nhật bài của em để kiểm tra lại.');
  const calls = (apiClient.get as jest.Mock).mock.calls.length;
  await act(async () => { jest.advanceTimersByTime(3600000); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls);
  await act(async () => { listeners.get('focus')?.(); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls + 1);
  expect(JSON.stringify(tree.toJSON())).not.toContain('Em có thể bấm Cập nhật bài của em để kiểm tra lại.');
});

test('a late response from the previous screen cannot overwrite the next assignment', async () => {
  let resolveOld!: (value: unknown) => void;
  (apiClient.get as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolveOld = done; }));
  await act(async () => { tree = create(<AssignedSubmission key="A" assignmentId="A" maxScore={10} />); });
  (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { ...waiting, status: 'GRADE_RELEASED', score: 4, feedback: 'Only B' } });
  await act(async () => { tree.update(<AssignedSubmission key="B" assignmentId="B" maxScore={10} />); });
  await act(async () => { resolveOld({ data: { ...waiting, status: 'GRADE_RELEASED', feedback: 'Private A' } }); });
  expect(JSON.stringify(tree.toJSON())).toContain('Only B');
  expect(JSON.stringify(tree.toJSON())).not.toContain('Private A');
});

test('invalid selected files show an actionable error before making a preview or privacy request', async () => {
  const createUrl = jest.fn(() => 'blob:invalid');
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createUrl });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: jest.fn() });
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  const input = tree.root.findAllByType('input').find(item => item.props.type === 'file')!;
  await act(async () => { input.props.onChange({ currentTarget: { files: [{ type: 'text/plain', size: 200 }], value: '' } }); });
  expect(JSON.stringify(tree.toJSON())).toContain('Em hãy chọn ảnh');
  expect(createUrl).not.toHaveBeenCalled();
  expect(apiClient.post).not.toHaveBeenCalled();
});

test('an inactive Expo tab stops polling and refetches when the route becomes active again', async () => {
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  mockRouteFocused = false;
  await act(async () => { tree.update(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  await act(async () => { jest.advanceTimersByTime(120000); });
  expect(apiClient.get).toHaveBeenCalledTimes(1);
  (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { ...waiting, status: 'RETAKE_REQUESTED', retakeInstruction: 'Welcome back' } });
  mockRouteFocused = true;
  await act(async () => { tree.update(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
  expect(JSON.stringify(tree.toJSON())).toContain('Welcome back');
});

test('status retry cannot interrupt an image check that is still running', async () => {
  let finishImage!: (error: Error) => void;
  (exportCropImage as jest.Mock).mockImplementationOnce(() => new Promise((_, reject) => { finishImage = reject; }));
  const createUrl = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:synthetic');
  try {
    await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
    const input = tree.root.findAllByType('input').find(item => item.props.type === 'file')!;
    await act(async () => { input.props.onChange({ currentTarget: { files: [{ type: 'image/png', size: 200 }], value: '' } }); });
    await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Kiểm tra ảnh')!.props.onClick(); });
    (apiClient.get as jest.Mock).mockRejectedValueOnce(new Error('Offline'));
    await act(async () => { jest.advanceTimersByTime(5000); });
    const retry = () => tree.root.findAllByProps({ accessibilityRole: 'button' }).find(node => node.props.onPress && node.props.children.props.children === 'Thử lại')!;
    expect(retry().props.disabled).toBe(true);
    await act(async () => { finishImage(new Error('Image check completed with an error')); });
    expect(retry().props.disabled).toBe(false);
    await act(async () => { retry().props.onPress(); });
    expect(JSON.stringify(tree.toJSON())).not.toContain('Chưa kết nối được');
  } finally { createUrl.mockRestore(); }
});

test('definitive unavailability clears a loaded image and result while a transport error preserves them', async () => {
  const createUrl = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:submitted');
  const revokeUrl = jest.spyOn(URL, 'revokeObjectURL');
  try {
    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { ...waiting, status: 'GRADE_RELEASED', score: 8, feedback: 'Synthetic feedback' } });
    await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} />); });
    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: {} });
    await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Xem ảnh đã gửi')!.props.onClick(); });
    expect(tree.root.findByType('img').props.src).toBe('blob:submitted');
    (apiClient.get as jest.Mock).mockRejectedValueOnce(new Error('Offline'));
    await act(async () => { listeners.get('focus')?.(); });
    expect(tree.root.findByType('img').props.src).toBe('blob:submitted');
    expect(JSON.stringify(tree.toJSON())).toContain('Synthetic feedback');
    (apiClient.get as jest.Mock).mockRejectedValueOnce({ isAxiosError: true, response: { status: 404 } });
    await act(async () => { listeners.get('focus')?.(); });
    expect(tree.root.findAllByType('img')).toHaveLength(0);
    expect(revokeUrl).toHaveBeenCalledWith('blob:submitted');
    expect(JSON.stringify(tree.toJSON())).not.toContain('Synthetic feedback');
    expect(JSON.stringify(tree.toJSON())).toContain('Bài này không còn khả dụng');
  } finally { createUrl.mockRestore(); revokeUrl.mockRestore(); }
});

test.each([
  ['privacy-check', 403], ['privacy-check', 404], ['privacy-check', 503],
  ['upload', 403], ['upload', 404], ['upload', 503],
])('%s with HTTP %s clears revoked content and preserves retryable content', async (stage, status) => {
  const onUnavailable = jest.fn();
  const createUrl = jest.spyOn(URL, 'createObjectURL').mockReturnValue('blob:selected');
  const revokeUrl = jest.spyOn(URL, 'revokeObjectURL');
  const fetchImage = jest.spyOn(globalThis, 'fetch').mockResolvedValue({ blob: async () => new Blob(['synthetic']) } as Response);
  (exportCropImage as jest.Mock).mockResolvedValue({ uri: 'blob:normalized' });
  try {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: { ...waiting, status: 'AWAITING_IMAGE', imageVersion: 0 } });
    await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} onUnavailable={onUnavailable} />); });
    const input = tree.root.findAllByType('input').find(item => item.props.type === 'file')!;
    await act(async () => { input.props.onChange({ currentTarget: { files: [new File(['synthetic'], 'image.png', { type: 'image/png' })], value: '' } }); });
    if (stage === 'privacy-check') (apiClient.post as jest.Mock).mockRejectedValueOnce({ isAxiosError: true, response: { status } });
    await act(async () => { await tree.root.findAllByType('button').find(button => button.props.children === 'Kiểm tra ảnh')!.props.onClick(); });
    if (stage === 'upload') {
      await act(async () => { tree.root.findAllByType('input').find(item => item.props.type === 'checkbox')!.props.onChange({ target: { checked: true } }); });
      (apiClient.post as jest.Mock).mockRejectedValueOnce({ isAxiosError: true, response: { status } });
      await act(async () => { await tree.root.findAllByType('button').find(button => button.props.children === 'Gửi bài làm')!.props.onClick(); });
    }
    expect(apiClient.post).toHaveBeenCalled();
    if (status === 503) {
      expect(onUnavailable).not.toHaveBeenCalled();
      expect(tree.root.findByType('img').props.src).toBe('blob:selected');
      expect(JSON.stringify(tree.toJSON())).toContain(stage === 'privacy-check' ? 'Chưa kiểm tra được ảnh' : 'Chưa gửi được ảnh');
      return;
    }
    expect(onUnavailable).toHaveBeenCalledTimes(1);
    expect(tree.root.findAllByType('img')).toHaveLength(0);
    expect(tree.root.findAllByType('input')).toHaveLength(0);
    expect(revokeUrl).toHaveBeenCalledWith('blob:selected');
    expect(JSON.stringify(tree.toJSON())).toContain('Bài này không còn khả dụng');
  } finally { createUrl.mockRestore(); revokeUrl.mockRestore(); fetchImage.mockRestore(); }
});

test('image denial clears results and blocks a late status response from restoring private content', async () => {
  const onUnavailable = jest.fn();
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} onUnavailable={onUnavailable} />); });
  let resolveStatus!: (value: unknown) => void;
  (apiClient.get as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolveStatus = done; }));
  await act(async () => { listeners.get('focus')?.(); });
  const statusSignal = (apiClient.get as jest.Mock).mock.calls[1][1].signal;
  (apiClient.get as jest.Mock).mockRejectedValueOnce({ isAxiosError: true, response: { status: 404 } });
  await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Xem ảnh đã gửi')!.props.onClick(); });
  expect(onUnavailable).toHaveBeenCalledTimes(1);
  expect(statusSignal.aborted).toBe(true);
  await act(async () => { resolveStatus({ data: { ...waiting, status: 'GRADE_RELEASED', feedback: 'Late private feedback' } }); });
  expect(JSON.stringify(tree.toJSON())).not.toContain('Late private feedback');
  expect(JSON.stringify(tree.toJSON())).toContain('Bài này không còn khả dụng');
  const calls = (apiClient.get as jest.Mock).mock.calls.length;
  await act(async () => { listeners.get('focus')?.(); jest.advanceTimersByTime(120000); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls);
});

test('a transient image error retains the assignment and offers an image retry', async () => {
  const onUnavailable = jest.fn();
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} onUnavailable={onUnavailable} />); });
  (apiClient.get as jest.Mock).mockRejectedValueOnce(new Error('Offline'));
  await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Xem ảnh đã gửi')!.props.onClick(); });
  expect(onUnavailable).not.toHaveBeenCalled();
  expect(JSON.stringify(tree.toJSON())).toContain('Chưa mở được ảnh');
  expect(JSON.stringify(tree.toJSON())).toContain('Cô/thầy đã nhận bài của em');
});

test('a late image denial from a closed preview cannot revoke the current assignment', async () => {
  const onUnavailable = jest.fn();
  await act(async () => { tree = create(<AssignedSubmission assignmentId="assignment" maxScore={10} onUnavailable={onUnavailable} />); });
  let rejectImage!: (error: unknown) => void;
  (apiClient.get as jest.Mock).mockImplementationOnce(() => new Promise((_, reject) => { rejectImage = reject; }));
  await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Xem ảnh đã gửi')!.props.onClick(); });
  const imageSignal = (apiClient.get as jest.Mock).mock.calls[1][1].signal;
  await act(async () => { tree.root.findAllByType('button').find(button => button.props.children === 'Ẩn ảnh đã gửi')!.props.onClick(); });
  expect(imageSignal.aborted).toBe(true);
  await act(async () => { rejectImage({ isAxiosError: true, response: { status: 404 } }); });
  expect(onUnavailable).not.toHaveBeenCalled();
  expect(JSON.stringify(tree.toJSON())).toContain('Cô/thầy đã nhận bài của em');
});
