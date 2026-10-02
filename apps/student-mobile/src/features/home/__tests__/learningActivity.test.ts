import { buildLearningActivity } from '../learningActivity';

const now = new Date(2026, 9, 2, 15);
const saved = (day: number, id = `saved-${day}`) => ({ sessionId: id, timestamp: new Date(2026, 9, day, 10).getTime() });

describe('Learning activity from confirmed local history', () => {
  it('starts empty and excludes benchmark samples and future dates', () => {
    const activity = buildLearningActivity([
      { ...saved(2), isSampleData: true }, saved(1, 'session_benchmark_1'), saved(3),
    ], now);
    expect(activity.streak).toBe(0);
    expect(activity.days.every(day => !day.completed)).toBe(true);
  });
  it('counts one completed day once and permits yesterday until today is completed', () => {
    const activity = buildLearningActivity([saved(1), saved(1, 'another-saved'), saved(0)], now);
    expect(activity.streak).toBe(2);
    expect(activity.completedToday).toBe(false);
    expect(activity.days.filter(day => day.completed).map(day => day.label)).toEqual(['T4', 'T5']);
  });
  it('breaks on a missed day and marks the correct weekday for today', () => {
    const activity = buildLearningActivity([saved(2), saved(0)], now);
    expect(activity.streak).toBe(1);
    expect(activity.completedToday).toBe(true);
    expect(activity.days[4]).toMatchObject({ label: 'T6', completed: true });
  });
});
