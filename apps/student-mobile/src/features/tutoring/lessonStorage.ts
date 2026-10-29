import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';

const validKey = (key: string) => /^mathvision_[a-z0-9_-]{1,1400}$/.test(key);
export async function readLessonStorage(key: string): Promise<string | null> {
  if (!validKey(key)) return null;
  if (Platform.OS === 'web') return typeof localStorage === 'undefined' ? null : localStorage.getItem(key);
  if (!FileSystem.documentDirectory) return null;
  const path = `${FileSystem.documentDirectory}${key}.json`;
  return (await FileSystem.getInfoAsync(path)).exists ? FileSystem.readAsStringAsync(path) : null;
}
let writes = Promise.resolve();
export function writeLessonStorage(key: string, raw: string): Promise<void> {
  if (!validKey(key) || raw.length > 250000) return Promise.reject(new Error('Invalid learning storage'));
  if(Platform.OS==='web'){
    try{if(typeof localStorage==='undefined')throw new Error('Learning storage unavailable');localStorage.setItem(key,raw);return Promise.resolve();}
    catch(error){return Promise.reject(error);}
  }
  const operation = writes.catch(() => {}).then(async () => {
    if (FileSystem.documentDirectory) await FileSystem.writeAsStringAsync(`${FileSystem.documentDirectory}${key}.json`, raw);
    else throw new Error('Learning storage unavailable');
  });
  writes = operation;
  return operation;
}
