import { Platform } from 'react-native';
import apiClient from '../services/api/apiClient';
import { TutorGuideRequest, TutorService } from '../features/tutoring/api/TutorService';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { post: jest.fn() } }));

const request: TutorGuideRequest = {
  problemText: 'Lan có 12 viên bi, thêm 5 viên. Hỏi có tất cả bao nhiêu viên?',
  problemConfirmed: true, stage: 'UNDERSTAND', studentAttempt: '', hintLevel: 0,
};
const guidance = { stage: 'UNDERSTAND', hint: 'Tìm số bi ban đầu và số bi được thêm.', question: 'Đề yêu cầu tìm gì?', feedback: '', guarded: false };

beforeEach(() => jest.clearAllMocks());

it.each([
  [{ kind: 'UNREADABLE', problemText: '', lines: [], needsProblem: false, needsCrop: true }, true],
  [{ kind: 'UNREADABLE', problemText: '', lines: [], needsProblem: false, needsCrop: 'true' }, false],
  [{ kind: 'WORK', problemText: '', lines: [{ text: 'first row', box: null, uncertain: false }], needsProblem: true, needsCrop: true }, false],
])('validates crop-required feedback before rendering partial content', async (data, valid) => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data });
  if (valid) await expect(TutorService.inspect('file:///masked.jpg', true)).resolves.toEqual(data);
  else await expect(TutorService.inspect('file:///masked.jpg', true)).rejects.toThrow('Chưa đọc được hướng dẫn');
});

const publicLesson = { sessionId: 'abcdefghijklmnopqrstuv', revision: 0, topic: 'Thêm bút', goal: 'Tìm số bút', outline: ['Chọn phép tính', 'Tính số bút'],
  stepIndex: 0, completed: [], status: 'READY', feedback: '', step: { title: 'Chọn phép tính', explanation: 'Xem số bút thay đổi.', question: 'Em chọn phép tính nào?',
    choices: ['Cộng', 'Trừ'], expression: '', unit: '', workExcerpt: '' } };

it('starts a lesson and sends only session revision and the pupil response for an answer', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: publicLesson });
  const lesson = await TutorService.startLesson(request.problemText, '');
  await TutorService.answerLesson(lesson, 'Cộng');
  expect(apiClient.post).toHaveBeenLastCalledWith('/student/tutor/lesson/answer', {
    sessionId: publicLesson.sessionId, revision: 0, answer: 'Cộng', hint: false,
  }, expect.objectContaining({ timeout: 45000 }));
});

it('rejects an inconsistent or oversized public lesson', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { ...publicLesson, stepIndex: 2 } });
  await expect(TutorService.startLesson(request.problemText, '')).rejects.toThrow('Chưa đọc được hướng dẫn');
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { ...publicLesson, step: { ...publicLesson.step, explanation: 'a'.repeat(501) } } });
  await expect(TutorService.startLesson(request.problemText, '')).rejects.toThrow('Chưa đọc được hướng dẫn');
});

it('blocks image upload before privacy acknowledgement', async () => {
  await expect(TutorService.readProblem('file:///photo.jpg', false)).rejects.toThrow('thông tin cá nhân');
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('inspects a privacy-reviewed notebook and preserves line geometry', async () => {
  const oldOS = Platform.OS; const oldFormData = global.FormData; const parts: unknown[][] = [];
  Platform.OS = 'android';
  global.FormData = class { append(...values: unknown[]) { parts.push(values); } } as any;
  const result = { kind: 'WORK', problemText: '', needsProblem: true,
    lines: [{ text: '49 : 7 × 2 = 14 (con)', box: [120, 300, 700, 410], uncertain: false }] };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: result });
  try {
    await expect(TutorService.inspect('file:///masked.jpg', true)).resolves.toEqual(result);
    expect(parts[0]).toEqual(['file', { uri: 'file:///masked.jpg', name: 'notebook.jpg', type: 'image/jpeg' }]);
    expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/inspect', expect.anything(), expect.objectContaining({ timeout: 45000 }));
  } finally { Platform.OS = oldOS; global.FormData = oldFormData; }
});

it('rejects malformed notebook boxes and invalid coaching focus before requests', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { kind: 'WORK', problemText: '', needsProblem: true,
    lines: [{ text: 'bước', box: [500, 0, 100, 20], uncertain: false }] } });
  await expect(TutorService.inspect('file:///photo.jpg', true)).rejects.toThrow('Chưa đọc được hướng dẫn');
  const coach = { problemText: '', workText: '2 + 5 = 7', stage: 'CHECK_WORK' as const,
    studentAttempt: '', focusText: '49 : 7', hintLevel: 0, previousHint: '' };
  await expect(TutorService.coach(coach)).rejects.toThrow('Chưa đọc được hướng dẫn');
});

it('sends one selected work step to the coach', async () => {
  const coach = { problemText: '', workText: '2 + 5 = 7\n49 : 7 × 2 = 14', stage: 'CHECK_WORK' as const,
    studentAttempt: 'Em chia trước.', focusText: '49 : 7 × 2 = 14', hintLevel: 0, previousHint: '' };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { ...guidance, stage: 'CHECK_WORK' } });
  await TutorService.coach(coach);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/coach', coach, expect.objectContaining({ timeout: 45000 }));
});

it('uploads actual web image bytes with privacy acknowledgement and cancellation', async () => {
  const oldOS = Platform.OS;
  const oldFetch = global.fetch;
  const oldFormData = global.FormData;
  const parts: unknown[][] = [];
  const image = new Blob(['photo-bytes'], { type: 'image/jpeg' });
  const abort = new AbortController();
  Platform.OS = 'web';
  global.fetch = jest.fn().mockResolvedValue({ ok: true, blob: async () => image });
  global.FormData = class { append(...values: unknown[]) { parts.push(values); } } as any;
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { problemText: request.problemText, needsReview: true, notes: '' } });
  try {
    await TutorService.readProblem('blob:photo', true, abort.signal);
    expect(global.fetch).toHaveBeenCalledWith('blob:photo', { signal: abort.signal });
    expect(parts).toEqual([['file', image, 'tutor-photo.jpg'], ['privacyConfirmed', 'true']]);
    expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/read', expect.anything(), expect.objectContaining({ signal: abort.signal, timeout: 45000 }));
  } finally {
    Platform.OS = oldOS; global.fetch = oldFetch; global.FormData = oldFormData;
  }
});

it('uses the native multipart file format through the authenticated client', async () => {
  const oldOS = Platform.OS;
  const oldFormData = global.FormData;
  const parts: unknown[][] = [];
  Platform.OS = 'android';
  global.FormData = class { append(...values: unknown[]) { parts.push(values); } } as any;
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { problemText: '', needsReview: true, notes: '' } });
  try {
    await TutorService.readProblem('file:///masked-crop.jpg', true);
    expect(parts[0]).toEqual(['file', { uri: 'file:///masked-crop.jpg', name: 'tutor-photo.jpg', type: 'image/jpeg' }]);
  } finally { Platform.OS = oldOS; global.FormData = oldFormData; }
});

it.each([
  [{ problemConfirmed: false }, 'xác nhận'],
  [{ problemText: '  x  ' }, '3 đến 4000'],
  [{ stage: 'CHECK_WORK', studentAttempt: '  ' }, 'bước mình đã làm'],
  [{ hintLevel: 3 }, 'bước học'],
  [{ studentAttempt: 'x'.repeat(2001) }, 'quá dài'],
])('rejects invalid tutoring input before spending a request', async (patch, message) => {
  await expect(TutorService.guide({ ...request, ...patch } as TutorGuideRequest)).rejects.toThrow(message);
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('forwards the confirmed problem and actual student attempt without cloud credentials', async () => {
  const abort = new AbortController();
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { ...guidance, stage: 'CHECK_WORK', feedback: 'Em hãy kiểm tra hàng đơn vị.' } });
  const payload = { ...request, stage: 'CHECK_WORK' as const, studentAttempt: 'Em định cộng 12 với 5.' };
  await TutorService.guide(payload, abort.signal);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/guide', payload, { timeout: 45000, signal: abort.signal });
});

it.each([
  { ...guidance, stage: 'PLAN' },
  { ...guidance, hint: 'x'.repeat(801) },
  { ...guidance, question: '' },
  { ...guidance, feedback: 'x'.repeat(501) },
  { ...guidance, guarded: undefined },
])('does not render malformed or mismatched-stage guidance', async response => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: response });
  await expect(TutorService.guide(request)).rejects.toThrow('Chưa đọc được hướng dẫn');
});

it.each([undefined, 'x'.repeat(501)])('rejects malformed read notes', async notes => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { problemText: '', needsReview: true, notes } });
  await expect(TutorService.readProblem('file:///photo.jpg', true)).rejects.toThrow('Chưa đọc được hướng dẫn');
});
