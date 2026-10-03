import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';

export type SavedLesson = {
  id: string; timestamp: number; problemText: string; workText: string;
  reflection: string; reviewedSteps: number;
};
// Save text only; private photos never enter the learning archive.
function storageKey(owner?: string) {
  return owner ? `mathvision_lessons_${Array.from(owner).map(c => c.codePointAt(0)!.toString(16)).join('_')}` : null;
}
function valid(value: any): value is SavedLesson {
  return value && typeof value.id === 'string' && value.id.length > 0 && value.id.length <= 100
    && Number.isFinite(value.timestamp) && value.timestamp > 0 && value.timestamp <= Date.now()
    && typeof value.problemText === 'string' && value.problemText.length <= 4000
    && typeof value.workText === 'string' && value.workText.length <= 6000
    && typeof value.reflection === 'string' && value.reflection.length <= 2000
    && Number.isInteger(value.reviewedSteps) && value.reviewedSteps >= 0 && value.reviewedSteps <= 35;
}
export async function loadLessons(owner?: string): Promise<SavedLesson[]> {
  const key = storageKey(owner);
  if (!key) return [];
  let raw: string | null = null;
  if (Platform.OS === 'web') raw = typeof localStorage === 'undefined' ? null : localStorage.getItem(key);
  else if (FileSystem.documentDirectory) {
    const path = `${FileSystem.documentDirectory}${key}.json`;
    if ((await FileSystem.getInfoAsync(path)).exists) raw = await FileSystem.readAsStringAsync(path);
  }
  if (!raw) return [];
  try {
    const items = JSON.parse(raw);
    return Array.isArray(items) ? items.filter(valid).slice(0, 30) : [];
  } catch { return []; }
}
let writes = Promise.resolve();
export function saveLesson(owner: string | undefined, lesson: SavedLesson) {
  const operation = writes.catch(() => {}).then(async () => {
    const key = storageKey(owner);
    if (!key || !valid(lesson)) throw new Error('Không lưu được bài học.');
    const previous = await loadLessons(owner);
    const existing = previous.find(item => item.id === lesson.id);
    const items = [{ ...lesson, timestamp: existing?.timestamp ?? lesson.timestamp,
      reviewedSteps: Math.max(lesson.reviewedSteps, existing?.reviewedSteps ?? 0) },
      ...previous.filter(item => item.id !== lesson.id)].slice(0, 30);
    const raw = JSON.stringify(items);
    if (Platform.OS === 'web' && typeof localStorage !== 'undefined') localStorage.setItem(key, raw);
    else if (FileSystem.documentDirectory) await FileSystem.writeAsStringAsync(`${FileSystem.documentDirectory}${key}.json`, raw);
    else throw new Error('Không lưu được bài học.');
  });
  writes = operation;
  return operation;
}
