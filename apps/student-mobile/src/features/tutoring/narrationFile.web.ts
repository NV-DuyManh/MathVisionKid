import { audioCues, type AudioCue } from './audioCues';
export function saveNarration(bytes: Uint8Array): { uri: string; dispose: () => void; cues?: AudioCue[] } {
  const uri = URL.createObjectURL(new Blob([new Uint8Array(bytes).buffer], { type: 'audio/wav' }));
  return { uri, cues: audioCues(bytes), dispose: () => URL.revokeObjectURL(uri) };
}
