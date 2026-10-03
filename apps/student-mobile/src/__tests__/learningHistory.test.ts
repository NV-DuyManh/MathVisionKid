import { Platform } from 'react-native';
import { loadLessons, saveLesson } from '../features/tutoring/learningHistory';

const records = new Map<string, string>();
Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: {
  getItem: (key: string) => records.get(key) ?? null,
  setItem: (key: string, value: string) => records.set(key, value),
} });
const lesson = () => ({ id: 'lesson-1', timestamp: Date.now()-1000, problemText: 'Tính 24 + 18.',
  workText: '', reflection: 'Em chọn phép cộng.', reviewedSteps: 1 });
const nativeOS = Platform.OS;
beforeEach(() => { Object.defineProperty(Platform, 'OS', { configurable: true, value: 'web' }); records.clear(); });
afterAll(() => Object.defineProperty(Platform, 'OS', { configurable: true, value: nativeOS }));

it('persists a real learning record and keeps accounts isolated', async () => {
  const first = lesson();
  await saveLesson('student-a', first);
  expect(await loadLessons('student-a')).toEqual([first]);
  expect(await loadLessons('student-b')).toEqual([]);
  expect(await loadLessons()).toEqual([]);
});
it('updates a saved lesson without inflating daily activity or losing progress', async () => {
  const first = lesson();
  await saveLesson('student-a', first);
  await saveLesson('student-a', { ...first, timestamp: Date.now(), reviewedSteps: 0, reflection: 'Em thử lại.' });
  expect(await loadLessons('student-a')).toEqual([{ ...first, reflection: 'Em thử lại.' }]);
});
it('does not report a successful save without an account or valid content', async () => {
  await expect(saveLesson(undefined, lesson())).rejects.toThrow();
  await expect(saveLesson('a', { ...lesson(), workText: 'x'.repeat(6001) })).rejects.toThrow();
  expect(records.size).toBe(0);
});
