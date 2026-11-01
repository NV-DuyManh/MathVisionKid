import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import RootLayout from '../app/_layout';
import { prepareIllustrations } from '../components/ui/AppIllustration';

jest.mock('../components/ui/AppIllustration', () => ({ prepareIllustrations: jest.fn() }));
jest.mock('expo-router', () => ({ Stack: Object.assign(({ children }: any) => require('react').createElement('Stack', {}, children), { Screen: 'Screen', Protected: ({ guard, children }: any) => guard ? children : null }) }));
jest.mock('expo-font', () => ({ useFonts: () => [true, null], isLoaded: () => true }));
jest.mock('expo-splash-screen', () => ({ preventAutoHideAsync: jest.fn().mockResolvedValue(null), hideAsync: jest.fn().mockResolvedValue(null) }));
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext({ user: { role: 'STUDENT', active: true }, isAuthenticated: true }), AuthProvider: ({ children }: any) => children }));

let view: TestRenderer.ReactTestRenderer;
beforeEach(() => { jest.clearAllMocks(); global.fetch = jest.fn().mockResolvedValue({ ok: true }); });
afterEach(() => { act(() => view?.unmount()); jest.useRealTimers(); });
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');

it('opens navigation only after every illustration has been prepared', async () => {
  let done!: () => void;
  (prepareIllustrations as jest.Mock).mockReturnValue(new Promise<void>(resolve => { done = resolve; }));
  await act(async () => { view = TestRenderer.create(<RootLayout />); });
  const progress = view.root.find(node => node.props.accessibilityRole === 'progressbar');
  expect(progress.props.accessibilityValue.max).toBe(100);
  expect(progress.props.accessibilityValue.now).toBeGreaterThan(0);
  expect(progress.props.accessibilityValue.now).toBeLessThan(85);
  expect(progress.props['aria-busy']).toBe(true);
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(0);
  await act(async () => { done(); });
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(1);
  expect(view.root.findAll(node => node.props.accessibilityRole === 'progressbar')).toHaveLength(0);
});

it('offers a retry after loading fails and does not open empty-image screens', async () => {
  (prepareIllustrations as jest.Mock).mockRejectedValueOnce(new Error('private URL')).mockResolvedValueOnce(undefined);
  await act(async () => { view = TestRenderer.create(<RootLayout />); });
  expect(text()).toContain('Chưa tải đủ hình');
  expect(text()).not.toContain('private URL');
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(0);
  const retry = view.root.findAll(node => node.props.accessibilityLabel === 'Tải lại hình' && typeof node.props.onPress === 'function')[0];
  await act(async () => { retry.props.onPress(); });
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(1);
});

it('shows a retry for a stalled first download instead of waiting indefinitely', async () => {
  jest.useFakeTimers();
  (prepareIllustrations as jest.Mock).mockReturnValue(new Promise(() => {}));
  await act(async () => { view = TestRenderer.create(<RootLayout />); });
  act(() => jest.advanceTimersByTime(15000));
  expect(text()).toContain('Chưa tải đủ hình');
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(0);
});

it.each([
  { role: 'ADMIN', active: true, authenticated: true },
  { role: 'TEACHER', active: true, authenticated: true },
  { role: 'STUDENT', active: false, authenticated: true },
  { role: 'STUDENT', active: true, authenticated: false },
])('keeps every Native learning screen protected for $role / active=$active / authenticated=$authenticated', async profile => {
  (prepareIllustrations as jest.Mock).mockResolvedValue(undefined);
  const { AuthContext } = require('../context/AuthContext');
  await act(async () => { view = TestRenderer.create(
    <AuthContext.Provider value={{ user: { role: profile.role, active: profile.active }, isAuthenticated: profile.authenticated }}><RootLayout /></AuthContext.Provider>
  ); });
  const names = view.root.findAllByType('Screen' as any).map(node => node.props.name);
  expect(names).toEqual(['index', 'login', 'privacy']);
});
