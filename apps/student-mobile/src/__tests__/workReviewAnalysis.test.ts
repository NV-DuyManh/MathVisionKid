import { analyzeRowPresentation, checkIncompleteWork } from '../features/tutoring/workReviewAnalysis';

it.each(['CALCULATION', 'OPERAND', 'UNIT'] as const)('uses red for the verified %s error and retains its specific feedback', kind => {
  const result = analyzeRowPresentation('1/3 + 2/4 = 2/6', '', 'FIX', 'Em chép sai mẫu số của phần cây xoài.', ['Đối chiếu với đề.'], kind);
  expect(result.badgeColor).toBe('#DC2626');
  expect(result.errorKind).toBe(kind);
  expect(result.detailedFeedback).toBe('Em chép sai mẫu số của phần cây xoài.');
});

it('keeps wording amber and does not call derived or equivalent fractions copied-number errors', () => {
  expect(analyzeRowPresentation('Số cây là:', '', 'FIX', 'Em đang tìm phần số cây.', [], 'EXPLANATION').badgeColor).toBe('#8C5900');
  expect(analyzeRowPresentation('1 - 11/15 = 4/15', '1/3 cây táo, 2/5 cây xoài.', 'OK').status).toBe('OK');
  expect(analyzeRowPresentation('2/6 + 2/5 = 11/15', '1/3 và 2/5', 'OK').errorKind).toBe('NONE');
});

it('never replaces uncertainty with a guessed numerical or wording error', () => {
  expect(analyzeRowPresentation('1/3 + 2/4 = 2/6', '1/3 và 2/5', 'UNSURE', 'Em đọc rõ lại mẫu số.').status).toBe('UNSURE');
  expect(analyzeRowPresentation('Số cây là:', '', 'UNSURE').label).toBe('Cần đối chiếu');
});

it('uses corroborated missing work even with an answer heading or an existing-row error', () => {
  const missing = 'Em còn thiếu tổng số cây từ số cây cam và phần tương ứng.';
  expect(checkIncompleteWork({ status: 'NEEDS_REVISION', complete: false, missingPart: missing, nextAction: 'Tìm tổng số cây.' }))
    .toEqual({ isIncomplete: true, missingDescription: missing, nextStepSummary: 'Tìm tổng số cây.' });
  expect(checkIncompleteWork({ status: 'NEEDS_REVIEW', complete: null, nextAction: 'Viết đáp số.' }).isIncomplete).toBe(false);
  expect(checkIncompleteWork({ status: 'CORRECT', complete: true, nextAction: 'Kiểm tra bằng cách khác.' }).isIncomplete).toBe(false);
});
