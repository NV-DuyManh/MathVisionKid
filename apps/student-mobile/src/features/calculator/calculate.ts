export type CalculatorMode = 'basic' | 'fraction' | 'remainder';
export type Operator = '+' | '−' | '×' | '÷';
export type CalculatorInput = {
  mode: CalculatorMode; operator: Operator;
  left: string; right: string; leftDenominator: string; rightDenominator: string;
};
export type Calculation = { expression: string; result: string; steps: string[] };
type Rational = { n: number; d: number };

function gcd(a: number, b: number): number {
  while (b) [a, b] = [b, a % b];
  return Math.abs(a) || 1;
}
function reduce(n: number, d: number): Rational {
  if (!Number.isSafeInteger(n) || !Number.isSafeInteger(d) || d === 0)
    throw new Error('Số quá lớn để tính chính xác. Em dùng số nhỏ hơn nhé.');
  const factor = gcd(n, d) * (d < 0 ? -1 : 1);
  return { n: n / factor, d: d / factor };
}
function whole(text: string, label: string, signed = false): number {
  if (!(signed ? /^-?\d{1,6}$/ : /^\d{1,6}$/).test(text.trim()))
    throw new Error(`${label}: em nhập số nguyên, tối đa 6 chữ số${signed ? ' (có thể có dấu âm)' : ', không âm'}.`);
  return Number(text);
}
function operand(text: string, denominator: string, mode: CalculatorMode, label: string): Rational {
  if (mode === 'fraction') {
    const n = whole(text, `Tử số ${label}`, true);
    const d = whole(denominator, `Mẫu số ${label}`);
    if (!d) throw new Error(`Mẫu số ${label} phải khác 0.`);
    return { n, d };
  }
  const value = text.trim().replace(',', '.');
  if (!/^-?\d{1,6}(?:\.\d{1,4})?$/.test(value))
    throw new Error(`${label}: nhập tối đa 6 chữ số trước dấu phẩy và 4 chữ số sau dấu phẩy.`);
  const digits = value.split('.')[1]?.length || 0;
  return reduce(Number(value.replace('.', '')), 10 ** digits);
}
const fraction = ({ n, d }: Rational) => d === 1 ? String(n) : `${n}/${d}`;

function columnSteps(left: number, right: number, operator: '+' | '−'): string[] {
  const negative = operator === '−' && left < right;
  const a = String(negative ? right : left).split('').reverse();
  const b = String(negative ? left : right).split('').reverse();
  const steps = negative ? ['Số thứ nhất nhỏ hơn số thứ hai. Tính phần chênh lệch bằng số lớn trừ số nhỏ, rồi đặt dấu âm trước kết quả.'] : [];
  const places = ['đơn vị', 'chục', 'trăm', 'nghìn', 'chục nghìn', 'trăm nghìn'];
  let carried = 0;
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = Number(a[i] || 0), y = Number(b[i] || 0);
    if (operator === '+') {
      const sum = x + y + carried;
      steps.push(`Hàng ${places[i]}: ${x} + ${y}${carried ? ' + 1 (nhớ)' : ''} = ${sum}. Viết ${sum % 10}${sum >= 10 ? ', nhớ 1 sang hàng tiếp theo' : ', không nhớ'}.`);
      carried = Math.floor(sum / 10);
    } else {
      const available = x - carried, borrow = available < y;
      const difference = available + (borrow ? 10 : 0) - y;
      steps.push(`Hàng ${places[i]}: ${x}${carried ? ' − 1 (đã cho mượn)' : ''}${borrow ? ' + 10 (mượn từ hàng bên trái)' : ''} − ${y} = ${difference}. Viết ${difference}.`);
      carried = borrow ? 1 : 0;
    }
  }
  if (operator === '+' && carried) steps.push('Còn nhớ 1 sau hàng cuối: viết thêm 1 ở bên trái.');
  return steps;
}

/** Exact decimal long division; repeating decimals remain a fraction, never a rounded answer. */
function numberText(value: Rational): string {
  let denominator = value.d;
  for (const factor of [2, 5]) while (denominator % factor === 0) denominator /= factor;
  if (denominator !== 1) return fraction(value);
  const absolute = BigInt(Math.abs(value.n)), divisor = BigInt(value.d);
  let remainder = absolute % divisor;
  let text = `${value.n < 0 ? '−' : ''}${absolute / divisor}`;
  if (remainder) text += ',';
  while (remainder) {
    remainder *= BigInt(10);
    text += String(remainder / divisor);
    remainder %= divisor;
  }
  return text;
}

export function calculate(input: CalculatorInput): Calculation {
  if (!['basic', 'fraction', 'remainder'].includes(input.mode) || !['+', '−', '×', '÷'].includes(input.operator))
    throw new Error('Em chọn một kiểu tính và phép tính nhé.');
  if (input.mode === 'remainder') {
    const dividend = whole(input.left, 'Số bị chia');
    const divisor = whole(input.right, 'Số chia');
    if (!divisor) throw new Error('Không thể chia cho 0. Em sửa số chia nhé.');
    const quotient = Math.floor(dividend / divisor), remainder = dividend % divisor;
    const steps: string[] = [];
    let partial = 0, started = false;
    const digits = String(dividend);
    for (let i = 0; i < digits.length; i++) {
      const digit = digits[i];
      partial = partial * 10 + Number(digit);
      if (!started && partial < divisor) continue;
      started = true;
      const q = Math.floor(partial / divisor), r = partial % divisor;
      steps.push(`Lấy ${partial} chia ${divisor}: viết ${q} vào thương. Nhân ${q} × ${divisor} = ${q * divisor}; trừ ${partial} − ${q * divisor} = ${r}.`
        + (i < digits.length - 1 ? ` Hạ chữ số ${digits[i + 1]} tiếp theo xuống, được ${r * 10 + Number(digits[i + 1])} để chia tiếp.` : ' Đã hạ hết các chữ số; đây là số dư cuối.'));
      partial = r;
    }
    if (!started) steps.push(`${dividend} nhỏ hơn ${divisor}, nên thương là 0 và số dư là ${dividend}.`);
    steps.push(`Kiểm tra: ${divisor} × ${quotient} + ${remainder} = ${dividend}. Số dư ${remainder} nhỏ hơn số chia ${divisor}.`);
    return { expression: `${dividend} ÷ ${divisor}`, result: `Thương ${quotient}, dư ${remainder}`, steps };
  }
  const a = operand(input.left, input.leftDenominator, input.mode, 'thứ nhất');
  const b = operand(input.right, input.rightDenominator, input.mode, 'thứ hai');
  if (input.operator === '÷' && b.n === 0) throw new Error('Không thể chia cho 0. Em sửa số thứ hai nhé.');
  const aText = input.mode === 'fraction' ? fraction(a) : numberText(a);
  const bText = input.mode === 'fraction' ? fraction(b) : numberText(b);
  const expression = `${a.n < 0 ? `(${aText})` : aText} ${input.operator} ${b.n < 0 ? `(${bText})` : bText}`;
  let n: number, d: number;
  const steps: string[] = [];
  switch (input.operator) {
    case '+': case '−': {
      d = a.d / gcd(a.d, b.d) * b.d;
      const left = a.n * (d / a.d), right = b.n * (d / b.d);
      n = input.operator === '+' ? left + right : left - right;
      if (input.mode === 'fraction' || a.d !== 1 || b.d !== 1) {
        steps.push(`Đưa hai số về cùng mẫu số ${d}: ${fraction(a)} = ${left}/${d}; ${fraction(b)} = ${right}/${d}.`);
        steps.push(`Giữ mẫu số ${d}, ${input.operator === '+' ? 'cộng' : 'trừ'} hai tử số: ${left} ${input.operator} ${right} = ${n}. Ta được ${n}/${d}.`);
      } else {
        if (a.n >= 0 && b.n >= 0) steps.push(...columnSteps(a.n, b.n, input.operator));
        else steps.push('Với số âm, em chú ý dấu của từng số. Cộng hai số trái dấu: lấy giá trị lớn trừ giá trị nhỏ và giữ dấu của số có giá trị lớn hơn. Trừ một số là cộng với số đổi dấu của nó.');
        steps.push(`${aText} ${input.operator} ${bText} = ${n}. Kiểm tra bằng phép tính ngược: ${n} ${input.operator === '+' ? '−' : '+'} ${bText} = ${aText}.`);
      }
      break;
    }
    case '×':
      n = a.n * b.n; d = a.d * b.d;
      steps.push(a.d === 1 && b.d === 1 ? `Nhân ${aText} với ${bText}. ${a.n >= 0 && b.n >= 0 ? `Đây là tổng của ${bText} nhóm, mỗi nhóm có ${aText}.` : 'Hai số khác dấu cho tích âm; cùng dấu cho tích không âm.'}`
        : `Nhân tử với tử: ${a.n} × ${b.n} = ${n}. Nhân mẫu với mẫu: ${a.d} × ${b.d} = ${d}. Ta được ${n}/${d}.`);
      break;
    case '÷':
      n = a.n * b.d; d = a.d * b.n;
      if (input.mode === 'basic' && a.d === 1 && b.d === 1 && a.n >= 0 && b.n > 0) {
        steps.push(...calculate({ ...input, mode: 'remainder', left: String(a.n), right: String(b.n) }).steps);
        if (a.n % b.n) steps.push(`Phần còn dư là ${a.n % b.n}. Khi chia tiếp phần dư, ta được ${(a.n % b.n)}/${b.n}; ghép với phần nguyên ${Math.floor(a.n / b.n)} để được kết quả đầy đủ.`);
      } else {
        steps.push(`Chia cho ${fraction(b)} là nhân với số đảo ngược ${b.d}/${b.n}. Tính ${fraction(a)} × ${b.d}/${b.n}.`);
        steps.push(`Nhân tử với tử: ${a.n} × ${b.d} = ${n}; mẫu với mẫu: ${a.d} × ${b.n} = ${d}.`);
      }
      break;
  }
  const value = reduce(n, d);
  const factor = gcd(n, d);
  if (factor > 1 && d !== 1) steps.push(`Rút gọn: chia cả tử và mẫu cho ${factor}, được ${fraction(value)}.`);
  const result = input.mode === 'fraction' ? fraction(value) : numberText(value);
  steps.push(`${expression} = ${result}.`);
  return { expression, result, steps };
}

/** Bounded, complete expression parser. No eval and no rounded intermediate values. */
export function calculateExpression(source: string): Calculation & { remainder?: Calculation } {
  const normalized = source.replace(/\s/g, '').replace(/−/g, '-').replace(/×/g, '*').replace(/:/g, '÷').replace(/,/g, '.');
  const tokens = normalized.match(/\d+(?:\.\d+)?|[+\-*/÷()%]/g) || [];
  if (!normalized || normalized.length > 120 || tokens.length > 60 || tokens.join('') !== normalized)
    throw new Error('Em nhập phép tính bằng các số và dấu trên bàn phím nhé.');
  let position = 0;
  const steps: string[] = [];
  const apply = (a: Rational, b: Rational, op: Operator): Rational => {
    if (op === '÷' && !b.n) throw new Error('Không thể chia cho 0. Em sửa số chia nhé.');
    let n: number, d: number;
    if (op === '+' || op === '−') {
      d = a.d / gcd(a.d, b.d) * b.d;
      const left = a.n * (d / a.d), right = b.n * (d / b.d);
      if (![left, right].every(Number.isSafeInteger)) throw new Error('Số quá lớn để tính chính xác. Em dùng số nhỏ hơn nhé.');
      n = left + (op === '+' ? 1 : -1) * right;
    } else {
      n = a.n * (op === '×' ? b.n : b.d);
      d = a.d * (op === '×' ? b.d : b.n);
    }
    const value = reduce(n, d);
    if ([a.n, a.d, b.n, b.d].every(part => Math.abs(part) <= 999999)) {
      const explained = calculate({ mode: a.d === 1 && b.d === 1 ? 'basic' : 'fraction', operator: op,
        left: String(a.n), right: String(b.n), leftDenominator: String(a.d), rightDenominator: String(b.d) });
      steps.push(...explained.steps);
    } else {
      steps.push(`Tính ${fraction(a)} ${op} ${fraction(b)} = ${fraction(value)}. Giữ kết quả chính xác để tính tiếp.`);
    }
    return value;
  };
  const primary = (): Rational => {
    const token = tokens[position++];
    let value: Rational;
    if (token === '-' || token === '+') {
      const next = primary(); value = { n: token === '-' ? -next.n : next.n, d: next.d };
    } else if (token === '(') {
      value = sum();
      if (tokens[position++] !== ')') throw new Error('Em thêm dấu đóng ngoặc nhé.');
    } else if (token && /^\d/.test(token)) {
      value = operand(token, '', 'basic', 'Số');
      // A slash entered with the fraction key keeps numerator/denominator together.
      if (tokens[position] === '/' && /^\d+$/.test(tokens[position + 1] || '') && value.d === 1) {
        position++;
        const denominator = whole(tokens[position++], 'Mẫu số');
        if (!denominator) throw new Error('Không thể chia cho 0. Mẫu số phải khác 0.');
        value = reduce(value.n, denominator);
      }
    } else throw new Error('Phép tính chưa đủ. Em nhập số tiếp theo nhé.');
    while (tokens[position] === '%') {
      position++;
      const before = value;
      value = reduce(value.n, value.d * 100);
      steps.push(`${fraction(before)}% nghĩa là ${fraction(before)} chia cho 100, bằng ${fraction(value)}.`);
    }
    return value;
  };
  const product = (): Rational => {
    let value = primary();
    while (tokens[position] === '*' || tokens[position] === '/' || tokens[position] === '÷') {
      const op = tokens[position++] === '*' ? '×' : '÷';
      value = apply(value, primary(), op);
    }
    return value;
  };
  const sum = (): Rational => {
    let value = product();
    while (tokens[position] === '+' || tokens[position] === '-') {
      const op = tokens[position++] === '+' ? '+' : '−';
      value = apply(value, product(), op);
    }
    return value;
  };
  const value = sum();
  if (position !== tokens.length) throw new Error('Em kiểm tra dấu ngoặc và các dấu phép tính nhé.');
  const expression = source.trim();
  const result = source.includes('/') ? fraction(value) : numberText(value);
  if (steps.length > 1) steps.unshift('Tính trong ngoặc trước; tiếp theo nhân, chia; cuối cùng cộng, trừ từ trái sang phải.');
  steps.push(`${expression} = ${result}.`);
  const division = normalized.match(/^(\d{1,6})[\/÷](\d{1,6})$/);
  const remainder = division ? calculate({ mode: 'remainder', operator: '÷', left: division[1], right: division[2], leftDenominator: '', rightDenominator: '' }) : undefined;
  return { expression, result, steps, remainder };
}
