import {
  safeEvaluateArithmetic,
  classifyMathLine,
  evaluateMathSolution,
} from '../utils/mathSolutionEvaluator';

describe('mathSolutionEvaluator', () => {
  describe('safeEvaluateArithmetic', () => {
    it('evaluates basic arithmetic operations correctly', () => {
      expect(safeEvaluateArithmetic('15 + 7')).toBe(22);
      expect(safeEvaluateArithmetic('450 - 120')).toBe(330);
      expect(safeEvaluateArithmetic('25 * 4')).toBe(100);
      expect(safeEvaluateArithmetic('25 x 4')).toBe(100);
      expect(safeEvaluateArithmetic('120 / 3')).toBe(40);
      expect(safeEvaluateArithmetic('120 : 3')).toBe(40);
    });

    it('respects operator precedence (multiplication and division before addition)', () => {
      expect(safeEvaluateArithmetic('2 + 3 * 4')).toBe(14);
      expect(safeEvaluateArithmetic('20 - 10 / 2')).toBe(15);
      expect(safeEvaluateArithmetic('10 + 6 : 2')).toBe(13);
    });

    it('handles parentheses correctly', () => {
      expect(safeEvaluateArithmetic('(15 + 5) : 2')).toBe(10);
      expect(safeEvaluateArithmetic('(12 - 4) x 3')).toBe(24);
    });

    it('returns null on invalid or division by zero expressions', () => {
      expect(safeEvaluateArithmetic('10 : 0')).toBeNull();
      expect(safeEvaluateArithmetic('abc + def')).toBeNull();
      expect(safeEvaluateArithmetic('')).toBeNull();
    });
  });

  describe('classifyMathLine', () => {
    it('classifies header lines correctly', () => {
      expect(classifyMathLine('Bài 1').role).toBe('HEADER');
      expect(classifyMathLine('Bài giải').role).toBe('HEADER');
      expect(classifyMathLine('Câu 2:').role).toBe('HEADER');
    });

    it('classifies word problem explanation lines correctly', () => {
      expect(classifyMathLine('Số học sinh nữ là:').role).toBe('EXPLANATION');
      expect(classifyMathLine('Mỗi bạn được chia số kẹo là:').role).toBe('EXPLANATION');
      expect(classifyMathLine('Tổng số ki-lô-gam gạo là:').role).toBe('EXPLANATION');
    });

    it('classifies and validates correct equations', () => {
      const res = classifyMathLine('15 + 7 = 22 (học sinh)');
      expect(res.role).toBe('EQUATION');
      expect(res.validation?.isValid).toBe(true);
      expect(res.validation?.expectedResult).toBe(22);
      expect(res.validation?.observedResult).toBe(22);
      expect(res.validation?.unit).toBe('học sinh');
    });

    it('detects incorrect calculations with carry/borrow error hints', () => {
      const res = classifyMathLine('15 + 7 = 21');
      expect(res.role).toBe('EQUATION');
      expect(res.validation?.isValid).toBe(false);
      expect(res.validation?.expectedResult).toBe(22);
      expect(res.validation?.observedResult).toBe(21);
      expect(res.validation?.hint).toContain('số nhớ');
    });

    it('classifies answer lines', () => {
      const res = classifyMathLine('Đáp số: 22 học sinh');
      expect(res.role).toBe('ANSWER');
    });
  });

  describe('evaluateMathSolution (Full Worksheet & Multi-Step Logic)', () => {
    it('checks arithmetic and answer consistency without claiming word-problem correctness', () => {
      const lines = [
        { lineId: '1', text: 'Bài giải' },
        { lineId: '2', text: 'Số học sinh nữ là:' },
        { lineId: '3', text: '15 + 7 = 22 (học sinh)' },
        { lineId: '4', text: 'Đáp số: 22 học sinh' },
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.verdict).toBe('ALL_CORRECT');
      expect(result.summary.equationCount).toBe(1);
      expect(result.summary.correctEquations).toBe(1);
      expect(result.summary.hasAnswer).toBe(true);
      expect(result.summary.answerValidation?.matchesLastEquation).toBe(true);
      expect(result.summary.answerValidation?.status).toBe('PERFECT');
      expect(result.summary.hint).toContain('đối chiếu cách giải');
      expect(result.summary.hint).not.toContain('hoàn toàn chính xác');
    });

    it('detects multi-step chained equations (Bài toán 2 phép tính)', () => {
      const lines = [
        { lineId: '1', text: 'Bài giải' },
        { lineId: '2', text: 'Chiều rộng hình chữ nhật là:' },
        { lineId: '3', text: '18 - 6 = 12 (cm)' },
        { lineId: '4', text: 'Diện tích hình chữ nhật là:' },
        { lineId: '5', text: '18 x 12 = 216 (cm2)' },
        { lineId: '6', text: 'Đáp số: 216 cm2' },
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.verdict).toBe('ALL_CORRECT');
      expect(result.summary.equationCount).toBe(2);
      expect(result.summary.correctEquations).toBe(2);
      expect(result.summary.multiStepChain?.isChained).toBe(true);
      expect(result.summary.multiStepChain?.chainedValue).toBe(12);
      expect(result.summary.answerValidation?.matchesLastEquation).toBe(true);
      expect(result.summary.answerValidation?.status).toBe('PERFECT');
    });

    it('detects cascade error when Step 1 is wrong but Step 2 chained logic is preserved', () => {
      const lines = [
        { lineId: '1', text: 'Bài giải' },
        { lineId: '2', text: 'Chiều rộng hình chữ nhật là:' },
        { lineId: '3', text: '18 - 6 = 10 (cm)' }, // Calculated 10 instead of 12
        { lineId: '4', text: 'Diện tích hình chữ nhật là:' },
        { lineId: '5', text: '18 x 10 = 180 (cm2)' }, // Correctly used their step 1 result
        { lineId: '6', text: 'Đáp số: 180 cm2' },
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.verdict).toBe('HAS_CALCULATION_ERROR');
      expect(result.summary.incorrectEquations).toBe(1);
      expect(result.summary.correctEquations).toBe(1);
      expect(result.summary.multiStepChain?.isChained).toBe(true);
      expect(result.summary.multiStepChain?.chainedValue).toBe(10);
      expect(result.summary.multiStepChain?.chainDescription).toContain('sai dây chuyền');
    });

    it('detects mismatch between final answer line and the last equation', () => {
      const lines = [
        { lineId: '1', text: 'Bài giải' },
        { lineId: '2', text: '15 + 7 = 22 (kg)' },
        { lineId: '3', text: 'Đáp số: 25 kg' }, // Mismatch: wrote 25 instead of 22
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.answerValidation?.matchesLastEquation).toBe(false);
      expect(result.summary.answerValidation?.status).toBe('MISMATCH');
      expect(result.summary.verdict).toBe('HAS_ANSWER_ERROR');
      expect(result.summary.hint).toContain('Đáp số ghi 25 nhưng phép tính cuối ra 22');
    });

    it('detects and evaluates column math ("Đặt tính rồi tính") with separator line', () => {
      const lines = [
        { lineId: '1', text: '356' },
        { lineId: '2', text: '+ 128' },
        { lineId: '3', text: '---' },
        { lineId: '4', text: '484' },
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.verdict).toBe('ALL_CORRECT');
      expect(result.summary.equationCount).toBe(1);
      expect(result.summary.correctEquations).toBe(1);
      expect(result.lines[3].role).toBe('COLUMN_MATH');
      expect(result.lines[3].equationValidation?.isValid).toBe(true);
      expect(result.lines[3].equationValidation?.isColumnMath).toBe(true);
      expect(result.lines[3].equationValidation?.expectedResult).toBe(484);
    });

    it('detects and evaluates column math without separator line and flags carry error', () => {
      const lines = [
        { lineId: '1', text: '356' },
        { lineId: '2', text: '+ 128' },
        { lineId: '3', text: '474' }, // Miscalculated: forgot carry to tens
      ];

      const result = evaluateMathSolution(lines);
      expect(result.summary.verdict).toBe('HAS_CALCULATION_ERROR');
      expect(result.summary.equationCount).toBe(1);
      expect(result.summary.incorrectEquations).toBe(1);
      expect(result.lines[2].role).toBe('COLUMN_MATH');
      expect(result.lines[2].equationValidation?.isValid).toBe(false);
      expect(result.lines[2].equationValidation?.hint).toContain('số nhớ');
    });
  });
});
