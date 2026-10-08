import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { MathText } from '../components/domain/MathText';

it('stacks actual fractions in prose and expressions while preserving their readable source', () => {
  const source = 'Táo 1/3, xoài 2/5.\n1 − 1/3 − 2/5 = ?';
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MathText style={{ fontSize: 24 }}>{source}</MathText>); });
  expect(view!.root.findAll(node => node.props.testID === 'stacked-fraction' && node.type === 'View')).toHaveLength(4);
  expect(view!.root.findAll(node => node.props.accessibilityLabel === source.replaceAll('1/3','1 phần 3').replaceAll('2/5','2 phần 5')).length).toBeGreaterThan(0);
  act(() => view!.unmount());
});

it.each(['Ngày 2/5/2026', 'Ảnh 3/[?]', 'Chia 3/0', '90 × 2 ÷ 15', '1.5/2', '1/2.5', '1,5/2', '1/2,5'])('keeps non-fraction or unresolved text literal: %s', source => {
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MathText>{source}</MathText>); });
  expect(view!.root.findAll(node => node.props.testID === 'stacked-fraction')).toHaveLength(0);
  expect(view!.root.findAllByType('Text' as any).some(node => node.props.children === source)).toBe(true);
  act(() => view!.unmount());
});
