import { classifyMathLine, evaluateMathSolution, safeEvaluateArithmetic } from '../utils/mathSolutionEvaluator';

const lines = (...texts: string[]) => texts.map((text, index) => ({ lineId: String(index), text }));

describe('complete arithmetic parsing', () => {
  it.each([
    ['2+(3-5)', 0], ['-5+2', -3], ['2*-3', -6], ['-(2+3)', -5],
    ['1,5 + 0,5', 2], ['2 × 3 + 8 ÷ 4', 8], ['.5 + .25', .75],
    ['18−6', 12], ['(2+(3*(4-1)))', 11],
  ])('evaluates %s fully', (expression, expected) => {
    expect(safeEvaluateArithmetic(expression as string)).toBe(expected);
  });

  it.each(['12+', '12..5', '2(3+4)', '2+(3', '2+3)', '2**3', '2 / -0', '1e3', '9007199254740992', '1/0', ')2('])('rejects %s', expression => {
    expect(safeEvaluateArithmetic(expression)).toBeNull();
  });

  it.each(['12 += 12', '2+3=5=99', '2+3=5+9', '2+3=5e99', '2+3=5 (kg', '12 - 5'])('requires review of %s', text => {
    expect(classifyMathLine(text).role).toBe('UNRESOLVED_MATH');
    expect(evaluateMathSolution(lines('2+3=5', text)).summary.verdict).toBe('NEEDS_REVIEW');
  });

  it.each(['1+0,5=1,5', '2 × 3 = 6', '8 ÷ 4 = 2', 'Bài 2: 15+7=22', '0.1+0.2=0.3'])('recognizes %s', text => {
    expect(classifyMathLine(text).validation?.isValid).toBe(true);
  });
});

describe('solution review integrity', () => {
  it('checks confirmed correction rather than stale prediction', () => {
    const result = evaluateMathSolution([{ lineId: 'eq', predictedText: '2+3=5', finalText: '2+3=5', verifiedTextRaw: '2+3=6', verdict: 'CORRECTED' }], { requireConfirmation: true });
    expect(result.summary.verdict).toBe('HAS_CALCULATION_ERROR');
    expect(result.lines[0].equationValidation?.observedResult).toBe(6);
  });

  it('keeps an explicitly empty correction empty', () => {
    expect(evaluateMathSolution([{ lineId: 'eq', predictedText: '2+3=5', verifiedTextRaw: '', verdict: 'CORRECTED' }]).summary.verdict).toBe('EMPTY');
  });

  it('does not announce success before source text is confirmed', () => {
    expect(evaluateMathSolution([{ lineId: 'eq', predictedText: '2+3=5', verdict: 'UNVERIFIED' }], { requireConfirmation: true }).summary.verdict).toBe('NEEDS_CONFIRMATION');
  });

  it('requires operand confirmation as well as result confirmation in column math', () => {
    const result = evaluateMathSolution([
      { lineId: 'top', text: '356', verdict: 'UNVERIFIED' },
      { lineId: 'bottom', text: '+128', verdict: 'CORRECT' },
      { lineId: 'result', text: '484', verdict: 'CORRECT' },
    ], { requireConfirmation: true });
    expect(result.summary.verdict).toBe('NEEDS_CONFIRMATION');
    expect(result.lines[2].confirmed).toBe(false);
  });

  it('keeps skipped or blank rows as boundaries rather than stitching separate numbers', () => {
    expect(evaluateMathSolution([
      { lineId: 'top', text: '356' }, { lineId: 'skip', text: 'other', verdict: 'SKIPPED' },
      { lineId: 'bottom', text: '+128' }, { lineId: 'result', text: '484' },
    ]).summary.equationCount).toBe(0);
  });

  it('detects an incorrect answer even when arithmetic is correct', () => {
    const result = evaluateMathSolution(lines('2+3=5', 'Đáp số: 99'));
    expect(result.summary.verdict).toBe('HAS_ANSWER_ERROR');
  });

  it('checks units and does not mistake the exponent for the answer', () => {
    const good = evaluateMathSolution(lines('18×12=216 (cm2)', 'Đáp số: 216 cm²'));
    expect(good.summary.answerValidation?.status).toBe('PERFECT');
    expect(good.summary.answerValidation?.declaredNumbers).toEqual([216]);
    const wrong = evaluateMathSolution(lines('15+7=22 (kg)', 'Đáp số: 22 g'));
    expect(wrong.summary.verdict).toBe('HAS_ANSWER_ERROR');
    expect(wrong.summary.answerValidation?.status).toBe('UNIT_MISMATCH');
  });

  it('flags missing units, multiple numbers and missing word-problem answer', () => {
    expect(evaluateMathSolution(lines('15+7=22', 'Đáp số: 22 kg')).summary.answerValidation?.status).toBe('UNIT_UNVERIFIED');
    expect(evaluateMathSolution(lines('2+3=5', 'Đáp số: 5 và 99')).summary.answerValidation?.status).toBe('AMBIGUOUS_ANSWER');
    expect(evaluateMathSolution(lines('Số học sinh là:', '15+7=22')).summary.verdict).toBe('INCOMPLETE');
  });

  it('does not use an equation from a different exercise for the answer', () => {
    const result = evaluateMathSolution(lines('Bài 1', '2+3=5', 'Đáp số: 5', 'Bài 2', 'Đáp số: 5'));
    expect(result.summary.verdict).toBe('HAS_ANSWER_ERROR');
    expect(result.summary.answerValidations[1].status).toBe('NO_EQUATION');
  });

  it('does not claim semantic correctness from a coincidentally repeated number', () => {
    const result = evaluateMathSolution(lines('Lời giải bất kỳ chưa đối chiếu đề bài:', '2+3=5', '5×2=10', 'Đáp số: 10'));
    expect(result.summary.multiStepChain?.chainDescription).toContain('đối chiếu');
    expect(result.summary.hint).not.toContain('lời giải và');
  });
});
