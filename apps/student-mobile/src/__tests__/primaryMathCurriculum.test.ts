import { getCurriculumProblem, getProblemsByGrade, PRIMARY_MATH_CURRICULUM } from '../data/primaryMathCurriculum';
import { getPrimaryChapters } from '../data/primaryMathLessons';
import { lessonSupplements } from '../data/primaryMathLessonSupplements';

it('provides twenty authored exercises per grade in multiple program sections', () => {
  expect(PRIMARY_MATH_CURRICULUM).toHaveLength(100);
  for (const grade of [1, 2, 3, 4, 5] as const) {
    const problems = getProblemsByGrade(grade);
    expect(problems).toHaveLength(20);
    expect(new Set(problems.map(problem => problem.section)).size).toBeGreaterThanOrEqual(3);
    expect(problems.every(problem => problem.bookSeries === 'Bài luyện tập')).toBe(true);
  }
});

it('recognizes the entire prepared source and rejects a changed quantity', () => {
  const problem = getProblemsByGrade(1)[0];
  expect(getCurriculumProblem(`  ${problem.problemText.replace(/ /g, '  ')} `)).toBe(problem);
  expect(getCurriculumProblem(problem.problemText.replace('15', '16'))).toBeUndefined();
  expect(getProblemsByGrade(3)[1].title).toBe('Số vở trong hai thùng');
  expect(getProblemsByGrade(4)[1].topic).toBe('Ôn tập phép cộng');
});

it('keeps the original exercises and gives all 120 lessons two examples and five distinct exercises', () => {
  const ids: string[] = [];
  const lessonIds: string[] = [];
  const countPerGrade = { 1: 15, 2: 16, 3: 39, 4: 22, 5: 28 };
  for (const grade of [1, 2, 3, 4, 5] as const) {
    const chapters = getPrimaryChapters(grade);
    const lessons = chapters.flatMap(chapter => chapter.lessons);
    expect(lessons).toHaveLength(countPerGrade[grade]);
    for (const chapter of chapters) {
      expect(chapter.lessons.length).toBeGreaterThan(0);
      ids.push(chapter.id, ...chapter.lessons.map(lesson => lesson.id));
    }
    for (const lesson of lessons) {
      lessonIds.push(lesson.id);
      expect(lesson.examples).toHaveLength(2);
      const questions = [...lesson.examples, ...lesson.selfPractice];
      for (const [question, answer] of questions) {
        expect(question.trim()).not.toBe('');
        expect(answer.trim()).not.toBe('');
      }
      expect(lesson.practice.length + lesson.selfPractice.length).toBe(5);
      const prompts = [...questions.map(([question]) => question), ...lesson.practice.map(exercise => exercise.problemText)];
      expect(new Set(prompts.map(prompt => prompt.normalize('NFC').trim())).size).toBe(7);
    }
    const exercises = lessons.flatMap(lesson => lesson.practice);
    expect(exercises.map(exercise => exercise.id).sort()).toEqual(getProblemsByGrade(grade).map(exercise => exercise.id).sort());
  }
  expect(new Set(ids).size).toBe(ids.length);
  expect(lessonIds.sort()).toEqual(Object.keys(lessonSupplements).sort());
});
