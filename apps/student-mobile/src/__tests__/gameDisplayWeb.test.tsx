import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { enterGameDisplay, GameDisplay } from '../features/training-games/GameDisplay.web';
import type { TrainingGameId } from '@mathvisionkid/training-games';

const lock = jest.fn(), unlock = jest.fn(), fullscreen = jest.fn(), exit = jest.fn();
const savedDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
const savedScreen = Object.getOwnPropertyDescriptor(globalThis, 'screen');
let view: TestRenderer.ReactTestRenderer | undefined;
beforeEach(() => {
  jest.clearAllMocks();
  Object.defineProperty(globalThis, 'document', { configurable: true, value: { documentElement: {} } });
  Object.defineProperty(globalThis, 'screen', { configurable: true, value: {} });
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: () => ({ matches: true }) });
  Object.defineProperty(screen, 'orientation', { configurable: true, value: { lock, unlock } });
  Object.defineProperty(document, 'fullscreenElement', { configurable: true, value: null, writable: true });
  Object.defineProperty(document.documentElement, 'requestFullscreen', { configurable: true, value: fullscreen });
  Object.defineProperty(document, 'exitFullscreen', { configurable: true, value: exit });
  lock.mockResolvedValue(undefined);
  exit.mockImplementation(async () => { Object.defineProperty(document, 'fullscreenElement', { value: null }); });
});
afterEach(() => {
  act(() => view?.unmount()); view = undefined;
  if (savedDocument) Object.defineProperty(globalThis, 'document', savedDocument); else delete (globalThis as any).document;
  if (savedScreen) Object.defineProperty(globalThis, 'screen', savedScreen); else delete (globalThis as any).screen;
});

it('keeps the play gesture fullscreen request and locks landscape after it resolves', async () => {
  let finish!: () => void;
  fullscreen.mockImplementation(() => new Promise<void>(resolve => { finish = resolve; }));
  enterGameDisplay('race-to-finish');
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  expect(fullscreen).toHaveBeenCalledTimes(1);
  expect(lock).not.toHaveBeenCalled();
  await act(async () => {
    Object.defineProperty(document, 'fullscreenElement', { value: document.documentElement });
    finish();
  });
  expect(lock).toHaveBeenCalledWith('landscape');
  await act(async () => view?.unmount());
  expect(unlock).toHaveBeenCalled();
  expect(exit).toHaveBeenCalledTimes(1);
});

it('does not lock a game after the learner has already left it', async () => {
  let finish!: () => void;
  fullscreen.mockImplementation(() => new Promise<void>(resolve => { finish = resolve; }));
  enterGameDisplay('race-to-finish');
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  act(() => view?.unmount());
  await act(async () => {
    Object.defineProperty(document, 'fullscreenElement', { value: document.documentElement });
    finish();
  });
  expect(lock).not.toHaveBeenCalled();
  expect(exit).toHaveBeenCalled();
});

it('keeps a game mounted when the browser rejects fullscreen', async () => {
  fullscreen.mockRejectedValue(new Error('Fullscreen unavailable'));
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  expect(view?.toJSON()).toBeTruthy();
  expect(lock).not.toHaveBeenCalled();
});

it('allows a new fullscreen gesture after the browser rejected the first attempt', async () => {
  fullscreen.mockRejectedValueOnce(new Error('User gesture required')).mockResolvedValueOnce(undefined);
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  await act(async () => enterGameDisplay('race-to-finish'));
  expect(fullscreen).toHaveBeenCalledTimes(2);
  expect(lock).toHaveBeenCalledWith('landscape');
});

it('preserves fullscreen that was already active when the learner entered a game', async () => {
  Object.defineProperty(document, 'fullscreenElement', { value: document.documentElement });
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  expect(fullscreen).not.toHaveBeenCalled();
  expect(lock).toHaveBeenCalledWith('landscape');
  act(() => view?.unmount());
  expect(exit).not.toHaveBeenCalled();
});

it('keeps navigation usable when fullscreen throws immediately', async () => {
  fullscreen.mockImplementation(() => { throw new Error('Fullscreen unsupported'); });
  expect(() => enterGameDisplay('race-to-finish')).not.toThrow();
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId="race-to-finish"><></></GameDisplay>); });
  expect(lock).not.toHaveBeenCalled();
});

it.each([
  ['race-to-finish', 'landscape'],
  ['terrain-racing', 'portrait'],
  ['energy-defense', 'portrait'],
  ['planet-rescue', null],
  ['block-island', null],
] as [TrainingGameId, string | null][])('uses the original orientation policy for %s', async (gameId, direction) => {
  fullscreen.mockResolvedValue(undefined);
  enterGameDisplay(gameId);
  await act(async () => { view = TestRenderer.create(<GameDisplay gameId={gameId}><></></GameDisplay>); });
  if (direction) expect(lock).toHaveBeenCalledWith(direction);
  else {
    expect(fullscreen).not.toHaveBeenCalled();
    expect(lock).not.toHaveBeenCalled();
  }
});
