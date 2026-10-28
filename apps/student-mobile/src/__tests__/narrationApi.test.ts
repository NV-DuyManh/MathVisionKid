import apiClient from '../services/api/apiClient';
import { downloadNarration, readNarrationProgress, prioritizeNarration } from '../features/tutoring/narrationApi';
jest.mock('../services/api/apiClient', () => ({ post: jest.fn() }));
const source = { sessionId: 'owned-narration-session-123', revision: 1 };
const wav = new Uint8Array(50); wav.set([82,73,70,70]); wav.set([87,65,86,69],8);
const ready = { phase: 'ready', mode: 'online', percent: 100, elapsedMs: 1, completedChunks: 1, totalChunks: 1 };
const respond = (url: string) => Promise.resolve({ data: url.endsWith('/status') || url.endsWith('/prepare') ? ready : wav.buffer });
beforeEach(() => { jest.clearAllMocks(); (apiClient.post as jest.Mock).mockReset().mockImplementation(respond); });
afterEach(() => jest.useRealTimers());
it('downloads a private WAV bound to the current lesson and cancellation signal', async () => {
  const signal = new AbortController().signal;
  await expect(downloadNarration(source, [' Em gộp hai nhóm. ', ''], signal)).resolves.toEqual(wav);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/lesson/narration', { ...source, paragraphs: ['Em gộp hai nhóm.'], voice: 'vi-VN-NamMinhNeural' },
    expect.objectContaining({ signal, responseType: 'arraybuffer', headers: { Accept: 'audio/wav, application/json' } }));
});
it('sends canonical whitespace and forwards only validated public progress from its existing polling loop', async () => {
  jest.useFakeTimers();
  const listener = jest.fn();
  const pendingState = { ...ready, phase: 'synthesizing', percent: 45, completedChunks: 1, totalChunks: 2 };
  let polls = 0;
  (apiClient.post as jest.Mock).mockImplementation((url: string) => Promise.resolve({ data: url.endsWith('/prepare') ? {}
    : url.endsWith('/status') ? { ...(polls++ ? ready : pendingState), providerDetail: 'private-response' } : wav.buffer }));
  const pending = downloadNarration(source, [' Em\n gộp\t hai  nhóm. ', ''], new AbortController().signal, 'vi-VN-NamMinhNeural', listener);
  await jest.advanceTimersByTimeAsync(1000); await expect(pending).resolves.toEqual(wav);
  expect(listener.mock.calls.map(call => call[0])).toEqual([pendingState, ready]);
  expect(apiClient.post).toHaveBeenCalledTimes(4);
  expect((apiClient.post as jest.Mock).mock.calls.every(call => JSON.stringify(call[1].paragraphs) === JSON.stringify(['Em gộp hai nhóm.']))).toBe(true);
});

it('does not publish malformed progress or let a broken observer cancel valid audio', async () => {
  const listener = jest.fn();
  (apiClient.post as jest.Mock).mockImplementation((url: string) => Promise.resolve({ data: url.endsWith('/prepare') ? {} : { ...ready, percent: 101 } }));
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal, 'vi-VN-NamMinhNeural', listener)).rejects.toThrow('Chưa đọc được tiến độ.');
  expect(listener).not.toHaveBeenCalled();
  (apiClient.post as jest.Mock).mockImplementation((url: string) => Promise.resolve({ data: url.endsWith('/prepare') ? {} : url.endsWith('/status') ? ready : wav.buffer }));
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal, 'vi-VN-NamMinhNeural', () => { throw new Error('Observer unavailable'); })).resolves.toEqual(wav);
});
it('promotes only the same owned preparation using explicit foreground intent and a bounded request', async () => {
  const signal=new AbortController().signal;
  await prioritizeNarration({ ...source,prefetch:true },[' Em đọc lại nhé. ',''],signal,'vi-VN-HoaiMyNeural',8000);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/lesson/narration/prepare',{
    ...source,paragraphs:['Em đọc lại nhé.'],voice:'vi-VN-HoaiMyNeural',prefetch:false,
  },{signal,timeout:5000});
  (apiClient.post as jest.Mock).mockClear();
  await prioritizeNarration(source,['Em đọc lại nhé.'],signal,'vi-VN-NamMinhNeural',850);
  expect(apiClient.post).toHaveBeenLastCalledWith(expect.any(String),expect.anything(),{signal,timeout:850});
});
it('does not promote after cancellation or expiry or with an unsupported voice', async () => {
  const controller=new AbortController();controller.abort();
  await prioritizeNarration(source,['Em đọc lại nhé.'],controller.signal,'vi-VN-NamMinhNeural');
  await prioritizeNarration(source,['Em đọc lại nhé.'],new AbortController().signal,'vi-VN-NamMinhNeural',0);
  await prioritizeNarration(source,['Em đọc lại nhé.'],new AbortController().signal,'invalid' as any);
  expect(apiClient.post).not.toHaveBeenCalled();
});
it('rejects an invalid media response or oversized text instead of passing it to the player', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: new Uint8Array(50).buffer });
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal)).rejects.toThrow();
  (apiClient.post as jest.Mock).mockClear();
  await expect(downloadNarration(source, ['x'.repeat(5000)], new AbortController().signal)).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('forwards the selected female voice and rejects unknown voices before sending', async () => {
  const signal = new AbortController().signal;
  await downloadNarration(source, ['Em đọc lại nhé.'], signal, 'vi-VN-HoaiMyNeural');
  expect(apiClient.post).toHaveBeenLastCalledWith('/student/tutor/lesson/narration', expect.objectContaining({ voice: 'vi-VN-HoaiMyNeural' }), expect.anything());
  (apiClient.post as jest.Mock).mockClear();
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], signal, 'bad' as any)).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('briefly retries busy capacity but never multiplies provider or expired-session failures', async () => {
  jest.useFakeTimers();
  (apiClient.post as jest.Mock).mockRejectedValueOnce({ response: { status: 429 } }).mockImplementation(respond);
  const pending = downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal);
  await jest.advanceTimersByTimeAsync(1000);
  await expect(pending).resolves.toEqual(wav);
  expect((apiClient.post as jest.Mock).mock.calls.filter(call => call[0].endsWith('/prepare'))).toHaveLength(2);
  for (const status of [409, 410, 503]) {
    (apiClient.post as jest.Mock).mockReset().mockRejectedValue({ response: { status } });
    await expect(downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal)).rejects.toMatchObject({ response: { status } });
    expect(apiClient.post).toHaveBeenCalledTimes(1);
  }
});

it('cancels a busy retry immediately when the pupil closes or changes voice', async () => {
  jest.useFakeTimers();
  (apiClient.post as jest.Mock).mockRejectedValue({ response: { status: 429 } });
  const controller = new AbortController();
  const pending = downloadNarration(source, ['Em đọc lại nhé.'], controller.signal);
  const rejected = expect(pending).rejects.toThrow('Đã dừng');
  await jest.advanceTimersByTimeAsync(0);
  controller.abort();
  await rejected;
  await jest.advanceTimersByTimeAsync(2000);
  expect(apiClient.post).toHaveBeenCalledTimes(1);
  expect(jest.getTimerCount()).toBe(0);
});

it('bounds capacity retries instead of polling forever', async () => {
  jest.useFakeTimers();
  (apiClient.post as jest.Mock).mockRejectedValue({ response: { status: 429 } });
  const pending = downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal);
  const rejected = expect(pending).rejects.toThrow('Đã hết thời gian');
  await jest.advanceTimersByTimeAsync(45000);
  await rejected;
  expect((apiClient.post as jest.Mock).mock.calls.length).toBeLessThanOrEqual(46);
});

it('validates measured progress without accepting impossible completion or unknown modes', async () => {
  const state = { phase: 'synthesizing', mode: 'online', percent: 45, elapsedMs: 2000, completedChunks: 1, totalChunks: 2 };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: state });
  await expect(readNarrationProgress(source, ['Em đọc lại nhé.'], new AbortController().signal, 'vi-VN-NamMinhNeural')).resolves.toEqual(state);
  for (const invalid of [{ ...state, percent: 101 }, { ...state, completedChunks: 3 }, { ...state, mode: 'debug-provider-secret' }]) {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: invalid });
    await expect(readNarrationProgress(source, ['Em đọc lại nhé.'], new AbortController().signal, 'vi-VN-NamMinhNeural')).rejects.toThrow();
  }
});

it('stops an unfinished background narration at 45 seconds using short requests', async () => {
  jest.useFakeTimers();
  (apiClient.post as jest.Mock).mockImplementation((url:string) => Promise.resolve({data:url.endsWith('/status')
    ? {...ready,phase:'synthesizing',percent:75,completedChunks:9,totalChunks:12}
    :url.endsWith('/prepare')?{}:wav.buffer}));
  const pending=downloadNarration(source,['Bài giảng dài đã được xác nhận.'],new AbortController().signal);
  const rejected=expect(pending).rejects.toThrow('Đã hết thời gian');
  await jest.advanceTimersByTimeAsync(45000);await rejected;
  expect((apiClient.post as jest.Mock).mock.calls.filter(call=>call[0].endsWith('/lesson/narration'))).toHaveLength(0);
  expect((apiClient.post as jest.Mock).mock.calls.filter(call=>call[0].endsWith('/prepare'))).toHaveLength(1);
  expect((apiClient.post as jest.Mock).mock.calls.filter(call=>!call[0].endsWith('/lesson/narration')).every(call=>call[2].timeout<=5000)).toBe(true);
});

it.each([
  { code: 'ERR_NETWORK' }, { code: 'ECONNABORTED' }, { code: 'ETIMEDOUT' }, { code: 'ECONNRESET' },
  ...[408, 429, 500, 502, 503, 504].map(status => ({ response: { status } })),
])('keeps the existing job after a transient progress-read failure: %j', async failure => {
  jest.useFakeTimers();let polls=0;
  (apiClient.post as jest.Mock).mockImplementation((url:string) => {
    if (url.endsWith('/prepare')) return Promise.resolve({data:{}});
    if (url.endsWith('/status')) return ++polls===1 ? Promise.reject(failure) : Promise.resolve({data:ready});
    return Promise.resolve({data:wav.buffer});
  });
  const pending=downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal);
  await jest.advanceTimersByTimeAsync(1000);
  await expect(pending).resolves.toEqual(wav);
  expect((apiClient.post as jest.Mock).mock.calls.filter(call=>call[0].endsWith('/prepare'))).toHaveLength(1);
  expect(polls).toBe(2);
});

it.each([400,401,403,404,409,410,422,501])('does not retry a terminal progress HTTP %s', async status => {
  (apiClient.post as jest.Mock).mockImplementation((url:string) => url.endsWith('/prepare')
    ? Promise.resolve({data:{}}) : Promise.reject({response:{status}}));
  await expect(downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal)).rejects.toMatchObject({response:{status}});
  expect(apiClient.post).toHaveBeenCalledTimes(2);
});

it('rejects malformed progress as a validation error instead of treating it as a network failure', async () => {
  (apiClient.post as jest.Mock).mockImplementation((url:string) => Promise.resolve({data:url.endsWith('/prepare')?{}:{...ready,percent:101}}));
  await expect(downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal)).rejects.toThrow('Chưa đọc được tiến độ.');
  expect(apiClient.post).toHaveBeenCalledTimes(2);
});

it('restarts idempotent preparation when a completed job has lost its cached WAV', async () => {
  jest.useFakeTimers();let prepares=0;
  (apiClient.post as jest.Mock).mockImplementation((url:string) => Promise.resolve({data:url.endsWith('/prepare')
    ? (++prepares===1?{}:ready) : url.endsWith('/status')?{...ready,phase:'waiting',percent:0,completedChunks:0,totalChunks:0}:wav.buffer}));
  const pending=downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal);
  await jest.advanceTimersByTimeAsync(1000);
  await expect(pending).resolves.toEqual(wav);
  expect(prepares).toBe(2);
  expect((apiClient.post as jest.Mock).mock.calls.filter(call=>call[0].endsWith('/status'))).toHaveLength(1);
});

it.each(['waiting','temporary-status-failure'])('retains one 45-second deadline during %s recovery', async mode => {
  jest.useFakeTimers();const began=Date.now();
  (apiClient.post as jest.Mock).mockImplementation((url:string) => {
    if (url.endsWith('/prepare')) return Promise.resolve({data:{}});
    return mode==='waiting' ? Promise.resolve({data:{...ready,phase:'waiting',percent:0,completedChunks:0,totalChunks:0}}) : Promise.reject({response:{status:503}});
  });
  const pending=downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal);
  const rejected=expect(pending).rejects.toThrow('Đã hết thời gian');
  await jest.advanceTimersByTimeAsync(45000);await rejected;
  expect(Date.now()-began).toBe(45000);
  const calls=(apiClient.post as jest.Mock).mock.calls;
  expect(calls.filter(call=>call[0].endsWith('/prepare'))).toHaveLength(mode==='waiting'?45:1);
  expect(calls.every(call=>call[2].timeout>0 && call[2].timeout<=5000)).toBe(true);
});

it.each(['prepare','status'])('never disables the %s timeout when the final millisecond expires between checks', async stage => {
  const now=jest.spyOn(Date,'now').mockReturnValue(46000);
  (apiClient.post as jest.Mock).mockImplementation((url:string) => {
    if (url.endsWith('/prepare')) return Promise.resolve({data:{}});
    if (url.endsWith('/status')) return Promise.resolve({data:ready});
    return Promise.resolve({data:wav.buffer});
  });
  const beforeTick=stage==='prepare'?[1000,45999]:[1000,45999,45999,45999];
  beforeTick.forEach(value=>now.mockReturnValueOnce(value));
  try {
    await expect(downloadNarration(source,['Em đọc lại nhé.'],new AbortController().signal)).rejects.toThrow('Đã hết thời gian');
    expect((apiClient.post as jest.Mock).mock.calls.every(call=>call[2].timeout>0)).toBe(true);
    const calls=(apiClient.post as jest.Mock).mock.calls;
    expect(calls[calls.length-1][2].timeout).toBe(1);
  } finally { now.mockRestore(); }
});
