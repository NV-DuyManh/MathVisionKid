import { Platform } from 'react-native';
import apiClient from '../../../services/api/apiClient';

export type TutorStage = 'UNDERSTAND' | 'PLAN' | 'NEXT_STEP' | 'CHECK_WORK';
export interface TutorReadResult { problemText: string; needsReview: boolean; notes: string }
export interface NotebookLine { text: string; box: [number, number, number, number] | null; uncertain: boolean }
export interface NotebookRead {
  kind: 'PROBLEM' | 'WORK' | 'MIXED' | 'MULTIPLE' | 'UNREADABLE';
  problemText: string; lines: NotebookLine[]; needsProblem: boolean; needsCrop?: boolean;
}
export interface CoachRequest {
  problemText: string; workText: string; stage: TutorStage; studentAttempt: string;
  focusText: string; hintLevel: number; previousHint: string;
}
export interface TutorGuidance {
  stage: TutorStage;
  hint: string;
  question: string;
  feedback: string;
  guarded: boolean;
}
export interface TutorGuideRequest {
  problemText: string;
  problemConfirmed: boolean;
  stage: TutorStage;
  studentAttempt: string;
  hintLevel: number;
  previousHint?: string;
}
const STAGES: TutorStage[] = ['UNDERSTAND', 'PLAN', 'NEXT_STEP', 'CHECK_WORK'];
const TIMEOUT = 45000;
const INVALID_RESPONSE = 'Chưa đọc được hướng dẫn. Em hãy thử lại nhé.';

export type LessonStep = { title: string; explanation: string; question: string; choices: string[]; expression: string; unit: string; workExcerpt: string };
export type LessonResponse = {
  sessionId: string; revision: number; topic: string; goal: string; outline: string[]; stepIndex: number;
  step: LessonStep | null; completed: { title: string; expression: string; answer: string; unit: string; explanation: string }[];
  status: 'READY' | 'HINT' | 'TRY_AGAIN' | 'CORRECT' | 'COMPLETE'; feedback: string;
};
function lessonResponse(value: any): LessonResponse {
  const bounded = (v: any, max: number) => typeof v === 'string' && v.length <= max;
  const stepValid = (s: any) => s && bounded(s.title, 100) && bounded(s.explanation, 500) && bounded(s.question, 220)
    && Array.isArray(s.choices) && s.choices.length <= 4 && s.choices.every((c: any) => bounded(c, 100))
    && bounded(s.expression, 220) && bounded(s.unit, 20) && bounded(s.workExcerpt, 500);
  if (!value || !bounded(value.sessionId, 100) || value.sessionId.length < 20 || !Number.isInteger(value.revision) || value.revision < 0
      || !bounded(value.topic, 120) || !bounded(value.goal, 220) || !bounded(value.feedback, 500)
      || !Array.isArray(value.outline) || value.outline.length < 2 || value.outline.length > 6 || !value.outline.every((t: any) => bounded(t, 100))
      || !Array.isArray(value.completed) || value.completed.length > value.outline.length
      || !value.completed.every((s: any) => bounded(s.title, 100) && bounded(s.expression, 220) && bounded(s.answer, 100) && bounded(s.unit, 20) && bounded(s.explanation, 500))
      || value.stepIndex !== value.completed.length || !['READY', 'HINT', 'TRY_AGAIN', 'CORRECT', 'COMPLETE'].includes(value.status)
      || (value.step === null) !== (value.status === 'COMPLETE') || (value.step !== null && !stepValid(value.step))) throw new Error(INVALID_RESPONSE);
  return value as LessonResponse;
}

export const TutorService = {
  async startLesson(problemText: string, workText: string, signal?: AbortSignal): Promise<LessonResponse> {
    const { data } = await apiClient.post('/student/tutor/lesson', { problemText, workText }, { timeout: TIMEOUT, signal });
    return lessonResponse(data);
  },
  async answerLesson(lesson: LessonResponse, answer: string, hint = false, signal?: AbortSignal): Promise<LessonResponse> {
    const { data } = await apiClient.post('/student/tutor/lesson/answer', { sessionId: lesson.sessionId, revision: lesson.revision, answer, hint }, { timeout: TIMEOUT, signal });
    return lessonResponse(data);
  },
  async inspect(imageUri: string, privacyConfirmed: boolean, signal?: AbortSignal): Promise<NotebookRead> {
    if (!privacyConfirmed || !imageUri) throw new Error('Em hãy kiểm tra thông tin trên ảnh trước nhé.');
    const form = new FormData();
    if (Platform.OS === 'web') {
      const image = await fetch(imageUri, { signal });
      if (!image.ok) throw new Error('Chưa mở được ảnh.');
      form.append('file', await image.blob(), 'notebook.jpg');
    } else form.append('file', { uri: imageUri, name: 'notebook.jpg', type: 'image/jpeg' } as any);
    form.append('privacyConfirmed', 'true');
    const { data } = await apiClient.post<NotebookRead>('/student/tutor/inspect', form, {
      transformRequest: [(value) => value], timeout: TIMEOUT, signal,
    });
    if (!['PROBLEM', 'WORK', 'MIXED', 'MULTIPLE', 'UNREADABLE'].includes(data?.kind)
      || typeof data.problemText !== 'string' || data.problemText.length > 4000 || typeof data.needsProblem !== 'boolean'
      || (data.needsCrop !== undefined && typeof data.needsCrop !== 'boolean')
      || (data.needsCrop === true && (data.kind !== 'UNREADABLE' || data.problemText !== '' || data.lines?.length !== 0))
      || !Array.isArray(data.lines) || data.lines.length > 35 || data.lines.some(row => typeof row.text !== 'string'
        || !row.text.trim() || row.text.length > 500 || typeof row.uncertain !== 'boolean'
        || (row.box !== null && (!Array.isArray(row.box) || row.box.length !== 4 || row.box.some(n => !Number.isInteger(n) || n < 0 || n > 1000)
          || row.box[0] >= row.box[2] || row.box[1] >= row.box[3])))) throw new Error(INVALID_RESPONSE);
    return data;
  },

  async coach(request: CoachRequest, signal?: AbortSignal): Promise<TutorGuidance> {
    if ((request.problemText + request.workText).trim().length < 3 || request.problemText.length > 4000
      || request.workText.length > 6000 || request.studentAttempt.length > 2000 || request.focusText.length > 500
      || !STAGES.includes(request.stage) || !Number.isInteger(request.hintLevel) || request.hintLevel < 0 || request.hintLevel > 2
      || request.previousHint.length > 1200 || (request.focusText && !request.workText.includes(request.focusText))) throw new Error(INVALID_RESPONSE);
    const { data } = await apiClient.post<TutorGuidance>('/student/tutor/coach', request, { timeout: TIMEOUT, signal });
    if (data?.stage !== request.stage || typeof data.hint !== 'string' || !data.hint.trim() || data.hint.length > 800
      || typeof data.question !== 'string' || !data.question.trim() || data.question.length > 300
      || typeof data.feedback !== 'string' || data.feedback.length > 500 || typeof data.guarded !== 'boolean') throw new Error(INVALID_RESPONSE);
    return data;
  },
  async readProblem(imageUri: string, privacyConfirmed: boolean, signal?: AbortSignal): Promise<TutorReadResult> {
    if (!privacyConfirmed) throw new Error('Em hãy xác nhận đã che thông tin cá nhân trước khi đọc ảnh.');
    if (!imageUri) throw new Error('Em hãy chọn ảnh đề bài.');
    const form = new FormData();
    if (Platform.OS === 'web') {
      const image = await fetch(imageUri, { signal });
      if (!image.ok) throw new Error('Không thể đọc ảnh đã chọn.');
      form.append('file', await image.blob(), 'tutor-photo.jpg');
    } else {
      form.append('file', { uri: imageUri, name: 'tutor-photo.jpg', type: 'image/jpeg' } as any);
    }
    form.append('privacyConfirmed', 'true');
    const { data } = await apiClient.post<TutorReadResult>('/student/tutor/read', form, {
      transformRequest: [(value) => value], timeout: TIMEOUT, signal,
    });
    if (typeof data?.problemText !== 'string' || data.problemText.length > 4000 || typeof data.needsReview !== 'boolean'
      || typeof data.notes !== 'string' || data.notes.length > 500) {
      throw new Error(INVALID_RESPONSE);
    }
    return data;
  },

  async guide(request: TutorGuideRequest, signal?: AbortSignal): Promise<TutorGuidance> {
    if (!request.problemConfirmed) throw new Error('Em hãy xác nhận lại đề bài trước khi nhận gợi ý.');
    if (request.problemText.trim().length < 3 || request.problemText.length > 4000) throw new Error('Em hãy nhập đề bài rõ ràng, từ 3 đến 4000 ký tự.');
    if (!STAGES.includes(request.stage) || !Number.isInteger(request.hintLevel) || request.hintLevel < 0 || request.hintLevel > 2) {
      throw new Error('Em hãy chọn bước học phù hợp.');
    }
    if (request.studentAttempt.length > 2000 || (request.previousHint?.length ?? 0) > 1200) throw new Error('Bước làm của em quá dài.');
    if (request.stage === 'CHECK_WORK' && !request.studentAttempt.trim()) throw new Error('Em hãy viết bước mình đã làm trước nhé.');
    const { data } = await apiClient.post<TutorGuidance>('/student/tutor/guide', request, { timeout: TIMEOUT, signal });
    if (data?.stage !== request.stage || typeof data.hint !== 'string' || !data.hint.trim() || data.hint.length > 800
      || typeof data.question !== 'string' || !data.question.trim() || data.question.length > 300
      || typeof data.feedback !== 'string' || data.feedback.length > 500 || typeof data.guarded !== 'boolean') {
      throw new Error(INVALID_RESPONSE);
    }
    return data;
  },
};
