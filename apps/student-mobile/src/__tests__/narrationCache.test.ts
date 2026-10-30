import { createNarrationCache, downloadPreparedNarration, getPreparedNarrationAsset } from '../features/tutoring/narrationCache';
import { saveNarration } from '../features/tutoring/narrationFile';
import { downloadNarration, prioritizeNarration } from '../features/tutoring/narrationApi';
import type { NarrationVoice } from '../features/tutoring/narrationVoices';
import type { NarrationProgress, NarrationProgressListener } from '../features/tutoring/narrationApi';
jest.mock('../features/tutoring/narrationFile', () => ({ saveNarration: jest.fn(() => ({ uri: 'file:///warm.wav', dispose: jest.fn() })) }));
jest.mock('../features/tutoring/narrationApi', () => ({ NARRATION_WAIT_SECONDS: 60, prioritizeNarration: jest.fn().mockResolvedValue(undefined), downloadNarration: jest.fn() }));
const source = { sessionId: 'owned-narration-prefetch-123', revision: 1 };
const male: NarrationVoice = 'vi-VN-NamMinhNeural', female: NarrationVoice = 'vi-VN-HoaiMyNeural';
const bytes = new Uint8Array(50), parts = ['Em gộp hai nhóm.'];
let cache: ReturnType<typeof createNarrationCache>;
beforeEach(() => { jest.useFakeTimers(); cache = createNarrationCache(); jest.clearAllMocks(); (downloadNarration as jest.Mock).mockReset().mockResolvedValue(bytes); (prioritizeNarration as jest.Mock).mockReset().mockResolvedValue(undefined); });
afterEach(() => { cache.clear(); jest.useRealTimers(); });

it('shares a warming request with an early tap and reuses the ready audio when reopening', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const warm = cache.acquire(source, parts, male);
  const play = downloadPreparedNarration(cache, source, [' Em gộp hai nhóm. ', ''], new AbortController().signal, male);
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  finish(bytes); await expect(play).resolves.toBe(bytes); warm.release();
  await expect(downloadPreparedNarration(cache, source, parts, new AbortController().signal, male)).resolves.toBe(bytes);
  expect(downloadNarration).toHaveBeenCalledTimes(1);
});

it('isolates content, voice, session and fallback while reusing ready identical text on a later checked turn', async () => {
  for (const [next, words, voice] of [[source, parts, male], [source, parts, female], [{ ...source, revision: 2 }, parts, male],
    [{ ...source, sessionId: 'other-owned-session-12345' }, parts, male], [source, ['Lời giảng khác'], male], [{ ...source, useFallback: true }, parts, male]] as const) {
    const lease = cache.acquire(next, [...words], voice); await lease.promise; lease.release();
  }
  expect(downloadNarration).toHaveBeenCalledTimes(5);
});

it('reuses the same ready local file across a checked revision without another download or write', async () => {
  const warm = cache.acquire(source, parts, male, true); await warm.promise; warm.release();
  const current = await getPreparedNarrationAsset(cache, { ...source, revision: 2 }, ['  Em   gộp hai nhóm. '], new AbortController().signal, male);
  expect(current.uri).toBe('file:///warm.wav');
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(saveNarration).toHaveBeenCalledTimes(1);
  current.dispose();
});

it('keeps a transferred file alive while either the old player or current player holds it', async () => {
  const old = cache.acquire(source, parts, male); await old.promise;
  const current = await getPreparedNarrationAsset(cache, { ...source, revision: 2 }, parts, new AbortController().signal, male);
  const file = (saveNarration as jest.Mock).mock.results[0].value;
  cache.forget({ ...source, revision: 2 }, parts, male);
  expect(file.dispose).not.toHaveBeenCalled();
  old.release(); expect(file.dispose).not.toHaveBeenCalled();
  current.dispose(); expect(file.dispose).toHaveBeenCalledTimes(1);
});

it('does not transfer unfinished work to another revision', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish=resolve; }));
  const old = cache.acquire(source, parts, male, true);
  const rejected = expect(old.promise).rejects.toThrow('Đã dừng');
  const current = cache.acquire({ ...source, revision: 2 }, parts, male);
  await current.promise; finish(bytes); await rejected;
  expect(downloadNarration).toHaveBeenCalledTimes(2);
  current.release(); old.release();
});

it('does not extend file expiry when identical text is issued on a newer turn', async () => {
  const first=cache.acquire(source,parts,male); await first.promise; first.release();
  jest.advanceTimersByTime(4*60*1000);
  const next=cache.acquire({...source,revision:2},parts,male); await next.promise; next.release();
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  jest.advanceTimersByTime(60*1000+1);
  const expired=cache.acquire({...source,revision:3},parts,male); await expired.promise; expired.release();
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('closing the sheet does not cancel a request still needed by background preparation', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const warm = cache.acquire(source, parts, male), controller = new AbortController();
  const play = downloadPreparedNarration(cache, source, parts, controller.signal, male);
  const rejected = expect(play).rejects.toThrow('Đã dừng'); controller.abort(); await rejected;
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(false);
  finish(bytes); await warm.promise; warm.release();
  await downloadPreparedNarration(cache, source, parts, new AbortController().signal, male);
  expect(downloadNarration).toHaveBeenCalledTimes(1);
});

it('cancels the request when no consumer remains and ignores its late result', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const first = cache.acquire(source, parts, male), rejected = expect(first.promise).rejects.toThrow('Đã dừng');
  first.release(); first.release();
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(true);
  const next = cache.acquire(source, parts, male); await next.promise;
  finish(bytes); await rejected;
  next.release(); const reused = cache.acquire(source, parts, male); await reused.promise; reused.release();
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('drops speculative failures so a later tap can retry normally', async () => {
  (downloadNarration as jest.Mock).mockRejectedValueOnce(new Error('Provider unavailable'));
  const warm = cache.acquire(source, parts, male); await expect(warm.promise).rejects.toThrow(); warm.release();
  await expect(downloadPreparedNarration(cache, source, parts, new AbortController().signal, male)).resolves.toBe(bytes);
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('expires cached audio after five minutes and drops the least recently used entries', async () => {
  const first = cache.acquire(source, parts, male); await first.promise; first.release();
  jest.advanceTimersByTime(300001);
  const expired = cache.acquire(source, parts, male); await expired.promise; expired.release();
  expect(downloadNarration).toHaveBeenCalledTimes(2);
  for (let i = 2; i <= 5; i++) { const lease = cache.acquire(source, [`Lời giảng riêng ${i}.`], male); await lease.promise; lease.release(); }
  const evicted = cache.acquire(source, parts, male); await evicted.promise; evicted.release();
  expect(downloadNarration).toHaveBeenCalledTimes(7);
});

it('bounds retained audio to sixteen MiB', async () => {
  (downloadNarration as jest.Mock).mockResolvedValue(new Uint8Array(6 * 1024 * 1024));
  for (let i = 1; i <= 3; i++) { const lease = cache.acquire(source, i === 1 ? parts : [`Lời giảng riêng ${i}.`], male); await lease.promise; lease.release(); }
  const evicted = cache.acquire(source, parts, male); await evicted.promise; evicted.release();
  expect(downloadNarration).toHaveBeenCalledTimes(4);
});

it('clears private state when leaving the lesson or account and invalidates decoder failures', async () => {
  const first = cache.acquire(source, parts, male); await first.promise; first.release();
  cache.forget(source, parts, male);
  const next = cache.acquire(source, parts, male); await next.promise; next.release();
  cache.clear();
  const fresh = cache.acquire(source, parts, male); await fresh.promise; fresh.release();
  expect(downloadNarration).toHaveBeenCalledTimes(3);
});

it('does not start work for an already cancelled consumer', async () => {
  const controller = new AbortController(); controller.abort();
  await expect(downloadPreparedNarration(cache, source, parts, controller.signal, male)).rejects.toThrow('Đã dừng');
  expect(downloadNarration).not.toHaveBeenCalled();
});

it('keeps the other voice for the same script alive when the pupil opens listening', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const alternate = cache.acquire(source, parts, female, true);
  const signal = (downloadNarration as jest.Mock).mock.calls[0][2];
  await downloadPreparedNarration(cache, source, parts, new AbortController().signal, male);
  expect(signal.aborted).toBe(false);
  finish(bytes); await alternate.promise; alternate.release();
  await downloadPreparedNarration(cache, source, parts, new AbortController().signal, female);
  expect(downloadNarration).toHaveBeenCalledTimes(2);
});

it('prioritizes an explicit request over unused speculative synthesis', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const warm = cache.acquire(source, parts, male, true), rejected = expect(warm.promise).rejects.toThrow('Đã dừng');
  await downloadPreparedNarration(cache, source, ['Giải thích câu hỏi mới.'], new AbortController().signal, female);
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(true);
  finish(bytes); await rejected; warm.release();
});

it('writes the file before a tap and reopens it without another download or disk write', async () => {
  const warm=cache.acquire(source,parts,male,true);await warm.promise;warm.release();
  expect(saveNarration).toHaveBeenCalledTimes(1);
  const first=await getPreparedNarrationAsset(cache,source,parts,new AbortController().signal,male);
  const file=(saveNarration as jest.Mock).mock.results[0].value;
  expect(first.uri).toBe(file.uri);first.dispose();
  const reopened=await getPreparedNarrationAsset(cache,source,parts,new AbortController().signal,male);
  expect(saveNarration).toHaveBeenCalledTimes(1);expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect(prioritizeNarration).not.toHaveBeenCalled();
  expect(file.dispose).not.toHaveBeenCalled();
  cache.clear();expect(file.dispose).not.toHaveBeenCalled();
  reopened.dispose();expect(file.dispose).toHaveBeenCalledTimes(1);
});

it('promotes a pending speculative entry once without another download or changing its signal', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish=resolve; }));
  const warm=cache.acquire({ ...source,prefetch:true },parts,male,true);
  const signal=(downloadNarration as jest.Mock).mock.calls[0][2];
  expect(downloadNarration).toHaveBeenCalledWith({ ...source,prefetch:true },parts,signal,male,expect.any(Function));
  const first=cache.acquire({ ...source,prefetch:false },parts,male);
  const second=cache.acquire(source,parts,male);
  expect(prioritizeNarration).toHaveBeenCalledTimes(1);
  expect(prioritizeNarration).toHaveBeenCalledWith({ ...source,prefetch:false },parts,signal,male,60000);
  expect(downloadNarration).toHaveBeenCalledTimes(1);expect(signal.aborted).toBe(false);
  finish(bytes);await expect(first.promise).resolves.toBe(bytes);await expect(second.promise).resolves.toBe(bytes);
  first.release();second.release();warm.release();
});

it('reuses the same local file across equivalent line breaks and whitespace', async () => {
  const warm = cache.acquire(source, ['  Em\n gộp\t hai  nhóm.  '], male, true);
  await warm.promise; warm.release();
  const first = await getPreparedNarrationAsset(cache, source, parts, new AbortController().signal, male);
  const replay = await getPreparedNarrationAsset(cache, source, ['Em  gộp hai\nnhóm.'], new AbortController().signal, male);
  expect(first.uri).toBe(replay.uri);
  expect(downloadNarration).toHaveBeenCalledTimes(1);
  expect((downloadNarration as jest.Mock).mock.calls[0][1]).toEqual(parts);
  expect(saveNarration).toHaveBeenCalledTimes(1);
  expect(prioritizeNarration).not.toHaveBeenCalled();
  first.dispose(); replay.dispose();
});

it('shares measured progress with late listeners and releases only that lease subscription', async () => {
  let finish!: (data: Uint8Array) => void, progress!: NarrationProgressListener;
  (downloadNarration as jest.Mock).mockImplementationOnce((_source, _parts, _signal, _voice, update) => {
    progress = update;
    return new Promise(resolve => { finish = resolve; });
  });
  const early = jest.fn(), late = jest.fn();
  const warm = cache.acquire(source, parts, male, true, early);
  const state: NarrationProgress = { phase: 'synthesizing', percent: 45, elapsedMs: 1200, completedChunks: 1, totalChunks: 2, mode: 'online' };
  progress(state);
  const play = cache.acquire(source, parts, male, false, late);
  expect(early).toHaveBeenLastCalledWith(state);
  expect(late).toHaveBeenCalledTimes(1); expect(late).toHaveBeenLastCalledWith(state);
  play.release(); progress({ ...state, percent: 80, completedChunks: 2 });
  expect(early).toHaveBeenCalledTimes(2); expect(late).toHaveBeenCalledTimes(1);
  finish(bytes); await warm.promise; warm.release();
  expect(downloadNarration).toHaveBeenCalledTimes(1);
});

it('keeps separate subscriptions when leases use the same callback and ignores abandoned progress', async () => {
  let finish!: (data: Uint8Array) => void, progress!: NarrationProgressListener;
  (downloadNarration as jest.Mock).mockImplementationOnce((_source, _parts, _signal, _voice, update) => {
    progress = update;
    return new Promise(resolve => { finish = resolve; });
  });
  const listener = jest.fn();
  const first = cache.acquire(source, parts, male, true, listener);
  const second = cache.acquire(source, parts, male, true, listener);
  first.release();
  const state: NarrationProgress = { phase: 'synthesizing', percent: 45, elapsedMs: 1200, completedChunks: 1, totalChunks: 2, mode: 'online' };
  progress(state); expect(listener).toHaveBeenCalledTimes(1);
  const rejected = expect(second.promise).rejects.toThrow('Đã dừng');
  second.release(); progress(state); expect(listener).toHaveBeenCalledTimes(1);
  finish(bytes); await rejected;
});

it('forwards progress to direct downloads without a cache', async () => {
  const listener = jest.fn(), signal = new AbortController().signal;
  const asset = await getPreparedNarrationAsset(null, source, parts, signal, male, listener);
  expect(downloadNarration).toHaveBeenLastCalledWith(source, parts, signal, male, listener);
  asset.dispose();
  await downloadPreparedNarration(null, source, parts, signal, male, listener);
  expect(downloadNarration).toHaveBeenLastCalledWith(source, parts, signal, male, listener);
});

it('keeps a valid pending download when its one promotion request fails', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish=resolve; }));
  (prioritizeNarration as jest.Mock).mockRejectedValueOnce(new Error('temporary promotion failure'));
  const warm=cache.acquire(source,parts,male,true);
  const listener=downloadPreparedNarration(cache,source,parts,new AbortController().signal,male);
  await Promise.resolve();finish(bytes);
  await expect(listener).resolves.toBe(bytes);
  // Capacity retries in the existing download inherit foreground intent even
  // if the one immediate promotion request could not be delivered.
  expect((downloadNarration as jest.Mock).mock.calls[0][0].prefetch).toBe(false);
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(false);
  expect(downloadNarration).toHaveBeenCalledTimes(1);warm.release();
});

it('uses the original remaining preparation budget for a late foreground promotion', async () => {
  let finish!: (data: Uint8Array) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish=resolve; }));
  const warm=cache.acquire(source,parts,male,true);
  jest.advanceTimersByTime(59000);
  const listener=cache.acquire(source,parts,male);
  expect(prioritizeNarration).toHaveBeenCalledWith(source,parts,expect.any(AbortSignal),male,1000);
  finish(bytes);await listener.promise;listener.release();warm.release();
});

it('does not promote an expired entry and aborts pending promotion when the download fails', async () => {
  let fail!: (error: Error) => void;
  (downloadNarration as jest.Mock).mockImplementationOnce(() => new Promise((_,reject) => { fail=reject; }));
  const warm=cache.acquire(source,parts,male,true);
  jest.advanceTimersByTime(60000);
  const listener=cache.acquire(source,parts,male);
  expect(prioritizeNarration).not.toHaveBeenCalled();
  const rejected=expect(listener.promise).rejects.toThrow('download failed');
  fail(new Error('download failed'));await rejected;
  expect((downloadNarration as jest.Mock).mock.calls[0][2].aborted).toBe(true);
  listener.release();warm.release();
});
