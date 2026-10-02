import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AuthContext } from '../context/AuthContext';
import RecognitionLayout from '../app/recognition/_layout';
import { RecognitionSummary } from '../features/recognition/components/RecognitionSummary';
import { buildRecognitionMetrics } from '../features/recognition/analytics/recognitionMetrics';
import DevDemoScreen from '../app/dev-demo';

jest.mock('expo-router', () => ({
  Redirect: 'Redirect', Stack: 'Stack', useRouter: () => ({ replace: jest.fn() }),
}));

test.each([
  [false, false, 'Redirect'], [true, false, 'Stack'], [false, true, 'ActivityIndicator'],
])('recognition route honours authenticated=%s loading=%s', (isAuthenticated, isLoading, expected) => {
  let renderer: TestRenderer.ReactTestRenderer;
  act(() => { renderer = TestRenderer.create(<AuthContext.Provider value={{
    user: null, isAuthenticated, isLoading, login: jest.fn(), logout: jest.fn(),
  }}><RecognitionLayout /></AuthContext.Provider>); });
  expect(renderer!.root.findAllByType(expected as any).length).toBeGreaterThan(0);
  if (expected === 'Redirect') expect(renderer!.root.findByType('Redirect' as any).props.href).toBe('/login');
  act(() => renderer!.unmount());
});

test('student summary shows unknown accuracy when no independent references exist', () => {
  let renderer: TestRenderer.ReactTestRenderer;
  act(() => { renderer = TestRenderer.create(<RecognitionSummary metrics={buildRecognitionMetrics([])} />); });
  const text = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
  expect(text).toContain('Chưa có bản chuẩn');
  expect(text).toContain('—');
  expect(text).not.toContain('100%');
  act(() => renderer!.unmount());
});

test('student accounts cannot render developer diagnostic information', () => {
  let renderer: TestRenderer.ReactTestRenderer;
  act(() => { renderer = TestRenderer.create(<AuthContext.Provider value={{
    user: { role: 'STUDENT' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn(),
  }}><DevDemoScreen /></AuthContext.Provider>); });
  expect(renderer!.root.findByType('Redirect' as any).props.href).toBe('/(tabs)');
  expect(renderer!.root.findAllByType('Text' as any)).toHaveLength(0);
  act(() => renderer!.unmount());
});
