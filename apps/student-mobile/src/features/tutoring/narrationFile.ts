import { File, Paths } from 'expo-file-system';
export function saveNarration(bytes: Uint8Array): { uri: string; dispose: () => void } {
  const file = new File(Paths.cache, `narration-${Date.now()}-${Math.random().toString(36).slice(2)}.wav`);
  file.create(); file.writeSync(bytes);
  return { uri: file.uri, dispose: () => { try { file.delete(); } catch { /* Cache already released. */ } } };
}
