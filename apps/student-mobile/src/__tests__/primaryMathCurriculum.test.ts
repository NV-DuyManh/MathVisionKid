import { getCurriculumProblem, getProblemsByGrade, PRIMARY_MATH_CURRICULUM } from '../data/primaryMathCurriculum';

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
