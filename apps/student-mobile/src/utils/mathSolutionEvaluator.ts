/** Checks arithmetic and answer consistency; it does not grade word-problem meaning. */
export type LineSemanticRole = 'HEADER' | 'EXPLANATION' | 'EQUATION' | 'COLUMN_MATH' | 'ANSWER' | 'UNRESOLVED_MATH' | 'TEXT';

export interface EquationValidation {
  isValid: boolean;
  leftExpr: string;
  operands?: number[];
  expectedResult: number;
  observedResult: number;
  unit?: string;
  errorDetail?: string;
  hint?: string;
  chainedFromStep?: number;
  isColumnMath?: boolean;
}
export interface MultiStepChainInfo {
  isChained: boolean;
  chainDescription?: string;
  sourceStepIndex?: number;
  targetStepIndex?: number;
  chainedValue?: number;
}
export interface AnswerValidation {
  hasAnswer: boolean;
  answerText?: string;
  declaredNumbers: number[];
  matchesLastEquation: boolean;
  status: 'PERFECT' | 'MISMATCH' | 'MATCHED_INCORRECT_CALC' | 'NO_ANSWER' | 'NO_EQUATION' | 'UNIT_MISMATCH' | 'UNIT_UNVERIFIED' | 'AMBIGUOUS_ANSWER';
  message: string;
  lineId?: string;
}
export interface AnalyzedLine {
  lineId: string;
  text: string;
  role: LineSemanticRole;
  roleBadgeText: string;
  roleBadgeColor: string;
  equationValidation?: EquationValidation;
  confirmed: boolean;
  section: number;
}
export interface MathSolutionSummary {
  totalLines: number;
  headerCount: number;
  explanationCount: number;
  equationCount: number;
  correctEquations: number;
  incorrectEquations: number;
  unresolvedEquations: number;
  unconfirmedLineCount: number;
  hasAnswer: boolean;
  verdict: 'ALL_CORRECT' | 'HAS_CALCULATION_ERROR' | 'HAS_ANSWER_ERROR' | 'NEEDS_CONFIRMATION' | 'NEEDS_REVIEW' | 'INCOMPLETE' | 'TEXT_ONLY' | 'EMPTY';
  title: string;
  hint: string;
  badgeColor: string;
  multiStepChain?: MultiStepChainInfo;
  answerValidation?: AnswerValidation;
  answerValidations: AnswerValidation[];
}
export interface MathSolutionEvaluationResult {
  summary: MathSolutionSummary;
  lines: AnalyzedLine[];
}
interface MathInputLine {
  lineId: string;
  text?: string;
  finalText?: string;
  predictedText?: string;
  currentText?: string;
  verifiedTextRaw?: string;
  verdict?: string;
}
function normalizeMath(text: string): string {
  return text.replace(/[−–—]/g, '-').replace(/,/g, '.').replace(/[×xX·]/g, '*').replace(/[÷:]/g, '/');
}
function sameNumber(a: number, b: number): boolean {
  return Math.abs(a - b) <= Math.max(1, Math.abs(a), Math.abs(b)) * Number.EPSILON * 8;
}
/** Complete-expression parser: unary signs, parentheses, precedence; no ignored tokens. */
export function safeEvaluateArithmetic(rawExpr: string): number | null {
  const expr = normalizeMath(rawExpr).replace(/\s+/g, '');
  if (!expr || expr.length > 2048 || !/^[\d+\-*/.()]+$/.test(expr)) return null;
  let position = 0;
  const checked = (value: number): number => {
    if (!Number.isFinite(value) || Math.abs(value) > Number.MAX_SAFE_INTEGER) throw new Error('Invalid arithmetic');
    return value;
  };
  const factor = (depth: number): number => {
    if (depth > 32) throw new Error('Expression too deep');
    const next = expr[position];
    if (next === '+' || next === '-') {
      position++;
      return checked((next === '-' ? -1 : 1) * factor(depth + 1));
    }
    if (next === '(') {
      position++;
      const value = expression(depth + 1);
      if (expr[position++] !== ')') throw new Error('Unclosed parentheses');
      return value;
    }
    const number = expr.slice(position).match(/^(?:\d+(?:\.\d+)?|\.\d+)/);
    if (!number) throw new Error('Missing number');
    position += number[0].length;
    return checked(Number(number[0]));
  };
  const term = (depth: number): number => {
    let value = factor(depth);
    while (expr[position] === '*' || expr[position] === '/') {
      const operator = expr[position++];
      const right = factor(depth);
      if (operator === '/' && right === 0) throw new Error('Division by zero');
      value = checked(operator === '*' ? value * right : value / right);
    }
    return value;
  };
  const expression = (depth: number): number => {
    let value = term(depth);
    while (expr[position] === '+' || expr[position] === '-') {
      const operator = expr[position++];
      const right = term(depth);
      value = checked(operator === '+' ? value + right : value - right);
    }
    return value;
  };
  try {
    const value = expression(0);
    return position === expr.length ? value : null;
  } catch { return null; }
}
function parseQuantity(raw: string): { value: number; unit?: string } | null {
  // Unit digits such as cm² stay out of the answer's numeric value.
  const match = raw.trim().replace(/\.$/, '').match(/^([+\-−]?\s*(?:\d+(?:[.,]\d+)?|[.,]\d+))\s*(?:\(([^()]*)\)|\[([^\[\]]*)\]|([^()\[\]]*))?$/);
  if (!match) return null;
  const unit = (match[2] ?? match[3] ?? match[4] ?? '').trim();
  if (/^[eE][+\-]?\d/.test(unit) || /\s+\d/.test(unit)) return null;
  if (unit && !/^[\p{L}%][\p{L}\p{N}\s^²³./\-]*$/u.test(unit)) return null;
  const value = safeEvaluateArithmetic(match[1]);
  return value === null ? null : { value, unit: unit || undefined };
}
function validateEquation(leftExpr: string, observedResult: number, unit?: string): EquationValidation | null {
  const expectedResult = safeEvaluateArithmetic(leftExpr);
  if (expectedResult === null) return null;
  const isValid = sameNumber(expectedResult, observedResult);
  const difference = Math.abs(expectedResult - observedResult);
  return {
    isValid, leftExpr, expectedResult, observedResult, unit,
    operands: (normalizeMath(leftExpr).match(/(?:\d+(?:\.\d+)?|\.\d+)/g) || []).map(Number),
    errorDetail: isValid ? undefined : `Phép tính cho kết quả ${expectedResult}, nhưng bài làm ghi ${observedResult}.`,
    hint: isValid ? undefined : [1, 10, 100].some(value => sameNumber(value, difference))
      ? 'Em hãy kiểm tra từng hàng và số nhớ hoặc số mượn nhé.'
      : 'Em hãy tính lại theo thứ tự: trong ngoặc, nhân chia, rồi cộng trừ nhé.',
  };
}
function parseEquation(text: string): EquationValidation | null {
  const parts = text.split('=');
  if (parts.length !== 2) return null;
  const left = parts[0].replace(/^(?:bài|câu)\s*\d+\s*[:.)]\s*/i, '').trim();
  const right = parseQuantity(parts[1]);
  return right ? validateEquation(left, right.value, right.unit) : null;
}
export function classifyMathLine(rawText: string): {
  role: LineSemanticRole; roleBadgeText: string; roleBadgeColor: string; validation?: EquationValidation;
} {
  const text = rawText.trim();
  if (/^(đáp\s*số|đ\/s)\s*:?/i.test(text)) return { role: 'ANSWER', roleBadgeText: 'Đáp số', roleBadgeColor: '#7C3AED' };
  if (text.includes('=')) {
    const validation = parseEquation(text);
    return validation
      ? { role: 'EQUATION', roleBadgeText: validation.isValid ? 'Phép tính đúng' : 'Phép tính cần sửa', roleBadgeColor: validation.isValid ? '#15803D' : '#DC2626', validation }
      : { role: 'UNRESOLVED_MATH', roleBadgeText: 'Cần kiểm tra ký hiệu toán', roleBadgeColor: '#B45309' };
  }
  if (/^(bài\s*(giải|\d+|tập)?|câu\s*\d+|đề\s*bài)\s*[:.)]?$/i.test(text)) return { role: 'HEADER', roleBadgeText: 'Tiêu đề', roleBadgeColor: '#475569' };
  if (/^[\d\s+\-−–—xX×*·:/÷.,()]+$/.test(text) && (/[+xX×*·:/÷]/.test(text) || /\d\s*[-−–—]\s*\d/.test(text))) return { role: 'UNRESOLVED_MATH', roleBadgeText: 'Chưa đọc đủ phép tính', roleBadgeColor: '#B45309' };
  if (text.endsWith(':') || /^(số|mỗi|tổng\s*số|còn\s*lại|chiều\s*dài|chiều\s*rộng|vận\s*tốc|thời\s*gian|quãng\s*đường|giá\s*tiền)/i.test(text) || text.length > 10) return { role: 'EXPLANATION', roleBadgeText: 'Lời giải', roleBadgeColor: '#1D4ED8' };
  return { role: 'TEXT', roleBadgeText: 'Dòng chữ', roleBadgeColor: '#64748B' };
}
function normalizeUnit(unit?: string): string {
  return (unit || '').toLowerCase().replace(/²/g, '2').replace(/³/g, '3').replace(/[\s^]/g, '');
}
function checkAnswer(answer: AnalyzedLine, equation?: EquationValidation): AnswerValidation {
  const quantity = parseQuantity(answer.text.replace(/^(đáp\s*số|đ\/s)\s*:?\s*/i, ''));
  const base = { hasAnswer: true, answerText: answer.text, lineId: answer.lineId, declaredNumbers: quantity ? [quantity.value] : [], matchesLastEquation: false };
  if (!quantity) return { ...base, status: 'AMBIGUOUS_ANSWER', message: 'Em hãy kiểm tra lại con số và đơn vị trong đáp số.' };
  if (!equation) return { ...base, status: 'NO_EQUATION', message: 'Đã có đáp số nhưng chưa có phép tính tương ứng trong bài này.' };
  if (!sameNumber(quantity.value, equation.observedResult)) return { ...base, status: 'MISMATCH', message: `Đáp số ghi ${quantity.value} nhưng phép tính cuối ra ${equation.observedResult}. Em kiểm tra lại nhé!` };
  if (!equation.isValid) return { ...base, matchesLastEquation: true, status: 'MATCHED_INCORRECT_CALC', message: 'Đáp số dùng kết quả của phép tính còn sai. Em sửa phép tính trước nhé.' };
  if (quantity.unit && equation.unit && normalizeUnit(quantity.unit) !== normalizeUnit(equation.unit)) return { ...base, status: 'UNIT_MISMATCH', message: `Đáp số ghi đơn vị ${quantity.unit}, còn phép tính ghi ${equation.unit}. Em đối chiếu lại đề bài nhé.` };
  if (Boolean(quantity.unit) !== Boolean(equation.unit)) return { ...base, matchesLastEquation: true, status: 'UNIT_UNVERIFIED', message: 'Con số khớp, nhưng cần bổ sung hoặc kiểm tra đơn vị ở phép tính và đáp số.' };
  return { ...base, matchesLastEquation: true, status: 'PERFECT', message: 'Đáp số khớp với phép tính cuối của bài này.' };
}
export function evaluateMathSolution(input: MathInputLine[], options: { requireConfirmation?: boolean } = {}): MathSolutionEvaluationResult {
  let section = 0;
  const lines: AnalyzedLine[] = input.map(line => {
    const reviewed = line.verdict === 'CORRECT' || line.verdict === 'CORRECTED';
    const text = line.verdict === 'SKIPPED' ? '' : (reviewed
      ? line.verifiedTextRaw ?? line.currentText ?? line.finalText ?? line.text ?? line.predictedText ?? ''
      : line.currentText ?? line.finalText ?? line.text ?? line.predictedText ?? '').trim();
    if (/^(?:bài|câu)\s*\d+(?:\s*[:.)]|\s*$)/i.test(text)) section++;
    const classified = classifyMathLine(text);
    return { lineId: line.lineId, text, role: classified.role, roleBadgeText: classified.roleBadgeText, roleBadgeColor: classified.roleBadgeColor, equationValidation: classified.validation, confirmed: !options.requireConfirmation || reviewed, section };
  });
  // Only neighboring rows can form a vertical calculation; blank rows cannot be skipped.
  for (let index = 0; index + 2 < lines.length; index++) {
    const first = lines[index], second = lines[index + 1];
    if (first.role === 'COLUMN_MATH') continue;
    const top = parseQuantity(first.text);
    const bottom = second.text.match(/^([+\-−–—xX×*·:/÷])\s*(\d+(?:[.,]\d+)?)$/);
    if (!top || top.unit || !bottom) continue;
    const separator = /^[-_=~]{2,}$/.test(lines[index + 2].text);
    const resultIndex = index + (separator ? 3 : 2);
    const result = lines[resultIndex];
    const observed = result && parseQuantity(result.text);
    if (!result || !observed || result.section !== first.section) continue;
    const equation = validateEquation(`${first.text} ${bottom[1]} ${bottom[2]}`, observed.value, observed.unit);
    if (!equation) continue;
    for (let row = index; row <= resultIndex; row++) {
      lines[row].role = 'COLUMN_MATH';
      lines[row].roleBadgeColor = '#0D9488';
      lines[row].roleBadgeText = row === resultIndex ? (equation.isValid ? 'Kết quả đặt tính đúng' : 'Kết quả đặt tính cần sửa') : 'Đặt tính';
    }
    equation.isColumnMath = true;
    result.equationValidation = equation;
    result.confirmed = lines.slice(index, resultIndex + 1).every(line => line.confirmed);
  }
  for (const line of lines) {
    if (line.equationValidation && !line.confirmed) {
      line.roleBadgeText = 'Phép tính chờ xác nhận';
      line.roleBadgeColor = '#B45309';
    }
  }
  const equations = lines.filter(line => line.equationValidation);
  const answers: AnswerValidation[] = [];
  let previousEquation: AnalyzedLine | undefined;
  let multiStepChain: MultiStepChainInfo | undefined;
  let step = 0;
  for (const line of lines) {
    if (previousEquation && previousEquation.section !== line.section) previousEquation = undefined;
    if (line.equationValidation) {
      step++;
      const current = line.equationValidation, previous = previousEquation?.equationValidation;
      if (previous && current.operands?.some(value => sameNumber(value, previous.observedResult))) {
        current.chainedFromStep = step - 1;
        multiStepChain = {
          isChained: true, sourceStepIndex: step - 1, targetStepIndex: step, chainedValue: previous.observedResult,
          chainDescription: previous.isValid
            ? `Bước ${step} có dùng số ${previous.observedResult} từ bước trước. Em đối chiếu cách dùng số này với đề bài nhé.`
            : `Bước ${step} có dùng kết quả ${previous.observedResult} của bước trước đang tính sai, nên có thể sai dây chuyền. Em sửa bước trước rồi tính lại nhé.`,
        };
      }
      previousEquation = line;
    } else if (line.role === 'ANSWER') {
      answers.push(checkAnswer(line, previousEquation?.equationValidation));
      previousEquation = undefined;
    }
  }
  const totalLines = lines.filter(line => line.text).length;
  const headerCount = lines.filter(line => line.role === 'HEADER').length;
  const explanationCount = lines.filter(line => line.role === 'EXPLANATION').length;
  const correctEquations = equations.filter(line => line.equationValidation?.isValid).length;
  const incorrectEquations = equations.length - correctEquations;
  const unresolvedEquations = lines.filter(line => line.role === 'UNRESOLVED_MATH').length;
  const unconfirmedLineCount = lines.filter(line => line.text && !line.confirmed && line.role !== 'HEADER').length;
  const answerError = answers.find(answer => answer.status !== 'PERFECT');
  const incompleteSection = lines.some(line => line.role === 'EXPLANATION' && !lines.some(answer => answer.role === 'ANSWER' && answer.section === line.section));
  let verdict: MathSolutionSummary['verdict'] = 'EMPTY', title = 'Chưa đọc được nội dung', hint = 'Em hãy chụp rõ phép tính và lời giải nhé.', badgeColor = '#64748B';
  if (totalLines) {
    if (unconfirmedLineCount && (equations.length || unresolvedEquations || answers.length)) {
      verdict = 'NEEDS_CONFIRMATION'; title = 'Kiểm tra nội dung vừa đọc'; badgeColor = '#B45309';
      hint = `Còn ${unconfirmedLineCount} dòng chưa xác nhận. Em sửa chữ hoặc ký hiệu nếu cần, rồi xác nhận để kiểm tra toán.`;
    } else if (unresolvedEquations) {
      verdict = 'NEEDS_REVIEW'; title = 'Cần đọc rõ thêm phép tính'; badgeColor = '#B45309';
      hint = 'Có ký hiệu hoặc phép tính chưa đọc đủ. Em sửa lại dòng được đánh dấu trước khi kiểm tra nhé.';
    } else if (incorrectEquations) {
      verdict = 'HAS_CALCULATION_ERROR'; title = `Có ${incorrectEquations} phép tính cần sửa`; badgeColor = '#B45309';
      hint = 'Em xem gợi ý ở từng dòng. Nếu dùng kết quả của bước trước, hãy sửa bước đó trước nhé.';
    } else if (answerError) {
      verdict = 'HAS_ANSWER_ERROR'; title = 'Cần kiểm tra lại đáp số'; badgeColor = '#B45309'; hint = answerError.message;
    } else if (equations.length && incompleteSection) {
      verdict = 'INCOMPLETE'; title = 'Phép tính đúng, cần bổ sung đáp số'; badgeColor = '#2563EB';
      hint = 'Em viết đáp số kèm đơn vị và đối chiếu lời giải với câu hỏi của đề bài nhé.';
    } else if (equations.length) {
      verdict = 'ALL_CORRECT'; title = 'Các phép tính đã kiểm tra đều đúng'; badgeColor = '#15803D';
      hint = `${correctEquations} phép tính đúng${answers.length ? ', đáp số khớp' : ''}. ${explanationCount ? 'Em vẫn cần đối chiếu cách giải và đơn vị với đề bài.' : 'Em có thể xem lại từng dòng bên dưới.'}`;
    } else {
      verdict = 'TEXT_ONLY'; title = 'Đã đọc các dòng lời giải'; badgeColor = '#2563EB';
      hint = 'Chưa tìm thấy phép tính đầy đủ để kiểm tra. Em xem lại chữ số, dấu phép tính và đáp số nhé.';
    }
  }
  return {
    summary: { totalLines, headerCount, explanationCount, equationCount: equations.length, correctEquations, incorrectEquations, unresolvedEquations, unconfirmedLineCount, hasAnswer: answers.length > 0, verdict, title, hint, badgeColor, multiStepChain, answerValidation: answerError ?? answers[answers.length - 1], answerValidations: answers },
    lines,
  };
}
