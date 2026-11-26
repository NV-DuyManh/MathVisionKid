import path from 'node:path';

const source = path.join(path.dirname(require.resolve('@mathvisionkid/training-games')), '..');
const { RaceController } = require(path.join(source, 'games/race-to-finish/state/RaceController'));
const { DICE_ROLL_DURATION_MS, BOT_ANSWER_DELAY_MS } = require(path.join(source, 'games/race-to-finish/state/turnTiming'));
const player = (id: string, isBot = true) => ({ id, name: id, character: id === 'p1' ? 'fox' : 'penguin',
  isBot, currentTileId: 'tile_0', pathHistory: ['tile_0'], position: 0, hasShield: false,
  cleanseCount: 0, skipNextTurn: false, currentPose: 'idle_1', rank: null });
beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

test('dice holds its confirmed result for two seconds before opening the question', () => {
  const scheduled = jest.spyOn(global, 'setTimeout');
  const cancelled = jest.spyOn(global, 'clearTimeout');
  expect(DICE_ROLL_DURATION_MS).toBe(2500);
  const controller = new RaceController(() => .55); controller.connect();
  controller.startGame('single', [player('p1', false), player('p2')]);
  controller.roll();
  jest.advanceTimersByTime(500);
  expect(controller.getSnapshot().currentDiceValue).toBe(4);
  jest.advanceTimersByTime(1999);
  expect(controller.getSnapshot().gamePhase).toBe('rolling');
  jest.advanceTimersByTime(1);
  expect(controller.getSnapshot().gamePhase).toBe('showing_question');
  const questionTimer = scheduled.mock.results.at(-1)?.value;
  const snapshot = controller.getSnapshot();
  controller.disconnect();
  expect(cancelled).toHaveBeenCalledWith(questionTimer);
  jest.advanceTimersByTime(60000);
  expect(controller.getSnapshot()).toBe(snapshot);
  scheduled.mockRestore(); cancelled.mockRestore();
});

test('dice pause keeps the remaining readable time without rolling again', () => {
  const random = jest.fn(() => .55);
  const controller = new RaceController(random); controller.connect();
  controller.startGame('single', [player('p1', false), player('p2')]); controller.roll();
  jest.advanceTimersByTime(800); controller.send({ type: 'PAUSE', paused: true });
  const calls = random.mock.calls.length;
  jest.advanceTimersByTime(30000);
  expect(controller.getDiceTimeRemaining()).toBe(1700);
  expect(random).toHaveBeenCalledTimes(calls);
  controller.send({ type: 'PAUSE', paused: false }); jest.advanceTimersByTime(1699);
  expect(controller.getSnapshot().gamePhase).toBe('rolling');
  jest.advanceTimersByTime(1); expect(controller.getSnapshot().gamePhase).toBe('showing_question');
  controller.disconnect();
});

test('bot answers after ten active seconds, excluding paused time', () => {
  expect(BOT_ANSWER_DELAY_MS).toBe(10000);
  const controller = new RaceController(() => .55); controller.connect();
  controller.startGame('single', [player('p1'), player('p2')]);
  jest.advanceTimersByTime(850 + DICE_ROLL_DURATION_MS);
  expect(controller.getSnapshot().gamePhase).toBe('showing_question');
  jest.advanceTimersByTime(6000); controller.send({ type: 'PAUSE', paused: true });
  jest.advanceTimersByTime(30000);
  expect(controller.getSnapshot().gamePhase).toBe('showing_question');
  controller.send({ type: 'PAUSE', paused: false }); jest.advanceTimersByTime(3999);
  expect(controller.getSnapshot().gamePhase).toBe('showing_question');
  jest.advanceTimersByTime(1); expect(controller.getSnapshot().gamePhase).toBe('evaluating_answer');
  expect(controller.getLearnerCounts()).toEqual({ correct: 0, incorrect: 0 });
  controller.disconnect(); expect(jest.getTimerCount()).toBe(0);
});

test('restart invalidates a bot answer that was still pending', () => {
  const controller = new RaceController(() => .55); controller.connect();
  controller.startGame('single', [player('p1'), player('p2')]);
  jest.advanceTimersByTime(850 + DICE_ROLL_DURATION_MS + 9000);
  controller.startGame('single', [player('p1', false), player('p2')]);
  const fresh = controller.getSnapshot(); jest.advanceTimersByTime(30000);
  expect(controller.getSnapshot()).toBe(fresh);
  controller.disconnect(); expect(jest.getTimerCount()).toBe(0);
});
