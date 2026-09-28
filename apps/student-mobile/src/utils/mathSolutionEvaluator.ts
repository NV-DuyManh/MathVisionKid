/**
 * MathVision Kids — Primary School Math Solution Evaluator & Semantic Classifier
 *
 * Analyzes handwritten lines recognized by HandAI CRNN to classify:
 * 1. HEADER: "Bài 1", "Bài giải", "Câu 2:"
 * 2. EXPLANATION: Vietnamese word problem explanations ("Số kg gạo là:", "Mỗi hộp có:")
 * 3. EQUATION: Arithmetic calculations ("15 + 7 = 22 (kg)", "25 x 4 = 100")
 * 4. ANSWER: Final answer statements ("Đáp số: 22 kg")
 *
 * Validates arithmetic operations (addition, subtraction, multiplication, division)
 * and detects calculation/carry/borrow errors to guide elementary students.
 */

export type LineSemanticRole = 'HEADER' | 'EXPLANATION' | 'EQUATION' | 'COLUMN_MATH' | 'ANSWER' | 'TEXT';

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
  status: 'PERFECT' | 'MISMATCH' | 'MATCHED_INCORRECT_CALC' | 'NO_ANSWER' | 'NO_EQUATION';
  message: string;
}

export interface AnalyzedLine {
  lineId: string;
  text: string;
  role: LineSemanticRole;
  roleBadgeText: string;
  roleBadgeColor: string;
  equationValidation?: EquationValidation;
}

export interface MathSolutionSummary {
  totalLines: number;
  headerCount: number;
  explanationCount: number;
  equationCount: number;
  correctEquations: number;
  incorrectEquations: number;
  hasAnswer: boolean;
  verdict: 'ALL_CORRECT' | 'HAS_CALCULATION_ERROR' | 'TEXT_ONLY' | 'EMPTY';
  title: string;
  hint: string;
  badgeColor: string;
  multiStepChain?: MultiStepChainInfo;
  answerValidation?: AnswerValidation;
}

export interface MathSolutionEvaluationResult {
  summary: MathSolutionSummary;
  lines: AnalyzedLine[];
}

/**
 * Normalizes text for math detection: replaces Vietnamese math aliases
 * (e.g. 'x' or 'X' or '.' for multiply, ':' for divide).
 */
function cleanEquationString(raw: string): string {
  return raw
    .replace(/[–—]/g, '-')
    .replace(/[,]/g, '.')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Tries to extract an equation of the form:
 * <left side> = <right side> [unit]
 * Example: "15 + 7 = 22 (kg)" or "450 - 120 = 330" or "25 x 4 = 100" or "120 : 3 = 40"
 */
/**
 * Safely evaluates an arithmetic expression respecting standard order of operations
 * (parentheses, multiplication & division, then addition & subtraction).
 * No eval() or Function constructor used.
 */
export function safeEvaluateArithmetic(rawExpr: string): number | null {
  let expr = rawExpr
    .replace(/[–—]/g, '-')
    .replace(/[,]/g, '.')
    .replace(/x/gi, '*')
    .replace(/:/g, '/')
    .replace(/\s+/g, '');

  if (!expr || !/^[0-9+\-*/.()]+$/.test(expr)) {
    return null;
  }

  // Handle parentheses recursively
  let safeguard = 0;
  while (expr.includes('(') && safeguard++ < 10) {
    const start = expr.lastIndexOf('(');
    const end = expr.indexOf(')', start);
    if (end === -1) return null;
    const inner = expr.substring(start + 1, end);
    const innerResult = evaluateFlatExpression(inner);
    if (innerResult === null || isNaN(innerResult)) return null;
    expr = expr.substring(0, start) + innerResult + expr.substring(end + 1);
  }

  return evaluateFlatExpression(expr);
}

function evaluateFlatExpression(expr: string): number | null {
  const tokens = expr.match(/(\d+\.?\d*|[+\-*/])/g);
  if (!tokens || tokens.length === 0) return null;
  if (tokens.length === 1) return parseFloat(tokens[0]);

  // First pass: multiplication and division
  const pass1: (number | string)[] = [];
  let i = 0;
  while (i < tokens.length) {
    const token = tokens[i];
    if (token === '*' || token === '/') {
      const prevNum = pass1.pop();
      const nextNum = parseFloat(tokens[i + 1]);
      if (typeof prevNum !== 'number' || isNaN(nextNum)) return null;
      if (token === '*') {
        pass1.push(prevNum * nextNum);
      } else {
        if (nextNum === 0) return null;
        pass1.push(prevNum / nextNum);
      }
      i += 2;
    } else if (token === '+' || token === '-') {
      pass1.push(token);
      i++;
    } else {
      pass1.push(parseFloat(token));
      i++;
    }
  }

  // Second pass: addition and subtraction
  if (pass1.length === 0) return null;
  let total = typeof pass1[0] === 'number' ? pass1[0] : 0;
  let j = 1;
  while (j < pass1.length) {
    const op = pass1[j];
    const nextVal = pass1[j + 1];
    if (typeof nextVal !== 'number') break;
    if (op === '+') total += nextVal;
    else if (op === '-') total -= nextVal;
    j += 2;
  }

  return isNaN(total) ? null : Math.round(total * 10000) / 10000;
}

/**
 * Tries to extract an equation of the form:
 * <left side> = <right side> [unit]
 * Example: "15 + 7 = 22 (kg)" or "450 - 120 = 330" or "25 x 4 = 100" or "120 : 3 = 40"
 */
function parseAndValidateEquation(text: string): EquationValidation | null {
  // Must contain an equal sign '='
  if (!text.includes('=')) {
    return null;
  }

  const parts = text.split('=');
  if (parts.length < 2) return null;

  const rawLeft = parts[0].trim();
  const rawRight = parts.slice(1).join('=').trim();

  // Extract trailing unit if present, e.g. "(kg)" or "kg" or "(học sinh)"
  const unitMatch = rawRight.match(/[(\[]?([a-zA-Zà-ỹÀ-Ỹ\s\d^]+)[)\]]?$/);
  const unit = unitMatch ? unitMatch[1].trim() : undefined;

  // Extract right-hand number
  const rightNumberMatch = rawRight.match(/[-+]?\d*\.?\d+/);
  if (!rightNumberMatch) return null;
  const observedResult = parseFloat(rightNumberMatch[0]);

  // Extract operands from the left expression
  const operands = (rawLeft.match(/\d+\.?\d*/g) || []).map(Number);
  if (operands.length === 0) return null;

  try {
    const total = safeEvaluateArithmetic(rawLeft);
    if (total === null || isNaN(total)) return null;

    const expectedResult = Math.round(total * 10000) / 10000;
    const isValid = Math.abs(expectedResult - observedResult) < 0.0001;

    let hint: string | undefined;
    let errorDetail: string | undefined;

    if (!isValid) {
      errorDetail = `Phép tính cho kết quả ${expectedResult}, nhưng bài làm ghi ${observedResult}.`;
      
      // Diagnose common elementary math errors:
      const diff = Math.abs(expectedResult - observedResult);
      if (diff === 10 || diff === 1 || diff === 100) {
        hint = `Em hãy kiểm tra lại hàng nhớ (cộng hoặc mượn nhớ) của phép tính nhé! Kết quả đúng phải là ${expectedResult}.`;
      } else {
        hint = `Em hãy đặt tính ra nháp và tính lại cẩn thận nhé! Kết quả đúng phải là ${expectedResult}.`;
      }
    }

    return {
      isValid,
      leftExpr: rawLeft,
      operands,
      expectedResult,
      observedResult,
      unit,
      errorDetail,
      hint,
    };
  } catch {
    return null;
  }
}

/**
 * Classifies a line into its semantic role in a primary school math solution.
 */
export function classifyMathLine(rawText: string): {
  role: LineSemanticRole;
  roleBadgeText: string;
  roleBadgeColor: string;
  validation?: EquationValidation;
} {
  const text = rawText.trim();
  const lower = text.toLowerCase();

  // 1. Header line: "Bài 1", "Bài giải", "Câu 3"
  if (/^(bài\s*(giải|\d+|tập)?|câu\s*\d+|đề\s*bài)/i.test(lower)) {
    return {
      role: 'HEADER',
      roleBadgeText: '📌 Tiêu đề',
      roleBadgeColor: '#475569',
    };
  }

  // 2. Answer / Conclusion: "Đáp số: ...", "Đ/s:"
  if (/^(đáp\s*số|đ\/s)\s*:?/i.test(lower)) {
    return {
      role: 'ANSWER',
      roleBadgeText: '🎯 Đáp số',
      roleBadgeColor: '#7C3AED',
    };
  }

  // 3. Equation / Calculation: Check if line contains '=' and arithmetic operators
  const eq = parseAndValidateEquation(text);
  if (eq) {
    return {
      role: 'EQUATION',
      roleBadgeText: eq.isValid ? '✅ Phép tính đúng' : '❌ Phép tính sai',
      roleBadgeColor: eq.isValid ? '#15803D' : '#DC2626',
      validation: eq,
    };
  }

  // 4. Explanation Line: "Số ki-lô-gam...", "Mỗi bạn có...", ends with ':' or has descriptive words
  if (
    text.endsWith(':') ||
    /^(số|mỗi|tổng\s*số|còn\s*lại|chiều\s*dài|chiều\s*rộng|vận\s*tốc|thời\s*gian|quãng\s*đường|giá\s*tiền)/i.test(lower) ||
    (text.length > 10 && !/\d{3,}/.test(text))
  ) {
    return {
      role: 'EXPLANATION',
      roleBadgeText: '📝 Lời giải',
      roleBadgeColor: '#1D4ED8',
    };
  }

  // Fallback generic text
  return {
    role: 'TEXT',
    roleBadgeText: '📄 Dòng chữ',
    roleBadgeColor: '#64748B',
  };
}

/**
 * Evaluates the entire math worksheet containing multiple lines of text and equations.
 */
export function evaluateMathSolution(
  lines: Array<{ lineId: string; text?: string; finalText?: string; predictedText?: string }>
): MathSolutionEvaluationResult {
  const analyzedLines: AnalyzedLine[] = [];

  let headerCount = 0;
  let explanationCount = 0;
  let equationCount = 0;
  let correctEquations = 0;
  let incorrectEquations = 0;
  let hasAnswer = false;

  const rawLines = lines
    .map((l) => ({
      lineId: l.lineId,
      text: (l.finalText || l.text || l.predictedText || '').trim(),
    }))
    .filter((l) => l.text.length > 0);

  // Detect Column Math ("Đặt tính rồi tính")
  // e.g. Line i: "356", Line i+1: "+ 128", Line i+2 (or i+3): "484"
  const columnHandledIndices = new Set<number>();
  const columnDataByIndex = new Map<number, AnalyzedLine>();

  for (let i = 0; i < rawLines.length - 1; i++) {
    if (columnHandledIndices.has(i)) continue;

    const t1 = rawLines[i].text;
    const t2 = rawLines[i + 1].text;

    const t1NumMatch = t1.match(/^(\d+\.?\d*)$/);
    const t2OpMatch = t2.match(/^([+\-xX*:/])\s*(\d+\.?\d*)$/);

    if (t1NumMatch && t2OpMatch) {
      let sepIdx: number | null = null;
      let resIdx: number | null = null;

      if (i + 2 < rawLines.length) {
        const t3 = rawLines[i + 2].text;
        if (/^[-_=~]{2,}$/.test(t3)) {
          sepIdx = i + 2;
          if (i + 3 < rawLines.length) {
            const t4 = rawLines[i + 3].text;
            if (/^\d+\.?\d*$/.test(t4)) {
              resIdx = i + 3;
            }
          }
        } else if (/^\d+\.?\d*$/.test(t3)) {
          resIdx = i + 2;
        }
      }

      if (resIdx !== null) {
        const topNum = parseFloat(t1NumMatch[1]);
        const op = t2OpMatch[1];
        const bottomNum = parseFloat(t2OpMatch[2]);
        const observedResult = parseFloat(rawLines[resIdx].text);

        const leftExpr = `${topNum} ${op} ${bottomNum}`;
        const total = safeEvaluateArithmetic(leftExpr);

        if (total !== null && !isNaN(total)) {
          const expectedResult = Math.round(total * 10000) / 10000;
          const isValid = Math.abs(expectedResult - observedResult) < 0.0001;

          let hint: string | undefined;
          let errorDetail: string | undefined;

          if (!isValid) {
            errorDetail = `Đặt tính ${leftExpr} cho kết quả ${expectedResult}, nhưng bài làm ghi ${observedResult}.`;
            const diff = Math.abs(expectedResult - observedResult);
            if (diff === 10 || diff === 1 || diff === 100) {
              hint = `Em chú ý kiểm tra lại hàng nhớ (cộng hoặc mượn nhớ) nhé! Kết quả đúng phải là ${expectedResult}.`;
            } else {
              hint = `Em chú ý tính lần lượt từng hàng từ phải sang trái nhé! Kết quả đúng phải là ${expectedResult}.`;
            }
          }

          const validation: EquationValidation = {
            isValid,
            leftExpr,
            operands: [topNum, bottomNum],
            expectedResult,
            observedResult,
            isColumnMath: true,
            errorDetail,
            hint,
          };

          columnHandledIndices.add(i);
          columnDataByIndex.set(i, {
            lineId: rawLines[i].lineId,
            text: t1,
            role: 'COLUMN_MATH',
            roleBadgeText: '📐 Đặt tính: Số trên',
            roleBadgeColor: '#0D9488',
          });

          columnHandledIndices.add(i + 1);
          columnDataByIndex.set(i + 1, {
            lineId: rawLines[i + 1].lineId,
            text: t2,
            role: 'COLUMN_MATH',
            roleBadgeText: '📐 Đặt tính: Phép tính',
            roleBadgeColor: '#0D9488',
          });

          if (sepIdx !== null) {
            columnHandledIndices.add(sepIdx);
            columnDataByIndex.set(sepIdx, {
              lineId: rawLines[sepIdx].lineId,
              text: rawLines[sepIdx].text,
              role: 'COLUMN_MATH',
              roleBadgeText: '📐 Dấu gạch ngang',
              roleBadgeColor: '#0D9488',
            });
          }

          columnHandledIndices.add(resIdx);
          columnDataByIndex.set(resIdx, {
            lineId: rawLines[resIdx].lineId,
            text: rawLines[resIdx].text,
            role: 'COLUMN_MATH',
            roleBadgeText: isValid ? '✅ Kết quả đặt tính đúng' : '❌ Kết quả đặt tính sai',
            roleBadgeColor: isValid ? '#15803D' : '#DC2626',
            equationValidation: validation,
          });

          equationCount++;
          if (isValid) correctEquations++;
          else incorrectEquations++;
        }
      }
    }
  }

  for (let idx = 0; idx < rawLines.length; idx++) {
    if (columnDataByIndex.has(idx)) {
      analyzedLines.push(columnDataByIndex.get(idx)!);
      continue;
    }

    const { lineId, text } = rawLines[idx];
    const classification = classifyMathLine(text);

    if (classification.role === 'HEADER') headerCount++;
    if (classification.role === 'EXPLANATION') explanationCount++;
    if (classification.role === 'ANSWER') hasAnswer = true;
    if (classification.role === 'EQUATION') {
      equationCount++;
      if (classification.validation?.isValid) {
        correctEquations++;
      } else {
        incorrectEquations++;
      }
    }

    analyzedLines.push({
      lineId,
      text,
      role: classification.role,
      roleBadgeText: classification.roleBadgeText,
      roleBadgeColor: classification.roleBadgeColor,
      equationValidation: classification.validation,
    });
  }

  const totalLines = analyzedLines.length;

  // Determine overall verdict & child-friendly feedback
  let verdict: MathSolutionSummary['verdict'] = 'EMPTY';
  let title = 'Chưa phát hiện nội dung';
  let hint = 'MathVision chưa nhận diện được bài viết tay. Em hãy chụp lại rõ nét hơn nhé!';
  let badgeColor = '#64748B';

  if (totalLines > 0) {
    if (equationCount === 0) {
      verdict = 'TEXT_ONLY';
      title = 'Đã nhận diện chữ viết tay 📝';
      hint = 'MathVision đã đọc được các dòng chữ lời giải của em. Hãy viết thêm phép tính và đáp số nhé!';
      badgeColor = '#2563EB';
    } else if (incorrectEquations === 0) {
      verdict = 'ALL_CORRECT';
      title = 'Làm bài xuất sắc! 🎉';
      hint = explanationCount > 0
        ? `Tuyệt vời! Cả phần lời giải và tất cả ${correctEquations} phép tính đều hoàn toàn chính xác!`
        : `Tất cả ${correctEquations} phép tính đều hoàn toàn chính xác!`;
      badgeColor = '#15803D';
    } else {
      verdict = 'HAS_CALCULATION_ERROR';
      title = `Có ${incorrectEquations} phép tính cần kiểm tra lại 💡`;
      hint = `Phần lời giải rất tốt, nhưng có phép tính bị tính nhầm. Em hãy xem gợi ý chi tiết ở từng dòng bên dưới để sửa nhé!`;
      badgeColor = '#D97706';
    }
  }

  // 1. Analyze multi-step chain relationships (Bài toán nhiều bước tính)
  const equationLines = analyzedLines.filter(
    (l) => (l.role === 'EQUATION' || l.role === 'COLUMN_MATH') && l.equationValidation
  );

  let multiStepChain: MultiStepChainInfo | undefined;
  if (equationLines.length >= 2) {
    for (let i = 1; i < equationLines.length; i++) {
      const prevEq = equationLines[i - 1].equationValidation!;
      const currEq = equationLines[i].equationValidation!;
      const currOperands = currEq.operands || [];

      const usesObserved = currOperands.some(
        (op) => Math.abs(op - prevEq.observedResult) < 0.001
      );
      const usesExpected = currOperands.some(
        (op) => Math.abs(op - prevEq.expectedResult) < 0.001
      );

      if (usesObserved || usesExpected) {
        currEq.chainedFromStep = i;
        const chainedVal = usesObserved ? prevEq.observedResult : prevEq.expectedResult;
        
        if (prevEq.isValid) {
          multiStepChain = {
            isChained: true,
            sourceStepIndex: i,
            targetStepIndex: i + 1,
            chainedValue: chainedVal,
            chainDescription: `Bước ${i + 1} liên kết logic chính xác với kết quả ${chainedVal} của bước ${i}!`,
          };
        } else {
          multiStepChain = {
            isChained: true,
            sourceStepIndex: i,
            targetStepIndex: i + 1,
            chainedValue: chainedVal,
            chainDescription: `Bước ${i + 1} dùng số ${chainedVal} từ bước ${i}. Phương pháp liên kết đúng, nhưng bước ${i} tính nhầm nên bước ${i + 1} bị sai dây chuyền.`,
          };
        }
      }
    }
  }

  // 2. Validate final answer line against last equation
  let answerValidation: AnswerValidation | undefined;
  const answerLine = analyzedLines.find((l) => l.role === 'ANSWER');
  if (answerLine) {
    const rawNums = answerLine.text.match(/[-+]?\d*\.?\d+/g);
    const declaredNumbers = rawNums ? rawNums.map(Number) : [];

    if (equationLines.length > 0) {
      const lastEq = equationLines[equationLines.length - 1].equationValidation!;
      const matchesObserved = declaredNumbers.some(
        (n) => Math.abs(n - lastEq.observedResult) < 0.001
      );
      const matchesExpected = declaredNumbers.some(
        (n) => Math.abs(n - lastEq.expectedResult) < 0.001
      );

      if (matchesExpected && lastEq.isValid) {
        answerValidation = {
          hasAnswer: true,
          answerText: answerLine.text,
          declaredNumbers,
          matchesLastEquation: true,
          status: 'PERFECT',
          message: 'Đáp số khớp chính xác với kết quả bài giải!',
        };
      } else if (matchesObserved && !lastEq.isValid) {
        answerValidation = {
          hasAnswer: true,
          answerText: answerLine.text,
          declaredNumbers,
          matchesLastEquation: true,
          status: 'MATCHED_INCORRECT_CALC',
          message: `Đáp số khớp với phép tính cuối (${lastEq.observedResult}), nhưng phép tính đó bị tính nhầm (kết quả chuẩn là ${lastEq.expectedResult}).`,
        };
      } else {
        answerValidation = {
          hasAnswer: true,
          answerText: answerLine.text,
          declaredNumbers,
          matchesLastEquation: false,
          status: 'MISMATCH',
          message: declaredNumbers.length > 0
            ? `Đáp số ghi ${declaredNumbers[0]} nhưng phép tính cuối ra ${lastEq.observedResult}. Em kiểm tra lại nhé!`
            : 'Chưa tìm thấy con số trong dòng đáp số.',
        };
      }
    } else {
      answerValidation = {
        hasAnswer: true,
        answerText: answerLine.text,
        declaredNumbers,
        matchesLastEquation: false,
        status: 'NO_EQUATION',
        message: 'Đã có đáp số nhưng chưa có phép tính tương ứng.',
      };
    }
  }

  // Append answer mismatch warning to summary hint if applicable
  if (answerValidation && answerValidation.status === 'MISMATCH' && verdict === 'ALL_CORRECT') {
    hint += ` Chú ý: ${answerValidation.message}`;
  }

  const summary: MathSolutionSummary = {
    totalLines,
    headerCount,
    explanationCount,
    equationCount,
    correctEquations,
    incorrectEquations,
    hasAnswer,
    verdict,
    title,
    hint,
    badgeColor,
    multiStepChain,
    answerValidation,
  };

  return {
    summary,
    lines: analyzedLines,
  };
}
