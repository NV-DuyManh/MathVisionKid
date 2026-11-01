import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useIsFocused, useLocalSearchParams, useRouter } from 'expo-router';
import TrainingGameRoute, { generateStaticParams } from '../app/games/[gameId]';
import { AuthContext } from '../context/AuthContext';
import { GamePlayer, GameFallback } from '../features/training-games/GamePlayer';

jest.mock('expo-router', () => ({ useLocalSearchParams: jest.fn(), useRouter: jest.fn(), useIsFocused: jest.fn(), Redirect: 'Redirect', Stack: { Screen: 'StackScreen' } }));
jest.mock('../features/training-games/GamePlayer', () => {
  const React = require('react');
  return { GamePlayer: jest.fn(props => React.createElement('MountedGame', props)), GameFallback: jest.fn(props => React.createElement('GameFallback', props)) };
});
const A = '11111111-1111-4111-8111-111111111111', B = '22222222-2222-4222-8222-222222222222';
const auth = { user: { userId: A, role: 'STUDENT' }, isAuthenticated: true, isLoading: false, login: jest.fn(), logout: jest.fn() };
const dismissTo = jest.fn();
let tree: TestRenderer.ReactTestRenderer;
const render = (value: React.ComponentProps<typeof AuthContext.Provider>['value'] = auth) => { act(() => { tree = TestRenderer.create(<AuthContext.Provider value={value}><TrainingGameRoute /></AuthContext.Provider>); }); };
beforeEach(() => { jest.clearAllMocks(); jest.mocked(useLocalSearchParams).mockReturnValue({ gameId: 'planet-rescue' }); jest.mocked(useIsFocused).mockReturnValue(true); jest.mocked(useRouter).mockReturnValue({ dismissTo } as ReturnType<typeof useRouter>); });
afterEach(() => { if (tree) act(() => tree.unmount()); });
test('known allowlisted game receives only the authenticated UUID and no auth token', () => {
  render(); const props = tree.root.findByType(GamePlayer).props;
  expect(props.studentId).toBe(A); expect(props.gameId).toBe('planet-rescue'); expect(props.accessToken).toBeUndefined(); expect(props.refreshToken).toBeUndefined();
  expect(generateStaticParams().map(row => row.gameId).sort()).toEqual(['block-island','energy-defense','planet-rescue','race-to-finish','terrain-racing']);
});
test('auth loading/sign-out and missing UUID cannot mount gameplay', () => {
  render({ ...auth, isLoading: true }); expect(tree.toJSON()).toBeNull();
  act(() => tree.update(<AuthContext.Provider value={{ ...auth, isAuthenticated: false }}><TrainingGameRoute /></AuthContext.Provider>)); expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0);
  act(() => tree.update(<AuthContext.Provider value={{ ...auth, user: { role: 'STUDENT', id: 'local-learner-sandbox-01' } }}><TrainingGameRoute /></AuthContext.Provider>));
  expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0); expect(tree.root.findAllByType(GameFallback)).toHaveLength(1);
});
test('unknown ID renders a working fallback instead of importing arbitrary modules', () => {
  jest.mocked(useLocalSearchParams).mockReturnValue({ gameId: '../../not-allowed' }); render(); expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0);
  act(() => tree.root.findByType(GameFallback).props.onBack()); expect(dismissTo).toHaveBeenCalledWith('/games');
});
test('focus loss removes gameplay and switching students uses the new UUID', () => {
  render(); jest.mocked(useIsFocused).mockReturnValue(false); act(() => tree.update(<AuthContext.Provider value={auth}><TrainingGameRoute /></AuthContext.Provider>)); expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0);
  jest.mocked(useIsFocused).mockReturnValue(true); act(() => tree.update(<AuthContext.Provider value={{ ...auth, user: { userId: B, role: 'STUDENT' } }}><TrainingGameRoute /></AuthContext.Provider>)); expect(tree.root.findByType(GamePlayer).props.studentId).toBe(B);
});

test.each(['race-to-finish', 'terrain-racing', 'energy-defense', 'planet-rescue', 'block-island'])('route %s mounts the correct game and exits to the catalog', gameId => {
  jest.mocked(useLocalSearchParams).mockReturnValue({ gameId }); render();
  const props = tree.root.findByType(GamePlayer).props;
  expect(props.gameId).toBe(gameId); expect(props.trial).toBe(false);
  const options = tree.root.find(node => node.type === ('StackScreen' as React.ElementType)).props.options;
  expect(options.orientation).toBe(gameId === 'race-to-finish' ? 'landscape' : gameId === 'terrain-racing' || gameId === 'energy-defense' ? 'portrait' : 'default');
  expect(options.statusBarHidden).toBeUndefined(); expect(options.statusBarStyle).toBeUndefined();
  act(() => props.onExit()); expect(dismissTo).toHaveBeenCalledWith('/games');
});

test('mock cannot open a student session; explicit development trial gets an opaque owner', () => {
  const mock = { ...auth, user: { userId: 'mock_student_fixture', role: 'STUDENT' } };
  render(mock); expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0);
  jest.mocked(useLocalSearchParams).mockReturnValue({ gameId: 'planet-rescue', playMode: 'trial' });
  act(() => tree.update(<AuthContext.Provider value={mock}><TrainingGameRoute /></AuthContext.Provider>));
  const props = tree.root.findByType(GamePlayer).props;
  expect(props.trial).toBe(true); expect(props.studentId).toMatch(/^development-trial:\d+$/);
  expect(props.studentId).not.toContain('mock_student');
});

test('a trial query parameter never downgrades or replaces a real authenticated UUID', () => {
  jest.mocked(useLocalSearchParams).mockReturnValue({ gameId: 'planet-rescue', playMode: 'trial' }); render();
  const props = tree.root.findByType(GamePlayer).props; expect(props.studentId).toBe(A); expect(props.trial).toBe(false);
});

test('production rejects a mock trial even with an explicit trial query parameter', () => {
  const development = __DEV__;
  try {
    Object.defineProperty(global, '__DEV__', { value: false, writable: true, configurable: true });
    jest.mocked(useLocalSearchParams).mockReturnValue({ gameId: 'planet-rescue', playMode: 'trial' });
    render({ ...auth, user: { userId: 'mock_student_fixture', role: 'STUDENT' } });
    expect(tree.root.findAllByType(GamePlayer)).toHaveLength(0); expect(tree.root.findAllByType(GameFallback)).toHaveLength(1);
  } finally { Object.defineProperty(global, '__DEV__', { value: development, writable: true, configurable: true }); }
});
