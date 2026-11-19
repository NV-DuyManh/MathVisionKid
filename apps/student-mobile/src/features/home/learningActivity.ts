import type { StudentProfile } from '../student-profile/profileApi';

export const WEEKLY_ACTIVITY_GOAL = 5;

/** Backend-confirmed completions grouped in the same Vietnam time zone as profile statistics. */
export function buildCompletedLearningActivity(history: StudentProfile['history'], now = new Date()) {
  const vietnamDate = (instant: Date) => new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(instant);
  const today = vietnamDate(now);
  const calendar = new Date(`${today}T00:00:00Z`);
  const completed = new Set(history.filter(row => ['LESSON', 'QUIZ', 'GAME'].includes(row.source)
    && Number.isFinite(Date.parse(row.completedAt)) && Date.parse(row.completedAt) <= now.getTime())
    .map(row => vietnamDate(new Date(row.completedAt))));
  calendar.setUTCDate(calendar.getUTCDate() - (calendar.getUTCDay() + 6) % 7);
  return { days: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((label, index) => {
    const day = new Date(calendar);
    day.setUTCDate(day.getUTCDate() + index);
    const key = day.toISOString().slice(0, 10);
    return { label, today: key === today, completed: completed.has(key) };
  }) };
}
