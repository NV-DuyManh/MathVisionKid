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

it.each(['(3)/(5)', '( 3 ) / ( 5 )', '\\frac{3}{5}', '\\dfrac{3}{5}', '3⁄5', '-3/5'])('renders the OCR fraction form %s vertically', source => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MathText>{source}</MathText>); });
  expect(view.root.findAll(node => node.props.testID === 'stacked-fraction' && node.type === 'View')).toHaveLength(1);
  expect(view.root.findAll(node => node.props.accessibilityLabel === `${source.startsWith('-') ? '-' : ''}3 phần 5`).length).toBeGreaterThan(0);
  act(() => view.unmount());
});

it('renders inline TeX and Markdown fractions without leaking markup into Vietnamese prose', () => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MathText>{'Đề cho **\\(\\frac{1}{3}\\)** cây táo.\\[1-\\left(\\frac{1}{3}+\\frac{2}{5}\\right)=?\\]'}</MathText>); });
  expect(view.root.findAll(node => node.props.testID === 'stacked-fraction' && node.type === 'View')).toHaveLength(3);
  const rendered = view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join('');
  expect(rendered).not.toMatch(/\\(?:frac|left|right)|\*\*|\\[()[\]]|1\/3|2\/5/);
  expect(rendered).toContain('cây táo.');
  act(() => view.unmount());
});

it.each(['https://math.example/1/3?value=2/5', 'www.math.example/a/1/3', '/images/1/3.png', 'C:\\images\\1/3.png'])('preserves URL/path %s alongside a real fraction', source => {
  let view!: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<MathText>{`${source} và 2/5 số cây.`}</MathText>); });
  expect(view.root.findAll(node => node.props.testID === 'stacked-fraction' && node.type === 'View')).toHaveLength(1);
  expect(view.root.findAllByType('Text' as any).some(node => String(node.props.children).includes(source))).toBe(true);
  act(() => view.unmount());
});
