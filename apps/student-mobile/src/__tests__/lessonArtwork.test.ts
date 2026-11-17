import { PRIMARY_MATH_CURRICULUM } from '../data/primaryMathCurriculum';
import { getLessonArtwork, LESSON_ARTWORK_INVENTORY } from '../features/lesson-artwork/lessonArtwork';

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
