import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import QuizLayout from '../app/quiz/_layout';
import { AuthContext } from '../context/AuthContext';

jest.mock('expo-router', () => ({ Stack: 'Stack', Redirect: 'Redirect' }));
it('guards Quiz deep links on web and native until a Student session is authenticated', () => {
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<AuthContext.Provider value={{ isLoading: false, isAuthenticated: false } as any}><QuizLayout /></AuthContext.Provider>); });
  expect(view!.root.findByType('Redirect' as any).props.href).toBe('/login');
  expect(view!.root.findAllByType('Stack' as any)).toHaveLength(0);
  act(() => view!.update(<AuthContext.Provider value={{ isLoading: false, isAuthenticated: true } as any}><QuizLayout /></AuthContext.Provider>));
  expect(view!.root.findAllByType('Stack' as any)).toHaveLength(1);
  act(() => view!.unmount());
});
it('waits for authoritative session restoration instead of flashing another account Quiz', () => {
  let view: TestRenderer.ReactTestRenderer;
  act(() => { view = TestRenderer.create(<AuthContext.Provider value={{ isLoading: true, isAuthenticated: false } as any}><QuizLayout /></AuthContext.Provider>); });
  expect(view!.root.findAllByType('Stack' as any)).toHaveLength(0);
  expect(view!.root.findAllByType('Redirect' as any)).toHaveLength(0);
  act(() => view!.unmount());
});
