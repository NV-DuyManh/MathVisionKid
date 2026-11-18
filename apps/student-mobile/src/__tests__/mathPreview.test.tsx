import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { MathPreview } from '../components/domain/MathPreview';
import { MathText } from '../components/domain/MathText';

it('ends a narrow lesson preview at a complete token and keeps a visible fraction intact', () => {
  let tree!: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<MathPreview style={{ fontSize: 12 }}>Có 1/3 số cây là táo, còn lại là những cây khác.</MathPreview>); });
  act(() => tree.root.findAll(node => node.props.onLayout)[0].props.onLayout({ nativeEvent: { layout: { width: 110 } } }));
  const shown = tree.root.findByType(MathText).props.children;
  expect(shown).toContain('1/3');
  expect(shown).toMatch(/…$/);
  expect(shown).not.toMatch(/1\/…|1…/);
  expect(tree.root.findAllByProps({ testID: 'stacked-fraction' }).length).toBeGreaterThan(0);
  act(() => tree.unmount());
});
