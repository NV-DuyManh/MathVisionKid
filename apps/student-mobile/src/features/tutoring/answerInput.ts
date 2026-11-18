function greatestCommonDivisor(left: bigint, right: bigint): bigint {
  while (right !== 0n) [left, right] = [right, left % right];
  return left < 0n ? -left : left;
}

/** Convert only complete values that fit the input fields, with no rounded decimal. */
export function convertAnswerInput(value: string, toFraction: boolean): string | null {
  const text = value.trim();
  if (toFraction) {
    if (!/^-?\d{1,12}(?:[.,]\d{1,8})?$/.test(text)) return null;
    const places = text.split(/[.,]/)[1]?.length || 0;
    const numerator = BigInt(text.replace(/[.,]/, ''));
    const denominator = 10n ** BigInt(places);
    const divisor = greatestCommonDivisor(numerator, denominator);
    const result = `${numerator / divisor}/${denominator / divisor}`;
    return /^-?\d{1,12}\/[1-9]\d{0,11}$/.test(result) ? result : null;
  }
  const fraction = /^(-?\d{1,12})\/([1-9]\d{0,11})$/.exec(text);
  if (!fraction) return null;
  const numerator = BigInt(fraction[1]), denominator = BigInt(fraction[2]);
  const divisor = greatestCommonDivisor(numerator, denominator);
  let remainingDenominator = denominator / divisor;
  for (const factor of [2n, 5n]) {
    while (remainingDenominator % factor === 0n) remainingDenominator /= factor;
  }
  if (remainingDenominator !== 1n) return null;
  const absolute = numerator < 0n ? -numerator : numerator;
  let remainder = absolute % denominator;
  let result = `${numerator < 0n ? '-' : ''}${absolute / denominator}`;
  if (remainder) result += ',';
  while (remainder) {
    remainder *= 10n;
    result += remainder / denominator;
    remainder %= denominator;
  }
  return result.length <= 30 ? result : null;
}
