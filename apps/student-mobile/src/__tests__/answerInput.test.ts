import { convertAnswerInput } from '../features/tutoring/answerInput';

it.each([
  ['2', true, '2/1'], ['0,125', true, '1/8'], ['-1.25', true, '-5/4'], ['0', true, '0/1'],
  ['1/8', false, '0,125'], ['-5/4', false, '-1,25'], ['6/3', false, '2'], ['0/7', false, '0'],
  ['1/3', false, null], ['1/', false, null], ['1/0', false, null], ['0,', true, null],
  ['999999999999,12345678', true, null], ['1/3', true, null], ['abc', false, null],
])('converts %s to fraction=%s as %s without rounding', (value, mode, expected) => {
  expect(convertAnswerInput(value as string, mode as boolean)).toBe(expected);
});
