import apiClient from '../../services/api/apiClient';
import { measureVoice } from './voiceMetrics';
import { DEFAULT_NARRATION_VOICE, isNarrationVoice, NarrationVoice } from './narrationVoices';

export type NarrationSource = { sessionId: string; revision: number; useFallback?: boolean; prefetch?: boolean };
export const NARRATION_WAIT_SECONDS = 60;
export type NarrationProgress = { phase: 'waiting' | 'synthesizing' | 'fallback' | 'decoding' | 'ready' | 'failed'; percent: number;
  mode: 'online' | 'offline'; elapsedMs: number; completedChunks: number; totalChunks: number; retrying?: boolean };
export type NarrationProgressListener = (progress: NarrationProgress) => void;
export async function prepareLessonMedia(source: NarrationSource, voice: NarrationVoice, signal: AbortSignal): Promise<void> {
  if (!isNarrationVoice(voice)) return;
  await apiClient.post('/student/tutor/lesson/media/prepare', { sessionId: source.sessionId, revision: source.revision, voice }, { signal, timeout: 5000 });
}
export async function prioritizeNarration(source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice, timeout = 5000): Promise<void> {
  if (signal.aborted || timeout <= 0 || !isNarrationVoice(voice)) return;
  await apiClient.post('/student/tutor/lesson/narration/prepare', {
    ...source, paragraphs: paragraphs.map(part => part.trim().replace(/\s+/g, ' ')).filter(Boolean), voice, prefetch: false,
  }, { signal, timeout: Math.max(1, Math.min(5000, timeout)) });
}
export async function readNarrationProgress(source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice, timeout = 3000): Promise<NarrationProgress> {
  const { data } = await apiClient.post('/student/tutor/lesson/narration/status', { ...source, paragraphs: paragraphs.map(p => p.trim().replace(/\s+/g, ' ')).filter(Boolean), voice }, { signal, timeout: Math.max(1, timeout) });
  if (!data || !['waiting', 'synthesizing', 'fallback', 'decoding', 'ready', 'failed'].includes(data.phase)
    || !['online', 'offline'].includes(data.mode) || !['percent', 'elapsedMs', 'completedChunks', 'totalChunks'].every(key => Number.isInteger(data[key]) && data[key] >= 0)
    || data.percent > 100 || data.completedChunks > data.totalChunks) throw new Error('Chưa đọc được tiến độ.');
  return { phase: data.phase, mode: data.mode, percent: data.percent, elapsedMs: data.elapsedMs,
    completedChunks: data.completedChunks, totalChunks: data.totalChunks };
}
function waitForCapacity(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const cancel = () => { clearTimeout(timer); signal.removeEventListener('abort', cancel); reject(new Error('Đã dừng tải âm thanh.')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', cancel); resolve(); }, milliseconds);
    signal.addEventListener('abort', cancel, { once: true });
    if (signal.aborted) cancel();
  });
}
function retryableProgressError(error: unknown): boolean {
  const failure = error as { code?: string; response?: { status?: number } } | null;
  return [408, 429, 500, 502, 503, 504].includes(failure?.response?.status || 0)
    || !failure?.response && ['ERR_NETWORK', 'ECONNABORTED', 'ETIMEDOUT', 'ECONNRESET'].includes(failure?.code || '');
}
export async function downloadNarration(source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice = DEFAULT_NARRATION_VOICE, onProgress?: NarrationProgressListener): Promise<Uint8Array> {
  const parts = paragraphs.map(part => part.trim().replace(/\s+/g, ' ')).filter(Boolean);
  if (!isNarrationVoice(voice) || !source.sessionId || source.sessionId.length < 20 || !Number.isInteger(source.revision) || source.revision < 0
    || !parts.length || parts.length > 80 || parts.some(part => part.length > 1600) || parts.join('').length > 4000) throw new Error('Chưa mở được lời giảng.');
  let data: ArrayBuffer;
  const deadline = Date.now() + NARRATION_WAIT_SECONDS * 1000;
  let started = false, prepareFailures = 0;
  let progress: NarrationProgress = { phase: 'waiting', mode: source.useFallback ? 'offline' : 'online', percent: 0, elapsedMs: 0, completedChunks: 0, totalChunks: 0 };
  const notify = (state: NarrationProgress) => {
    progress = state;
    if (!signal.aborted) { try { onProgress?.(state); } catch { /* An observer cannot invalidate audio. */ } }
  };
  const retrying = () => notify({ ...progress, retrying: true });
  while (Date.now() < deadline) {
    if (signal.aborted) throw new Error('Đã dừng tải âm thanh.');
    let checkingProgress = false;
    try {
      if (!started) {
        const { data: prepared } = await apiClient.post('/student/tutor/lesson/narration/prepare', { ...source, paragraphs: parts, voice }, { signal, timeout: Math.max(1, Math.min(5000, deadline-Date.now())) });
        prepareFailures = 0;
        started = true;
        if (prepared?.phase === 'ready') break;
      }
      if (Date.now() >= deadline) throw new Error('Đã hết thời gian chuẩn bị lời giảng.');
      checkingProgress = true;
      const state = await readNarrationProgress(source, parts, signal, voice, Math.min(3000, deadline-Date.now()));
      checkingProgress = false;
      // A view observing the shared download must not start another polling loop.
      notify(state);
      if (state.phase === 'ready') break;
      if (state.phase === 'failed') throw new Error('Chưa chuẩn bị được âm thanh. Em thử lại nhé.');
      // A completed job's WAV may have expired/been evicted. Idempotent prepare
      // can restore it; merely polling waiting would otherwise exhaust the deadline.
      if (state.phase === 'waiting') started = false;
    } catch (error) {
      const busy = (error as { response?: { status?: number } } | null)?.response?.status === 429;
      if (signal.aborted) throw error;
      // Preparation is idempotent: a lost acknowledgement must not fail a warm-up
      // that may already be rendering. Never restart failed jobs or stale lessons.
      if (!busy && !retryableProgressError(error)) throw error;
      if (!busy && !checkingProgress && (started || ++prepareFailures > 2)) throw error;
      retrying();
    }
    await waitForCapacity(Math.min(1000, Math.max(0, deadline-Date.now())), signal);
  }
  if (Date.now()>=deadline) throw new Error('Đã hết thời gian chuẩn bị lời giảng.');
  const transfer = measureVoice('transfer',voice,{background:source.prefetch});
  try {
  for (let attempt = 0; ; attempt++) {
    const remaining = deadline - Date.now();
    if (remaining <= 0) throw new Error('Chưa chuẩn bị được âm thanh.');
    try {
      ({ data } = await apiClient.post('/student/tutor/lesson/narration', { ...source, paragraphs: parts, voice },
        { signal, timeout: remaining, responseType: 'arraybuffer', headers: { Accept: 'audio/wav, application/json' } }));
      break;
    } catch (error) {
      // Fetch the same ready asset again after a transient transfer failure.
      // Keep the original deadline, source and voice; never retry auth/validation.
      if (signal.aborted || attempt >= 2 || !retryableProgressError(error)) throw error;
      const delay = 500 * (attempt + 1);
      if (Date.now() + delay >= deadline) throw error;
      retrying();
      await waitForCapacity(delay, signal);
    }
  }
  const bytes = new Uint8Array(data);
  if (bytes.length <= 44 || bytes.length > 8 * 1024 * 1024 || bytes[0] !== 82 || bytes[1] !== 73 || bytes[2] !== 70 || bytes[3] !== 70
    || bytes[8] !== 87 || bytes[9] !== 65 || bytes[10] !== 86 || bytes[11] !== 69) throw new Error('Chưa mở được lời giảng.');
  transfer('ready');return bytes;
  } catch(error) { transfer(signal.aborted?'cancelled':'failed'); throw error; }
}
