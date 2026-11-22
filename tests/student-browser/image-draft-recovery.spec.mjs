import { test, expect, sites, login } from '../browser/fixtures.mjs';

async function picture(page, name = 'synthetic.png', mimeType = 'image/png', width = 800, height = 600) {
  const base64 = await page.evaluate(({ mimeType, width, height }) => {
    const canvas = document.createElement('canvas');
    canvas.width = width; canvas.height = height;
    const context = canvas.getContext('2d');
    context.fillStyle = '#fff'; context.fillRect(0, 0, width, height);
    context.fillStyle = '#f00'; context.fillRect(width * 0.1, height * 0.1, width * 0.25, height * 0.2);
    context.fillStyle = '#00f'; context.fillRect(width * 0.625, height * 0.6, width * 0.225, height * 0.25);
    return canvas.toDataURL(mimeType).split(',')[1];
  }, { mimeType, width, height });
  return { name, mimeType, buffer: Buffer.from(base64, 'base64') };
}

async function openPrivacy(page, file, mode = 'ARITHMETIC') {
  await page.goto(`${sites.portal.origin}/study/camera?mode=${mode}`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh từ thư viện', exact: true }).click();
  await (await chooser).setFiles(file || await picture(page));
  const photo = page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư');
  await expect(photo).toBeVisible();
  return photo;
}
async function openCrop(page, { masks = true, file, mode = 'ARITHMETIC' } = {}) {
  const photo = await openPrivacy(page, file, mode);
  if (masks) {
    for (const [x, y, right, bottom] of [[0.08, 0.08, 0.4, 0.35], [0.6, 0.55, 0.9, 0.9]]) {
      const box = await photo.boundingBox();
      await page.mouse.move(box.x + box.width * x, box.y + box.height * y);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width * right, box.y + box.height * bottom, { steps: 4 });
      await page.mouse.up();
    }
  }
  await page.getByRole('checkbox', { name: 'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh' }).click();
  await page.getByRole('button', { name: 'Tiếp tục xem lại', exact: true }).click();
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
}

async function maskedPixels(page) {
  return page.getByLabel('Ảnh bài tập đang căn chỉnh').evaluate(async element => {
    const image = element instanceof HTMLImageElement ? element : element.querySelector('img');
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
    const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0);
    return [[0.2, 0.2], [0.75, 0.7]].map(([x, y]) => [...ctx.getImageData(x * canvas.width, y * canvas.height, 1, 1).data].slice(0, 3));
  });
}

test('F5 restores the approved photo and both baked privacy masks', async ({ page, app }, testInfo) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await openCrop(page);
  expect((await maskedPixels(page)).flat().every(channel => channel < 24)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('before-refresh.png') });
  await page.reload();
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
  expect((await maskedPixels(page)).flat().every(channel => channel < 24)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('after-refresh.png') });
  expect(app.requests.filter(request => request.method === 'POST' && request.path !== '/student/app-usage/heartbeat')
    .map(request => request.path)).toEqual(['/auth/login']);
});

test('An empty crop opens a real image picker instead of navigating back', async ({ page, app }) => {
  app.realStudent = true;
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(`${sites.portal.origin}/study/crop`);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn lại ảnh', exact: true }).click();
  await (await chooser).setFiles(await picture(page));
  await expect(page).toHaveURL(/\/study\/privacy/);
  await expect(page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư')).toBeVisible();
});

test.beforeEach(async ({ app }) => { app.realStudent = true; });

async function start(page) {
  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
}
async function edges(page) {
  return Promise.all(['trái', 'phải', 'trên', 'dưới'].map(async edge => {
    const box = await page.getByLabel(`Kéo cạnh ${edge}`, { exact: true }).boundingBox();
    return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  }));
}
async function imageHash(page, label) {
  return page.getByLabel(label).evaluate(async element => {
    const image = element instanceof HTMLImageElement ? element : element.querySelector('img');
    const data = await (await fetch(image.src)).arrayBuffer();
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data))).join(',');
  });
}
async function storage(page, operation = 'read') {
  return page.evaluate(operation => new Promise((resolve, reject) => {
    const open = indexedDB.open('mathvision-private-photo-v1', 1);
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result, tx = db.transaction(['drafts', 'images'], operation === 'read' ? 'readonly' : 'readwrite');
      const request = tx.objectStore('drafts').getAll();
      let rows, pictures;
      request.onsuccess = () => {
        rows = request.result;
        for (const row of rows) {
          if (operation === 'expire') tx.objectStore('drafts').put({ ...row, expiresAt: Date.now() - 1000 }, row.scope);
          if (operation === 'corrupt') tx.objectStore('images').put({ privacy: new Blob(['broken'], { type: 'image/jpeg' }) }, row.scope);
        }
      };
      const blobs = tx.objectStore('images').getAll(); blobs.onsuccess = () => { pictures = blobs.result; };
      tx.oncomplete = () => { db.close(); resolve({ rows, imageCount: pictures.length,
        hasOnlyBlobs: pictures.every(image => image.privacy instanceof Blob && (!image.cropped || image.cropped instanceof Blob)) }); };
      tx.onerror = () => { db.close(); reject(tx.error); };
    };
  }), operation);
}

test('Crop edges, quarter turn and fine angle survive an immediate real reload', async ({ page }, testInfo) => {
  await start(page); await openCrop(page);
  await page.getByRole('button', { name: 'Thu hẹp từ cạnh trái', exact: true }).click();
  await page.getByRole('button', { name: 'Xoay ảnh 90 độ', exact: true }).click();
  const angle = page.getByRole('slider', { name: 'Góc căn thẳng ảnh', exact: true });
  await angle.focus(); await angle.press('ArrowRight');
  await expect(angle).toHaveValue('0.1');
  const before = await edges(page);
  const transform = await page.getByLabel('Ảnh bài tập đang căn chỉnh').evaluate(image => getComputedStyle(image).transform);
  await page.reload();
  await expect(angle).toHaveValue('0.1');
  await expect.poll(() => page.getByLabel('Ảnh bài tập đang căn chỉnh').evaluate(image => getComputedStyle(image).transform)).toBe(transform);
  await expect.poll(async () => (await edges(page)).every((point, i) => Math.abs(point.x - before[i].x) < 3 && Math.abs(point.y - before[i].y) < 3)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('crop-angle-restored.png') });
});

test('Preview reload preserves the cropped bytes and a second reload keeps baked masks', async ({ page }) => {
  await start(page); await openCrop(page);
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  const hash = await imageHash(page, 'Ảnh bài toán em đã chọn');
  await page.reload();
  await expect(page.getByLabel('Ảnh bài toán em đã chọn')).toBeVisible();
  expect(await imageHash(page, 'Ảnh bài toán em đã chọn')).toBe(hash);
  await page.getByRole('button', { name: 'Chỉnh lại vùng bài toán', exact: true }).click();
  await expect(page).toHaveURL(/\/study\/crop(?:\?|$)/);
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
  await page.reload();
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
  expect((await maskedPixels(page)).flat().every(channel => channel < 24)).toBe(true);
});

test('The unapproved original is stored only as a short-lived privacy draft', async ({ page, app }) => {
  await start(page); await openPrivacy(page);
  const pending = await storage(page);
  expect(pending.imageCount).toBe(1);
  expect(pending.hasOnlyBlobs).toBe(false);
  const [record] = pending.rows;
  expect(record.step).toBe('privacy');
  expect(record.expiresAt - record.createdAt).toBe(30000);
  await page.reload();
  await expect(page.getByLabel('Ảnh gốc để kiểm tra thông tin riêng tư')).toBeVisible();
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  // The fixture checks that usage heartbeats contain only connection state.
  expect(app.requests.filter(request => request.method === 'POST' && request.path !== '/student/app-usage/heartbeat')
    .map(request => request.path)).toEqual(['/auth/login']);
});

test('Only approved Blob data and URI-free metadata are stored', async ({ page }) => {
  await start(page); await openCrop(page);
  const stored = await storage(page);
  expect(stored.imageCount).toBe(1); expect(stored.hasOnlyBlobs).toBe(true);
  expect(JSON.stringify(stored.rows)).not.toMatch(/blob:|data:image|originalImageUri|rawUri/);
  const pixel = await page.evaluate(() => new Promise((resolve, reject) => {
    const open = indexedDB.open('mathvision-private-photo-v1');
    open.onsuccess = () => {
      const db = open.result, request = db.transaction('images').objectStore('images').getAll();
      request.onsuccess = async () => {
        const uri = URL.createObjectURL(request.result[0].privacy);
        try {
          const photo = new Image(); photo.src = uri; await photo.decode();
          const canvas = document.createElement('canvas'); canvas.width = photo.width; canvas.height = photo.height;
          const ctx = canvas.getContext('2d'); ctx.drawImage(photo, 0, 0);
          resolve([...ctx.getImageData(photo.width * 0.2, photo.height * 0.2, 1, 1).data].slice(0, 3));
        } catch (error) { reject(error); } finally { URL.revokeObjectURL(uri); db.close(); }
      };
    };
  }));
  expect(pixel.every(channel => channel < 24)).toBe(true);
});

for (const [operation, message] of [['expire', 'Ảnh đã hết thời gian lưu tạm. Em chọn lại ảnh để tiếp tục nhé.'],
  ['corrupt', 'Ảnh lưu tạm không còn mở được. Em chọn lại ảnh nhé.']]) {
  test(`${operation} draft has a working recovery path and is cleaned up`, async ({ page }) => {
    await start(page); await openCrop(page);
    await storage(page, operation); await page.reload();
    await expect(page.getByText(message, { exact: true })).toBeVisible();
    expect((await storage(page)).imageCount).toBe(0);
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Chọn lại ảnh', exact: true }).click();
    await (await chooser).setFiles(await picture(page));
    await expect(page).toHaveURL(/\/study\/privacy/);
  });
}

test('Cancel and reselecting the same file preserve the old draft until a new source is decoded', async ({ page }) => {
  await start(page); await openCrop(page);
  const hash = await imageHash(page, 'Ảnh bài tập đang căn chỉnh');
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh khác', exact: true }).click();
  await chooser;
  await page.getByLabel('Chọn ảnh bài tập', { exact: true }).dispatchEvent('cancel');
  expect(await imageHash(page, 'Ảnh bài tập đang căn chỉnh')).toBe(hash);
  const next = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh khác', exact: true }).click();
  await (await next).setFiles(await picture(page));
  await expect(page).toHaveURL(/\/study\/privacy/);
  await expect(page.getByRole('checkbox')).not.toBeChecked();
  const pending = await storage(page);
  expect(pending.imageCount).toBe(1);
  expect(pending.rows[0].step).toBe('privacy');
  expect(pending.hasOnlyBlobs).toBe(false);
});

test('A reopened tab restores the approved photo when the browser restores the same verified session', async ({ page, context }) => {
  await start(page); await openCrop(page);
  const session = await page.evaluate(() => Object.entries(sessionStorage));
  const hash = await imageHash(page, 'Ảnh bài tập đang căn chỉnh');
  await page.close();
  const reopened = await context.newPage();
  // Reopening a closed tab restores sessionStorage in browsers. Restore that
  // synthetic auth snapshot; /me is still verified on the new document.
  await reopened.addInitScript(entries => { for (const [key, value] of entries) sessionStorage.setItem(key, value); }, session);
  await reopened.goto(`${sites.portal.origin}/study/crop`);
  await expect(reopened.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
  expect(await imageHash(reopened, 'Ảnh bài tập đang căn chỉnh')).toBe(hash);
  await reopened.close();
});

test('An EXIF-oriented JPEG is normalized and retains its orientation after F5', async ({ page }) => {
  await start(page);
  const file = await picture(page, 'portrait-exif.jpeg', 'image/jpeg', 600, 800);
  const exif = Buffer.from('ffe1002245786966000049492a0008000000010012010300010000000600000000000000', 'hex');
  file.buffer = Buffer.concat([file.buffer.subarray(0, 2), exif, file.buffer.subarray(2)]);
  await openCrop(page, { file, masks: false });
  const size = () => page.getByLabel('Ảnh bài tập đang căn chỉnh').evaluate(element => {
    const image = element instanceof HTMLImageElement ? element : element.querySelector('img');
    return [image.naturalWidth, image.naturalHeight];
  });
  await expect.poll(size).toEqual([800, 600]);
  await page.reload(); await expect.poll(size).toEqual([800, 600]);
});

test('Rapid repeated picks open one chooser and a failed decode leaves the approved draft intact', async ({ page }) => {
  await start(page); await openCrop(page);
  const hash = await imageHash(page, 'Ảnh bài tập đang căn chỉnh');
  let count = 0; page.on('filechooser', () => count++);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Chọn ảnh khác', exact: true }).dblclick();
  await (await chooser).setFiles({ name: 'broken.heic', mimeType: 'image/heic', buffer: Buffer.from('not a photo') });
  await expect(page.getByRole('alert')).toContainText('Ảnh trước vẫn được giữ');
  expect(count).toBe(1);
  expect(await imageHash(page, 'Ảnh bài tập đang căn chỉnh')).toBe(hash);
  await page.reload(); await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
  expect(await imageHash(page, 'Ảnh bài tập đang căn chỉnh')).toBe(hash);
});

test('Editing changes metadata without rewriting photo blobs', async ({ page }) => {
  await page.addInitScript(() => {
    window.photoBlobWrites = 0;
    const put = IDBObjectStore.prototype.put;
    IDBObjectStore.prototype.put = function (...args) { if (this.name === 'images') window.photoBlobWrites++; return put.apply(this, args); };
  });
  await start(page); await openCrop(page);
  const before = await page.evaluate(() => window.photoBlobWrites);
  for (let i = 0; i < 5; i++) await page.getByRole('button', { name: 'Thu hẹp từ cạnh trái', exact: true }).click();
  expect(await page.evaluate(() => window.photoBlobWrites)).toBe(before);
});

test('A stale edit journal from another image revision cannot rotate the restored image', async ({ page }) => {
  await start(page); await openCrop(page);
  const angle = page.getByRole('slider', { name: 'Góc căn thẳng ảnh', exact: true });
  await angle.focus(); await angle.press('ArrowRight');
  await page.evaluate(() => {
    const key = 'mathvision-photo-edit-v1', edit = JSON.parse(localStorage.getItem(key));
    edit.imageRevision = 'another-image'; edit.cropEdit.fine = 37;
    localStorage.setItem(key, JSON.stringify(edit));
  });
  await page.reload(); await expect(angle).toHaveValue('0.1');
});

test('Delayed auth hydration never shows a premature missing-photo state', async ({ page }) => {
  await start(page); await openCrop(page);
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/v1/me', async route => { await gate; await route.fallback(); });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Đang xác minh tài khoản…', { exact: true })).toBeVisible();
  await expect(page.getByText('Chưa mở được ảnh bài tập', { exact: true })).toHaveCount(0);
  release();
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
});

test('A different verified account cannot restore the previous pupil photo', async ({ page }) => {
  await start(page); await openCrop(page);
  await page.route('**/api/v1/me', route => route.fulfill({ json: {
    userId: '550e8400-e29b-41d4-a716-446655440001', role: 'STUDENT', active: true, displayName: 'Bạn khác', gradeLevel: 5,
  } }));
  await page.reload();
  await expect(page.getByRole('button', { name: 'Chọn lại ảnh', exact: true })).toBeVisible();
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toHaveCount(0);
});

test('Logout removes image data and revisiting crop cannot display it', async ({ page }) => {
  await start(page); await openCrop(page);
  await page.goto(`${sites.portal.origin}/study/account`);
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
  await page.getByRole('button', { name: 'Xác nhận đăng xuất', exact: true }).click();
  await expect(page).toHaveURL(`${sites.portal.origin}/`);
  await expect.poll(async () => (await storage(page)).imageCount).toBe(0);
  await page.goto(`${sites.portal.origin}/study/crop`);
  await expect(page).toHaveURL(`${sites.portal.origin}/login`);
  await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toHaveCount(0);
});

test('Unavailable IndexedDB leaves a usable picker and an honest persistence warning', async ({ page }) => {
  await page.addInitScript(() => { IDBFactory.prototype.open = () => { throw new DOMException('Storage blocked', 'SecurityError'); }; });
  await start(page); await openCrop(page, { masks: false });
  await expect(page.getByText('Chưa lưu được ảnh trên thiết bị. Em vẫn có thể làm tiếp; tải lại trang có thể làm mất ảnh.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Chọn lại ảnh', exact: true })).toBeVisible();
  await expect(page.getByText('Đang khôi phục ảnh của em...', { exact: true })).toHaveCount(0);
});

for (const [name, type, width, height] of [['photo.jpg', 'image/jpeg', 800, 600], ['photo.jpeg', 'image/jpeg', 600, 800],
  ['photo.webp', 'image/webp', 800, 600], ['large.png', 'image/png', 4000, 3000]]) {
  test(`${name} survives crop reload without losing its approved image`, async ({ page }) => {
    await start(page);
    await openCrop(page, { file: await picture(page, name, type, width, height), masks: false });
    const hash = await imageHash(page, 'Ảnh bài tập đang căn chỉnh');
    await page.reload(); await expect(page.getByLabel('Ảnh bài tập đang căn chỉnh')).toBeVisible();
    expect(await imageHash(page, 'Ảnh bài tập đang căn chỉnh')).toBe(hash);
  });
}

test('After reload the upload uses baked masked pixels and terminal completion deletes the draft', async ({ page, app }) => {
  let received;
  const response = { submissionId: 'recovered-photo', status: 'FEEDBACK_READY', validation: { diagnosisState: 'VALID', isValid: true },
    studentFeedback: { title: 'Bài làm đúng', hint: 'Em đã tính đúng.' } };
  app.responses.set('POST /student/submissions', ({ route, json }) => { received = route.request().postDataBuffer(); return json(response, 201); });
  app.responses.set('GET /student/submissions/recovered-photo', ({ json }) => json(response));
  await start(page); await openCrop(page);
  await page.reload();
  await page.getByRole('button', { name: 'Dùng toàn ảnh', exact: true }).click();
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  await page.getByRole('button', { name: 'KIỂM TRA BÀI TOÁN', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Bài làm đúng', level: 2, exact: true })).toBeVisible();
  const jpegStart = received.indexOf(Buffer.from([0xff, 0xd8, 0xff]));
  const jpegEnd = received.lastIndexOf(Buffer.from([0xff, 0xd9])) + 2;
  expect(jpegStart).toBeGreaterThan(0); expect(jpegEnd).toBeGreaterThan(jpegStart);
  const pixels = await page.evaluate(async bytes => {
    const uri = URL.createObjectURL(new Blob([new Uint8Array(bytes)], { type: 'image/jpeg' }));
    try {
      const image = new Image(); image.src = uri; await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
      const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0);
      return [[0.2, 0.2], [0.75, 0.7]].flatMap(([x, y]) => [...ctx.getImageData(x * canvas.width, y * canvas.height, 1, 1).data].slice(0, 3));
    } finally { URL.revokeObjectURL(uri); }
  }, [...received.subarray(jpegStart, jpegEnd)]);
  expect(pixels.every(channel => channel < 24)).toBe(true);
  await expect.poll(async () => (await storage(page)).imageCount).toBe(0);
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/student/submissions')).toHaveLength(1);
});

test('Reload after a lost upload response never automatically submits the same photo again', async ({ page, app }) => {
  app.responses.set('POST /student/submissions', ({ route }) => route.abort('failed'));
  await start(page); await openCrop(page, { masks: false });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  await page.getByRole('button', { name: 'KIỂM TRA BÀI TOÁN', exact: true }).click();
  await expect(page.getByText('Chưa có kết quả', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Xem lại ảnh', exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/student/submissions')).toHaveLength(1);
  await page.getByRole('button', { name: 'Xem lại ảnh', exact: true }).click();
  await expect(page.getByLabel('Ảnh bài toán em đã chọn')).toBeVisible();
});

test('Reloaded crop continues through photo reading and a correct Work Review result', async ({ page, app }) => {
  const problemText = 'Một giỏ có 30 kg táo, đã bán 15 kg. Hỏi còn lại bao nhiêu kg táo?';
  const work = '30 - 15 = 15 (kg)';
  app.responses.set('POST /student/tutor/inspect', ({ json }) => json({ kind: 'MIXED', problemText, needsProblem: false,
    lines: [{ text: work, uncertain: false, box: null }] }));
  app.responses.set('POST /student/tutor/work-review', ({ body, json }) => json({ sourceId: body.sourceId,
    status: 'CORRECT', summary: 'Em đã trả lời câu hỏi.', praise: 'Em tính đúng rồi.', nextAction: 'Em giữ cách làm này nhé.', alternative: '',
    complete: true, completionVersion: 2, missingParts: [], arithmeticVerified: true,
    rows: [{ lineIndex: 0, sourceText: work, status: 'OK', errorKind: 'NONE', rowKind: 'CALCULATION', arithmeticCorrect: true,
      feedback: 'Phép tính đúng.', hints: [] }] }));
  app.responses.set('POST /student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  app.responses.set('POST /student/quizzes/from-learning', ({ json }) => json({ offered: false, quiz: null }));
  await start(page); await openCrop(page, { mode: 'MATH_TUTOR' });
  await page.reload();
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  await page.getByRole('button', { name: 'Bài đã làm', exact: true }).click();
  const result = page.getByText('Em làm đúng rồi!', { exact: true });
  await expect(result).toBeVisible();
  await page.reload();
  await expect(result).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/inspect')).toHaveLength(1);
  expect(app.requests.filter(request => request.path === '/student/tutor/work-review')).toHaveLength(1);
});

test('A known submission resumes by GET after reload without uploading again', async ({ page, app }) => {
  let completed = false;
  const pending = { submissionId: 'resume-photo', status: 'PROCESSING' };
  app.responses.set('POST /student/submissions', ({ json }) => json(pending, 201));
  app.responses.set('GET /student/submissions/resume-photo', ({ json }) => json(completed ? { ...pending, status: 'FEEDBACK_READY',
    validation: { diagnosisState: 'VALID', isValid: true }, studentFeedback: { title: 'Bài làm đúng', hint: 'Em tính đúng.' } } : pending));
  await start(page); await openCrop(page, { masks: false });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  await page.getByRole('button', { name: 'KIỂM TRA BÀI TOÁN', exact: true }).click();
  await expect.poll(async () => (await storage(page)).rows[0]?.meta.arithmeticSubmissionId).toBe('resume-photo');
  completed = true; await page.reload();
  await expect(page.getByRole('heading', { name: 'Bài làm đúng', level: 2, exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.method === 'POST' && request.path === '/student/submissions')).toHaveLength(1);
  expect(app.requests.some(request => request.method === 'GET' && request.path === '/student/submissions/resume-photo')).toBe(true);
});

test('Math Guide keeps the recognized problem and masked preview after F5', async ({ page, app }) => {
  const problemText = 'Lan có 12 viên bi, Minh cho Lan thêm 3 viên. Hỏi Lan có bao nhiêu viên bi?';
  app.responses.set('POST /student/tutor/inspect', ({ json }) =>
    json({ kind: 'PROBLEM', problemText, lines: [], needsProblem: false }));
  app.responses.set('POST /student/tutor/lesson/prepare', ({ json }) => json({ phase: 'ready' }));
  await start(page);
  await openCrop(page, { masks: false, mode: 'MATH_TUTOR' });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  const confirmation = page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' });
  await expect(confirmation).toBeVisible();
  await expect(page.getByLabel('Ảnh đề bài đã che thông tin')).toBeVisible();
  await page.reload();
  await expect(confirmation).toBeVisible();
  await expect(page.getByLabel('Ảnh đề bài đã che thông tin')).toBeVisible();
  await expect(page.getByText(/Lan có 12 viên bi/).first()).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/inspect')).toHaveLength(1);
});

test('Interrupted tutor photo reading requires explicit continuation after F5', async ({ page, app }) => {
  app.responses.set('POST /student/tutor/inspect', ({ route }) => route.abort('failed'));
  await start(page); await openCrop(page, { masks: false, mode: 'MATH_TUTOR' });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  await expect.poll(() => app.requests.filter(request => request.path === '/student/tutor/inspect').length).toBe(1);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Tiếp tục đọc ảnh', exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === '/student/tutor/inspect')).toHaveLength(1);
  await page.getByRole('button', { name: 'Tiếp tục đọc ảnh', exact: true }).click();
  await expect.poll(() => app.requests.filter(request => request.path === '/student/tutor/inspect').length).toBe(2);
});

test('A quota failure is reported without claiming the photo was saved', async ({ page }) => {
  await start(page);
  await page.evaluate(() => {
    const put = IDBObjectStore.prototype.put;
    IDBObjectStore.prototype.put = function (...args) {
      if (this.name === 'images') throw new DOMException('Storage full', 'QuotaExceededError');
      return put.apply(this, args);
    };
  });
  // Navigating to camera would reset the injected fault, so install it for each new document too.
  await page.addInitScript(() => {
    const put = IDBObjectStore.prototype.put;
    IDBObjectStore.prototype.put = function (...args) {
      if (this.name === 'images') throw new DOMException('Storage full', 'QuotaExceededError');
      return put.apply(this, args);
    };
  });
  await openCrop(page, { masks: false });
  await expect(page.getByText('Chưa lưu được ảnh trên thiết bị. Em vẫn có thể làm tiếp; tải lại trang có thể làm mất ảnh.', { exact: true })).toBeVisible();
  expect((await storage(page)).imageCount).toBe(0);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Chọn lại ảnh', exact: true })).toBeVisible();
});

test('Interrupted tutor photo recovery can switch to typed input without sending the image again', async ({ page, app }) => {
  app.responses.set('POST /student/tutor/inspect', ({ route }) => route.abort('failed'));
  await start(page);
  await openCrop(page, { masks: false, mode: 'MATH_TUTOR' });
  await page.getByRole('button', { name: 'Xác nhận cắt ảnh', exact: true }).click();
  const inspectRequests = () => app.requests.filter(request => request.path === '/student/tutor/inspect').length;
  await expect.poll(inspectRequests).toBe(1);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Tiếp tục đọc ảnh', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Nhập đề bằng chữ', exact: true }).click();
  await expect(page.getByPlaceholder('Nhập nội dung ở đây nhé…', { exact: true })).toBeVisible();
  expect(inspectRequests()).toBe(1);
});

test('F5 before privacy confirmation recovers the image and mask until the 30 second deadline', async ({ page }) => {
  await start(page);
  const photo = await openPrivacy(page, undefined, 'MATH_TUTOR');
  const box = await photo.boundingBox();
  await page.mouse.move(box.x + box.width * .15, box.y + box.height * .15);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width * .45, box.y + box.height * .38, { steps: 5 });
  await page.mouse.up();
  const undo = page.getByRole('button', { name: 'Hoàn tác vùng che vừa vẽ' });
  await expect(undo).toBeVisible();
  const temporary = (await storage(page)).rows[0];
  expect(temporary?.step).toBe('privacy');
  expect(temporary.expiresAt - temporary.createdAt).toBe(30000);

  await page.reload();
  await expect(photo).toBeVisible();
  await expect(undo).toBeVisible();
  await expect(page.getByRole('checkbox')).not.toBeChecked();

  await storage(page, 'expire');
  await page.reload();
  await expect(page).toHaveURL(/\/study\/camera\?mode=MATH_TUTOR/);
  await expect(page.getByRole('button', { name: 'Chọn ảnh từ thư viện' })).toBeVisible();
  expect((await storage(page)).imageCount).toBe(0);
});
