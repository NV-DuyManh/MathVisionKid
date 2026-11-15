import React from 'react';
import { act, create, ReactTestRenderer } from 'react-test-renderer';
import AssignedSubmission from '../AssignedSubmission.web';
import apiClient from '../../../services/api/apiClient';

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
  const calls = (apiClient.get as jest.Mock).mock.calls.length;
  await act(async () => { jest.advanceTimersByTime(3600000); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls);
  await act(async () => { listeners.get('focus')?.(); });
  expect(apiClient.get).toHaveBeenCalledTimes(calls + 1);
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
