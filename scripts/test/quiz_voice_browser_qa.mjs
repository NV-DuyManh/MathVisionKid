// Real Student Web UI -> isolated QA Spring -> real TTS -> real HTML audio decode.
// Headless browser evidence is not physical Android/iOS playback evidence.
import { spawn, spawnSync } from 'node:child_process';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '../..');
const out = path.join(root, 'runtime/quiz-voice-min-stars-timer-20261031');
const api = 'http://127.0.0.1:18082', web = 'http://localhost:8081';
const login = JSON.parse(await readFile(path.join(out, 'qa-login.json'), 'utf8'));
const response = await fetch(api + '/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(login) });
assert.equal(response.status, 200);
const tokens = await response.json();
const quizzes = spawnSync('docker', ['exec', 'mathvision-postgres', 'psql', '-U', 'mathvision', '-d', 'mathvision_voice_stars_timer_20261031', '-Atc',
  `SELECT json_agg(q.id) FROM student_quizzes q JOIN users u ON u.id=q.student_id WHERE u.email='${login.email}' AND q.topic_code IN ('DIGIT_APPEND_FIND_ORIGINAL_NUMBER','FRACTION_ADDITION_SUBTRACTION')`], { encoding: 'utf8', windowsHide: true });
assert.equal(quizzes.status, 0);
const ids = JSON.parse(quizzes.stdout);
assert.equal(ids.length, 2);
const profile = path.join(out, 'chrome-profile'); await mkdir(profile, { recursive: true });
const browser = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--autoplay-policy=no-user-gesture-required'], { windowsHide: true });
let ws, serial = 0;
const pending = new Map(), checks = [], requests = [];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, label, duration = 90000) {
  const deadline = Date.now() + duration;
  while (Date.now() < deadline) { if (await fn()) return; await sleep(250); }
  throw Error('Timeout: ' + label);
}
try {
  let endpoint;
  browser.stderr.on('data', bytes => { endpoint ||= bytes.toString().match(/DevTools listening on (ws:\/\/\S+)/)?.[1]; });
  await until(() => endpoint, 'Chrome endpoint');
  const port = new URL(endpoint).port;
  const pages = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  ws = new WebSocket(pages.find(page => page.type === 'page').webSocketDebuggerUrl);
  await new Promise(resolve => ws.addEventListener('open', resolve, { once: true }));
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++serial;
    const timer = setTimeout(() => { pending.delete(id); reject(Error('CDP timeout ' + method)); }, 120000);
    pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
  });
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Fetch.requestPaused') {
      const request = message.params, url = new URL(request.request.url);
      if (url.pathname.endsWith('/narration')) requests.push({ path: url.pathname, voice: JSON.parse(request.request.postData || '{}').voice });
      void send('Fetch.continueRequest', { requestId: request.requestId, url: api + url.pathname + url.search });
    }
    const item = pending.get(message.id);
    if (item) { pending.delete(message.id); clearTimeout(item.timer); message.error ? item.reject(Error(JSON.stringify(message.error))) : item.resolve(message.result); }
  });
  const evaluate = async expression => {
    const data = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (data.exceptionDetails) throw Error(data.exceptionDetails.text);
    return data.result.value;
  };
  const body = () => evaluate('document.body.innerText');
  const click = async label => {
    await until(() => evaluate(`!!document.querySelector('[aria-label=${JSON.stringify(label)}]:not([aria-disabled="true"])')`), label);
    await evaluate(`document.querySelector('[aria-label=${JSON.stringify(label)}]').click()`);
  };
  await send('Runtime.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 412, height: 915, deviceScaleFactor: 1, mobile: true });
  await send('Fetch.enable', { patterns: ['http://localhost:8080/api/v1/*', 'http://127.0.0.1:8080/api/v1/*', 'https://api.mathvisionkids.com/api/v1/*'].map(urlPattern => ({ urlPattern })) });
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `
    if(location.origin===${JSON.stringify(web)}) {
      sessionStorage.setItem('portal_access_token',${JSON.stringify(tokens.accessToken)});
      sessionStorage.setItem('portal_refresh_token',${JSON.stringify(tokens.refreshToken)});
      sessionStorage.setItem('portal_session_id','isolated-quiz-voice-browser');
      const play=HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play=function(...args){window.__quizAudio=this;return play.apply(this,args);};
    }` });
  for (const id of ids) {
    await send('Page.navigate', { url: web + '/quiz/' + id });
    await until(async () => (await body()).includes('Nghe cách giải'), 'Quiz page', 180000);
    for (const gender of ['Giọng nam', 'Giọng nữ']) {
      const selected = await evaluate(`!!document.querySelector('[aria-label="${gender}, đang chọn"]')`);
      if (!selected) await click(gender);
      await click('Nghe cách giải');
      await until(async () => (await body()).includes('Sẵn sàng') || (await body()).includes('Thử tải giọng đọc lại'), 'audio ready/error');
      if ((await body()).includes('Thử tải giọng đọc lại')) {
        await click('Thử tải giọng đọc lại');
        await until(async () => (await body()).includes('Sẵn sàng'), 'one explicit retry ready');
      }
      await click('Phát lời giảng');
      await until(() => evaluate('!!window.__quizAudio && window.__quizAudio.currentTime>.25 && !window.__quizAudio.paused && !window.__quizAudio.error'), 'actual PCM playback advances');
      checks.push({ quiz: id, voice: gender, result: 'PASS', verified: 'real browser decoding/playback advances' });
      console.log('PASS real browser audio:', id, gender);
      await click('Tạm dừng lời giảng');
    }
    const capture = await send('Page.captureScreenshot');
    await writeFile(path.join(out, 'browser-' + id + '.png'), Buffer.from(capture.data, 'base64'));
  }
  await writeFile(path.join(out, 'browser-acceptance.json'), JSON.stringify({ checks, requests, physicalPlaybackVerified: false }, null, 2));
} finally {
  ws?.close(); browser.kill();
  for (const item of pending.values()) clearTimeout(item.timer);
}
