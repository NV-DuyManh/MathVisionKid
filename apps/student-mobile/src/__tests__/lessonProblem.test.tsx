import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import { LessonProblem } from '../features/tutoring/LessonProblem';

it('fits a short question and adds only a small bounded allowance for long questions', () => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonProblem problem="Có 3 bút. Hỏi có bao nhiêu bút?" onEdit={jest.fn()} imageUri="file:///masked.jpg" />); });
  expect(view.root.findAllByProps({ testID: 'lesson-problem-content' })).toHaveLength(0);
  act(() => view.root.findAll(node => node.props.accessibilityLabel === 'Mở đề bài' && node.props.onPress)[0].props.onPress());
  const body = () => view.root.findAllByProps({ testID: 'lesson-problem-content' })[0];
  act(() => body().props.onContentSizeChange(320, 38));
  expect(StyleSheet.flatten(body().props.style).height).toBe(38);
  expect(view.root.findAllByType('Image' as any)).toHaveLength(0);
  act(() => body().props.onContentSizeChange(320, 500));
  const style = StyleSheet.flatten(body().props.style);
  expect(style.height).toBe(style.maxHeight);
  expect(style.maxHeight).toBeLessThanOrEqual(124);
  const imageButton = view.root.findAll(node => node.props.accessibilityLabel === 'Xem ảnh đề bài' && node.props.onPress)[0];
  act(() => imageButton.props.onPress());
  expect(view.root.findAllByType('Image' as any).length).toBeGreaterThan(0);
  act(() => view.unmount());
});
