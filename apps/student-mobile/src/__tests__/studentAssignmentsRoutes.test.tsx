import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Text } from 'react-native';

let mockAssignmentId: string | undefined;
let mockStudentId = 'student-a';
let mockFocused = true;
const mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  Link: ({ children }: { children: React.ReactNode }) => children,
  useLocalSearchParams: () => ({ id: mockAssignmentId }),
  useRouter: () => ({ replace: mockReplace }),
  useFocusEffect: (effect: React.EffectCallback) => {
    const focused = mockFocused;
    jest.requireActual<typeof React>('react').useEffect(() => focused ? effect() : undefined, [effect, focused]);
  },
}));
jest.mock('../context/AuthContext', () => {
  const react = jest.requireActual<typeof React>('react');
  return { AuthContext: react.createContext({ get user() { return { id: mockStudentId }; } }) };
});
jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { get: jest.fn() } }));
jest.mock('../features/recognition/AssignedSubmission.web', () => ({ __esModule: true, default: () => null }));

import apiClient from '../services/api/apiClient';
import StudentAssignments from '../app/(tabs)/assignments.web';
import StudentAssignmentDetail from '../app/(tabs)/assignment/[id].web';

const assignment = (title: string) => ({
  assignmentId: title, className: '5A', teacherName: 'An', title, prompt: '7 + 3', maxScore: 10,
  publishedAt: '2026-11-15T10:00:00Z', status: 'AWAITING_IMAGE', score: null as number | null,
});
const pageText = (view: TestRenderer.ReactTestRenderer) => view.root.findAllByType(Text)
  .map(node => React.Children.toArray(node.props.children).join(''))
  .join(' ');
const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
};

let view: TestRenderer.ReactTestRenderer;
beforeEach(() => { jest.useRealTimers(); mockStudentId = 'student-a'; mockFocused = true; mockAssignmentId = undefined; mockReplace.mockReset(); jest.mocked(apiClient.get).mockReset(); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('keeps a late detail response from replacing the list after back navigation', async () => {
  mockAssignmentId = 'a';
  const detail = deferred<{ data: ReturnType<typeof assignment> }>();
  const list = deferred<{ data: ReturnType<typeof assignment>[] }>();
  jest.mocked(apiClient.get).mockImplementation(path => path.endsWith('/a')
    ? detail.promise as any
    : list.promise as any);
  act(() => { view = TestRenderer.create(<StudentAssignments />); });
  expect(pageText(view)).toContain('‹ Quay lại Bài của em');
  const back = view.root.find(node => node.props.accessibilityRole === 'button'
    && node.props.onPress && pageTextFrom(node.props.children).includes('‹ Quay lại Bài của em'));
  act(() => back.props.onPress());
  mockAssignmentId = undefined;
  act(() => { view.update(<StudentAssignments />); });

  await act(async () => {
    detail.resolve({ data: assignment('Bài cũ') });
    list.resolve({ data: [assignment('Bài trong danh sách')] });
    await Promise.all([detail.promise, list.promise]);
  });
  expect(pageText(view)).toContain('Bài của em');
  expect(pageText(view)).toContain('Bài trong danh sách');
  expect(pageText(view)).not.toContain('Bài cũ');
});

function pageTextFrom(children: React.ReactNode): string {
  return React.Children.toArray(children).map(child => typeof child === 'string' || typeof child === 'number'
    ? String(child)
    : React.isValidElement(child) ? pageTextFrom((child.props as { children?: React.ReactNode }).children) : '').join(' ');
}

it('hides a previous detail when a new assignment id is denied', async () => {
  mockAssignmentId = 'a';
  const first = deferred<{ data: ReturnType<typeof assignment> }>();
  const denied = deferred<{ data: ReturnType<typeof assignment> }>();
  jest.mocked(apiClient.get).mockImplementation(path => path.endsWith('/a')
    ? first.promise as any
    : denied.promise.then(() => { throw new Error('Not found'); }) as any);
  act(() => { view = TestRenderer.create(<StudentAssignmentDetail />); });
  await act(async () => {
    first.resolve({ data: assignment('Bài trước') });
    await first.promise;
  });
  expect(pageText(view)).toContain('Bài trước');
  mockAssignmentId = 'b';
  act(() => { view.update(<StudentAssignmentDetail />); });
  expect(pageText(view)).not.toContain('Bài trước');
  await act(async () => {
    denied.resolve({ data: assignment('Không được trả về') });
    await denied.promise;
  });
  expect(pageText(view)).not.toContain('Bài trước');
  expect(pageText(view)).toContain('Bài này không còn khả dụng hoặc em chưa được giao bài.');
});

it('shows released zero, leaves missing work unscored and ignores a late response from another student', async () => {
  const previous = deferred<{ data: ReturnType<typeof assignment>[] }>();
  jest.mocked(apiClient.get).mockReturnValueOnce(previous.promise as any).mockResolvedValueOnce({
    data: [{ ...assignment('Bài điểm không'), score: 0, status: 'GRADE_RELEASED' }, assignment('Bài chưa nộp')],
  } as any);
  act(() => { view = TestRenderer.create(<StudentAssignments />); });
  mockStudentId = 'student-b';
  await act(async () => { view.update(<StudentAssignments />); });
  await act(async () => {
    previous.resolve({ data: [{ ...assignment('Kết quả của A'), score: 8, status: 'GRADE_RELEASED' }] });
    await previous.promise;
  });
  expect(jest.mocked(apiClient.get).mock.calls.map(([path]) => path)).toEqual([
    '/student/assignments/history', '/student/assignments/history',
  ]);
  expect(pageText(view)).toContain('0/10 điểm');
  expect(pageText(view).match(/0\/10 điểm/g)).toHaveLength(1);
  expect(pageText(view)).toContain('Bài chưa nộp');
  expect(pageText(view)).not.toContain('Kết quả của A');
});

it('keeps the assignment detail mounted when returning to a focused tab', async () => {
  mockAssignmentId = 'a';
  const detail = '/student/assignments/a';
  jest.mocked(apiClient.get).mockImplementation(async path => ({
    data: path === detail ? assignment('Bài đang làm') : { status: 'AWAITING_IMAGE', imageVersion: 0 },
  } as any));
  await act(async () => { view = TestRenderer.create(<StudentAssignments />); });
  const submission = view.root.findByProps({ assignmentId: 'a', maxScore: 10 });
  mockFocused = false;
  await act(async () => { view.update(<StudentAssignments />); });
  mockFocused = true;
  await act(async () => { view.update(<StudentAssignments />); });
  expect(view.root.findByProps({ assignmentId: 'a', maxScore: 10 })).toBe(submission);
  expect(jest.mocked(apiClient.get).mock.calls.filter(([path]) => path === detail)).toHaveLength(1);
});
