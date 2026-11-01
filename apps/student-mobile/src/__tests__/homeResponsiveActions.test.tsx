import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { HomeDashboard } from '../components/home/HomeDashboard';

jest.mock('react-native/Libraries/Utilities/useWindowDimensions', () => ({
  __esModule: true, default: () => ({ width: 390, height: 844, scale: 1, fontScale: 1 }),
}));
jest.mock('expo-router', () => ({ useRouter: () => ({ push: jest.fn() }), useFocusEffect: jest.fn() }));
jest.mock('../features/calculator/PocketCalculator', () => ({ PocketCalculator: () => null }));

it('lets a learner choose a grade directly on a spacious screen after a resize', () => {
  const onPractice = jest.fn();
  let tree: TestRenderer.ReactTestRenderer;
  act(() => { tree = TestRenderer.create(<HomeDashboard userName="An" onAcquire={() => {}} onArithmetic={() => {}}
    onPractice={onPractice} onTips={() => {}} onPrivacy={() => {}} />); });
  const root = tree!.root.findAll(node => typeof node.props.onLayout === 'function')[0];
  expect(tree!.root.findAll(node => node.props.accessibilityLabel?.startsWith('Câu đố của em'))).toHaveLength(0);
  act(() => root.props.onLayout({ nativeEvent: { layout: { width: 1100 } } }));
  const choice = tree!.root.findAll(node => node.props.accessibilityLabel === 'Luyện tập lớp 5' && typeof node.props.onPress === 'function')[0];
  expect(choice).toBeDefined();
  act(() => choice.props.onPress());
  expect(onPractice).toHaveBeenCalledWith(5);
  act(() => root.props.onLayout({ nativeEvent: { layout: { width: 350 } } }));
  expect(tree!.root.findAll(node => node.props.accessibilityLabel === 'Luyện tập lớp 5')).toHaveLength(0);
  act(() => tree!.unmount());
});
