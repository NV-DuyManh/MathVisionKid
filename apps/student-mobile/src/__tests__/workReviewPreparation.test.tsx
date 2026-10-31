import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { WorkReviewPreparation } from '../features/tutoring/WorkReviewPreparation';

let view: TestRenderer.ReactTestRenderer;
const confirm = jest.fn(), edit = jest.fn();
const props = { problem: 'Có 12 bút, thêm 5 bút. Có tất cả bao nhiêu bút?', work: '12 + 5 = 18', problemImage: 'file:///problem.jpg', workImage: 'file:///work.jpg',
  photoCurrent: true, disabled: false, onConfirm: confirm, onEdit: edit };
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
beforeEach(() => jest.clearAllMocks());
afterEach(() => act(() => view.unmount()));

it('shows the written work first, preserves the wrong value, and asks for explicit transcription confirmation', () => {
  act(() => { view = TestRenderer.create(<WorkReviewPreparation {...props} />); });
  expect(text()).toContain('12 + 5 = 18');
  expect(confirm).not.toHaveBeenCalled();
  act(() => button('Chỉnh chỗ chưa đọc đúng').props.onPress());
  expect(edit).toHaveBeenCalledWith('work');
  act(() => button('Đối chiếu đề bài').props.onPress());
  expect(button('Đối chiếu đề bài').props.accessibilityState.selected).toBe(true);
  expect(text()).toContain(props.problem);
  act(() => button('Chỉnh đề bài').props.onPress());
  expect(edit).toHaveBeenCalledWith('problem');
  act(() => button('Nội dung đã đúng · Xem nhận xét').props.onPress());
  expect(confirm).toHaveBeenCalledTimes(1);
});

it.each(['problem', 'work'] as const)('blocks grading until an unread symbol in %s is clarified, even when another tab is open', field => {
  act(() => { view = TestRenderer.create(<WorkReviewPreparation {...props} {...{ [field]: props[field] + ' [?]' }} />); });
  expect(button('Nội dung đã đúng · Xem nhận xét').props.disabled).toBe(true);
  act(() => button('Đối chiếu đề bài').props.onPress());
  expect(button('Nội dung đã đúng · Xem nhận xét').props.disabled).toBe(true);
  expect(confirm).not.toHaveBeenCalled();
});
