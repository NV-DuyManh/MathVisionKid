import apiClient from '../services/api/apiClient';
import { downloadNarration } from '../features/tutoring/narrationApi';
jest.mock('../services/api/apiClient', () => ({ post: jest.fn() }));
const source = { sessionId: 'owned-narration-session-123', revision: 1 };
const wav = new Uint8Array(50); wav.set([82,73,70,70]); wav.set([87,65,86,69],8);
beforeEach(() => jest.clearAllMocks());
it('downloads a private WAV bound to the current lesson and cancellation signal', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: wav.buffer }); const signal = new AbortController().signal;
  await expect(downloadNarration(source, [' Em gộp hai nhóm. ', ''], signal)).resolves.toEqual(wav);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/lesson/narration', { ...source, paragraphs: ['Em gộp hai nhóm.'], voice: 'vi-VN-NamMinhNeural' },
    expect.objectContaining({ signal, responseType: 'arraybuffer', headers: { Accept: 'audio/wav' } }));
});
it('rejects an invalid media response or oversized text instead of passing it to the player', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: new Uint8Array(50).buffer });
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], new AbortController().signal)).rejects.toThrow();
  (apiClient.post as jest.Mock).mockClear();
  await expect(downloadNarration(source, ['x'.repeat(5000)], new AbortController().signal)).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('forwards the selected female voice and rejects unknown voices before sending', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: wav.buffer }); const signal = new AbortController().signal;
  await downloadNarration(source, ['Em đọc lại nhé.'], signal, 'vi-VN-HoaiMyNeural');
  expect(apiClient.post).toHaveBeenLastCalledWith('/student/tutor/lesson/narration', expect.objectContaining({ voice: 'vi-VN-HoaiMyNeural' }), expect.anything());
  (apiClient.post as jest.Mock).mockClear();
  await expect(downloadNarration(source, ['Em đọc lại nhé.'], signal, 'bad' as any)).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});
