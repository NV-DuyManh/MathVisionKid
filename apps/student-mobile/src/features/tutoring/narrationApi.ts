import apiClient from '../../services/api/apiClient';
import { DEFAULT_NARRATION_VOICE, isNarrationVoice, NarrationVoice } from './narrationVoices';

export type NarrationSource = { sessionId: string; revision: number };
export async function downloadNarration(source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice = DEFAULT_NARRATION_VOICE): Promise<Uint8Array> {
  const parts = paragraphs.map(part => part.trim()).filter(Boolean);
  if (!isNarrationVoice(voice) || !source.sessionId || source.sessionId.length < 20 || !Number.isInteger(source.revision) || source.revision < 0
    || !parts.length || parts.length > 80 || parts.some(part => part.length > 1600) || parts.join('').length > 4000) throw new Error('Chưa mở được lời giảng.');
  const { data } = await apiClient.post('/student/tutor/lesson/narration', { ...source, paragraphs: parts, voice },
    { signal, timeout: 45000, responseType: 'arraybuffer', headers: { Accept: 'audio/wav' } });
  const bytes = new Uint8Array(data);
  if (bytes.length <= 44 || bytes.length > 8 * 1024 * 1024 || bytes[0] !== 82 || bytes[1] !== 73 || bytes[2] !== 70 || bytes[3] !== 70
    || bytes[8] !== 87 || bytes[9] !== 65 || bytes[10] !== 86 || bytes[11] !== 69) throw new Error('Chưa mở được lời giảng.');
  return bytes;
}
