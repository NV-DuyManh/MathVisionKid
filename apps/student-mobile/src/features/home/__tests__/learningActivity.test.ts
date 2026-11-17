import { buildCompletedLearningActivity } from '../learningActivity';

const now = new Date('2026-11-16T17:30:00Z'); // Tuesday 00:30 in Vietnam.
const completed = (completedAt: string) => ({ source: 'LESSON' as const, completedAt, stars: 1 });

it('uses completed backend activity and Vietnam days across UTC midnight', () => {
  const activity = buildCompletedLearningActivity([
    completed('2026-11-15T17:10:00Z'), completed('2026-11-16T17:10:00Z'),
    completed('2026-11-16T17:20:00Z'), completed('invalid'), completed('2026-11-17T17:10:00Z'),
  ], now);
  expect(activity.days.filter(day => day.completed).map(day => day.label)).toEqual(['T2', 'T3']);
  expect(activity.days.find(day => day.today)).toEqual({ label: 'T3', today: true, completed: true });
});

it('does not invent completed days when history has not arrived', () => {
  const activity = buildCompletedLearningActivity([], now);
  expect(activity.days.every(day => !day.completed)).toBe(true);
  expect(activity.days.filter(day => day.today)).toHaveLength(1);
});
