import { calculateExpression, type Calculation } from './calculate';

// Integer scales avoid floating-point rounding, including squared/cubed units.
export const UNIT_GROUPS = {
  length: { label: 'Độ dài', units: [['km', 1000000], ['hm', 100000], ['dam', 10000], ['m', 1000], ['dm', 100], ['cm', 10], ['mm', 1]] },
  area: { label: 'Diện tích', units: [['km²', 1000000000000], ['ha', 10000000000], ['hm²', 10000000000], ['a', 100000000], ['dam²', 100000000], ['m²', 1000000], ['dm²', 10000], ['cm²', 100], ['mm²', 1]] },
  mass: { label: 'Khối lượng', units: [['tấn', 1000000000], ['tạ', 100000000], ['yến', 10000000], ['kg', 1000000], ['hg', 100000], ['dag', 10000], ['g', 1000], ['mg', 1]] },
  volume: { label: 'Thể tích', units: [['m³', 1000000000], ['dm³', 1000000], ['cm³', 1000], ['mm³', 1], ['l', 1000000], ['ml', 1000]] },
} as const;
export type UnitGroup = keyof typeof UNIT_GROUPS;
export type Measurement = { value: string; unit: string };

function gcd(a: bigint, b: bigint): bigint {
  while (b) [a, b] = [b, a % b];
  return a < BigInt(0) ? -a : a;
}

/** Exact finite decimal, or a reduced fraction when the decimal would repeat. */
function format(n: bigint, d: bigint): string {
  const factor = gcd(n, d);
  n /= factor; d /= factor;
  let remaining = d;
  for (const prime of [BigInt(2), BigInt(5)]) while (remaining % prime === BigInt(0)) remaining /= prime;
  if (remaining !== BigInt(1)) return `${n}/${d}`;
  const sign = n < BigInt(0) ? '−' : '';
  if (n < BigInt(0)) n = -n;
  let result = `${sign}${n / d}`, rest = n % d;
  if (rest) result += ',';
  while (rest) { rest *= BigInt(10); result += rest / d; rest %= d; }
  return result;
}

export function convertUnits(group: UnitGroup, measurements: Measurement[], target: string): Calculation {
  const units: readonly (readonly [string, number])[] = UNIT_GROUPS[group]?.units || [];
  const targetScale = units.find(([unit]) => unit === target)?.[1];
  if (!targetScale || measurements.length < 1 || measurements.length > 2)
    throw new Error('Em chọn các đơn vị cùng loại và nhập một hoặc hai số đo nhé.');
  let totalN = BigInt(0), totalD = BigInt(1);
  const steps: string[] = [], terms: string[] = [];
  for (const { value, unit } of measurements) {
    const scale = units.find(([symbol]) => symbol === unit)?.[1];
    if (!scale) throw new Error('Các số đo phải có cùng loại đơn vị.');
    const source = value.trim();
    if (!/^(?:\d{1,6}(?:[,.]\d{1,4})?|\d{1,6}\s*\/\s*\d{1,6}|\d{1,6}\s+\d{1,6}\s*\/\s*\d{1,6})$/.test(source))
      throw new Error('Em nhập số đo không âm, có thể là số thập phân, phân số hoặc hỗn số như 2 1/4.');
    const calculated = calculateExpression(source);
    steps.push(...calculated.steps.filter(step => step.startsWith('Đổi hỗn số')));
    const canonical = calculated.result.replace(',', '.');
    const [top, bottom] = canonical.includes('/') ? canonical.split('/') : [canonical.replace('.', ''), String(10 ** (canonical.split('.')[1]?.length || 0))];
    const n = BigInt(top) * BigInt(scale), d = BigInt(bottom) * BigInt(targetScale);
    const common = gcd(totalD, d);
    totalN = totalN * (d / common) + n * (totalD / common);
    totalD *= d / common;
    const factor = gcd(totalN, totalD);
    totalN /= factor; totalD /= factor;
    const ratio = scale >= targetScale ? format(BigInt(scale), BigInt(targetScale)) : format(BigInt(targetScale), BigInt(scale));
    const operation = scale >= targetScale ? '×' : '÷';
    steps.push(`${source} ${unit} = ${calculated.result} ${operation} ${ratio} = ${format(n, d)} ${target}.`);
    terms.push(`${source} ${unit}`);
  }
  const result = `${format(totalN, totalD)} ${target}`;
  if (measurements.length === 2) steps.push(`Cộng hai số đo sau khi đổi: ${terms.join(' + ')} = ${result}.`);
  return { expression: terms.join(' + '), result, steps };
}
