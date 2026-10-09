import { calculate, calculateExpression, CalculatorInput } from '../features/calculator/calculate';

const base: CalculatorInput = { mode: 'basic', operator: '+', left: '0', right: '0', leftDenominator: '', rightDenominator: '' };
const result = (values: Partial<CalculatorInput>) => calculate({ ...base, ...values });

it.each([
  ['1+3', '4'], ['2+3×4', '14'], ['(2+3)×4', '20'], ['20÷5÷2', '2'],
  ['1/3+2/5', '11/15'], ['1−1/3−2/5', '4/15'], ['16÷(4/15)', '60'],
  ['6÷2/3', '9'], ['1/3÷2/3', '1/2'], ['1/2×3/4', '3/8'], ['0,1+0,2', '0,3'], ['25%', '0,25'],
  ['200×10%', '20'], ['200+10%', '200,1'], ['(-3)+5', '2'], ['8−(-2)', '10'],
  ['999999+1', '1000000'], ['0,0001×0,0001×0,0001', '0,000000000001'],
] as const)('evaluates complete expression %s', (expression, expected) => {
  expect(calculateExpression(expression).result).toBe(expected);
});
it.each(['', '1+', '1÷0', '1/0', '(1+2', '1+2)', '2(3)', '1abc+2', '1..2', '1234567', '1+'.repeat(70)])('rejects incomplete or invalid expression %s', expression => {
  expect(() => calculateExpression(expression)).toThrow();
});
it('explains actual fractions and preserves long-division rows in one calculator', () => {
  expect(calculateExpression('1/3+2/5').steps.join(' ')).toContain('mẫu số 15');
  const division = calculateExpression('1005÷5');
  expect(division.remainder?.result).toBe('Thương 201, dư 0');
  expect(division.remainder?.steps.join(' ')).toContain('Hạ chữ số 0');
});

it.each([
  ['17843', '3', '÷', '17843/3'], ['0,1', '0,2', '+', '0,3'],
  ['1.25', '0.5', '−', '0,75'], ['12', '3', '÷', '4'],
  ['0', '999999', '×', '0'], ['-3', '2', '×', '−6'],
  ['7', '12', '−', '−5'], ['999999', '999999', '×', '999998000001'],
  ['1', '8', '÷', '0,125'], ['1', '3', '÷', '1/3'],
] as const)('calculates %s %s %s exactly', (left, right, operator, expected) => {
  expect(result({ left, right, operator }).result).toBe(expected);
});

it.each([
  ['1', '3', '2', '5', '+', '11/15'], ['1', '1', '11', '15', '−', '4/15'],
  ['16', '1', '4', '15', '÷', '60'], ['3', '2', '2', '3', '×', '1'],
  ['1', '2', '3', '4', '÷', '2/3'], ['1', '3', '2', '3', '−', '-1/3'],
  ['0', '5', '1', '2', '×', '0'], ['2', '4', '4', '8', '+', '1'],
] as const)('calculates fractions %s/%s and %s/%s', (left, leftDenominator, right, rightDenominator, operator, expected) => {
  const answer = result({ mode: 'fraction', left, leftDenominator, right, rightDenominator, operator });
  expect(answer.result).toBe(expected);
  expect(answer.steps.length).toBeGreaterThan(1);
});

it('grounds fraction explanations in the entered operands and reduces the result', () => {
  const answer = result({ mode: 'fraction', left: '1', leftDenominator: '6', right: '1', rightDenominator: '3' });
  expect(answer.steps.join(' ')).toContain('mẫu số 6');
  expect(answer.steps.join(' ')).toContain('1/3 = 2/6');
  expect(answer.steps.join(' ')).toContain('chia cả tử và mẫu cho 3');
  expect(answer.result).toBe('1/2');
});

it.each([['17', '5', 'Thương 3, dư 2'], ['1005', '5', 'Thương 201, dư 0'],
  ['3', '9', 'Thương 0, dư 3'], ['0', '7', 'Thương 0, dư 0'], ['49572', '6', 'Thương 8262, dư 0']])
('checks quotient and remainder for %s divided by %s', (left, right, expected) => {
  expect(result({ mode: 'remainder', left, right }).result).toBe(expected);
});

it('keeps an internal zero in the explained division', () => {
  const answer = result({ mode: 'remainder', left: '1005', right: '5' });
  expect(answer.steps.join(' ')).toContain('Lấy 0 chia 5: viết 0 vào thương');
  expect(answer.steps.join(' ')).toContain('5 × 201 + 0 = 1005');
});

it('explains actual carrying and chained borrowing', () => {
  expect(result({ left: '95', right: '17' }).steps.join(' ')).toContain('5 + 7 = 12. Viết 2, nhớ 1');
  expect(result({ left: '1000', right: '1', operator: '−' }).steps.join(' ')).toContain('0 − 1 (đã cho mượn) + 10');
  expect(result({ mode: 'remainder', left: '1005', right: '5' }).steps.join(' ')).toContain('Hạ chữ số 0 tiếp theo xuống, được 0');
});

it.each([
  { left: '' }, { left: '1+2' }, { left: 'NaN' }, { left: '1e3' }, { left: '1000000' }, { left: '0,12345' },
  { left: '1.2.3' }, { operator: '÷', right: '0' }, { mode: 'remainder', left: '-1', right: '3' },
  { mode: 'remainder', left: '17', right: '0' }, { mode: 'remainder', left: '1,2', right: '3' },
  { mode: 'fraction', leftDenominator: '0', rightDenominator: '2' },
  { mode: 'fraction', leftDenominator: '3', rightDenominator: '-2' },
  { mode: 'fraction', leftDenominator: '3', rightDenominator: '2', operator: '÷', right: '0' },
  { left: '999999.9999', right: '999999.9999', operator: '×' },
] as Partial<CalculatorInput>[])('rejects incomplete, invalid or unsafe arithmetic %#', input => {
  expect(() => result(input)).toThrow();
});

it('obeys division invariants for different operand widths', () => {
  for (const dividend of [0, 1, 17, 1005, 17843, 999999]) for (const divisor of [1, 3, 5, 97, 999999]) {
    const answer = result({ mode: 'remainder', left: String(dividend), right: String(divisor) });
    const [, q, r] = answer.result.match(/^Thương (\d+), dư (\d+)$/)!;
    expect(Number(q) * divisor + Number(r)).toBe(dividend);
    expect(Number(r)).toBeLessThan(divisor);
  }
});
