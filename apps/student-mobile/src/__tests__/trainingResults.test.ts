import { TrainingResultStore } from '../features/training-games/resultStore';
import { trainingStudentId } from '../features/training-games/identity';
import { TrainingSessionBridge, type TrainingSessionResult } from '@mathvisionkid/training-games';

jest.mock('@react-native-async-storage/async-storage', () => ({ __esModule: true, default: { getItem: jest.fn(), setItem: jest.fn() } }));
const A = '11111111-1111-4111-8111-111111111111', B = '22222222-2222-4222-8222-222222222222';
const result = (studentId = A, sessionId = 'one'): TrainingSessionResult => ({ schemaVersion: 1, eventId: `${sessionId}:result:v1`, sessionId, studentId, gameId: 'planet-rescue', gameVersion: '0.1.0', mode: 'easy', startedAt: '2026-10-24T00:00:00Z', completedAt: '2026-10-24T00:01:00Z', playtimeSeconds: 60, status: 'won', score: 80, maxScore: 100, correctCount: 8, incorrectCount: 1, skillsPracticed: ['Phân số'], pauseCount: 1, syncStatus: 'local-only' });
function memory() { const rows = new Map<string, string>(); return { rows, getItem: jest.fn(async (key: string) => rows.get(key) ?? null), setItem: jest.fn(async (key: string, value: string) => { rows.set(key, value); }) }; }
test('uses authenticated student UUID only, never demo, email, display name or teacher account', () => {
  expect(trainingStudentId({ role: 'STUDENT', userId: A }, true)).toBe(A);
  for (const user of [{ role: 'STUDENT', email: 'fixture@example.invalid' }, { role: 'STUDENT', id: 'local-learner-sandbox-01' }, { role: 'TEACHER', userId: A }, { id: A }]) expect(trainingStudentId(user, true)).toBeNull();
  expect(trainingStudentId({ role: 'STUDENT', id: A }, false)).toBeNull();
});
test('A login/play/logout, B login/play, A login again: both histories stay isolated', async () => {
  const disk = memory(), store = new TrainingResultStore(disk);
  await store.save(A, result(A, 'a')); expect(await store.history(B, 'planet-rescue')).toEqual([]);
  await store.save(B, result(B, 'b'));
  expect((await store.history(A, 'planet-rescue')).map(row => row.sessionId)).toEqual(['a']);
  expect((await store.history(B, 'planet-rescue')).map(row => row.sessionId)).toEqual(['b']);
  expect(await store.history(A, 'block-island')).toEqual([]);
});
test('concurrent duplicate completion is idempotent and preserves different sessions', async () => {
  const store = new TrainingResultStore(memory());
  await Promise.all([store.save(A, result()), store.save(A, result()), store.save(A, result(A, 'two'))]);
  expect((await store.history(A, 'planet-rescue')).map(row => row.sessionId).sort()).toEqual(['one', 'two']);
  await expect(store.save(B, result(A))).rejects.toThrow('owner');
  await expect(store.save(A, { ...result(), eventId: 'fake' })).rejects.toThrow();
});
test('storage failure is visible, pending result retries, corrupt data is preserved', async () => {
  const disk = memory(), store = new TrainingResultStore(disk); disk.setItem.mockRejectedValueOnce(Error('full'));
  await expect(store.save(A, result())).rejects.toThrow('full'); expect(store.error(A)).toBeTruthy(); expect(store.error(B)).toBeNull();
  await store.retry(A); expect(store.error(A)).toBeNull(); expect(await store.history(A, 'planet-rescue')).toHaveLength(1);
  const key = [...disk.rows.keys()][0]; disk.rows.set(key, 'corrupt');
  await expect(store.save(A, result(A, 'next'))).rejects.toThrow(); expect(disk.rows.get(key)).toBe('corrupt');
});
test('late asynchronous callback from A cannot write into B, bridge ignores post-disposal events', async () => {
  const disk = memory(), store = new TrainingResultStore(disk); const pending: Promise<void>[] = [];
  const bridge = new TrainingSessionBridge({ studentId: A, gameId: 'planet-rescue', mountId: 'a-mount', onResult: value => { pending.push(store.save(A, value)); } });
  bridge.observe({ attemptId: 'a', started: true, paused: false, mode: 'easy', skillsPracticed: ['Phân số'] });
  bridge.dispose(); await store.save(B, result(B, 'b')); bridge.observe({ attemptId: 'late', started: true, paused: false, mode: 'easy', status: 'won', skillsPracticed: [] });
  await Promise.all(pending);
  expect((await store.history(A, 'planet-rescue'))[0].status).toBe('abandoned');
  expect((await store.history(B, 'planet-rescue')).map(row => row.sessionId)).toEqual(['b']);
});
