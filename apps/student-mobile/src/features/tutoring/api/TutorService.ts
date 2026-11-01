import { Platform } from 'react-native';
import apiClient from '../../../services/api/apiClient';

export type TutorStage = 'UNDERSTAND' | 'PLAN' | 'NEXT_STEP' | 'CHECK_WORK';
export interface TutorReadResult { problemText: string; needsReview: boolean; notes: string }
export interface WrittenDivision { dividend: string; divisor: string; quotient: string | null; rows: string[] }
export interface DivisionCheck { status: 'CORRECT' | 'TRY_AGAIN' | 'NEEDS_REVIEW'; field: '' | 'dividend' | 'divisor' | 'quotient' | 'rows'; rowIndex: number | null; message: string; hints?: string[] }
export interface NotebookLine { text: string; box: [number, number, number, number] | null; uncertain: boolean; division?: WrittenDivision | null }
export function divisionText(value: WrittenDivision): string {
  return `${value.dividend} : ${value.divisor}\nThương đã viết: ${value.quotient ?? ''}\nCác hàng đã viết:\n${value.rows.join('\n')}`;
}
export function savedDivision(text: string): WrittenDivision | null {
  const match = /^(.*?) : (.*?)\nThương đã viết: (.*?)\nCác hàng đã viết:\n([\s\S]*)$/.exec(text);
  if (!match) return null;
  const value = { dividend: match[1], divisor: match[2], quotient: match[3] || null, rows: match[4] ? match[4].split('\n') : [] };
  return validDivision(value) ? value : null;
}
function validDivision(value: any): value is WrittenDivision {
  const number = (v: any) => typeof v === 'string' && v.length <= 24 && /^(?:[0-9]|\[\?\])+$/.test(v);
  return value && number(value.dividend) && number(value.divisor) && (value.quotient === null || number(value.quotient))
    && Array.isArray(value.rows) && value.rows.length <= 30
    && value.rows.every((r: any) => typeof r === 'string' && r.length <= 40 && /^(?:[0-9 +\-−]|\[\?\])+$/.test(r));
}
export interface NotebookRead {
  kind: 'PROBLEM' | 'WORK' | 'MIXED' | 'MULTIPLE' | 'UNREADABLE';
  problemText: string; lines: NotebookLine[]; needsProblem: boolean; needsCrop?: boolean;
}
export type WorkReviewRequest = { sourceId: string; problemText: string; workText: string; problemConfirmed: boolean; workConfirmed: boolean };
export type WorkReviewRow = { lineIndex: number; sourceText: string; status: 'OK' | 'FIX' | 'UNSURE'; feedback: string; hints: string[] };
export type WorkReview = { sourceId: string; status: 'CORRECT' | 'NEEDS_REVISION' | 'NEEDS_REVIEW'; summary: string; praise: string;
  rows: WorkReviewRow[]; nextAction: string; alternative: string };
/** Same physical line separators as Python splitlines; blank rows do not get review indexes. */
export function trimWorkReviewLine(text: string): string {
  return text.replace(/^[\u0009-\u000D\u001C-\u0020\u0085\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]+|[\u0009-\u000D\u001C-\u0020\u0085\u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]+$/g, '');
}
export function workReviewLines(text: string): string[] {
  return text.split(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/).map(trimWorkReviewLine).filter(Boolean);
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

export type CompletedLessonStep = { kind?: 'MATH' | 'UNDERSTAND'; title: string; expression: string; answer: string; unit: string; explanation: string; solutionSentence?: string; calculationDetails?: string[]; guidance?: string[] };
export type LessonStep = { kind?: 'MATH' | 'UNDERSTAND'; title: string; explanation: string; question: string; choices: string[]; expression: string; unit: string; workExcerpt: string; solutionSentence?: string; guidance?: string[] };
export type LessonSummary = { givens: string[]; question: string };
export type LessonReply = { answer: string; spokenExplanation: string; followUp: string; guarded: boolean };
export type LearningCheck = {expression:string;question:string;checked:boolean;correct:boolean;feedback:string};
export type LessonResponse = {
  sessionId: string; revision: number; topic: string; goal: string; outline: string[]; stepIndex: number;
  step: LessonStep | null; completed: CompletedLessonStep[];
  status: 'READY' | 'HINT' | 'TRY_AGAIN' | 'CORRECT' | 'COMPLETE' | 'PREPARING' | 'RETRYABLE' | 'UNAVAILABLE'; feedback: string; conclusion?: string; understandingSteps?: 0 | 3; preparingMath?: boolean;
  summary?: LessonSummary | null;
  review?:{question:string;choices:string[];studentAnswer:string}|null;
};
function lessonResponse(value: any): LessonResponse {
  if(value?.review!=null){
    const review=value.review;
    if(typeof review.question!=='string'||!review.question.trim()||review.question.length>220||!Array.isArray(review.choices)||review.choices.length>4
      ||review.choices.some((item:unknown)=>typeof item!=='string'||!item.trim()||item.length>100)
      ||typeof review.studentAnswer!=='string'||review.studentAnswer.length>100||!value.completed?.length
      ||value.completed[value.completed.length-1].answer!==review.studentAnswer
      ||review.choices.length&&!review.choices.includes(review.studentAnswer))throw new Error(INVALID_RESPONSE);
  }
  const bounded = (v: any, max: number) => typeof v === 'string' && v.length <= max;
  const understanding = value?.understandingSteps === undefined ? 0 : value.understandingSteps;
  const preparing = value?.preparingMath === true;
  const waiting = ['PREPARING', 'RETRYABLE', 'UNAVAILABLE'].includes(value?.status);
  const phaseValid = (s: any, index: number) => s && (s.kind === undefined ? 'MATH' : s.kind) === (index < understanding ? 'UNDERSTAND' : 'MATH')
    && (index >= understanding || (s.expression === '' && s.unit === '' && !s.solutionSentence));
  const guidanceValid = (v: any) => v === undefined || (Array.isArray(v) && v.length <= 6 && v.every((item: any) => bounded(item, 500) && item.trim()));
  const summary = value?.summary;
  const summaryValid = summary == null || (understanding === 3 && value.stepIndex >= 2
    && typeof summary === 'object' && !Array.isArray(summary)
    && Array.isArray(summary.givens) && summary.givens.length >= 1 && summary.givens.length <= 12
    && summary.givens.every((item: any) => bounded(item, 200) && item.trim())
    && bounded(summary.question, 100) && summary.question.trim());
  const stepValid = (s: any) => s && bounded(s.title, 100) && bounded(s.explanation, 500) && bounded(s.question, 220)
    && Array.isArray(s.choices) && s.choices.length <= 4 && s.choices.every((c: any) => bounded(c, 100))
    && bounded(s.expression, 220) && bounded(s.unit, 20) && bounded(s.workExcerpt, 500)
    && (s.solutionSentence === undefined || bounded(s.solutionSentence, 220)) && guidanceValid(s.guidance);
  if (!value || !summaryValid || ![0, 3].includes(understanding) || !bounded(value.sessionId, 100) || value.sessionId.length < 20 || !Number.isInteger(value.revision) || value.revision < 0
      || !bounded(value.topic, 120) || !bounded(value.goal, 220) || !bounded(value.feedback, 500)
      || (value.preparingMath !== undefined && typeof value.preparingMath !== 'boolean')
      || !Array.isArray(value.outline) || (preparing ? understanding !== 3 || value.outline.length !== 3 : value.outline.length - understanding < 2 || value.outline.length - understanding > 6) || !value.outline.every((t: any) => bounded(t, 100))
      || !Array.isArray(value.completed) || value.completed.length > value.outline.length
      || !value.completed.every((s: any, index: number) => phaseValid(s, index) && bounded(s.title, 100) && bounded(s.expression, 220) && bounded(s.answer, 100) && bounded(s.unit, 20) && bounded(s.explanation, 500)
        && (s.solutionSentence === undefined || bounded(s.solutionSentence, 220))
        && guidanceValid(s.guidance)
        && (s.calculationDetails === undefined || (Array.isArray(s.calculationDetails) && s.calculationDetails.length <= 5 && s.calculationDetails.every((d: any) => bounded(d, 500)))))
      || (value.conclusion !== undefined && !bounded(value.conclusion, 150))
      || value.stepIndex !== value.completed.length || !['READY', 'HINT', 'TRY_AGAIN', 'CORRECT', 'COMPLETE', 'PREPARING', 'RETRYABLE', 'UNAVAILABLE'].includes(value.status)
      || (waiting && (!preparing || understanding !== 3 || value.stepIndex !== 3))
      || (preparing && value.status === 'COMPLETE') || (value.step === null) !== (value.status === 'COMPLETE' || waiting)
      || (value.step === null ? value.stepIndex !== value.outline.length
        : value.stepIndex >= value.outline.length || !phaseValid(value.step, value.stepIndex) || !stepValid(value.step)
          || (value.stepIndex < understanding && value.step.choices.length < 2))) throw new Error(INVALID_RESPONSE);
  if (value.status !== 'COMPLETE' && value.conclusion) throw new Error(INVALID_RESPONSE);
  return value as LessonResponse;
}

export const TutorService = {
  async lessonPreparation(lesson: Pick<LessonResponse, 'sessionId' | 'revision'>, retry = false, signal?: AbortSignal): Promise<LessonResponse> {
    const { data } = await apiClient.post('/student/tutor/lesson/preparation', {
      sessionId: lesson.sessionId, revision: lesson.revision, retry,
    }, { timeout: 10000, signal });
    return lessonResponse(data);
  },
  async resumeLesson(sessionId:string,problemText:string,signal?:AbortSignal):Promise<LessonResponse> {
    const {data}=await apiClient.post('/student/tutor/lesson/resume',{sessionId,problemText},{timeout:15000,signal});
    return lessonResponse(data);
  },
  async checkUnderstanding(source:{sessionId:string;revision:number},answer='',signal?:AbortSignal):Promise<LearningCheck> {
    const {data}=await apiClient.post('/student/tutor/lesson/checkpoint',{...source,answer},{timeout:15000,signal});
    if(!data||typeof data.expression!=='string'||!data.expression.trim()||data.expression.length>300
      ||typeof data.question!=='string'||!data.question.trim()||data.question.length>200||typeof data.checked!=='boolean'
      ||typeof data.correct!=='boolean'||typeof data.feedback!=='string'||data.feedback.length>300
      ||data.correct&&!data.checked||data.checked!==!!answer.trim())throw new Error(INVALID_RESPONSE);
    return data;
  },
  async askLesson(request: { sessionId: string; revision: number; stepIndex: number; question: string }, signal?: AbortSignal): Promise<LessonReply> {
    if (!request.question.trim() || request.question.length > 500) throw new Error('Em viết một câu hỏi ngắn nhé.');
    const { data } = await apiClient.post<LessonReply>('/student/tutor/lesson/ask', request, { timeout: TIMEOUT, signal });
    if (!data || typeof data.answer !== 'string' || !data.answer.trim() || data.answer.length > 650
      || typeof data.spokenExplanation !== 'string' || !data.spokenExplanation.trim() || data.spokenExplanation.length > 1600
      || typeof data.followUp !== 'string' || data.followUp.length > 200 || typeof data.guarded !== 'boolean') throw new Error(INVALID_RESPONSE);
    return data;
  },
  async transcribeQuestion(uri: string, signal?: AbortSignal): Promise<string> {
    const form = new FormData();
    if (Platform.OS === 'web') {
      const blob = await (await fetch(uri, { signal })).blob();
      if (blob.size > 3 * 1024 * 1024) throw new Error('Em ghi câu hỏi ngắn hơn nhé.');
      form.append('file', blob, 'question.webm');
    } else form.append('file', { uri, name: 'question.m4a', type: 'audio/mp4' } as any);
    form.append('audioConsent', 'true');
    const { data } = await apiClient.post<{ text: string }>('/student/tutor/transcribe', form, {
      transformRequest: [value => value], headers: { 'Content-Type': undefined }, timeout: TIMEOUT, signal });
    if (typeof data?.text !== 'string' || !data.text.trim() || data.text.length > 500) throw new Error('Chưa nghe rõ câu hỏi. Em thử lại nhé.');
    return data.text;
  },
  async reviewWork(request: WorkReviewRequest, signal?: AbortSignal): Promise<WorkReview> {
    const bounded = (value: unknown, max: number, blank = false): value is string => typeof value === 'string'
      && value.length <= max && (blank || !!value.trim());
    if (!request || request.problemConfirmed !== true || request.workConfirmed !== true
      || !bounded(request.sourceId, 100) || request.sourceId.length < 16
      || !bounded(request.problemText, 4000) || request.problemText.trim().length < 3
      || !bounded(request.workText, 6000) || request.workText.trim().length < 3
      || request.problemText.includes('[?]') || request.workText.includes('[?]')) throw new Error('Em kiểm tra và xác nhận đề cùng bài làm trước nhé.');
    const source = workReviewLines(request.workText);
    if (!source.length || source.length > 35 || source.some(row => row.length > 500)) throw new Error('Em chọn một phần bài làm nhỏ hơn nhé.');
    const { data } = await apiClient.post('/student/tutor/work-review', request, { timeout: TIMEOUT, signal });
    if (!data || data.sourceId !== request.sourceId || !['CORRECT', 'NEEDS_REVISION', 'NEEDS_REVIEW'].includes(data.status)
      || !bounded(data.summary, 500) || !bounded(data.praise, 300, true) || !bounded(data.nextAction, 300)
      || !bounded(data.alternative, 600, true) || !Array.isArray(data.rows) || data.rows.length !== source.length
      || data.rows.some((row: any, index: number) => !row || row.lineIndex !== index || row.sourceText !== source[index]
        || !['OK', 'FIX', 'UNSURE'].includes(row.status) || !bounded(row.feedback, 400)
        || !Array.isArray(row.hints) || row.hints.length > 2 || row.hints.some((hint: unknown) => !bounded(hint, 300))
        || (row.status === 'OK' && row.hints.length))
      || (data.status === 'CORRECT' ? !data.praise.trim() || data.rows.some((row: WorkReviewRow) => row.status !== 'OK')
        : !!data.praise.trim() || !!data.alternative.trim())
      || (data.status === 'NEEDS_REVISION' && !data.rows.some((row: WorkReviewRow) => row.status === 'FIX'))) throw new Error(INVALID_RESPONSE);
    return data;
  },
  async checkDivision(division: WrittenDivision, confirmed: boolean, signal?: AbortSignal): Promise<DivisionCheck> {
    if (!confirmed || !validDivision(division)) throw new Error('Em kiểm tra lại các số trước nhé.');
    const { data } = await apiClient.post('/student/tutor/division/check', { division, confirmed }, { timeout: 15000, signal });
    if (!data || !['CORRECT', 'TRY_AGAIN', 'NEEDS_REVIEW'].includes(data.status)
      || !['', 'dividend', 'divisor', 'quotient', 'rows'].includes(data.field)
      || typeof data.message !== 'string' || !data.message.trim() || data.message.length > 600
      || (data.rowIndex !== null && (!Number.isInteger(data.rowIndex) || data.rowIndex < 0 || data.rowIndex >= division.rows.length || data.field !== 'rows'))
      || (data.status === 'CORRECT' && (data.field !== '' || data.rowIndex !== null))
      || (data.status !== 'CORRECT' && data.field === '')
      || (data.hints !== undefined && (!Array.isArray(data.hints) || data.hints.length > 2
        || data.hints.some((hint: unknown) => typeof hint !== 'string' || !hint.trim() || hint.length > 300)
        || (data.status !== 'TRY_AGAIN' && data.hints.length > 0)))) throw new Error(INVALID_RESPONSE);
    return data;
  },
  async prepareLesson(problemText: string, workText: string, signal?: AbortSignal): Promise<void> {
    if (problemText.trim().length < 3 || problemText.length > 4000 || workText.length > 6000
      || problemText.includes('[?]') || workText.includes('[?]')) return;
    const { data } = await apiClient.post('/student/tutor/lesson/prepare', { problemText, workText }, { timeout: TIMEOUT, signal });
    if (!['preparing', 'ready', 'busy', 'unavailable'].includes(data?.phase)) throw new Error(INVALID_RESPONSE);
  },
  async startLesson(problemText: string, workText: string,
    confirmation: { problemConfirmed: boolean; workConfirmed: boolean; guidedUnderstanding?: boolean; startWithReading?: boolean }, signal?: AbortSignal): Promise<LessonResponse> {
    if (confirmation?.problemConfirmed !== true || (workText.trim() && confirmation.workConfirmed !== true)
      || (confirmation.guidedUnderstanding !== undefined && typeof confirmation.guidedUnderstanding !== 'boolean')
      || (confirmation.startWithReading !== undefined && typeof confirmation.startWithReading !== 'boolean')
      || (confirmation.startWithReading === true && confirmation.guidedUnderstanding !== true)
      || problemText.includes('[?]') || workText.includes('[?]')) throw new Error('Em kiểm tra lại đề và các số với ảnh trước nhé.');
    const { data } = await apiClient.post('/student/tutor/lesson', { problemText, workText, ...confirmation }, { timeout: TIMEOUT, signal });
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
        || (row.division != null && !validDivision(row.division))
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
