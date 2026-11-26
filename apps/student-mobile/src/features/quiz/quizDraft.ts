import { tokenStorage } from '../../services/auth/tokenStorage';

export type QuizDraft = { answer: string; requestId?: string };

export function quizDraftRun(owner: string, startedAt: string | null): string | null {
  if (!startedAt) return null;
  try {
    const scope = tokenStorage.getDraftScopeId();
    return scope ? JSON.stringify([owner, scope, startedAt]) : null;
  } catch { return null; }
}

const key = (id: string) => `mathvision.quiz.draft.v1:${id}`;
const requestIdFormat = /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i;

export function readQuizDraft(id: string, run: string): QuizDraft | null {
  try {
    const value = JSON.parse(window.sessionStorage.getItem(key(id)) ?? 'null');
    if (value?.run !== run || typeof value.answer !== 'string' || value.answer.length > 100) return null;
    const requestId = typeof value.requestId === 'string' && requestIdFormat.test(value.requestId) ? value.requestId : undefined;
    return { answer: value.answer, requestId };
  } catch { return null; }
}

export function saveQuizDraft(id: string, run: string, draft: QuizDraft | null): void {
  try {
    if (draft?.answer) window.sessionStorage.setItem(key(id), JSON.stringify({ run, ...draft }));
    else if (readQuizDraft(id, run)) window.sessionStorage.removeItem(key(id));
  } catch { /* The quiz remains usable when storage is unavailable. */ }
}
