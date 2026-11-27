import { getPrimaryChapters } from '../data/primaryMathLessons';
import { getPrimaryMathExample } from '../data/primaryMathExampleSteps';
import { checkPracticeAnswer, PRIMARY_PRACTICE_ANSWERS } from '../features/primary-lessons/practiceAnswer';

it('has a checkable answer for all 600 exercises', () => {
  let count = 0;
  for (const grade of [1, 2, 3, 4, 5] as const) {
    for (const lesson of getPrimaryChapters(grade).flatMap(chapter => chapter.lessons)) {
      const questions = [...lesson.practice.map(problem => problem.problemText), ...lesson.selfPractice.map(([question]) => question)];
      const keys = PRIMARY_PRACTICE_ANSWERS[lesson.id];
      expect(keys).toHaveLength(questions.length);
      if (!keys) throw new Error(`Missing answers for ${lesson.id}`);
      keys.forEach((key, index) => {
        expect(key.trim()).toBeTruthy();
        expect(checkPracticeAnswer('', key, questions[index])).toBe(false);
        expect(checkPracticeAnswer(key.split('|')[0], key, questions[index])).toBe(true);
        count += 1;
      });
    }
  }
  expect(count).toBe(600);
});

it.each([
  ['21 102', '21.102', '', true],
  ['21,102', '21.102', '', false],
  ['3.375', '3,375 dm³', '', true],
  ['3375', '3,375 dm³', '', false],
  ['20 cm3', '20 cm²', '', false],
  ['20 centimètres', '20 cm²', '', false],
  ['20 xăng-ti-mét vuông', '20 cm²', '', true],
  ['8/12', '2/3', 'Rút gọn 12/18.', false],
  ['0,4', '2/5', 'Viết tỉ số.', false],
  ['10 / 25', '2/5', 'Viết tỉ số.', true],
  ['1/0', '2/5', 'Viết tỉ số.', false],
  ['2', '2 giờ 30 phút|2h30|2:30', '', false],
  ['2:30', '2 giờ 30 phút|2h30|2:30', '', true],
  ['7.500.2', '7.500', '', false],
  ['9,10', '9, 10', '', true],
  ['10,9', '9, 10', '', false],
  ['Thu ba', 'thứ ba|thứ 3', '', true],
])('matches %s against %s using the question format', (value, key, question, expected) => {
  expect(checkPracticeAnswer(value, key, question)).toBe(expected);
});

it('uses each natural-number example’s factored expression after the first step', () => {
  const easy = getPrimaryMathExample('grade-5-review-natural', 'easy');
  const advanced = getPrimaryMathExample('grade-5-review-natural', 'advanced');
  expect(easy?.problem).toBe('Tính nhẩm 48 × 13 + 48 × 7.');
  expect(easy?.steps[1].question).toBe('Tính nhẩm 48 × (13 + 7).');
  expect(advanced?.steps[1].question).toBe('Tính nhanh 75 × (28 + 12) − 480 : 6.');
});
