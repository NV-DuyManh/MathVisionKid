import { File, Paths } from 'expo-file-system';
import { audioCues, type AudioCue } from './audioCues';
export async function saveNarration(bytes: Uint8Array): Promise<{ uri: string; dispose: () => void; cues?: AudioCue[] }> {
  const file = new File(Paths.cache, `narration-${Date.now()}-${Math.random().toString(36).slice(2)}.wav`);
  file.create();
  // Speech prefetch must yield to taps/scrolling while native storage writes the WAV.
  try { await file.write(bytes); }
  catch (error) { try { file.delete(); } catch { /* Keep the original write failure. */ } throw error; }
  return { uri: file.uri, cues: audioCues(bytes), dispose: () => { try { file.delete(); } catch { /* Cache already released. */ } } };
}
