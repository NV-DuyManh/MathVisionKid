import type { RecognitionSession } from '../recognition/analytics/recognitionAnalyticsStore';

type SavedSession = Pick<RecognitionSession, 'sessionId' | 'timestamp' | 'isSampleData'>;

function dayKey(date: Date) {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

/** Local confirmed history only; sample benchmarks never count as learning. */
export function buildLearningActivity(sessions: SavedSession[], now = new Date()) {
  const completed = new Set(sessions
    .filter(session => !session.isSampleData && !session.sessionId.startsWith('session_benchmark_')
      && Number.isFinite(session.timestamp) && session.timestamp <= now.getTime())
    .map(session => dayKey(new Date(session.timestamp))));
  const cursor = new Date(now);
  if (!completed.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (completed.has(dayKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  const monday = new Date(now);
  monday.setDate(monday.getDate() - (monday.getDay() + 6) % 7);
  const days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map((label, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + index);
    return { label, date: date.toLocaleDateString('vi-VN'), completed: completed.has(dayKey(date)) };
  });
  return { streak, days, completedToday: completed.has(dayKey(now)) };
}
