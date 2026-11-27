import { getPrimaryMathExample } from '../data/primaryMathExampleSteps';
import { getPrimaryChapters } from '../data/primaryMathLessons';

it('ships prepared steps for both examples of every primary lesson', () => {
  const grades = [1, 2, 3, 4, 5] as const;
  const lessons = grades.flatMap(grade => getPrimaryChapters(grade).flatMap(chapter => chapter.lessons));
  expect(lessons).toHaveLength(120);
  const openingQuestions = new Set<string>();
  for (const lesson of lessons) {
    for (const [index, level] of (['easy', 'advanced'] as const).entries()) {
      const example = getPrimaryMathExample(lesson.id, level);
      expect(example).toBeDefined();
      if (!example) throw new Error(`Missing ${lesson.id}/${level}`);
      expect([example.problem, example.solution]).toEqual(lesson.examples[index]);
      expect(example.steps).toHaveLength(2);
      openingQuestions.add(example.steps[0].question);
      for (const step of example.steps) {
        expect(step.correct).toBeTruthy();
        expect(step.hint).toBeTruthy();
        expect(new Set(step.choices).size).toBe(2);
        expect(step.choices).toContain(step.correct);
      }
    }
  }
  expect(openingQuestions.size).toBeGreaterThan(220);
});

it('rejects unsupported route values without using free-form problem text', () => {
  expect(getPrimaryMathExample('grade-5-review-natural', 'other')).toBeUndefined();
  expect(getPrimaryMathExample('grade-5-missing', 'easy')).toBeUndefined();
  expect(getPrimaryMathExample(['grade-5-review-natural'], 'easy')).toBeUndefined();
});
