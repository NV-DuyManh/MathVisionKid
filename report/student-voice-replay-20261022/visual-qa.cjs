const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root = __dirname, base = 'http://127.0.0.1:8093/study';
const problem = 'Lan có 36 bút, mẹ cho thêm 27 bút. Hỏi Lan có tất cả bao nhiêu bút?';
const explanation = ['Mình gộp hai nhóm bút để tìm số bút của Lan.', 'Em đặt các chữ số thẳng hàng.', 'Cộng hàng đơn vị trước rồi cộng hàng chục nhé.'];
const lesson = { sessionId: 'voice-replay-session-00001', revision: 0, topic: 'Phép cộng', goal: 'Tìm số bút', feedback: '', outline: ['Hiểu đề', 'Cộng số bút', 'Kiểm tra lại'], stepIndex: 0, completed: [], status: 'READY', understandingSteps: 0, step: { kind: 'MATH', title: 'Tính số bút của Lan', explanation: explanation[0], guidance: explanation.slice(1), question: 'Lan có tất cả bao nhiêu bút?', choices: [], expression: '36 + 27', unit: 'bút', workExcerpt: '' } };
(async () => {
  fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  const rows = [], errors = [], evidence = {};
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, permissions: ['microphone'], reducedMotion: 'reduce' });
    await context.addInitScript(() => {
      sessionStorage.setItem('portal_access_token', 'voice-replay-fixture');
      window.__spoken = []; window.__audio = [];
      window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
      Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: { getVoices: () => [{ voiceURI: 'vi-fixture', name: 'HoaiMy Natural', lang: 'vi-VN' }], speak: item => window.__spoken.push(item), cancel: () => {}, addEventListener: () => {}, removeEventListener: () => {} } });
      const NativeAudio = window.Audio;
      window.Audio = function (...args) { const element = new NativeAudio(...args); window.__audio.push(element); return element; };
      window.Audio.prototype = NativeAudio.prototype;
    });
    let asks = 0, transcriptions = 0;
    await context.route('**/api/v1/**', route => {
      const url = route.request().url(); let data = { id: 'voice-pupil', name: 'Minh', role: 'STUDENT', grade: 4 };
      if (url.endsWith('/tutor/lesson')) data = lesson;
      if (url.includes('transcribe')) { transcriptions++; data = { text: 'Vì sao cộng hàng đơn vị trước?' }; }
      if (url.endsWith('/tutor/lesson/ask')) { asks++; data = { answer: 'Em bắt đầu từ hàng đơn vị để biết có cần nhớ sang hàng chục không.', spokenExplanation: 'Em nhìn hàng đơn vị trước nhé. Nếu gộp được một chục, em nhớ một sang hàng chục. Sau đó em cộng hàng chục và phần nhớ.', followUp: 'Hàng đơn vị của hai số là những chữ số nào?', guarded: false }; }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    });
    const page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
    async function capture(name) {
      await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(100);
      const metrics = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, overflow: document.documentElement.scrollWidth > innerWidth + 1, broken: [...document.images].filter(i => i.complete && !i.naturalWidth).length,
        outside: [...document.querySelectorAll('[role=button]')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && r.bottom > 0 && r.top < innerHeight && (r.left < -1 || r.right > innerWidth + 1); }).map(e => e.getAttribute('aria-label')) }));
      assert(!metrics.overflow && !metrics.broken && !metrics.outside.length, JSON.stringify(metrics));
      rows.push({ name, ...metrics }); await page.screenshot({ path: path.join(root, 'screenshots', `${name}-${metrics.width}.png`) });
    }
    async function done() { await page.evaluate(() => window.__spoken.at(-1).onend()); }
    for (const [width, height] of [[320, 740], [390, 844], [768, 1024], [1440, 1000], [844, 390]]) {
      await page.setViewportSize({ width, height });
      await page.goto(base + '/learning/math-guide?problemText=' + encodeURIComponent(problem));
      await page.getByRole('checkbox').click(); await page.getByRole('button', { name: 'Bắt đầu từng bước', exact: true }).click();
      await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
      await page.getByRole('button', { name: 'Nghe giảng kỹ hơn', exact: true }).waitFor(); await capture('listening');
      await page.getByRole('button', { name: 'Nghe giảng kỹ hơn', exact: true }).click(); await done();
      const second = await page.evaluate(() => window.__spoken.at(-1).text);
      await page.getByRole('button', { name: 'Tạm dừng lời giảng', exact: true }).click();
      await page.getByRole('button', { name: 'Nghe tiếp lời giảng', exact: true }).click();
      assert.equal(await page.evaluate(() => window.__spoken.at(-1).text), second);
      await page.getByRole('button', { name: 'Nghe ý trước', exact: true }).click();
      assert.equal(await page.evaluate(() => window.__spoken.at(-1).text), explanation[0]);
      for (let i = 0; i < 4; i++) await done();
      await page.getByRole('button', { name: 'Nghe lại lời giảng', exact: true }).waitFor();
      await page.getByRole('button', { name: 'Các ý đã nghe', exact: true }).click(); await capture('heard-ideas');
      await page.getByRole('button', { name: 'Nghe lại ý 2', exact: true }).click();
      assert.equal(await page.evaluate(() => window.__spoken.at(-1).text), explanation[1]);
      await page.getByRole('button', { name: 'Đóng Nghe giảng', exact: true }).click();
      await page.getByRole('button', { name: 'Hỏi bài', exact: true }).click(); await capture('question');
      await page.getByRole('button', { name: 'Ghi âm câu hỏi', exact: true }).click();
      await page.getByRole('button', { name: 'Nói xong', exact: true }).waitFor(); await page.waitForTimeout(2200);
      assert.equal(await page.getByRole('button', { name: 'Đồng ý và ghi âm', exact: true }).count(), 0);
      await page.getByRole('button', { name: 'Nói xong', exact: true }).click();
      await page.getByRole('button', { name: 'Nghe lại câu hỏi vừa nói', exact: true }).waitFor();
      await page.getByRole('button', { name: 'Nghe lại câu hỏi vừa nói', exact: true }).click();
      await page.getByRole('button', { name: 'Tạm dừng bản ghi', exact: true }).waitFor(); await page.waitForTimeout(300);
      await page.getByRole('button', { name: 'Tạm dừng bản ghi', exact: true }).click();
      const track = await page.getByRole('button', { name: 'Chọn vị trí nghe trong bản ghi', exact: true }).boundingBox();
      await page.mouse.click(track.x + track.width / 2, track.y + track.height / 2);
      try { await page.waitForFunction(() => window.__audio.at(-1).currentTime > .25, null, { timeout: 2000 }); }
      catch (error) { console.error(await page.evaluate(() => ({ audio: window.__audio.map(e => ({ time: e.currentTime, duration: e.duration, src: e.src, error: e.error?.message })), text: document.body.innerText }))); throw error; }
      await page.getByRole('button', { name: 'Lùi bản ghi 5 giây', exact: true }).click();
      const audio = await page.evaluate(() => ({ time: window.__audio.at(-1).currentTime, paused: window.__audio.at(-1).paused, src: window.__audio.at(-1).src.startsWith('blob:') }));
      assert(audio.time < .1 && audio.paused && audio.src); await capture('recording-replay');
      await page.getByRole('button', { name: 'Nghe lại câu hỏi vừa nói', exact: true }).click();
      await page.waitForFunction(() => window.__audio.at(-1).ended);
      await page.getByRole('button', { name: 'Nghe lại câu hỏi vừa nói', exact: true }).click();
      await page.getByRole('button', { name: 'Tạm dừng bản ghi', exact: true }).waitFor();
      const restarted = await page.evaluate(() => ({ time: window.__audio.at(-1).currentTime, duration: window.__audio.at(-1).duration, ended: window.__audio.at(-1).ended, paused: window.__audio.at(-1).paused }));
      assert(!restarted.ended && restarted.time < restarted.duration - .25, JSON.stringify({ width, restarted }));
      await page.getByRole('button', { name: 'Tạm dừng bản ghi', exact: true }).click();
      const before = asks; await page.getByRole('button', { name: 'Gửi câu hỏi', exact: true }).click();
      await page.getByRole('button', { name: 'Nghe giải thích', exact: true }).waitFor(); assert.equal(asks, before + 1);
      await page.getByRole('button', { name: 'Nghe giải thích', exact: true }).click();
      for (let i = 0; i < 4; i++) await done();
      await page.getByRole('button', { name: 'Nghe lại giải thích', exact: true }).waitFor();
      await page.getByRole('button', { name: 'Nghe lại từ đầu', exact: true }).click(); assert.equal(asks, before + 1);
      await page.getByRole('button', { name: 'Tạm dừng lời giảng', exact: true }).click(); await capture('reply-replay');
      await page.getByRole('button', { name: 'Đóng Hỏi bài', exact: true }).click();
    }
    evidence.asks = asks; evidence.transcriptions = transcriptions;
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(root, 'visual-qa.json'), JSON.stringify({ fixture: 'Actual exported Student UI; isolated lesson/reply/transcription responses. Chromium fake microphone produces real local browser audio. Speech completion is simulated; no physical-device or listening-quality claim.', rows, errors, evidence }, null, 2));
    console.log(JSON.stringify({ captures: rows.length, errors, evidence }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
