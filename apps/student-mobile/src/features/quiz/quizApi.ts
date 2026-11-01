import apiClient from '../../services/api/apiClient';
import type { NarrationVoice } from '../tutoring/narrationVoices';

export type QuizAttempt = { number: number; answer: string; correct: boolean; submittedAt: string; elapsedMillis: number; stars?: number; mode?: string; questionText?: string | null; solutionViewed?: boolean | null; runStartedAt?: string | null };
export type Quiz = {
  quizId: string; sourceType: 'LESSON' | 'WORK_REVIEW'; sourceId: string; topicCode: string; topicName: string;
  skillCode: string; gradeLevel: number; taxonomyVersion: string; verificationStatus: string; confidencePercent: number;
  questionText: string; unit: string; answerFormat: 'INTEGER' | 'FRACTION'; status: 'READY' | 'DEFERRED' | 'IN_PROGRESS' | 'COMPLETED';
  createdAt: string; startedAt: string | null; completedAt: string | null; serverNow: string; elapsedMillis: number;
  stars: number; wrongAttempts: number; solutionViewed: boolean; completedWithSolution: boolean; canRevealSolution: boolean;
  attempts: QuizAttempt[]; explanationText: string | null; correctAnswer: string | null;
  replayMode?: 'NONE' | 'PRACTICE' | 'CHALLENGE'; originalQuestionText?: string | null;
};
export type QuizGroup = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
export type QuizLibrary = { items: Quiz[]; page: number; totalPages: number; totalElements: number };
export type QuizPreparation = { preparationId: string; revision: number; status: 'GENERATING' | 'READY' | 'INVALIDATED' | 'UNSUPPORTED' | 'FAILED'; errorCode: string | null };
const listeners = new Set<() => void>();
export function onQuizChanged(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
function changed() { listeners.forEach(listener => listener()); }
async function mutate<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const { data } = await apiClient.post<T>(`/student/quizzes/${path}`, body, { signal, timeout: 20000 });
  changed(); return data;
}
export const quizApi = {
  async prepare(workflowKey: string, revision: number, problemText: string, problemConfirmed: boolean, signal?: AbortSignal): Promise<QuizPreparation> {
    return (await apiClient.post('/student/quizzes/prepare', { workflowKey, revision, confirmedProblemText: problemText, problemConfirmed }, { signal, timeout: 12000 })).data;
  },
  async preparationStatus(id: string, signal?: AbortSignal): Promise<QuizPreparation> {
    return (await apiClient.get(`/student/quizzes/preparations/${id}`, { signal, timeout: 12000 })).data;
  },
  async count(signal?: AbortSignal): Promise<{ pendingCount: number; totalStars: number }> {
    return (await apiClient.get('/student/quizzes/pending-count', { signal })).data;
  },
  async list(group: QuizGroup, page = 0, signal?: AbortSignal): Promise<QuizLibrary> {
    return (await apiClient.get('/student/quizzes', { params: { group, page, size: 12 }, signal })).data;
  },
  async get(id: string, signal?: AbortSignal): Promise<Quiz> { return (await apiClient.get(`/student/quizzes/${id}`, { signal })).data; },
  async fromLearning(sourceType: 'LESSON' | 'WORK_REVIEW', sourceId: string, signal?: AbortSignal) {
    for (let attempt = 0; ; attempt++) {
      try { return await mutate<{ offered: boolean; quiz: Quiz }>('from-learning', { sourceType, sourceId }, signal); }
      catch (error: any) {
        if (error?.response?.data?.error?.code !== 'QUIZ_GENERATING' || attempt >= 7 || signal?.aborted) throw error;
        await quizWait(500, signal);
      }
    }
  },
  start: (id: string, signal?: AbortSignal) => mutate<Quiz>(`${id}/start`, undefined, signal),
  replay: (id: string, mode: 'PRACTICE' | 'CHALLENGE' = 'CHALLENGE', signal?: AbortSignal) => mutate<Quiz>(`${id}/replay`, { mode }, signal),
  defer: (id: string, signal?: AbortSignal) => mutate<Quiz>(`${id}/defer`, undefined, signal),
  submit: (id: string, requestId: string, answer: string, signal?: AbortSignal) => mutate<{ quiz: Quiz; attempt: QuizAttempt }>(`${id}/submit`, { requestId, answer }, signal),
  reveal: (id: string, signal?: AbortSignal) => mutate<Quiz>(`${id}/reveal-solution`, undefined, signal),
  async audio(id: string, voice: NarrationVoice, signal: AbortSignal): Promise<Uint8Array> {
    const { data } = await apiClient.post(`/student/quizzes/${id}/narration`, { voice }, { responseType: 'arraybuffer', signal, timeout: 45000 });
    const bytes = new Uint8Array(data);
    if (bytes.length <= 44 || bytes.length > 8 * 1024 * 1024 || bytes[0] !== 82 || bytes[1] !== 73 || bytes[2] !== 70 || bytes[3] !== 70
      || bytes[8] !== 87 || bytes[9] !== 65 || bytes[10] !== 86 || bytes[11] !== 69) throw new Error('Invalid audio');
    return bytes;
  },
};
export function quizWait(milliseconds: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const cancel = () => { clearTimeout(timer); signal?.removeEventListener('abort', cancel); reject(new Error('Đã dừng chuẩn bị Quiz.')); };
    const timer = setTimeout(() => { signal?.removeEventListener('abort', cancel); resolve(); }, milliseconds);
    signal?.addEventListener('abort', cancel, { once: true });
    if (signal?.aborted) cancel();
  });
}
export function quizError(error: unknown): string {
  const failure = error as { response?: { data?: { error?: { code?: string; message?: string } }; status?: number } };
  const detail = failure?.response?.data?.error;
  return detail?.code?.startsWith('QUIZ_') && detail.message ? detail.message
    : failure?.response?.status === 401 ? 'Em đăng nhập lại để mở Quiz của mình nhé.'
    : 'Chưa kết nối được với Quiz. Bài của em vẫn được giữ; em thử lại nhé.';
}
