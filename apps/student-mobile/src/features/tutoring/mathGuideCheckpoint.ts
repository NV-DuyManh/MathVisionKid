import { tokenStorage } from '../../services/auth/tokenStorage';
import type { WorkReviewCheckpoint } from './StudentWorkReview';
import type { NotebookLine, NotebookRead } from './api/TutorService';
import { validLearningProgress, type LearningProgress } from './learningProgress';

const STORAGE_KEY = 'mathvision.math-guide.active.v1';
const MAX_AGE = 7 * 86400000;
const MAX_SIZE = 250000;

export type MathGuideCheckpoint = {
  lessonId: string;
  quizPreparationKey: string;
  reading: NotebookRead | null;
  problem: string;
  work: string;
  workLines: NotebookLine[];
  problemConfirmed: boolean;
  sourceNeedsReview: boolean;
  workConfirmed: boolean;
  workImageCurrent: boolean;
  uncertainWork: boolean;
  problemPhoto: boolean;
  workPhoto: boolean;
  editing: 'problem' | 'work' | null;
  reviewStarted: boolean;
  reviewFocused: boolean;
  progress: LearningProgress | null;
  historyIndex: number | null;
  hintOpen: boolean;
  hintPage: number;
  fractionInput: boolean;
  answerEdited: boolean;
  pendingAnswer: string;
  savedToHistory: boolean;
  workReview: WorkReviewCheckpoint | null;
};

type StoredCheckpoint = {
  scope: string; route: string; savedAt: number; checkpoint: MathGuideCheckpoint;
};

export function mathGuideScope(owner: string | undefined): string | null {
  if (!owner || typeof window === 'undefined') return null;
  try {
    const tab = tokenStorage.getDraftScopeId();
    return tab ? JSON.stringify([owner, tab]) : null;
  } catch { return null; }
}

export function readMathGuideCheckpoint(scope: string, route: string): MathGuideCheckpoint | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw || raw.length > MAX_SIZE) return null;
    const saved = JSON.parse(raw) as StoredCheckpoint;
    if (!saved || saved.scope !== scope || saved.savedAt > Date.now()
        || !Number.isFinite(saved.savedAt) || Date.now() - saved.savedAt >= MAX_AGE) return null;
    if (saved.route !== route) return null;
    const row = saved.checkpoint;
    if (!row || typeof row.problem !== 'string' || row.problem.length > 4000
        || typeof row.work !== 'string' || row.work.length > 6000
        || typeof row.lessonId !== 'string' || typeof row.quizPreparationKey !== 'string'
        || !Array.isArray(row.workLines) || row.workLines.some(line => !line || typeof line.text !== 'string')
        || row.reading && (!Array.isArray(row.reading.lines) || typeof row.reading.problemText !== 'string')
        || row.workReview?.result && !Array.isArray(row.workReview.result.rows)
        || row.progress && !validLearningProgress(row.progress)) return null;
    return row;
  } catch { return null; }
}

export function saveMathGuideCheckpoint(scope: string, route: string, checkpoint: MathGuideCheckpoint): boolean {
  try {
    const serialized = JSON.stringify({ scope, route, checkpoint, savedAt: Date.now() } satisfies StoredCheckpoint);
    if (serialized.length > MAX_SIZE) return false;
    window.sessionStorage.setItem(STORAGE_KEY, serialized);
    return true;
  } catch { return false; }
}

export function clearMathGuideCheckpoint(): void {
  try { window.sessionStorage.removeItem(STORAGE_KEY); } catch { /* Storage can be disabled. */ }
}
