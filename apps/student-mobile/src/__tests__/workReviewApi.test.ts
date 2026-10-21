import apiClient from '../services/api/apiClient';
import { TutorService, WorkReviewRequest, workReviewLines } from '../features/tutoring/api/TutorService';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { post: jest.fn() } }));
const request: WorkReviewRequest = { sourceId: 'work_source_abcdefghijkl', problemText: 'Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?',
  workText: 'Số bút là:\n12 + 5 = 18\nĐáp số: 18 bút', problemConfirmed: true, workConfirmed: true };
const response = { sourceId: request.sourceId, status: 'NEEDS_REVISION', summary: 'Mình cùng xem lại phép cộng nhé.', praise: '',
  rows: request.workText.split('\n').map((sourceText, lineIndex) => ({ lineIndex, sourceText, status: lineIndex === 1 ? 'FIX' : 'UNSURE',
    feedback: lineIndex === 1 ? 'Em kiểm tra lại tổng hai nhóm nhé.' : 'Mình xem sau khi em sửa phép tính.', hints: lineIndex === 1 ? ['Cộng hàng đơn vị trước nhé.'] : [] })),
  nextAction: 'Em sửa dòng được nhắc tới rồi kiểm tra lại.', alternative: '' };
beforeEach(() => jest.clearAllMocks());

it('sends only confirmed source text and binds every feedback row to its source index', async () => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: response });
  await expect(TutorService.reviewWork(request)).resolves.toEqual(response);
  expect(apiClient.post).toHaveBeenCalledWith('/student/tutor/work-review', request, expect.objectContaining({ timeout: 45000 }));
  expect(workReviewLines(' a\r\n\n b\u2028c ')).toEqual(['a', 'b', 'c']);
  expect(workReviewLines('\ufeffa\u001f\n\u0085 b\u001f')).toEqual(['\ufeffa', 'b']);
});

it.each([
  { problemConfirmed: false }, { workConfirmed: false }, { workConfirmed: 'true' }, { sourceId: 'short' },
  { problemText: '[?] bút' }, { workText: '12 + [?] = 18' }, { workText: Array(36).fill('Dòng').join('\n') },
  { workText: 'a'.repeat(501) }, { workText: ' \n ' },
])('rejects incomplete or oversized source before a request', async patch => {
  await expect(TutorService.reviewWork({ ...request, ...patch } as any)).rejects.toThrow();
  expect(apiClient.post).not.toHaveBeenCalled();
});

it.each([
  { sourceId: 'another_source_abcdefgh' }, { rows: response.rows.slice(1) },
  { rows: response.rows.map((row, i) => i === 1 ? { ...row, sourceText: '12 + 5 = 17' } : row) },
  { rows: response.rows.map((row, i) => i === 1 ? { ...row, lineIndex: 0 } : row) },
  { rows: response.rows.map((row, i) => i === 1 ? { ...row, hints: [''] } : row) },
  { rows: response.rows.map((row, i) => i === 1 ? { ...row, hints: ['a', 'b', 'c'] } : row) },
  { status: 'CORRECT', praise: 'Em làm tốt!', rows: response.rows }, { praise: 'Bài em đúng rồi!' },
  { alternative: 'Cách giải khác' }, { nextAction: '' }, { summary: 'a'.repeat(501) },
  { status: 'NEEDS_REVISION', rows: response.rows.map(row => ({ ...row, status: 'UNSURE' })) },
])('rejects malformed, detached or contradictory feedback', async patch => {
  (apiClient.post as jest.Mock).mockResolvedValue({ data: { ...response, ...patch } });
  await expect(TutorService.reviewWork(request)).rejects.toThrow('Chưa đọc được hướng dẫn');
});

it('accepts grounded success and an optional method discussion without changing the source', async () => {
  const correct = { ...response, status: 'CORRECT', praise: 'Em đã viết câu lời giải và giữ đúng đơn vị.',
    rows: response.rows.map(row => ({ ...row, status: 'OK', hints: [] })), alternative: 'Em thử gộp các nhóm theo cách khác rồi so sánh nhé.' };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: correct });
  await expect(TutorService.reviewWork(request)).resolves.toEqual(correct);
});
