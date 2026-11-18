import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { LessonCalculation } from '../features/tutoring/LessonCalculation';

it.each(['36 + 27', '103 − 8', '0 - 0'])('shows supplied integers in columns without computing or exposing an answer: %s', expression => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonCalculation expression={expression} />); });
  expect(view.root.findAll(node => node.props.accessibilityLabel === expression + ' bằng bao nhiêu?').length).toBeGreaterThan(0);
  const text = view.root.findAllByType('Text' as any).map(node => node.props.children).join(' ');
  expect(text).toContain('?'); expect(text).not.toContain('63');
  act(() => view.unmount());
});

it.each(['1/3 + 2/5', '-8 + 3', '(24 + 6) : 5'])('keeps non-column expressions intact: %s', expression => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonCalculation expression={expression} />); });
  expect(view.root.findAll(node => node.props.accessibilityLabel === expression + ' bằng bao nhiêu?')).toHaveLength(0);
  act(() => view.unmount());
});

it.each(['12 ÷ 3', '12 : 3'])('stacks a simple division without showing its answer: %s', expression => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonCalculation expression={expression} />); });
  expect(view.root.findAllByProps({ testID: 'stacked-fraction' }).length).toBeGreaterThan(0);
  expect(view.root.findAllByProps({ accessibilityLabel: '12 chia 3 bằng bao nhiêu?' }).length).toBeGreaterThan(0);
  act(() => view.unmount());
});

it('lays out a multiplication horizontally with the elementary-school symbol', () => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<LessonCalculation expression="5*6" />); });
  expect(view.root.findAllByProps({ testID: 'stacked-fraction' })).toHaveLength(0);
  expect(view.root.findAllByType('Text' as any).map(node => node.props.children).join(' ')).toContain('5 × 6 = ?');
  act(() => view.unmount());
});
