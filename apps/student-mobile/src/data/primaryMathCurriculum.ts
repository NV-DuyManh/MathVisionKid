import exercises from './primaryMathCurriculumData.json';

/** Public projection of the server-owned authored curriculum. Regenerate with
 * ai/runtime/scripts/export_primary_math_curriculum.py after editing its source. */
export interface CurriculumProblem {
  id: string;
  grade: 1 | 2 | 3 | 4 | 5;
  section: string;
  order: number;
  week: number | null;
  source: { kind: string; reference: string; topic: string };
  bookSeries: string;
  topic: string;
  title: string;
  problemText: string;
  guidance: string;
  sampleSolution: { lines: string[]; finalAnswer: string };
  difficulty: 'Dễ' | 'Trung bình' | 'Thử thách';
}

export const PRIMARY_MATH_CURRICULUM = exercises as CurriculumProblem[];

export function getProblemsByGrade(grade: 1 | 2 | 3 | 4 | 5): CurriculumProblem[] {
  return PRIMARY_MATH_CURRICULUM.filter(problem => problem.grade === grade);
}

export function getCurriculumProblem(problemText: string): CurriculumProblem | undefined {
  const source = problemText.normalize('NFC').trim().replace(/\s+/g, ' ');
  return PRIMARY_MATH_CURRICULUM.find(problem => problem.problemText.normalize('NFC').trim().replace(/\s+/g, ' ') === source);
}
