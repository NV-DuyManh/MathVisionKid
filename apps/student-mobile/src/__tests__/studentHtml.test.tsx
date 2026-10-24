import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import StudentHtml from '../app/+html';

jest.mock('expo-router/html', () => {
  const react = require('react');
  return {
  ScrollViewStyleReset: () => null,
  useServerDocumentContext: () => ({
    headNodes: react.createElement('style', { id: 'router-generated-css' }),
    bodyNodes: react.createElement('script', { src: '/study/_expo/entry.js' }),
    htmlAttributes: { dir: 'ltr' },
    bodyAttributes: { 'data-router-document': 'ready' },
  }),
  };
});

it('retains Router 58 resources and document attributes so the static student website can hydrate', () => {
  let renderer: TestRenderer.ReactTestRenderer;
  act(() => { renderer = TestRenderer.create(<StudentHtml><div id="root" /></StudentHtml>); });
  expect(renderer!.root.findByType('html').props.lang).toBe('vi');
  expect(renderer!.root.findByType('html').props.dir).toBe('ltr');
  expect(renderer!.root.findByType('head').findByProps({ id: 'router-generated-css' })).toBeDefined();
  const body = renderer!.root.findByType('body');
  expect(body.props['data-router-document']).toBe('ready');
  expect(body.findByProps({ id: 'root' })).toBeDefined();
  expect(body.findByType('script').props.src).toBe('/study/_expo/entry.js');
  act(() => renderer!.unmount());
});
