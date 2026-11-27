import { test, expect, sites, login } from '../browser/fixtures.mjs';

const fixtures = [
  { grade: 1, chapters: 6, lessons: 15, lesson: 'Phép cộng và bảng cộng', query: 'phep cong va bang cong', foreign: 'grade-5-decimals-add' },
  { grade: 2, chapters: 6, lessons: 16, lesson: 'Cộng có nhớ', query: 'cong co nho', foreign: 'grade-5-decimals-add' },
  { grade: 3, chapters: 16, lessons: 39, lesson: 'Diện tích hình chữ nhật', query: 'dien tich hinh chu nhat', foreign: 'grade-5-decimals-add' },
  { grade: 4, chapters: 7, lessons: 22, lesson: 'Nhân và chia hai phân số', query: 'nhan va chia hai phan so', foreign: 'grade-3-area-rectangle' },
  { grade: 5, chapters: 8, lessons: 28, lesson: 'Cộng số thập phân', query: 'cong so thap phan', foreign: 'grade-3-area-rectangle' },
];

async function enterLessons(page, app, grade) {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  // /me still returns grade 5. The personal profile must win for every other grade.
  await expect.poll(() => Boolean(app.studentProfile)).toBe(true);
  app.studentProfile.gradeLevel = grade;
  await page.goto(`${sites.portal.origin}/study/lessons`);
}

for (const { grade, chapters, lessons, lesson, query, foreign } of fixtures) {
  test(`grade ${grade} shows its own illustrated curriculum from Của em`, async ({ page, app }) => {
    await enterLessons(page, app, grade);
    await expect(page.getByRole('heading', { name: `Toán lớp ${grade}`, exact: true })).toBeVisible();
    const chapterButtons = page.getByRole('button', { name: /^Chương \d+: / });
    const lessonButtons = page.getByRole('button', { name: /^Mở bài: / });
    await expect(chapterButtons).toHaveCount(chapters);
    await expect(page.getByRole('button', { name: /^Chọn Lớp / })).toHaveCount(0);
    for (const chapter of await chapterButtons.all()) await chapter.click();
    await expect(lessonButtons).toHaveCount(lessons);
    const images = chapterButtons.or(lessonButtons).locator('img');
    await expect(images).toHaveCount(chapters + lessons);
    await expect.poll(() => images.evaluateAll(items => items.filter(img => img.complete && img.naturalWidth > 0).length))
      .toBe(chapters + lessons);
    const sources = await images.evaluateAll(items => items.map(img => img.currentSrc));
    expect(new Set(sources).size).toBe(chapters + lessons);

    await page.getByRole('textbox', { name: 'Tìm bài học trong lớp', exact: true }).fill(query);
    const card = page.getByRole('button', { name: `Mở bài: ${lesson}`, exact: true });
    await expect(card).toBeVisible();
    await expect.poll(() => card.locator('img').evaluate(image => image.complete && image.naturalWidth > 0)).toBe(true);
    await card.click();
    await expect(page.getByRole('button', { name: 'Ví dụ dễ', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ví dụ nâng cao', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Ví dụ dễ', exact: true }).press('Enter');
    await expect(page.getByRole('button', { name: 'Ví dụ dễ', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByRole('button', { name: 'Học từng bước: Ví dụ dễ', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Ví dụ nâng cao', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Ví dụ nâng cao', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByRole('button', { name: 'Học từng bước: Ví dụ nâng cao', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Luyện tập (5 bài)', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: /^Bài [1-5](?: · |$)/ })).toHaveCount(5);
    await expect(page.getByRole('textbox', { name: /^Đáp án: Bài [1-5]$/ })).toHaveCount(5);
    await expect(page.getByRole('button', { name: /^Kiểm tra đáp án: Bài [1-5]$/ })).toHaveCount(5);
    await expect(page.getByRole('button', { name: /^Xem cách làm: Bài/ })).toHaveCount(0);
    await page.getByRole('button', { name: 'Học từng bước: Ví dụ nâng cao', exact: true }).click();
    await expect(page.getByTestId('prepared-example-step')).toBeVisible();
    await expect(page.locator('#confirmed-problem-body')).toHaveCount(0);

    await page.goto(`${sites.portal.origin}/study/lessons?lesson=${foreign}&grade=5`);
    await expect(page.getByText(`Bài em mở không có trong chương trình lớp ${grade}.`, { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
  });
}

test('missing profile grade offers recovery without showing a default grade', async ({ page, app }) => {
  await enterLessons(page, app, null);
  await expect(page.getByText('Chưa tải được lớp của em', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: /^Chương / })).toHaveCount(0);
  app.studentProfile.gradeLevel = 3;
  await page.getByRole('button', { name: 'Tải lại hồ sơ', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Toán lớp 3', exact: true })).toBeVisible();
});

test('prepared examples open directly and teach with the authored choices', async ({ page, app }) => {
  const tutorRequests = [];
  page.on('request', request => {
    if (new URL(request.url()).pathname.startsWith('/api/v1/student/tutor/')) tutorRequests.push(request);
  });
  await enterLessons(page, app, 5);
  await page.goto(`${sites.portal.origin}/study/lessons?lesson=grade-5-review-natural`);
  for (const [level, label, choice] of [['easy', 'Ví dụ dễ', '48'], ['advanced', 'Ví dụ nâng cao', '75 × (28 + 12)']]) {
    const toggle = page.getByRole('button', { name: label, exact: true });
    if ((await toggle.getAttribute('aria-expanded')) !== 'true') await toggle.press('Enter');
    const panel = page.locator(`#example-grade-5-review-natural-${level}`);
    await expect(panel.getByRole('button', { name: /Chụp bài làm/ })).toHaveCount(0);
    await panel.getByRole('button', { name: 'Xem gợi ý cách giải' }).click();
    await expect(panel.locator(`#example-grade-5-review-natural-${level}-hint`)).toBeVisible();
    await panel.getByRole('button', { name: `Học từng bước: ${label}` }).click();
    await expect(page).toHaveURL(new RegExp(`exampleLevel=${level}`));
    await expect(page.getByTestId('prepared-example-step')).toBeVisible();
    await expect(page.locator('#confirmed-problem-body')).toHaveCount(0);
    if (level === 'easy') {
      await page.getByRole('button', { name: '13', exact: true }).click();
      await expect(page.getByText('Chưa đúng. Em thử lại hoặc xem gợi ý nhé.')).toBeVisible();
    }
    await page.getByRole('button', { name: choice, exact: true }).click();
    await page.getByRole('button', { name: 'Bước tiếp theo', exact: true }).click();
    await expect(page.getByTestId('prepared-example-step')).toContainText(level === 'easy'
      ? 'Tính nhẩm 48 × (13 + 7).' : 'Tính nhanh 75 × (28 + 12) − 480 : 6.');
    await page.getByRole('button', { name: level === 'easy' ? '960' : '2.920', exact: true }).click();
    await page.getByRole('button', { name: 'Xem bài giải', exact: true }).click();
    await expect(page.getByTestId('prepared-example-solution')).toBeVisible();
    await page.getByRole('button', { name: 'Về bài học', exact: true }).click();
  }
  expect(tutorRequests).toHaveLength(0);
});

test('practice checks an answer and offers a hint only after a wrong attempt', async ({ page, app }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await enterLessons(page, app, 5);
  await page.goto(`${sites.portal.origin}/study/lessons?lesson=grade-5-review-natural`);
  const first = page.getByRole('textbox', { name: 'Đáp án: Bài 1', exact: true });
  const second = page.getByRole('textbox', { name: 'Đáp án: Bài 2', exact: true });
  const check = page.getByRole('button', { name: 'Kiểm tra đáp án: Bài 1', exact: true });
  await expect(check).toBeDisabled();
  await expect(page.getByText('Gợi ý cách giải', { exact: true })).toHaveCount(0);
  await first.fill('350');
  await first.press('Enter');
  await expect(first).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByText(/Hai tích có chung thừa số 35/)).toBeVisible();
  await expect(page.getByTestId('correct-answer-feedback')).toHaveCount(0);
  await first.fill('700');
  await check.click();
  await expect(page.getByTestId('correct-answer-feedback')).toBeVisible();
  await expect(page.getByTestId('correct-answer-celebration').locator(':scope > *').first()).toBeVisible();
  await expect(page.getByText('Gợi ý cách giải', { exact: true })).toHaveCount(0);
  await second.fill('21.102');
  await second.press('Enter');
  await expect(page.getByTestId('correct-answer-feedback')).toHaveCount(2);
});

test('the personal profile and lesson search agree on grade five', async ({ page, app }) => {
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
  await page.setViewportSize({ width: 1280, height: 800 });
  await enterLessons(page, app, 5);
  const navigation = page.getByRole('navigation', { name: 'Điều hướng học sinh' });
  await navigation.getByRole('link', { name: 'Của em', exact: true }).click();
  await expect(page.getByText('Khối 5', { exact: true })).toBeVisible();
  await navigation.getByRole('link', { name: 'Bài học', exact: true }).click();
  const search = page.getByRole('textbox', { name: 'Tìm bài học trong lớp', exact: true });
  await search.fill('dien tich hinh chu nhat');
  await expect(page.getByRole('button', { name: 'Mở bài: Diện tích hình chữ nhật', exact: true })).toHaveCount(0);
  await search.fill('cong so thap phan');
  await page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true }).click();
  await page.getByRole('button', { name: 'Học từng bước: Cộng số thập phân', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/learning\/math-guide\?/);
  await expect(page.locator('#confirmed-problem-body')).toBeVisible();

  const globalSearch = page.getByRole('searchbox', { name: 'Tìm bài học, chủ đề' });
  await globalSearch.fill('dien tich hinh chu nhat');
  await expect(page.getByRole('link', { name: 'Diện tích hình chữ nhật', exact: true })).toHaveCount(0);
  await globalSearch.fill('cong so thap phan');
  await page.getByRole('link', { name: 'Cộng số thập phân', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/lessons\?lesson=grade-5-decimals-add/);
  await expect(page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true })).toHaveAttribute('aria-expanded', 'true');
  await page.getByRole('button', { name: 'Chụp bài làm: Cộng số thập phân', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/camera\?mode=MATH_TUTOR/);
  expect(new URL(page.url()).searchParams.get('problemText')).toBeTruthy();
});
