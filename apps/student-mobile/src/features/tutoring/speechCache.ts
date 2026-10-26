import { TutorService } from './api/TutorService';
import { narrationSegments } from './narration';
import { readSpeechPreferences } from './speechPreferences';

type Entry = { controller: AbortController; promise: Promise<Uint8Array>; expires: number; bytes?: Uint8Array };
const entries = new Map<string, Entry>();
const TTL = 10 * 60 * 1000, MAX_BYTES = 8 * 1024 * 1024, MAX_ENTRIES = 12;
let owner = '', generation = 0;
const canceled = () => new Error('Speech preparation canceled');
// The fixed reading introduction from lesson.py:source_understanding. This is
// speculative cache fill only: playback always requests the checked response's
// exact text, so a different/updated introduction simply misses this cache.
const READING_OPENING = [
  'Đọc lại nguyên đề. Tách điều đã biết và điều cần tìm trước khi tính.',
  'Nhìn tên đồ vật, số lượng và đơn vị trong mỗi lựa chọn. Chọn câu khớp với điều đang hỏi.',
  'Câu nào là điều đề đã cho biết?',
];

export function clearSpeechCache(): void {
  generation++;
  for (const entry of entries.values()) entry.controller.abort();
  entries.clear();
}

export function setSpeechOwner(value: string): void {
  if (owner !== value) { clearSpeechCache(); owner = value; }
}

export async function prefetchLessonOpening(signal?: AbortSignal): Promise<void> {
  const { voiceId } = await readSpeechPreferences();
  if (signal?.aborted) return;
  await getSpeechAudio(narrationSegments(READING_OPENING)[0], voiceId, signal);
}

function trimCache() {
  for (const [key, entry] of entries) {
    if (entry.expires <= Date.now()) { entry.controller.abort(); entries.delete(key); }
  }
  let size = [...entries.values()].reduce((sum, entry) => sum + (entry.bytes?.byteLength || 0), 0);
  while (entries.size > MAX_ENTRIES || size > MAX_BYTES) {
    const [key, entry] = entries.entries().next().value!;
    size -= entry.bytes?.byteLength || 0;
    entry.controller.abort(); entries.delete(key);
  }
}

function waitForAudio(promise: Promise<Uint8Array>, signal?: AbortSignal): Promise<Uint8Array> {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(canceled());
  return new Promise((resolve, reject) => {
    const abort = () => { signal.removeEventListener('abort', abort); reject(canceled()); };
    signal.addEventListener('abort', abort, { once: true });
    promise.then(bytes => {
      signal.removeEventListener('abort', abort);
      if (signal.aborted) reject(canceled()); else resolve(bytes);
    }, error => { signal.removeEventListener('abort', abort); reject(error); });
  });
}

/** Account-private bytes only. Players/files remain owned by each playback. */
export function getSpeechAudio(text: string, voice: string, signal?: AbortSignal): Promise<Uint8Array> {
  if (signal?.aborted) return Promise.reject(canceled());
  trimCache();
  const key = JSON.stringify([owner, voice, text]);
  let entry = entries.get(key);
  if (entry) {
    entries.delete(key); entries.set(key, entry);
  } else {
    const epoch = generation, controller = new AbortController();
    const created: Entry = { controller, expires: Date.now() + TTL, promise: Promise.resolve(new Uint8Array()) };
    entries.set(key, created);
    created.promise = Promise.resolve().then(() => {
      if (controller.signal.aborted) throw canceled();
      // Pace is applied by the player; all three speeds reuse the same MP3.
      return TutorService.synthesizeSpeech(text, voice, 1, controller.signal);
    }).then(bytes => {
      if (generation !== epoch || controller.signal.aborted || entries.get(key) !== created) throw canceled();
      created.bytes = bytes; trimCache(); return bytes;
    }).catch(error => {
      if (entries.get(key) === created) entries.delete(key);
      throw error;
    });
    entry = created;
    trimCache();
  }
  return waitForAudio(entry.promise, signal);
}

/** Warm the first clip, then a bounded look-ahead without delaying playback. */
export function warmSpeechSegments(segments: string[], voice: string, signal?: AbortSignal): Promise<Uint8Array> {
  if (!segments.length) return Promise.resolve(new Uint8Array());
  const epoch = generation;
  const first = getSpeechAudio(segments[0], voice, signal);
  let firstFailed = false;
  void first.catch(() => { firstFailed = true; });
  // Fetch the next clip alongside the opening. Later look-ahead stays sequential
  // to fit the existing two-request synthesis limit.
  void (async () => {
    for (const segment of segments.slice(1, 4)) {
      if (firstFailed || generation !== epoch || signal?.aborted) return;
      await getSpeechAudio(segment, voice, signal);
    }
  })().catch(() => {});
  return first;
}

/** Audio is optional: a slow provider must not hold a valid lesson indefinitely. */
export async function prefetchNarration(paragraphs: string[], signal?: AbortSignal, waitMs = 4000): Promise<boolean> {
  const preferences = await readSpeechPreferences();
  if (signal?.aborted) throw canceled();
  const segments = narrationSegments(paragraphs);
  if (!segments.length) return true;
  const first = warmSpeechSegments(segments, preferences.voiceId, signal);
  if (waitMs === 0) { void first.catch(() => {}); return false; }
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      first.then(() => true),
      new Promise<false>(resolve => { timer = setTimeout(() => resolve(false), waitMs); }),
    ]);
  } catch {
    if (signal?.aborted) throw canceled();
    return false;
  } finally { clearTimeout(timer); }
}
