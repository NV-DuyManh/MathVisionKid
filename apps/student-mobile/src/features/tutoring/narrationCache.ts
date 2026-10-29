import { downloadNarration, prioritizeNarration, NARRATION_WAIT_SECONDS, type NarrationSource, type NarrationProgress, type NarrationProgressListener } from './narrationApi';
import type { NarrationVoice } from './narrationVoices';
import { saveNarration } from './narrationFile';
import { measureVoice } from './voiceMetrics';

type Entry = { controller: AbortController; promise: Promise<Uint8Array>; users: number; foregroundUsers: number; bytes: number; expires: number; prefetch: boolean; deadline: number;
  source: NarrationSource; text: string; asset?: ReturnType<typeof saveNarration>; evicted?: boolean;
  progress?: NarrationProgress; failed?: boolean; listeners: Set<NarrationProgressListener> };
export type NarrationCache = ReturnType<typeof createNarrationCache>;
const cacheKey = (source: NarrationSource, parts: string[], voice: NarrationVoice) =>
  JSON.stringify([source.sessionId, source.revision, voice, !!source.useFallback, parts.map(part => part.trim().replace(/\s+/g, ' ')).filter(Boolean)]);

/** One lesson-screen lifetime, never global or persisted across accounts. */
export function createNarrationCache() {
  const entries = new Map<string, Entry>();
  const drop = (key: string, entry: Entry) => {
    if (entries.get(key) === entry) entries.delete(key);
    entry.evicted = true;
    if (!entry.users) { entry.asset?.dispose(); entry.asset = undefined; }
  };
  const prune = () => {
    let size = [...entries.values()].reduce((total, entry) => total + entry.bytes, 0);
    for (const [key, entry] of entries) {
      if (entry.bytes && (entry.expires <= Date.now() || entries.size > 4 || size > 16 * 1024 * 1024)) {
        drop(key, entry); size -= entry.bytes;
      }
    }
  };
  return {
    acquire(source: NarrationSource, paragraphs: string[], voice: NarrationVoice, background = false, onProgress?: NarrationProgressListener) {
      prune();
      const parts = paragraphs.map(part => part.trim().replace(/\s+/g, ' ')).filter(Boolean);
      const key = cacheKey(source, parts, voice);
      let entry = entries.get(key);
      if (!entry) {
        // A new server-checked turn may issue the same text again. Move only a
        // completed local file; in-flight work must still use its own revision.
        for (const [oldKey, ready] of entries) {
          if (ready.bytes && ready.expires > Date.now() && ready.source.revision < source.revision
            && oldKey === cacheKey({ ...source, revision: ready.source.revision }, parts, voice)) {
            entries.delete(oldKey);
            ready.source = { ...source, prefetch: false }; ready.prefetch = false;
            entry = ready; break;
          }
        }
      }
      if (__DEV__ && !background) console.info('[narration-latency]', { stage: 'cache', state: entry?.bytes ? 'ready' : entry ? 'pending' : 'miss',
        revision: source.revision, voice, paragraphs: parts.length, characters: parts.join('').length });
      const measure = measureVoice('prepare',voice,{background,cache:entry?.bytes?'ready':entry?'pending':'miss'});
      if (!background && !entry?.bytes) {
        if (entry?.prefetch && !entry.controller.signal.aborted && entry.deadline > Date.now()) {
          // Promote the same work once. Keep its original download and deadline.
          entry.prefetch = false;
          entry.source.prefetch = false;
          void prioritizeNarration(source, parts, entry.controller.signal, voice, entry.deadline-Date.now()).catch(() => {});
        }
        // A tap for new content takes priority over speculative work for another voice/step.
        for (const [otherKey, other] of entries) {
          const sameScript = other.source.sessionId === source.sessionId && other.source.revision === source.revision
            && !!other.source.useFallback === !!source.useFallback && other.text === JSON.stringify(parts);
          if (otherKey !== key && !sameScript && !other.bytes && !other.foregroundUsers) { other.controller.abort(); drop(otherKey, other); }
        }
      }
      if (!entry) {
        const controller = new AbortController();
        const downloadSource = { ...source, prefetch: background };
        const next: Entry = { controller, users: 0, foregroundUsers: 0, bytes: 0, expires: Infinity, prefetch: background,
          source: downloadSource, text: JSON.stringify(parts), deadline: Date.now()+NARRATION_WAIT_SECONDS*1000, promise: Promise.resolve(new Uint8Array()), listeners: new Set() };
        next.promise = downloadNarration(downloadSource, parts, controller.signal, voice, progress => {
          if (controller.signal.aborted) return;
          next.progress = progress;
          next.listeners.forEach(listener => listener(progress));
        }).then(bytes => {
          if (controller.signal.aborted) throw new Error('Đã dừng chuẩn bị âm thanh.');
          // Write once while reading; reopening the sheet reuses the local file directly.
          next.asset = saveNarration(bytes);
          next.bytes = bytes.byteLength; next.expires = Date.now() + 5 * 60 * 1000;
          prune();
          return bytes;
        }).catch(error => {
          next.failed = !controller.signal.aborted;
          controller.abort();
          drop(key, next);
          throw error;
        });
        entry = next; entries.set(key, entry);
      } else {
        entries.delete(key); entries.set(key, entry);
      }
      const current = entry;
      void current.promise.then(()=>measure('ready'),()=>measure(current.failed?'failed':'cancelled'));
      current.users++;
      if (!background) current.foregroundUsers++;
      // Each lease owns its subscription, even if two views pass the same callback.
      const listener = onProgress ? (progress: NarrationProgress) => { try { onProgress(progress); } catch { /* Keep other listeners and audio usable. */ } } : undefined;
      if (listener) { current.listeners.add(listener); if (current.progress) listener(current.progress); }
      let released = false;
      return { promise: current.promise, get asset() { return current.asset; }, release() {
        if (released) return;
        if(!current.bytes)measure('cancelled');
        released = true; if (listener) current.listeners.delete(listener);
        current.users--; if (!background) current.foregroundUsers--;
        if (!current.users && !current.bytes) {
          current.controller.abort();
          drop(key, current);
        }
        if (!current.users && current.evicted) { current.asset?.dispose(); current.asset = undefined; }
      } };
    },
    clear() {
      for (const [key, entry] of entries) { entry.controller.abort(); drop(key, entry); }
    },
    forget(source: NarrationSource, paragraphs: string[], voice: NarrationVoice) {
      const key = cacheKey(source, paragraphs, voice);
      const entry = entries.get(key);
      if (entry) { entry.controller.abort(); drop(key, entry); }
    },
  };
}

/** Hold the warm local file until the player releases it; no second write on sheet open. */
export async function getPreparedNarrationAsset(cache: NarrationCache | null, source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice, onProgress?: NarrationProgressListener): Promise<ReturnType<typeof saveNarration>> {
  if (signal.aborted) throw new Error('Đã dừng tải âm thanh.');
  if (!cache) {
    const bytes = await downloadNarration(source, paragraphs, signal, voice, onProgress);
    if (signal.aborted) throw new Error('Đã dừng tải âm thanh.');
    return saveNarration(bytes);
  }
  const lease = cache.acquire(source, paragraphs, voice, false, onProgress);
  return new Promise((resolve, reject) => {
    const abort = () => { lease.release(); reject(new Error('Đã dừng tải âm thanh.')); };
    signal.addEventListener('abort', abort, { once: true });
    lease.promise.then(() => {
      if (signal.aborted) return;
      const asset = lease.asset;
      if (!asset) { lease.release(); reject(new Error('Chưa mở được tệp âm thanh.')); return; }
      resolve({ uri: asset.uri, cues: asset.cues, dispose: lease.release });
    }, error => { lease.release(); reject(error); }).finally(() => signal.removeEventListener('abort', abort));
    if (signal.aborted) abort();
  });
}

/** Closing a sheet releases its interest without cancelling an active warm-up. */
export function downloadPreparedNarration(cache: NarrationCache | null, source: NarrationSource, paragraphs: string[], signal: AbortSignal, voice: NarrationVoice, onProgress?: NarrationProgressListener): Promise<Uint8Array> {
  if (signal.aborted) return Promise.reject(new Error('Đã dừng tải âm thanh.'));
  if (!cache) return downloadNarration(source, paragraphs, signal, voice, onProgress);
  const lease = cache.acquire(source, paragraphs, voice, false, onProgress);
  return new Promise<Uint8Array>((resolve, reject) => {
    const abort = () => { lease.release(); reject(new Error('Đã dừng tải âm thanh.')); };
    signal.addEventListener('abort', abort, { once: true });
    lease.promise.then(bytes => { if (!signal.aborted) resolve(bytes); }, reject).finally(() => {
      signal.removeEventListener('abort', abort); lease.release();
    });
    if (signal.aborted) abort();
  });
}
