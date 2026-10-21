import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { HintCheckIn } from '../features/tutoring/HintCheckIn';

let view: TestRenderer.ReactTestRenderer;
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
afterEach(() => { if (view) act(() => view.unmount()); });

it.each([['(−7) + 3', '+'], ['-7 × 3', '×'], ['12 − 5', '−'], ['12-5', '-']])(
  'teaches the binary operation in %s', (expression, symbol) => {
    act(() => { view = TestRenderer.create(<HintCheckIn expression={expression} onReady={jest.fn()} />); });
    expect(text()).toContain(`Dấu ${symbol} có nghĩa gì?`);
  },
);

it('uses a generic learning check for a unary sign without inventing a subtraction', () => {
  act(() => { view = TestRenderer.create(<HintCheckIn expression="−7" onReady={jest.fn()} />); });
  expect(text()).toContain('Khi xem gợi ý, em nên làm gì tiếp?');
  expect(text()).not.toContain('Phép trừ');
});

it('asks about equal parts and only focuses the answer on explicit readiness', () => {
  const ready = jest.fn();
  act(() => { view = TestRenderer.create(<HintCheckIn expression="1/3+1/4" onReady={ready} />); });
  expect(text()).toContain('Mẫu số cho biết điều gì?');
  act(() => button('Số phần đã được chọn').props.onPress());
  expect(text()).toContain('Em chọn lại nhé.');
  expect(button('Em đã hiểu, để em thử')).toBeUndefined();
  act(() => button('Số phần bằng nhau của một hình nguyên').props.onPress());
  expect(ready).not.toHaveBeenCalled();
  act(() => button('Em đã hiểu, để em thử').props.onPress());
  expect(ready).toHaveBeenCalledTimes(1);
});

it('asks a source reading check for a reading hint instead of asking the pupil to calculate', () => {
  act(() => { view = TestRenderer.create(<HintCheckIn expression="" reading onReady={jest.fn()} />); });
  expect(text()).toContain('Ở bước hiểu đề, em cần làm gì?');
  act(() => button('Tính đáp số ngay').props.onPress());
  expect(text()).toContain('Em chọn lại nhé.');
  act(() => button('Tìm điều đã biết và điều cần tìm').props.onPress());
  expect(button('Em đã hiểu, để em thử')).toBeDefined();
});

it('uses a second fraction concept after deeper help instead of repeating the same check', () => {
  act(() => { view = TestRenderer.create(<HintCheckIn expression="1/3+1/4" depth={2} onReady={jest.fn()} />); });
  expect(text()).toContain('Tử số cho biết điều gì?');
  expect(text()).not.toContain('Mẫu số cho biết điều gì?');
});

it('cannot activate readiness when the lesson is busy or expired', () => {
  const ready = jest.fn();
  act(() => { view = TestRenderer.create(<HintCheckIn expression="1/3" disabled onReady={ready} />); });
  expect(button('Số phần bằng nhau của một hình nguyên').props.disabled).toBe(true);
});
