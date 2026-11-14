import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Text } from 'react-native';

let mockAssignmentId: string | undefined;
const mockReplace = jest.fn();
jest.mock('expo-router', () => ({
  Link: ({ children }: { children: React.ReactNode }) => children,
  useLocalSearchParams: () => ({ id: mockAssignmentId }),
  useRouter: () => ({ replace: mockReplace }),
}));
jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { get: jest.fn() } }));

import apiClient from '../services/api/apiClient';
import StudentAssignments from '../app/(tabs)/assignments.web';
import StudentAssignmentDetail from '../app/(tabs)/assignment/[id].web';

const assignment = (title: string) => ({
  assignmentId: title, className: '5A', teacherName: 'An', title, prompt: '7 + 3', maxScore: 10,
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
beforeEach(() => { jest.useRealTimers(); mockAssignmentId = undefined; mockReplace.mockReset(); jest.mocked(apiClient.get).mockReset(); });
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
