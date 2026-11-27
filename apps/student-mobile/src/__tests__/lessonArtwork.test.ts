import { PRIMARY_MATH_CURRICULUM } from '../data/primaryMathCurriculum';
import { getPrimaryChapters } from '../data/primaryMathLessons';
import { getLessonArtwork, LESSON_ARTWORK_INVENTORY } from '../features/lesson-artwork/lessonArtwork';
import { PRIMARY_CATALOG_ARTWORK } from '../features/primary-lessons/primaryCatalogArtwork';

it('covers every chapter and lesson across the five grades with catalog artwork', () => {
  const grades = [1, 2, 3, 4, 5] as const;
  const ids = grades.flatMap(grade => getPrimaryChapters(grade).flatMap(
    chapter => [chapter.id, ...chapter.lessons.map(lesson => lesson.id)],
  ));
  expect(Object.keys(PRIMARY_CATALOG_ARTWORK).sort()).toEqual(ids.sort());
  expect(Object.values(PRIMARY_CATALOG_ARTWORK).every(source => source !== undefined)).toBe(true);
});

it('covers every actual curriculum ID with a distinct reviewed topic illustration', () => {
  const entries = Object.entries(LESSON_ARTWORK_INVENTORY);
  expect(entries.map(([id]) => id).sort()).toEqual(PRIMARY_MATH_CURRICULUM.map(problem => problem.id).sort());
  expect(new Set(entries.map(([, art]) => art.assetPath)).size).toBe(100);
  for (const [id, art] of entries) {
    expect(art.status).toBe('GENERATED_REVIEWED');
    expect(art.generatedSource).toMatch(/\.png$/);
    expect(getLessonArtwork(id).description).toBe(art.description);
    expect(getLessonArtwork(id).source).toBeDefined();
  }
  expect(getLessonArtwork('unknown-lesson').description).toBe('Quyển vở và bút học toán');
});
