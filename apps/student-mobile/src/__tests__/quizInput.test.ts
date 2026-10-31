import { quizTime, submissionId, validQuizAnswer } from '../features/quiz/quizInput';

it('accepts final numbers and exact fractions with only permitted units', () => {
  for (const value of ['48', '48 quyển', '48 quyển sách', '48,00', '96/2', '96 / 2']) expect(validQuizAnswer(value, 'quyển sách')).toBe(true);
  for (const value of ['', '1/0', '1/000', '48 người', '48+0', '1e9', '<script>', '1/2/3']) expect(validQuizAnswer(value, 'quyển sách')).toBe(false);
  expect(validQuizAnswer('3/4', '')).toBe(true);
});
it('creates distinct retry identifiers without sending time or reward authority', () => {
  const values = Array.from({ length: 100 }, submissionId);
  expect(new Set(values).size).toBe(100);
  values.forEach(value => expect(value).toMatch(/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/));
});
it('shows elapsed time without resetting at an hour', () => {
  expect(quizTime(30000)).toBe('0:30'); expect(quizTime(60001)).toBe('1:00'); expect(quizTime(3600000)).toBe('60:00');
});
