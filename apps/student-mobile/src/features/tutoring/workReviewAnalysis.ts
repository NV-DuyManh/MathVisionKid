import { COLORS } from '../../constants/theme';
import type { WorkReview, WorkReviewRow } from './api/TutorService';

export type RowErrorKind = NonNullable<WorkReviewRow['errorKind']>;

export function isWorkReviewIssue(row: Pick<WorkReviewRow, 'sourceText' | 'status' | 'errorKind' | 'rowKind'>): boolean {
  if (row.status !== 'FIX' || row.rowKind === 'HEADING' || row.rowKind === 'EXPLANATION') return false;
  if (row.rowKind === 'CALCULATION' || row.rowKind === 'ANSWER' || row.errorKind === 'DEPENDENT') return true;
  return row.errorKind !== 'EXPLANATION'
    && (/[=＝≠<>≤≥≈]/.test(row.sourceText) || /^(?:đáp số|đáp án|kết quả)\s*[:：]\s*\(?[+-]?\d/iu.test(row.sourceText)
      || /^\(?[+-]?\d[\d.,\s()+*/×÷:−-]*$/u.test(row.sourceText));
}
export interface RowPresentation {
  status: WorkReviewRow['status'];
  errorKind: RowErrorKind;
  label: string;
  badgeColor: string;
  badgeBg: string;
  badgeBorder: string;
  detailedFeedback: string;
  hints: string[];
}

/** Present the source-bound verdict; never re-grade a row by guessing its operands. */
export function analyzeRowPresentation(
  sourceText: string | undefined | null,
  problemText: string | undefined | null,
  backendStatus: WorkReviewRow['status'] = 'UNSURE',
  backendFeedback = '',
  backendHints: string[] = [],
  backendErrorKind?: RowErrorKind,
): RowPresentation {
  const status = backendStatus;
  const errorKind = status === 'FIX' ? backendErrorKind || 'NONE' : 'NONE';
  const common = { status, errorKind, detailedFeedback: backendFeedback, hints: status === 'OK' ? [] : backendHints };
  if (status === 'OK') return { ...common, label: 'Đã kiểm tra đúng',
    badgeColor: '#16A34A', badgeBg: '#EDF9F1', badgeBorder: '#D1ECD9' };
  if (status === 'UNSURE') return { ...common, label: 'Cần đối chiếu',
    badgeColor: COLORS.primaryDark, badgeBg: '#F3E8FF', badgeBorder: '#C084FC' };
  if (errorKind === 'CALCULATION' || errorKind === 'OPERAND' || errorKind === 'DEPENDENT' || errorKind === 'UNIT') return { ...common,
    label: errorKind === 'OPERAND' ? 'Viết sai số từ đề' : errorKind === 'UNIT' ? 'Cần sửa đơn vị'
      : errorKind === 'DEPENDENT' ? 'Cần tính lại sau khi sửa bước trước' : 'Sai tính toán',
    badgeColor: '#DC2626', badgeBg: '#FEF2F2', badgeBorder: '#F87171' };
  return { ...common, label: errorKind === 'EXPLANATION' ? 'Cần xem lại lời dẫn' : 'Cùng sửa bước này',
    badgeColor: '#8C5900', badgeBg: '#FFF8E9', badgeBorder: '#F59E0B' };
}

export interface IncompleteCheckResult {
  isIncomplete: boolean;
  missingDescription: string;
  nextStepSummary: string;
}

/** Missing work is independent of mistakes in the rows already written. */
export function checkIncompleteWork(result: Pick<WorkReview, 'complete' | 'missingPart' | 'nextAction' | 'status'>): IncompleteCheckResult {
  const isIncomplete = result.complete === false && result.status !== 'CORRECT';
  return {
    isIncomplete,
    missingDescription: isIncomplete ? result.missingPart || result.nextAction : '',
    nextStepSummary: isIncomplete ? result.nextAction : '',
  };
}
