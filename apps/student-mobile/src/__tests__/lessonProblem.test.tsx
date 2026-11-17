import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import { LessonProblem } from '../features/tutoring/LessonProblem';

it('opens the text by default, bounds long questions and switches exclusively between text and image', () => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonProblem problem="Có 3 bút. Hỏi có bao nhiêu bút?" onEdit={jest.fn()} imageUri="file:///masked.jpg" />); });
  expect(view.root.findAllByProps({ testID: 'lesson-problem-content' }).length).toBeGreaterThan(0);
  const body = () => view.root.findAllByProps({ testID: 'lesson-problem-content' })[0];
  act(() => body().props.onContentSizeChange(320, 38));
  expect(StyleSheet.flatten(body().props.style).height).toBe(38);
  expect(view.root.findAllByType('Image' as any)).toHaveLength(0);
  act(() => body().props.onContentSizeChange(320, 500));
  const style = StyleSheet.flatten(body().props.style);
  expect(style.height).toBe(style.maxHeight);
  expect(style.maxHeight).toBeLessThanOrEqual(124);
  const readAll = view.root.findAll(node => node.props.accessibilityLabel === 'Đọc toàn bộ đề bài' && node.props.onPress)[0];
  act(() => readAll.props.onPress());
  expect(view.root.findAllByProps({ accessibilityLabel: 'Toàn bộ đề bài' }).length).toBeGreaterThan(0);
  act(() => view.root.findAll(node => node.props.accessibilityLabel === 'Đóng Toàn bộ đề bài' && node.props.onPress)[0].props.onPress());
  const imageButton = view.root.findAll(node => node.props.accessibilityLabel === 'Xem ảnh đề bài' && node.props.onPress)[0];
  act(() => imageButton.props.onPress());
  expect(view.root.findAllByType('Image' as any).length).toBeGreaterThan(0);
  expect(body().findAll(node => node.type === 'Text' && String(node.props.children).includes('Có 3 bút'))).toHaveLength(0);
  act(() => view.root.findAll(node => node.props.accessibilityLabel === 'Xem đề bài bằng chữ' && node.props.onPress)[0].props.onPress());
  expect(view.root.findAllByType('Image' as any)).toHaveLength(0);
  act(() => view.unmount());
});
