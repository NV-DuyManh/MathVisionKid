import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import RootLayout from '../app/_layout';
import { prepareIllustrations } from '../components/ui/AppIllustration';

jest.mock('../components/ui/AppIllustration', () => ({ prepareIllustrations: jest.fn() }));
jest.mock('expo-router', () => ({ Stack: Object.assign(({ children }: any) => require('react').createElement('Stack', {}, children), { Screen: 'Screen' }) }));
jest.mock('expo-font', () => ({ useFonts: () => [true, null] }));
jest.mock('expo-splash-screen', () => ({ preventAutoHideAsync: jest.fn().mockResolvedValue(null), hideAsync: jest.fn().mockResolvedValue(null) }));
jest.mock('../context/AuthContext', () => ({ AuthProvider: ({ children }: any) => children }));

let view: TestRenderer.ReactTestRenderer;
beforeEach(() => { jest.clearAllMocks(); global.fetch = jest.fn().mockResolvedValue({ ok: true }); });
afterEach(() => { act(() => view?.unmount()); jest.useRealTimers(); });
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');

it('opens navigation only after every illustration has been prepared', async () => {
  let done!: () => void;
  (prepareIllustrations as jest.Mock).mockReturnValue(new Promise<void>(resolve => { done = resolve; }));
  await act(async () => { view = TestRenderer.create(<RootLayout />); });
  expect(text()).toContain('Đang chuẩn bị');
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(0);
  await act(async () => { done(); });
  expect(view.root.findAllByType('Stack' as any)).toHaveLength(1);
  expect(text()).not.toContain('Đang chuẩn bị');
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
