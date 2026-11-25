import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { renderToString } from 'react-dom/server';
import PortalLoginRedirect from '../app/login.web';
import { workspaceOrigin } from '../config/workspaceOrigin.web';

jest.mock('react-native', () => ({ Text: 'Text' }));
jest.mock('../config/workspaceOrigin.web', () => ({ workspaceOrigin: jest.fn(() => 'https://portal.example.test') }));

const originalWindow = Object.getOwnPropertyDescriptor(globalThis, 'window');
let tree: TestRenderer.ReactTestRenderer | undefined;

function location(pathname: string, origin = 'https://portal.example.test') {
  const replace = jest.fn();
  Object.defineProperty(globalThis, 'window', { configurable: true, value: {
    location: { pathname, origin, search: '?session=expired', href: `${origin}${pathname}?session=expired`, replace },
  } });
  return replace;
}

afterEach(() => {
  act(() => tree?.unmount());
  tree = undefined;
  if (originalWindow) Object.defineProperty(globalThis, 'window', originalWindow);
  else Reflect.deleteProperty(globalThis, 'window');
  jest.mocked(workspaceOrigin).mockReset().mockReturnValue('https://portal.example.test');
});

test.each(['/study/login', '/learn/login'])('mounted %s retains the query and current portal origin', async path => {
  const replace = location(path, 'https://school.example.test');
  await act(async () => { tree = TestRenderer.create(<PortalLoginRedirect />); });
  expect(replace).toHaveBeenCalledWith('https://school.example.test/login?session=expired');
  expect(tree!.toJSON()).toBeNull();
});

test('a standalone login already at the destination explains the failure without a redirect loop', async () => {
  const replace = location('/login');
  await act(async () => { tree = TestRenderer.create(<PortalLoginRedirect />); });
  expect(replace).not.toHaveBeenCalled();
  expect(tree!.root.findByType('Text' as React.ElementType).props.accessibilityRole).toBe('alert');
});

test('a browser navigation failure displays the existing recovery message', async () => {
  const replace = location('/study/login');
  replace.mockImplementation(() => { throw new Error('Navigation unavailable'); });
  await act(async () => { tree = TestRenderer.create(<PortalLoginRedirect />); });
  expect(tree!.root.findByType('Text' as React.ElementType).props.children).toContain('Chưa mở được trang đăng nhập');
});

test('static rendering waits for the browser snapshot and does not show a false error', () => {
  location('/study/login');
  expect(renderToString(<PortalLoginRedirect />)).toBe('');
});

test('StrictMode cancels the obsolete setup before dispatching navigation', async () => {
  const replace = location('/study/login');
  await act(async () => { tree = TestRenderer.create(<React.StrictMode><PortalLoginRedirect /></React.StrictMode>); });
  expect(replace).toHaveBeenCalledTimes(1);
});
