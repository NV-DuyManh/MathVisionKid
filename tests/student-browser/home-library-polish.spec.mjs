import { readFileSync } from 'node:fs';
import { test, expect, sites, login } from '../browser/fixtures.mjs';

const curriculum = JSON.parse(readFileSync(new URL('../../apps/student-mobile/src/data/primaryMathCurriculumData.json', import.meta.url), 'utf8'));
const gradeFive = curriculum.filter(problem => problem.grade === 5);
const widths = [360, 390, 430, 768, 1024, 1280, 1440];
const home = `${sites.portal.origin}/study/`;

async function noPageOverflow(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}

test('learning streak shows gold star and sparkles only on completed days', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await page.setViewportSize({ width: 360, height: 640 });
  await page.clock.setFixedTime(new Date('2026-11-13T12:00:00Z'));
  await login(page, 'STUDENT');

  const streak = page.getByTestId('learning-streak');
  await streak.scrollIntoViewIfNeeded();
  const completedToday = streak.getByLabel('T6: đã học, hôm nay', { exact: true });
  const star = completedToday.locator('img');
  await expect.poll(() => star.evaluateAll(images => images.length === 1 && images[0].complete && images[0].naturalWidth > 0)).toBe(true);
  await expect(completedToday.getByTestId('completed-day-sparkles')).toBeVisible();
  await expect(streak.getByTestId('completed-day-sparkles')).toHaveCount(1);
  await expect(streak.getByLabel('T7: chưa có hoạt động hoàn thành', { exact: true }).locator('img')).toHaveCount(0);
  await expect(streak.getByLabel('T5: chưa có hoạt động hoàn thành', { exact: true }).locator('img')).toHaveCount(0);
  await noPageOverflow(page);
  await streak.screenshot({ path: testInfo.outputPath('learning-streak.png') });
});

for (const width of widths) {
  test(`home and grade-five library retain current styling and usable controls at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
    await page.addInitScript(problemText => {
      const owner = '550e8400-e29b-41d4-a716-446655440000';
      const key = `mathvision_lessons_${Array.from(owner).map(character => character.codePointAt(0).toString(16)).join('_')}`;
      localStorage.setItem(key, JSON.stringify([{ id: 'saved-curriculum-browser', timestamp: Date.now() - 1000,
        problemText, workText: 'Bài làm đã lưu', reflection: '', reviewedSteps: 1 }]));
    }, gradeFive[0].problemText);
    await page.setViewportSize({ width, height: 900 });
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    const homeRobot = page.locator('img[src*="robot-mascot"]');
    await expect.poll(() => homeRobot.evaluateAll(images => images.length > 0 && images.every(image => image.complete && image.naturalWidth > 0))).toBe(true);
    await expect(page.locator('img[src*="mathvision-star"], img[src*="mathvision-icon-v2"]')).toHaveCount(0);
    await noPageOverflow(page);
    const quickCards = page.getByTestId('quick-actions-grid').getByRole('button');
    await expect(quickCards).toHaveCount(4);
    const bounds = await quickCards.evaluateAll(cards => cards.map(card => {
      const rect = card.getBoundingClientRect(); return { x: rect.x, y: rect.y, width: rect.width };
    }));
    expect(Math.max(...bounds.map(card => card.y)) - Math.min(...bounds.map(card => card.y))).toBeLessThanOrEqual(1);
    expect(Math.max(...bounds.map(card => card.width)) - Math.min(...bounds.map(card => card.width))).toBeLessThanOrEqual(1);
    await expect(page.getByRole('button', { name: 'Tiện ích tiếp theo', exact: true })).toHaveCount(0);
    if (width < 768) {
      await expect(page.getByRole('heading', { name: 'Trang chủ', exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Thông báo học tập', exact: true })).toBeVisible();
    } else {
      await expect(page.getByTestId('home-hero').getByRole('heading')).toContainText('khám phá Toán học nhé!');
      await expect(page.getByRole('button', { name: 'Thông báo', exact: true })).toBeVisible();
    }
    await expect(page.getByRole('heading', { name: 'Hành trình học tập', exact: true })).toBeVisible();
    await expect(page.getByTestId('learning-journey').getByRole('button')).toHaveCount(width < 768 ? 3 : 4);
    await expect(page.getByRole('heading', { name: 'Bài học gợi ý cho em', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Luyện tập lớp \d$/ })).toHaveCount(0);
    await page.getByRole('button', { name: 'Chụp bài toán', exact: true }).scrollIntoViewIfNeeded();
    await testInfo.attach(`home-top-${width}`, { body: await page.screenshot({ path: testInfo.outputPath('home-recovered.png') }), contentType: 'image/png' });
    await page.getByText('Chuỗi học tập', { exact: true }).scrollIntoViewIfNeeded();
    await expect(page.getByText('Chuỗi học tập', { exact: true })).toBeVisible();
    for (const day of ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']) await expect(page.getByLabel(new RegExp(`^${day}:`))).toBeVisible();
    await testInfo.attach(`home-streak-${width}`, { body: await page.screenshot(), contentType: 'image/png' });

    await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
    const expression = page.getByRole('textbox', { name: 'Phép tính', exact: true });
    await expect(expression).toHaveValue('');
    await page.getByRole('button', { name: 'Nhập 2', exact: true }).click();
    await page.getByRole('button', { name: 'Cộng', exact: true }).click();
    await page.getByRole('button', { name: 'Nhập 3', exact: true }).click();
    await expect(expression).toHaveValue('2+3');
    await page.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
    await expect(page.getByTestId('calculator-popup').locator('[aria-live="polite"]').filter({ hasText: '5' }).first()).toBeVisible();
    await noPageOverflow(page);
    await testInfo.attach(`calculator-${width}`, { body: await page.screenshot(), contentType: 'image/png' });
    await page.getByRole('button', { name: 'Đóng máy tính', exact: true }).click();

    await page.getByRole('button', { name: 'Bảo vệ thông tin riêng tư của em', exact: true }).click();
    await expect(page.getByText('Bảo vệ thông tin cá nhân', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Đóng thông tin bảo mật', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Chương trình Toán lớp 5', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /^Học bài / })).toHaveCount(width < 768 ? 1 : 3);
    await page.getByRole('button', { name: 'Luyện tập. Làm bài theo chủ đề', exact: true }).first().click();
    await expect(page).toHaveURL(/\/study\/lessons/);
    await expect(page.getByText('Chương trình học của em', { exact: true })).toBeVisible();
    await expect(page.getByText('20 bài học', { exact: true })).toBeVisible();
    await expect(page.getByText('1/20', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
    const savedSection = page.getByRole('button', { name: `Chủ đề ${gradeFive[0].section}`, exact: true });
    await expect(savedSection).toHaveAttribute('aria-expanded', 'false');
    await savedSection.click();
    await expect(page.getByText('Đã lưu bài làm', { exact: true })).toBeVisible();
    await savedSection.click();
    await expect(page.getByRole('button', { name: /^Chọn Lớp / })).toHaveCount(0);
    await expect(page.getByRole('button', { name: /^Câu đố của em/ })).toHaveCount(0);
    await expect(page.getByText('Hôm nay em học gì?', { exact: true })).toHaveCount(0);
    await noPageOverflow(page);
    await testInfo.attach(`library-${width}`, { body: await page.screenshot(), contentType: 'image/png' });

    const search = page.getByRole('textbox', { name: 'Tìm bài học', exact: true });
    await page.getByRole('button', { name: 'Số và phép tính', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Số và phép tính', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(gradeFive.filter(problem => problem.section === 'Số và phép tính').length);
    await search.fill('cong so thap phan');
    await expect(page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(1);
    await page.getByRole('button', { name: 'Xóa tìm kiếm bài học', exact: true }).click();
    await page.getByRole('button', { name: 'Tất cả chủ đề', exact: true }).click();
    await search.fill('chuyen dong deu');
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(2);
    await search.fill('khong-co-bai-xyz');
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
    await expect(page.getByText('Chưa tìm thấy bài phù hợp. Em thử tìm bằng từ khác nhé.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Xem tất cả bài học', exact: true }).click();
    await expect(search).toHaveValue('');
    await expect(page.getByRole('button', { name: /^Mở bài: / })).toHaveCount(0);
    await page.getByRole('button', { name: 'Chủ đề Số và phép tính', exact: true }).click();

    const problem = gradeFive.find(item => item.title === 'Cộng số thập phân');
    await page.getByRole('button', { name: `Mở bài: ${problem.title}`, exact: true }).click();
    await page.getByRole('button', { name: `Xem gợi ý: ${problem.title}`, exact: true }).click();
    await expect(page.getByText(problem.guidance, { exact: true })).toBeVisible();
    await page.getByRole('button', { name: `Học từng bước: ${problem.title}`, exact: true }).click();
    await expect(page).toHaveURL(/\/study\/learning\/math-guide/);
    await expect(page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số', exact: true })).toBeVisible();
    await page.goto(home);
    await page.getByRole('button', { name: 'Chụp bài toán', exact: true }).click();
    await expect(page).toHaveURL(/\/study\/camera\?mode=MATH_TUTOR/);
    await expect(page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true })).toBeVisible();
  });

  test(`welcome uses onboarding or shared login at ${width}px`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    await page.setViewportSize({ width, height: 900 });
    await page.goto(`${sites.portal.origin}/study/welcome`);
    if (width >= 768) {
      await expect(page).toHaveURL(`${sites.portal.origin}/login`);
      await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
      return;
    }
    await expect(page.getByRole('heading', { name: 'Học Toán thông minh cùng AI', exact: true })).toBeVisible();
    await expect(page.getByTestId('welcome-card-2')).toHaveAttribute('aria-hidden', 'true');
    await expect(page.getByTestId('welcome-card-3')).toHaveAttribute('aria-hidden', 'true');
    await expect(page.getByRole('button', { name: 'Trang giới thiệu trước', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Trang giới thiệu tiếp theo', exact: true })).toHaveCount(0);
    await expect(page.getByText(/^Trang [123] trên 3$/)).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Bỏ qua giới thiệu', exact: true })).toBeVisible();
    for (const index of [2, 3, 2, 1]) {
      await page.getByRole('tab', { name: `Trang giới thiệu ${index}`, exact: true }).click();
      await expect(page.getByRole('tab', { name: `Trang giới thiệu ${index}`, exact: true })).toHaveAttribute('aria-selected', 'true');
      await expect(page.getByTestId(`welcome-card-${index}`)).not.toHaveAttribute('aria-hidden', 'true');
    }
    await expect.poll(async () => {
      const [cardBounds, pagerBounds] = await Promise.all([
        page.getByTestId('welcome-card-1').boundingBox(),
        page.getByTestId('welcome-pager').boundingBox(),
      ]);
      if (!cardBounds || !pagerBounds) return Number.POSITIVE_INFINITY;
      return Math.max(Math.abs(cardBounds.x - pagerBounds.x), Math.abs(cardBounds.width - pagerBounds.width));
    }, { message: 'The selected welcome card settles within the pager before capture' }).toBeLessThanOrEqual(1);
    await noPageOverflow(page);
    await testInfo.attach(`welcome-${width}`, { body: await page.screenshot({ path: testInfo.outputPath('onboarding-recovered.png') }), contentType: 'image/png' });
    await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click();
    await expect(page).toHaveURL(`${sites.portal.origin}/login`);
    await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
  });
}

test('library remains usable by keyboard in landscape with reduced motion and enlarged content', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await page.setViewportSize({ width: 844, height: 390 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Bài học', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/lessons$/);
  await expect(page.getByRole('heading', { name: 'Chương trình học của em', exact: true })).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.zoom = '1.5'; });
  const search = page.getByRole('textbox', { name: 'Tìm bài học', exact: true });
  await search.focus();
  await expect(search).toBeFocused();
  await page.keyboard.type('cong so thap phan');
  const lesson = page.getByRole('button', { name: 'Mở bài: Cộng số thập phân', exact: true });
  await expect(lesson).toBeVisible();
  await lesson.focus();
  await page.keyboard.press('Enter');
  await expect(lesson).toHaveAttribute('aria-expanded', 'true');
  await expect(page.getByRole('button', { name: 'Học từng bước: Cộng số thập phân', exact: true })).toBeVisible();
  await noPageOverflow(page);
  await testInfo.attach('library-landscape-keyboard-150-percent', { body: await page.screenshot(), contentType: 'image/png' });
});
