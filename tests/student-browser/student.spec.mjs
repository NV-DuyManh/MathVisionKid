import { test, expect, sites, login } from '../browser/fixtures.mjs';
import { fileURLToPath } from 'node:url';
import { studentPort } from '../browser/sites.mjs';

test('Student can add missing written work from the solved-work action on web', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ status: 'READY' }));
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  const url = `${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: 'Tính: 23 + 17' })}`;
  await page.goto(url);
  await page.getByRole('button', { name: 'Bài đã có lời giải', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bài đã có lời giải', exact: true })).toBeVisible();
  await testInfo.attach('Add missing work choices on web', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Đóng', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Bài đã có lời giải', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Bài đã có lời giải', exact: true }).click();
  await page.getByRole('button', { name: 'Nhập bài làm bằng chữ', exact: true }).click();
  await page.getByRole('textbox', { name: 'Nội dung bài làm', exact: true }).fill('23 + 17 = 40');
  await page.getByRole('button', { name: 'Dùng nội dung này', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Bài đã có lời giải', exact: true })).toBeVisible();
  await page.goto(url);
  await page.getByRole('button', { name: 'Bài đã có lời giải', exact: true }).click();
  await page.getByRole('button', { name: 'Chụp lại cả đề và bài giải', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/camera\?mode=MATH_TUTOR/);
  expect(app.requests.some(request => request.path === '/student/tutor/work-review')).toBe(false);
});

test('Work Review edits all affected calculations with compact stacked fractions and celebrates a verified correction', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  const problem = 'Có 30 kg táo, bán 15 kg. Sau đó bán một nửa số táo còn lại. Hỏi lần sau bán bao nhiêu kg táo?';
  const work = 'Bài giải:\n30 - 15 = 14 (kg)\n14 × 1/2 = 7 (kg)';
  const corrected = 'Bài giải:\n30 - 15 = 15 (kg)\n15 × 1/2 = 7,5 (kg)';
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/quizzes/from-learning', ({ body, json }) => {
    expect(body.sourceType).toBe('WORK_REVIEW');
    return json({ offered: false, quiz: null });
  });
  app.responses.set('POST /student/tutor/work-review', ({ body, json }) => {
    expect(body.problemText).toBe(problem);
    expect(body.problemConfirmed && body.workConfirmed).toBe(true);
    const correct = body.workText === corrected;
    if (!correct) expect(body.workText).toBe(work);
    return json({ sourceId: body.sourceId, status: correct ? 'CORRECT' : 'NEEDS_REVISION',
      summary: 'Đã kiểm tra bài làm.', praise: correct ? 'Em đã tính đúng và giữ đúng đơn vị.' : '',
      nextAction: 'Em xem lại phép tính nhé.', alternative: '', complete: true, missingPart: '', arithmeticVerified: correct,
      rows: body.workText.split('\n').map((sourceText, lineIndex) => ({ sourceText, lineIndex,
        rowKind: lineIndex === 0 ? 'HEADING' : 'CALCULATION', arithmeticCorrect: lineIndex === 0 ? null : correct || lineIndex === 2,
        status: correct || lineIndex === 0 ? 'OK' : 'FIX',
        errorKind: correct || lineIndex === 0 ? 'NONE' : lineIndex === 1 ? 'CALCULATION' : 'DEPENDENT',
        feedback: 'Em tính lại sau khi sửa bước trước nhé.', hints: [] })) });
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/learning/math-guide?${new URLSearchParams({ problemText: problem, workText: work })}`);
  await page.getByRole('button', { name: 'Bài đã có lời giải', exact: true }).click();
  await expect(page.getByText('Sai tính toán', { exact: false }).first()).toBeVisible();
  await expect(page.getByText('Cần tính lại sau khi sửa bước trước', { exact: false }).first()).toBeVisible();
  await expect(page.getByText('Cần đối chiếu', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Em nhập các dòng vừa sửa', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Chụp lại bài em đã sửa', exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Dòng 2 em vừa sửa', exact: true }).fill('30 - 15 = 15 (kg)');
  await page.getByRole('textbox', { name: 'Dòng 3 em vừa sửa, phần 1', exact: true }).fill('15 × ');
  await page.getByRole('textbox', { name: 'Dòng 3 em vừa sửa, phần 2', exact: true }).fill(' = 7,5 (kg)');
  const numerator = page.getByRole('textbox', { name: 'Dòng 3 em vừa sửa, tử số 1', exact: true });
  const denominator = page.getByRole('textbox', { name: 'Dòng 3 em vừa sửa, mẫu số 1', exact: true });
  const top = await numerator.boundingBox(), bottom = await denominator.boundingBox();
  expect(top.y + top.height).toBeLessThanOrEqual(bottom.y);
  const editor = page.getByTestId('work-line-expression');
  expect((await editor.boundingBox()).height).toBeLessThan(90);
  await testInfo.attach('Work Review synthetic correction', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Nhận xét lại bài', exact: true }).click();
  await expect(page.getByText('Em làm đúng rồi!', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Chụp lại bài em đã sửa', exact: true })).toHaveCount(0);
  const reviews = app.requests.filter(request => request.path === '/student/tutor/work-review');
  expect(reviews).toHaveLength(2);
  expect(reviews[1].body.sourceId).not.toBe(reviews[0].body.sourceId);
});

test('Student retries photo reading after a temporary service failure', async ({ page, app, browserName }) => {
  app.realStudent = true;
  let firstUpload;
  let inspections = 0;
  const problemText = 'Tính 384 + 219';
  app.responses.set('POST /student/tutor/inspect', async ({ route, json }) => {
    const request = route.request();
    expect(request.headers()['content-type']).toMatch(/^multipart\/form-data; boundary=/);
    const body = request.postDataBuffer();
    expect(body.toString('latin1')).toContain('filename="notebook.jpg"');
    expect(body.toString('latin1')).toMatch(/name="privacyConfirmed"\r\n\r\ntrue/);
    // WebKit interception omits Blob-backed file bytes from postDataBuffer.
    if (browserName !== 'webkit') {
      const start = body.indexOf('\r\n\r\n') + 4;
      const jpeg = body.subarray(start, body.indexOf('\r\n--', start));
      expect([...jpeg.subarray(0, 3)]).toEqual([255, 216, 255]);
      if (firstUpload) expect(jpeg.equals(firstUpload)).toBe(true);
      else firstUpload = jpeg;
    }
    if (++inspections === 1) return json({ error: { code: 'TUTOR_BUSY' } }, 503);
    return json({ kind: 'PROBLEM', problemText, lines: [], needsProblem: false });
  });
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera?mode=MATH_TUTOR`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thư viện' }).click();
  await (await chooser).setFiles(fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url)));
  await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' }).click();
  await page.getByRole('button', { name: 'Tiếp tục xem lại' }).click();
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh' }).click();
  await expect(page).toHaveURL(/\/study\/learning\/math-guide/);
  await expect(page.getByText(/Đang có nhiều yêu cầu đọc ảnh/)).toBeVisible();
  const retry = page.getByRole('button', { name: 'Đọc lại ảnh', exact: true });
  await expect(retry).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Nhập đề bằng chữ', exact: true })).toBeVisible();
  await retry.click();
  await expect(page.getByText(problemText, { exact: true })).toBeVisible();
  expect(app.requests.filter(({ path }) => path === '/student/tutor/inspect')).toHaveLength(2);
});

test('Student previews and crops a local worksheet without sending it', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera?mode=ARITHMETIC`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thư viện' }).click();
  await (await chooser).setFiles(fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url)));
  await expect(page).toHaveURL(/\/study\/privacy/);
  const privacyImage = page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư');
  await expect(privacyImage).toBeVisible();
  const imageBounds = await privacyImage.boundingBox();
  await page.mouse.move(imageBounds.x + imageBounds.width * 0.2, imageBounds.y + imageBounds.height * 0.2);
  await page.mouse.down();
  await page.mouse.move(imageBounds.x + imageBounds.width * 0.5, imageBounds.y + imageBounds.height * 0.5, { steps: 8 });
  await page.mouse.up();
  const undoMask = page.getByRole('button', { name: 'Hoàn tác vùng che vừa vẽ' });
  await expect(undoMask).toBeVisible();
  await undoMask.click();
  await expect(undoMask).toHaveCount(0);
  const maskEditor = page.getByText('Chỉnh vùng che bằng số', { exact: true });
  await maskEditor.focus();
  await maskEditor.press('Enter');
  const addMask = page.getByRole('button', { name: 'Thêm vùng che', exact: true });
  await addMask.focus();
  await addMask.press('Enter');
  const confirmation = page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' });
  await confirmation.click();
  await expect(confirmation).toBeChecked();
  const offset = page.getByRole('spinbutton', { name: 'Cách trái' });
  await offset.fill('12');
  await offset.press('Tab');
  await expect(offset).toHaveValue('12');
  await expect(confirmation).not.toBeChecked();
  await testInfo.attach('Student privacy accessibility tree', { body: await page.getByRole('group', { name: 'Vị trí và kích thước vùng che (px)' }).ariaSnapshot(), contentType: 'text/plain' });
  await maskEditor.press('Enter');
  await confirmation.click();
  await page.getByRole('button', { name: 'Tiếp tục xem lại' }).click();
  await expect(page).toHaveURL(/\/study\/crop/);
  const cropImage = page.getByLabel('Ảnh bài tập đang căn chỉnh');
  await expect(cropImage).toBeVisible();
  await expect.poll(() => cropImage.evaluate(async element => {
    const source = element instanceof HTMLImageElement ? element : element.querySelector('img');
    if (!source?.src) return false;
    const image = new Image();
    image.src = source.src;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext('2d');
    context.drawImage(image, 0, 0);
    const rgb = (x, y) => [...context.getImageData(Math.floor(canvas.width * x), Math.floor(canvas.height * y), 1, 1).data].slice(0, 3);
    return rgb(0.25, 0.125).every(channel => channel < 24) && rgb(0.9, 0.9).some(channel => channel > 64);
  })).toBe(true);
  await page.setViewportSize({ width: 320, height: 300 });
  await expect.poll(async () => (await cropImage.boundingBox()).height).toBeGreaterThan(60);
  await page.getByRole('button', { name: 'Xoay ảnh 90 độ' }).click();
  await page.getByRole('button', { name: 'Đặt lại ảnh và khung cắt' }).click();
  const angle = page.getByRole('slider', { name: 'Góc căn thẳng ảnh' });
  await angle.focus();
  await angle.press('ArrowRight');
  await expect(angle).toHaveAttribute('aria-valuetext', '0,1 độ');
  await angle.press('ArrowLeft');
  await expect(angle).toHaveValue('0');
  const edge = page.getByRole('combobox', { name: 'Cạnh cần chỉnh' });
  await edge.focus();
  await edge.press('Home');
  await expect(edge).toHaveValue('top');
  const shrink = page.getByRole('button', { name: 'Thu hẹp từ cạnh trên' });
  await shrink.focus();
  for (let i = 0; i < 5; i++) await shrink.press('Enter');
  const sourceHeight = await cropImage.evaluate(async element => {
    const image = element instanceof HTMLImageElement ? element : element.querySelector('img');
    await image.decode();
    return image.naturalHeight;
  });
  await testInfo.attach('Student worksheet crop fixture', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh' }).click();
  await expect(page).toHaveURL(/\/study\/preview/);
  const resultImage = page.getByLabel('Ảnh bài toán em đã chọn');
  await expect.poll(() => resultImage.evaluate(async element => {
    const image = element instanceof HTMLImageElement ? element : element.querySelector('img');
    await image.decode();
    return image.naturalHeight;
  })).toBe(Math.round(sourceHeight * 0.7));
  await expect(page.getByRole('button', { name: 'Chỉnh lại vùng bài toán' })).toBeVisible();
  await testInfo.attach('Student worksheet preview fixture', { body: await page.screenshot(), contentType: 'image/png' });
  expect(app.requests.filter(({ method }) => method === 'POST').map(({ path }) => path)).toEqual(['/auth/login']);
});

const arithmeticOutcomes = [
  { status: 'NEEDS_RETAKE', imageQualityIssue: 'BLUR', route: 'quality-failure',
    title: 'Ảnh bị rung hoặc hơi mờ', action: 'Chụp lại thật rõ', next: /\/study\/camera\?/ },
  { status: 'OUT_OF_SCOPE', route: 'out-of-scope',
    title: 'Dạng bài này MathVision đang học thêm', action: 'Chụp phép tính đặt dọc khác', next: /\/study\/camera\?/ },
  { status: 'FEEDBACK_READY', validation: { diagnosisState: 'VALID', isValid: true }, route: 'correct',
    title: 'Bài làm đúng', studentFeedback: { title: 'Bài làm đúng', hint: 'Em đã cộng đúng.' },
    action: 'Kiểm tra bài toán khác', next: /\/study\/camera\?/ },
];

for (const { route, title, action, next, ...response } of arithmeticOutcomes) {
  test(`Student submits a worksheet and can act on the ${route} result`, async ({ page, app }, testInfo) => {
    app.realStudent = true;
    const submission = { submissionId: 'worksheet-1', ...response };
    let imageReceived = false;
    app.responses.set('POST /student/submissions', async ({ route: requestRoute, json }) => {
      const request = requestRoute.request();
      const body = request.postDataBuffer();
      imageReceived = request.headers()['content-type']?.startsWith('multipart/form-data;') &&
        body?.includes(Buffer.from('name="image";')) && body?.includes(Buffer.from([0xff, 0xd8, 0xff]));
      await expect(page.getByRole('heading', { name: 'Đang gửi bài toán' })).toBeVisible();
      return json(submission, 201);
    });
    app.responses.set('GET /student/submissions/worksheet-1', ({ json }) => json(submission));
    await login(page, 'STUDENT');
    await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
    await page.goto(`${sites.portal.origin}/study/camera?mode=ARITHMETIC`);
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Chọn ảnh từ thư viện' }).click();
    await (await chooser).setFiles(fileURLToPath(new URL('../../backend/business-api/src/test/resources/fixtures/worksheet-addition.jpg', import.meta.url)));
    await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' }).click();
    await page.getByRole('button', { name: 'Tiếp tục xem lại' }).click();
    await page.getByRole('button', { name: 'Xác nhận cắt ảnh' }).click();
    await page.getByRole('button', { name: 'KIỂM TRA BÀI TOÁN' }).click();
    await expect(page).toHaveURL(new RegExp(`/study/results/${route}\\?`));
    expect(imageReceived).toBe(true);
    await expect(page.getByRole('heading', { name: title, level: 2 })).toBeInViewport();
    await expect(page.locator('[aria-live="polite"]').filter({ hasText: title })).toBeVisible();
    const nextAction = page.getByRole('button', { name: action, exact: true });
    await expect(nextAction).toBeInViewport();
    expect((await nextAction.boundingBox()).height).toBeGreaterThanOrEqual(44);
    await testInfo.attach('Student worksheet result', { body: await page.screenshot(), contentType: 'image/png' });
    await nextAction.focus();
    await nextAction.press('Enter');
    await expect(page).toHaveURL(next);
    expect(app.requests.filter(request => request.method === 'POST').map(request => request.path)).toEqual(['/auth/login', '/student/submissions']);
  });
}

test('Portal login enters the real Student bundle, navigates and survives a deep-link reload', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page).toHaveURL(`${sites.portal.origin}/study/`);
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.getByRole('tab', { name: 'Bài học' }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/lessons`);
  await expect(page.getByText('Hôm nay em học gì?', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Hôm nay em học gì?', { exact: true })).toBeVisible();
  const originalViewport = page.viewportSize();
  await page.setViewportSize({ width: 320, height: 844 });
  await page.getByRole('button', { name: 'Chọn Lớp 3' }).click();
  await page.getByRole('button', { name: /^Mở bài:/ }).first().click();
  await page.getByRole('button', { name: /^Xem gợi ý:/ }).click();
  await expect(page.getByRole('button', { name: /^Ẩn gợi ý:/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await page.setViewportSize(originalViewport);
  await page.goto(`${sites.portal.origin}/study/quiz`);
  await expect(page.getByText('Câu đố của em', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Unmatched Route', { exact: true })).toHaveCount(0);
  expect(app.requests.some(request => request.path === '/student/quizzes')).toBe(true);
});

test('Của em keeps saved work, while the avatar opens account settings and logout', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.evaluate(() => {
    const owner = Array.from('550e8400-e29b-41d4-a716-446655440000', char => char.codePointAt(0).toString(16)).join('_');
    localStorage.setItem(`mathvision_lessons_${owner}`, JSON.stringify([{
      id: 'fixture-saved-lesson', timestamp: Date.now() - 1000, problemText: '17 + 25',
      workText: '42', reflection: 'Em nhớ cộng hàng đơn vị trước.', reviewedSteps: 3,
    }]));
  });
  await page.setViewportSize({ width: 320, height: 844 });
  await page.getByRole('tab', { name: 'Thành tích', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Nhiệm vụ của em' })).toBeVisible();
  await expect(page.getByText(/Hoàn thành bài học/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await page.getByRole('tab', { name: 'Của em', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Đăng xuất', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Ghi chú', exact: true }).click();
  await expect(page.getByText('Em nhớ cộng hàng đơn vị trước.').first()).toBeVisible();
  await page.getByRole('button', { name: 'Trang cá nhân của em', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/account`);
  await expect(page.getByRole('heading', { name: 'Hồ sơ của em', exact: true })).toBeVisible();
  const logout = page.getByRole('button', { name: 'Đăng xuất', exact: true });
  await logout.click();
  const cancel = page.getByRole('button', { name: 'Ở lại', exact: true });
  await cancel.click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/account`);
  expect(app.requests.filter(({ path }) => path === '/auth/logout')).toHaveLength(0);
  await logout.click();
  await page.getByRole('button', { name: 'Xác nhận đăng xuất', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/`);
  await expect(page.getByRole('banner').getByRole('link', { name: 'Đăng nhập', exact: true })).toBeVisible();
  await expect.poll(() => app.requests.filter(({ path }) => path === '/auth/logout').length).toBe(1);
  await page.goBack();
  await expect(page).toHaveURL(`${sites.portal.origin}/`);
  await page.goto(`${sites.portal.origin}/study/profile`);
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
});

test('Avatar account page saves name and photo, restores a preset, and validates password change', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Trang cá nhân của em', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/account`);
  await page.getByRole('textbox', { name: 'Tên hiển thị', exact: true }).fill('Sao Thông Minh');
  await page.getByRole('button', { name: 'Chọn hình Hành tinh', exact: true }).click();
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('textbox', { name: 'Tên hiển thị', exact: true })).toHaveValue('Sao Thông Minh');
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thiết bị', exact: true }).click();
  await (await chooser).setFiles(fileURLToPath(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url)));
  await expect(page.getByText('Đã cập nhật ảnh đại diện.', { exact: true })).toBeVisible();
  await expect.poll(() => page.locator('img[src^="data:image/"]').count()).toBeGreaterThan(0);
  await page.reload();
  await expect.poll(() => page.locator('img[src^="data:image/"]').count()).toBeGreaterThan(0);
  await testInfo.attach('Account settings with selected photo', { body: await page.screenshot({ path: testInfo.outputPath('account-settings.png') }), contentType: 'image/png' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize().width);
  await page.getByRole('button', { name: 'Chọn hình Lá xanh', exact: true }).click();
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
  await expect(page.getByText('Đã lưu hồ sơ của em.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator('img[src^="data:image/"]')).toHaveCount(0);
  await page.getByRole('button', { name: 'Đổi mật khẩu', exact: true }).click();
  await page.getByLabel('Mật khẩu hiện tại', { exact: true }).fill('incorrect-password');
  await page.getByLabel('Mật khẩu mới', { exact: true }).fill('NewPassword-123');
  await page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill('different-password');
  await page.getByRole('button', { name: 'Cập nhật mật khẩu', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Hai lần nhập mật khẩu mới chưa giống nhau.');
  expect(app.requests.filter(request => request.path === '/student/profile/password')).toHaveLength(0);
  await page.getByLabel('Nhập lại mật khẩu mới', { exact: true }).fill('NewPassword-123');
  await page.getByRole('button', { name: 'Cập nhật mật khẩu', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Mật khẩu hiện tại chưa đúng. Em kiểm tra lại nhé.');
  await page.getByLabel('Mật khẩu hiện tại', { exact: true }).fill('CurrentPassword-123');
  await page.getByRole('button', { name: 'Cập nhật mật khẩu', exact: true }).click();
  await expect(page.getByText('Đã đổi mật khẩu. Các phiên đăng nhập khác đã kết thúc.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Quay lại', exact: true }).click();
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
});

test('A photo picker opened in an old session cannot upload into a new session', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Trang cá nhân của em', exact: true }).click();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thiết bị', exact: true }).click();
  const selected = await chooser;
  await page.evaluate(() => window.sessionStorage.setItem('portal_session_id', crypto.randomUUID()));
  await selected.setFiles(fileURLToPath(new URL('../../apps/student-mobile/assets/illustrations/student-avatar.png', import.meta.url)));
  await expect(page.getByRole('alert')).toHaveText('Chưa cập nhật được ảnh. Em kiểm tra ảnh và kết nối rồi thử lại nhé.');
  expect(app.requests.filter(request => request.path === '/student/profile/photo')).toHaveLength(0);
});

test('anonymous Student deep link returns to login and missing bundles return 404', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/login`);
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  for (const width of [320, 768, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(page.getByRole('textbox', { name: 'Email', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await expect(page.locator('.oly-grid-paper')).toHaveCount(0);
  }
  await page.goto(`${sites.portal.origin}/study/quiz`);
  // Mounted Student deliberately delegates login to the shared Portal.
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeVisible();
  const missing = await page.request.get(`http://127.0.0.1:${studentPort}/study/_expo/static/js/web/missing.js`);
  expect(missing.status()).toBe(404);
});

test('Student quiz starts, shows feedback and completes with the existing API contract', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => {
    const reward = '[aria-label="3 sao"]';
    window.quizRewardWasDimmed = false;
    new MutationObserver(() => {
      const element = document.querySelector(reward);
      if (element && Number(getComputedStyle(element).opacity) < 1) window.quizRewardWasDimmed = true;
    }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['style'] });
  });
  const id = 'notebook-fixture';
  const path = `/student/quizzes/${id}`;
  const now = new Date().toISOString();
  let quiz = {
    quizId: id, sourceType: 'LESSON', sourceId: 'fixture', topicCode: 'ADD', topicName: 'Phép cộng',
    skillCode: 'ADD', gradeLevel: 3, taxonomyVersion: '1', verificationStatus: 'VERIFIED', confidencePercent: 100,
    questionText: 'Tính 17 + 25', unit: '', answerFormat: 'INTEGER', status: 'READY',
    createdAt: now, startedAt: null, completedAt: null, serverNow: now, elapsedMillis: 0,
    stars: 0, wrongAttempts: 0, solutionViewed: false, completedWithSolution: false, canRevealSolution: false,
    attempts: [], explanationText: null, correctAnswer: null, timerRunning: false,
  };
  app.responses.set(`GET ${path}`, ({ json }) => json(quiz));
  app.responses.set(`POST ${path}/start`, ({ json }) => {
    quiz = { ...quiz, status: 'IN_PROGRESS', startedAt: now, timerRunning: true };
    return json(quiz);
  });
  app.responses.set(`POST ${path}/activity`, ({ json }) => json(quiz));
  // The browser can prefetch narration as soon as a quiz starts. This scenario covers text feedback.
  app.responses.set(`POST ${path}/narration`, ({ reject }) => reject(422));
  app.responses.set(`POST ${path}/submit`, ({ json, body }) => {
    expect(body.requestId).toEqual(expect.any(String));
    expect(body.answer).toBe(quiz.attempts.length ? '42' : '41');
    const correct = body.answer === '42';
    const attempt = { number: quiz.attempts.length + 1, answer: body.answer, correct, submittedAt: now, elapsedMillis: 1000 };
    quiz = { ...quiz, attempts: [...quiz.attempts, attempt], wrongAttempts: correct ? 1 : quiz.wrongAttempts + 1,
      ...(correct ? { status: 'COMPLETED', completedAt: now, timerRunning: false, stars: 3 } : {}) };
    return json({ quiz, attempt });
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/quiz/${id}`);
  await page.getByRole('button', { name: 'Bắt đầu tính giờ' }).click();
  const answer = page.getByRole('textbox', { name: 'Đáp án của em' });
  await answer.fill('41');
  const submit = page.getByRole('button', { name: 'Hoàn thành', exact: true });
  const buttonOffset = (await submit.boundingBox()).y - (await answer.boundingBox()).y;
  await submit.click();
  await expect(page.locator('[aria-live="polite"]').filter({ hasText: 'Chưa đúng rồi, nhưng em thử kiểm tra lại nhé!' })).toBeVisible();
  const nextOffset = (await submit.boundingBox()).y - (await answer.boundingBox()).y;
  expect(Math.abs(nextOffset - buttonOffset)).toBeLessThan(2);
  await testInfo.attach('Student quiz fixture feedback', { body: await page.screenshot(), contentType: 'image/png' });
  await answer.fill('42');
  await page.getByRole('button', { name: 'Hoàn thành', exact: true }).click();
  await expect(page.getByText('Em đã hoàn thành rồi!', { exact: true })).toBeVisible();
  const reward = page.getByLabel('3 sao', { exact: true });
  await expect(reward).toBeVisible();
  await expect(reward).toHaveCSS('opacity', '1');
  expect(await page.evaluate(() => window.quizRewardWasDimmed)).toBe(false);
  await testInfo.attach('Student quiz fixture completed', { body: await page.screenshot(), contentType: 'image/png' });
});

test('the old Student web login uses the same Portal form', async ({ page, app }) => {
  app.realStudent = true;
  await page.goto(`${sites.portal.origin}/study/login`);
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  await expect(page.locator('input[autocomplete="current-password"]')).toHaveCount(1);
});

test('student can find rank, switch leaderboards and open all six games on a narrow screen', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  const rank = { name: 'Chiến Thần', masterStars: 102, progress: 0, goal: 0 };
  let profile = {
    displayName: 'Bạn nhỏ yêu toán', gradeLevel: 5, joinedAt: null, classrooms: [{ id: 'class-5a', name: 'Lớp 5A' }],
    avatar: 'star', leaderboardVisible: false, publicAlias: 'Sao Toán', selectedTitle: null,
    stars: 214, rank, highestRank: rank.name, position: null,
    stats: { lessons: 1, quizzes: 0, games: 0, days: 1, week: 1, month: 1, today: 1, streak: 1 },
    titles: [], history: [],
  };
  const entries = Array.from({ length: 12 }, (_, index) => ({
    position: index + 1, alias: `Bạn Sao ${index + 1}`, avatar: 'star', stars: 200 - index, rank, self: false,
  }));
  await page.route('**/api/v1/student/profile', async route => {
    if (route.request().method() === 'PUT') profile = { ...profile, ...route.request().postDataJSON() };
    await route.fulfill({ json: profile });
  });
  await page.route('**/api/v1/student/leaderboard*', async route => {
    const classroom = new URL(route.request().url()).searchParams.get('classroom');
    await route.fulfill({ json: { entries: classroom ? entries.slice(0, 2) : entries, ownPosition: null } });
  });
  app.responses.set('GET /student/rank-milestones', ({ json }) => json([
    { name: 'Đồng', stars: 0, top: null },
    { name: 'Thách Đấu', stars: 162, top: 200 },
  ]));
  await page.setViewportSize({ width: 320, height: 660 });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/account`);
  await page.getByRole('textbox', { name: 'Tên hiển thị' }).fill('Bạn nhỏ thích tính nhẩm');
  await page.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bạn nhỏ thích tính nhẩm' })).toBeVisible();
  await testInfo.attach('Profile and rank at 320 px', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Xem thành tích', exact: true }).click();
  await expect(page.getByText('Đạt Top 200 toàn hệ thống để lên Thách Đấu.')).toBeVisible();
  await page.getByRole('button', { name: 'Xem các bậc xếp hạng' }).click();
  await expect(page.getByText('Từ 162 sao và thuộc Top 200 toàn hệ thống')).toBeVisible();
  await testInfo.attach('Rank milestones at 320 px', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Đóng Các bậc xếp hạng' }).click();
  const board = page.getByRole('heading', { name: 'Bảng xếp hạng', exact: true });
  await board.scrollIntoViewIfNeeded();
  await expect(page.getByText('Bạn Sao 10', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Bạn Sao 11', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Xem thêm xếp hạng' }).click();
  await expect(page.getByText('Bạn Sao 11', { exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'Lớp 5A', exact: true }).click();
  await expect(page.getByText('Bạn Sao 2', { exact: true })).toBeVisible();
  await expect(page.getByText('Bạn Sao 3', { exact: true })).toHaveCount(0);
  await testInfo.attach('Class leaderboard at 320 px', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Toàn hệ thống', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Xem thêm xếp hạng' })).toBeVisible();
  await page.getByRole('tab', { name: 'Của em', exact: true }).click();
  await page.getByRole('button', { name: 'Trò chơi rèn luyện cho em' }).click();
  await expect(page.getByTestId('game-star-quest')).toBeVisible();
  const cards = page.getByTestId(/^training-card-/);
  await expect(cards).toHaveCount(5);
  await expect(page.getByRole('button', { name: /^Mở thử thách tính sao ·/ })).toHaveCount(5);
  for (const card of await cards.all()) {
    const box = await card.boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(320);
  }
  await testInfo.attach('Game icons at 320 px', { body: await page.screenshot(), contentType: 'image/png' });
  await page.getByTestId('game-star-quest').click();
  await expect(page.getByRole('heading', { name: 'Vượt 5 chặng tính nhẩm' })).toBeVisible();
  await page.getByRole('button', { name: 'Quay lại danh sách trò chơi' }).click();
  await expect(page.getByTestId('game-star-quest')).toBeVisible();
});

test('race challenge recovers a lost answer response and explains the reward limit', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  const id = 'race-fixture';
  let answered = 0;
  let retried = false;
  const payload = () => ({ id, question: answered, prompt: answered < 5 ? '3 × 4' : null,
    correct: answered, length: 5, completed: answered === 5, stars: 0, rewardStatus: answered === 5 ? 'GAME_LIMIT' : null });
  await page.route('**/api/v1/student/game-runs?mode=RACE_TO_FINISH', async route => {
    expect(route.request().method()).toBe('POST');
    await route.fulfill({ json: payload() });
  });
  await page.route('**/api/v1/student/game-runs/race-fixture/answers', async route => {
    const { question, answer } = route.request().postDataJSON();
    expect(answer).toBe(12);
    if (question === 0 && answered === 1) retried = true;
    else {
      expect(question).toBe(answered);
      answered++;
      if (answered === 1) return route.abort('connectionreset');
    }
    await route.fulfill({ json: payload() });
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/games`);
  await page.getByRole('button', { name: 'Mở thử thách tính sao · Đua Về Đích' }).click();
  await page.getByRole('button', { name: 'Bắt đầu hoặc học tiếp' }).click();
  const input = page.getByRole('textbox', { name: 'Đáp án' });
  const submit = page.getByRole('button', { name: 'Gửi đáp án', exact: true });
  await input.fill('12');
  await submit.click();
  await expect(input).not.toBeEditable();
  await page.getByRole('button', { name: 'Gửi lại đáp án', exact: true }).click();
  await expect(page.getByText('Chặng 2/5 · 1 câu đúng', { exact: true })).toBeVisible();
  expect(retried).toBe(true);
  for (let i = 1; i < 5; i++) {
    await input.fill('12');
    await submit.click();
    if (i < 4) await expect(page.getByText(`Chặng ${i + 2}/5 · ${i + 1} câu đúng`, { exact: true })).toBeVisible();
  }
  await expect(page.getByText('Hôm nay em đã nhận đủ sao từ các trò chơi. Ngày mai em có thể nhận thêm.')).toBeVisible();
  await testInfo.attach('Race challenge reward limit', { body: await page.screenshot(), contentType: 'image/png' });
});

test('all five games load their bundled artwork and enter gameplay', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  // This test changes the viewport itself. The orientation test covers the
  // fullscreen request, which can prevent Chromium from resizing the window.
  await page.addInitScript(() => {
    HTMLElement.prototype.requestFullscreen = async () => { throw new Error('Resize-controlled viewport'); };
  });
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('response', response => {
    if (response.status() >= 400 && /\/study\/(?:assets|_expo)\//.test(response.url())) {
      failures.push(`${response.status()} ${new URL(response.url()).pathname}`);
    }
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  const viewport = page.viewportSize();
  for (const [game, start] of [
    ['race-to-finish', 'start-race-button'],
    ['terrain-racing', null],
    ['energy-defense', null],
    ['planet-rescue', 'rescue-start'],
    ['block-island', null],
  ]) {
    if (viewport.height > viewport.width) {
      await page.setViewportSize(game === 'race-to-finish'
        ? { width: viewport.height, height: viewport.width } : viewport);
    }
    await page.goto(`${sites.portal.origin}/study/games/${game}`);
    await expect(page.getByTestId(`training-player-${game}`)).toBeVisible();
    if (start) {
      await expect(page.getByTestId(start)).toBeEnabled();
      await page.getByTestId(start).click();
      await expect(page.getByTestId(start)).toHaveCount(0);
    } else if (game === 'energy-defense') {
      await page.getByRole('button', { name: 'BẮT ĐẦU', exact: true }).click();
      await expect(page.getByTestId('energy-wave-count')).toBeVisible();
    } else if (game === 'block-island') {
      await page.getByRole('button', { name: 'Bắt đầu hành trình mới', exact: true }).click();
      await page.getByRole('button', { name: 'Xác nhận bắt đầu', exact: true }).click();
      await expect(page.getByTestId('island-material-items')).toBeVisible();
    } else {
      await expect(page.getByTestId('supercar-status')).toBeVisible();
    }
    await expect.poll(() => page.locator('img').evaluateAll(images =>
      images.filter(image => image.currentSrc && (!image.complete || image.naturalWidth === 0)).length,
    )).toBe(0);
    expect(failures).toEqual([]);
    await testInfo.attach(`${game} gameplay`, { body: await page.screenshot(), contentType: 'image/png' });
  }
});

test('each game opens with its own mobile display policy', async ({ page, app, isMobile }) => {
  test.skip(!isMobile, 'The web orientation request is for touch devices.');
  app.realStudent = true;
  await page.addInitScript(() => {
    const calls = [];
    window.gameDisplayCalls = calls;
    let fullscreen = null;
    Object.defineProperty(document, 'fullscreenElement', { get: () => fullscreen });
    HTMLElement.prototype.requestFullscreen = async function () { fullscreen = this; calls.push('fullscreen'); };
    document.exitFullscreen = async () => { fullscreen = null; calls.push('exit'); };
    screen.orientation.lock = async direction => { calls.push(direction); };
    screen.orientation.unlock = () => { calls.push('unlock'); };
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();

  for (const [game, selector, direction] of [
    ['race-to-finish', '[data-testid="race-setup-exit"]', 'landscape'],
    ['terrain-racing', '[data-testid^="supercar-state-"]', 'portrait'],
    ['energy-defense', '[data-testid="energy-mode-selection"]', 'portrait'],
    ['planet-rescue', '[data-testid="rescue-mode-select"]', null],
    ['block-island', '[data-testid="island-intro"]', null],
  ]) {
    await page.goto(`${sites.portal.origin}/study/games`);
    await page.getByTestId(`training-play-${game}`).click();
    await expect.poll(() => page.evaluate(() => window.gameDisplayCalls)).toEqual(direction ? ['fullscreen', direction] : []);
    await expect(page.getByRole('button', { name: 'Mở trò chơi toàn màn hình và xoay ngang' })).toHaveCount(direction === 'landscape' ? 1 : 0);
    if (game === 'race-to-finish') {
      const viewport = page.viewportSize();
      await expect(page.locator(selector)).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Về danh sách trò chơi' })).toBeVisible();
      await page.setViewportSize({ width: viewport.height, height: viewport.width });
      await expect(page.locator(selector)).toBeVisible();
      await page.setViewportSize(viewport);
      await expect(page.locator(selector)).toBeHidden();
      await page.setViewportSize({ width: viewport.height, height: viewport.width });
      await page.locator(selector).click();
      await expect(page.getByTestId(`training-play-${game}`)).toBeVisible();
      expect(await page.evaluate(() => window.gameDisplayCalls.slice(-2))).toEqual(['exit', 'unlock']);
      await page.setViewportSize(viewport);
    } else {
      await expect(page.locator(selector)).toBeVisible();
    }
  }
});

test('camera fallback opens the rear capture picker and sends the selected image to privacy review', async ({ page, app }) => {
  app.realStudent = true;
  await page.addInitScript(() => {
    const query = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = options => options.name === 'camera' ? Promise.resolve({ state: 'denied' }) : query(options);
    navigator.mediaDevices.getUserMedia = () => Promise.reject(new DOMException('Camera denied', 'NotAllowedError'));
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera`);
  await expect(page.getByText(/Chưa mở được máy ảnh/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Chụp ảnh bài toán' })).toBeDisabled();
  const [picker] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.getByRole('button', { name: 'Chụp bằng máy ảnh điện thoại' }).click(),
  ]);
  expect(await picker.element().getAttribute('capture')).toBe('environment');
  const png = await page.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 240;
    canvas.height = 160;
    return canvas.toDataURL().split(',')[1];
  });
  await picker.setFiles({ name: 'synthetic-math.png', mimeType: 'image/png', buffer: Buffer.from(png, 'base64') });
  await expect(page).toHaveURL(`${sites.portal.origin}/study/privacy`);
  await expect(page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư')).toBeVisible();
});

test('camera permission, live preview and shutter work with a simulated video stream', async ({ page, app }) => {
  app.realStudent = true;
  await page.addInitScript(() => {
    const query = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = options => options.name === 'camera' ? Promise.resolve({ state: 'prompt' }) : query(options);
    navigator.mediaDevices.getUserMedia = async () => {
      const canvas = document.createElement('canvas');
      canvas.width = 320;
      canvas.height = 240;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#c4ddff';
      ctx.fillRect(0, 0, 320, 240);
      return canvas.captureStream(15);
    };
  });
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/camera`);
  await page.getByRole('button', { name: 'Cho phép mở máy ảnh' }).click();
  const shutter = page.getByRole('button', { name: 'Chụp ảnh bài toán' });
  await expect(shutter).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Chụp bằng máy ảnh điện thoại' })).toHaveCount(0);
  await shutter.click();
  await expect(page).toHaveURL(`${sites.portal.origin}/study/privacy`);
  await expect(page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư')).toBeVisible();
});

test('Student calculator keeps simple answers compact and supports mixed numbers and exact unit conversion', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  // Complete the Portal -> Student handoff before starting another navigation.
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  // Calculator is independent of lesson generation; open it without a source draft.
  await page.goto(`${sites.portal.origin}/study/learning/math-guide`);
  await page.getByRole('button', { name: 'Mở máy tính bỏ túi', exact: true }).click();
  const expression = page.getByRole('textbox', { name: 'Phép tính', exact: true });
  await expression.fill('2+3');
  await page.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Xem cách tính', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Nhập hỗn số', exact: true }).click();
  await page.getByRole('textbox', { name: 'Phần nguyên hỗn số', exact: true }).fill('2');
  await page.getByRole('textbox', { name: 'Tử số hỗn số', exact: true }).fill('1');
  await page.getByRole('textbox', { name: 'Mẫu số hỗn số', exact: true }).fill('4');
  await page.getByRole('button', { name: 'Thêm hỗn số vào phép tính', exact: true }).click();
  await expect(expression).toHaveValue('2 1/4');
  await expression.fill('1/3+2/5');
  await page.getByRole('button', { name: 'Tính kết quả', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Xem cách tính', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Đổi đơn vị', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo cần đổi', exact: true }).fill('15');
  await page.getByRole('button', { name: 'Thêm số đo', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo thêm', exact: true }).fill('25');
  await page.getByRole('button', { name: 'Đơn vị đích: cm', exact: true }).click();
  await page.getByRole('button', { name: 'Chọn m', exact: true }).click();
  await page.getByRole('button', { name: 'Đổi đơn vị ngay', exact: true }).click();
  await expect(page.getByText('15,25 m', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Đổi diện tích', exact: true }).click();
  await page.getByRole('textbox', { name: 'Số đo cần đổi', exact: true }).fill('2');
  await page.getByRole('button', { name: 'Đổi đơn vị ngay', exact: true }).click();
  await expect(page.getByText('200 dm²', { exact: true })).toBeVisible();
  await page.screenshot({ path: `.local-artifacts/dependency-setup-20261107/calculator-conversion-${test.info().project.name}.png` });
  await page.getByRole('button', { name: 'Tính toán', exact: true }).click();
  await expect(expression).toHaveValue('1/3+2/5');
  await page.getByRole('button', { name: 'Đóng máy tính', exact: true }).click();
  await expect(expression).toHaveCount(0);
});
