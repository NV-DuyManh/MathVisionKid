import answerKeys from '../../data/primaryMathPracticeAnswers.json';
import { sameStoredAnswer } from '../tutoring/learningProgress';

export const PRIMARY_PRACTICE_ANSWERS: Readonly<Partial<Record<string, readonly string[]>>> = answerKeys;

function normalize(text: string): string {
  return text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').replace(/đ/g, 'd')
    .replace(/[−–]/g, '-').trim().replace(/[.!?]+$/, '')
    .replace(/\s*;\s*|,\s+|\s+va\s+/g, ';')
    .replace(/\s*([=<>+/])\s*/g, '$1').replace(/\s+/g, ' ');
}

const unitNames: Readonly<Partial<Record<string, string>>> = {
  'met': 'm', 'met vuong': 'm2', 'met khoi': 'm3',
  'xang-ti-met': 'cm', 'xang-ti-met vuong': 'cm2', 'xang-ti-met khoi': 'cm3',
  'de-xi-met': 'dm', 'de-xi-met vuong': 'dm2', 'de-xi-met khoi': 'dm3',
  'mi-li-met': 'mm', 'ki-lo-met': 'km', 'ki-lo-gam': 'kg',
  'lit': 'l', 'd': 'dong', 'phan tram': '%', 'do c': '°c',
};

function quantity(value: string, allowDecimalDot: boolean) {
  const parts = /^(-?\d(?:[\d., ]*\d)?(?:\/\d+)?)(?:\s*([a-z%°]+[23]?(?:[ /-]+[a-z°]+[23]?)*))?$/.exec(value);
  if (!parts) return;
  let number = parts[1];
  // In a Vietnamese integer, a period or space can group thousands.
  if (/^-?\d{1,3}(?: \d{3})+(?:,\d+)?$/.test(number)) number = number.replace(/ /g, '');
  if (/^-?\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(number) && (!allowDecimalDot || number.includes(',') || number.split('.').length > 2)) {
    number = number.replace(/\./g, '');
  }
  if (!/^-?\d+(?:[.,]\d+|\/[1-9]\d*)?$/.test(number)) return;
  const unit = parts[2] ?? '';
  return { number, unit: unitNames[unit] ?? unit };
}

export function checkPracticeAnswer(value: string, keys: string, question: string): boolean {
  const attempt = normalize(value);
  if (!attempt) return false;
  const prompt = normalize(question);
  return keys.split('|').some(key => {
    const expected = normalize(key);
    if (attempt === expected) return true;
    if (/^\d+(?:;\d+)+$/.test(expected) && attempt.replace(/,/g, ';') === expected) return true;
    const answer = quantity(expected, false);
    if (!answer) return false;
    const typed = quantity(attempt, answer.number.includes(','));
    if (!typed || (typed.unit && typed.unit !== answer.unit)) return false;
    if (answer.number.includes('/')) {
      if (/rut gon/.test(prompt)) return typed.number === answer.number;
      if (/(?:phan so|ti so)/.test(prompt) && !typed.number.includes('/')) return false;
    }
    return sameStoredAnswer(typed.number, answer.number);
  });
}

const naturalReviewHints = [
  'Hai tích có chung thừa số 35. Đặt 35 ra ngoài ngoặc rồi cộng hai số còn lại.',
  'Đặt tính sao cho các chữ số cùng hàng thẳng cột. Cộng từ hàng đơn vị và nhớ sang hàng tiếp theo khi cần.',
  'Đặt tính thẳng cột rồi trừ từ phải sang trái. Khi một hàng không đủ để trừ, đổi một đơn vị ở hàng bên trái.',
  'Tách 36 thành 30 + 6. Tính hai tích với 205 rồi cộng lại.',
  'Đặt tính chia. Chia từ trái sang phải rồi nhân thương với 27 để tự kiểm tra.',
] as const;

export function practiceHint(lessonId: string, index: number, explanation: string): string {
  return (lessonId === 'grade-5-review-natural' ? naturalReviewHints[index] : undefined) ?? explanation;
}
