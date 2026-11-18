export type SourceFraction = { numerator: number; denominator: number };

export type HintVisual =
  | { kind: 'fractions'; values: SourceFraction[]; commonDenominator?: number }
  | { kind: 'array'; rows: number; columns: number }
  | { kind: 'sharing'; amount: number; groups: number; allowsRemainder?: true }
  | { kind: 'relation'; initial: number; change: number; mode: 'add' | 'remove' };

const fraction = String.raw`(\d{1,2})\s*\/\s*([1-9]\d?)`;
const groupKinds = 'nhom|hop|tui|gio|hang|dia|ban|nguoi';
const numberPair = /^([1-9]\d?)\s*([+−\-×*÷:/])\s*([1-9]\d?)$/u;

export function fractionsInProblem(text: string): SourceFraction[] {
  const found: SourceFraction[] = [];
  const pattern = /(?<![\p{L}\p{N}_/.,+\-−])(\d+)\s*\/\s*(\d+)(?![\p{L}\p{N}_/]|[.,]\d)/gu;
  for (const match of text.matchAll(pattern)) {
    const before = text.slice(0, match.index).trimEnd();
    const after = text.slice(match.index + match[0].length).trimStart();
    if (/[+\-−/]$/u.test(before) || after.startsWith('/') || /(?:ngày|date|dated)\s*[:=]?$/iu.test(before)) continue;
    const value = { numerator: Number(match[1]), denominator: Number(match[2]) };
    if (!Number.isSafeInteger(value.numerator) || !Number.isSafeInteger(value.denominator) || value.denominator === 0) continue;
    if (!found.some(item => item.numerator === value.numerator && item.denominator === value.denominator)) found.push(value);
    if (found.length === 2) break;
  }
  return found;
}

function fractionVisual(source: string, expression: string): HintVisual | null {
  const pair = new RegExp(`^${fraction}\\s*[+−-]\\s*${fraction}$`, 'u').exec(expression)
    ?? new RegExp(`^1\\s*[−-]\\s*\\(\\s*${fraction}\\s*\\+\\s*${fraction}\\s*\\)$`, 'u').exec(expression);
  const single = new RegExp(`^(?:1\\s*[−-]\\s*)?${fraction}$`, 'u').exec(expression);
  const operands = pair ?? single;
  if (!operands) return null;
  const values = [{ numerator: Number(operands[1]), denominator: Number(operands[2]) }];
  if (pair) values.push({ numerator: Number(pair[3]), denominator: Number(pair[4]) });
  const given = exactExpression(fold(source.trim()), expression)
    ? values.filter((item, index) => values.findIndex(value =>
      value.numerator === item.numerator && value.denominator === item.denominator) === index)
    : fractionsInProblem(source);
  if (values.some(value => value.denominator > 20 || value.numerator > value.denominator * 3 ||
    !given.some(item => item.numerator === value.numerator && item.denominator === value.denominator))) return null;

  let commonDenominator: number | undefined;
  if (pair && values.every(value => value.numerator > 0 && value.numerator <= value.denominator) &&
    values[0].denominator !== values[1].denominator) {
    const [first, second] = values.map(value => value.denominator);
    for (let multiple = first; multiple <= 24; multiple += first) {
      if (multiple % second === 0) { commonDenominator = multiple; break; }
    }
  }
  return { kind: 'fractions', values: given.filter(item =>
    values.some(value => value.numerator === item.numerator && value.denominator === item.denominator)), commonDenominator };
}

function fold(text: string) {
  return text.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '').replace(/đ/g, 'd');
}

function exactExpression(source: string, expression: string) {
  const canonical = (value: string) => value.replace(/\s/g, '').replace(/×/g, '*').replace(/[:÷]/g, ':').replace(/−/g, '-');
  return canonical(source.replace(/^tinh\s*:?\s*/u, '').replace(/\s*(?:=\s*\?|\?|[.])$/u, '')) === canonical(expression);
}

/** The caller supplies only the active, already revealed expression from a confirmed lesson. */
export function buildHintVisual(problem: string, expression: string): HintVisual | null {
  if (!problem.trim() || /\[\?\]|\uFFFD/u.test(problem) || !expression.trim() || expression.length > 90 || problem.length > 4000) return null;
  const clean = expression.trim();
  const fractional = fractionVisual(problem, clean);
  if (fractional) return fractional;
  const operands = numberPair.exec(clean);
  if (!operands) return null;
  const [, a, operator, b] = operands;
  const left = Number(a), right = Number(b);
  const source = fold(problem.trim()).replace(/\s+/g, ' ');
  // The tutor's canonical integer division can use a slash. A slash alone
  // never establishes sharing: the confirmed source must specify division.
  const exact = exactExpression(source, operator === '/' ? `${a} ÷ ${b}` : clean);
  const noun = String.raw`([a-z]+(?: [a-z]+){0,2})`;
  const wholeNumber = String.raw`(?<![\w/.,+\-])`;
  const groups = (count: string, each: string) =>
    new RegExp(`${wholeNumber}${count} (${groupKinds})\\b[^.?!\\d]{0,48}(?:[.!,] )?moi \\1 (?:co|chua) ${each}\\b(?![.,/]\\d)`, 'u').test(source);

  if ('×*'.includes(operator) && left <= 6 && right <= 6) {
    if (exact || groups(a, b)) return { kind: 'array', rows: left, columns: right };
    if (groups(b, a)) return { kind: 'array', rows: right, columns: left };
  }
  if ('÷:/'.includes(operator) && left <= 30 && right >= 2 && right <= 6) {
    const fairShare = new RegExp(`\\b(?:chia deu ${a} ${noun}|${wholeNumber}${a} ${noun}(?:[,.])? chia deu) (?:cho|vao|thanh) ${b} (?:${groupKinds})\\b`, 'u');
    const sharesFromSource = fairShare.test(source);
    if (left % right === 0 && (exact || sharesFromSource)) return { kind: 'sharing', amount: left, groups: right };
    if (left % right !== 0 && sharesFromSource && /(?:con du|du lai|du bao nhieu|bao nhieu .* du)\b/u.test(source)) {
      return { kind: 'sharing', amount: left, groups: right, allowsRemainder: true };
    }
  }
  if ('+−-'.includes(operator) && left <= 30 && right <= 30) {
    const mode = operator === '+' ? 'add' : 'remove';
    const verb = mode === 'add' ? '(?:them|nhan them|mua them|cho them)' : '(?:cho di|bot|lay ra|ban di)';
    const relation = new RegExp(`\\bco ${a} ${noun}[,.] (?:[a-z]+ ){0,3}${verb} ${b} \\1\\b(?![.,/]\\d)`, 'u');
    if (relation.test(source) && (mode === 'add' || right <= left)) return { kind: 'relation', initial: left, change: right, mode };
  }
  return null;
}
