// Real browser + PostgreSQL QA. No API mocks or fabricated product data.
// Requires the built Student web export and local QA Spring/FastAPI processes.
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, writeFile, mkdir, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '../..');
const out = path.resolve(root, process.env.QUIZ_QA_REPORT || 'report/smart-quiz-qa');
const web = process.env.QUIZ_WEB_EXPORT || 'C:/Users/khatr/smart-quiz-web-20261027';
const api = process.env.QUIZ_QA_API || 'http://127.0.0.1:18080';
const webPort = Number(process.env.QUIZ_WEB_PORT || 8081);
const webBase = process.env.QUIZ_WEB_URL || `http://127.0.0.1:${webPort}`;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
await mkdir(out, { recursive: true });
const result = { environment: 'Chrome headless, real local Spring/FastAPI/PostgreSQL; no physical device', checks: [], screenshots: [], exceptions: [], networkFailures: [], browserLogs: [] };
result.preparationRequests = [];
result.reviewMode = 'Existing isolated QA Quiz; real PRACTICE/CHALLENGE API calls; no WorkReview invoked by this script.';
function check(label, condition) { assert.ok(condition, label); result.checks.push({ label, status: 'PASS' }); console.log('PASS', label); }
async function until(fn, label, timeout = 60000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { if (await fn()) return; await sleep(200); }
  throw new Error('Timeout: ' + label);
}
const profile = await mkdtemp(path.join(tmpdir(), 'mathvision-quiz-'));
let browser, ws, files, proxy;
let diagnose = async () => {};
try {
  files = http.createServer(async (req, res) => {
    try {
      let file = path.resolve(web, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
      if (file !== path.resolve(web) && !file.startsWith(path.resolve(web) + path.sep)) { res.writeHead(403).end(); return; }
      try { if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html'); await stat(file); }
      catch { try { await stat(file + '.html'); file += '.html'; } catch { file = path.join(web, 'index.html'); } }
      res.setHeader('Content-Type', ({ '.js': 'application/javascript', '.css': 'text/css', '.html': 'text/html', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.json': 'application/json', '.ttf': 'font/ttf' })[path.extname(file)] || 'application/octet-stream');
      res.end(await readFile(file));
    } catch { res.writeHead(500).end(); }
  });
  proxy = http.createServer((req, res) => {
    const target = http.request(api + req.url, { method: req.method, headers: req.headers }, response => { res.writeHead(response.statusCode, response.headers); response.pipe(res); });
    target.on('error', () => res.writeHead(502).end()); req.pipe(target);
  });
  await Promise.all([process.env.QUIZ_WEB_URL ? Promise.resolve() : new Promise((resolve, reject) => { files.once('error', reject); files.listen(webPort, '127.0.0.1', resolve); }),
    new Promise((resolve, reject) => { proxy.once('error', reject); proxy.listen(0, '127.0.0.1', resolve); })]);
  const proxyBase = 'http://127.0.0.1:' + proxy.address().port;
  const executable = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  browser = spawn(executable, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', 'about:blank'], { windowsHide: true, stdio: 'ignore' });
  let port;
  await until(async () => { try { port = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; return true; } catch { return false; } }, 'Chrome startup');
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  ws = new WebSocket(tabs.find(tab => tab.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let serial = 0; const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Fetch.requestPaused') {
      const paused = message.params;
      const target = new URL(paused.request.url);
      // Redirect transport to the real local API; never synthesize a response.
      void send('Fetch.continueRequest', { requestId: paused.requestId, url: proxyBase + target.pathname + target.search })
        .catch(error => result.exceptions.push(String(error)));
    }
    if (message.method === 'Runtime.exceptionThrown') result.exceptions.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
    if (message.method === 'Network.loadingFailed') result.networkFailures.push({ reason: message.params.errorText, type: message.params.type });
    if (message.method === 'Network.requestWillBeSent' && message.params.request.url.endsWith('/student/quizzes/prepare')) {
      const data = JSON.parse(message.params.request.postData || '{}');
      result.preparationRequests.push({ problemText: data.confirmedProblemText ?? data.problemText, confirmed: data.problemConfirmed, revision: data.revision });
    }
    if (message.method === 'Log.entryAdded') result.browserLogs.push({ level: message.params.entry.level, text: message.params.entry.text });
    const request = pending.get(message.id);
    if (request) { pending.delete(message.id); clearTimeout(request.timer); message.error ? request.reject(new Error(JSON.stringify(message.error))) : request.resolve(message.result); }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++serial; const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 60000);
    pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => { const value = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (value.exceptionDetails) throw new Error(value.exceptionDetails.exception?.description || value.exceptionDetails.text); return value.result.value; };
  const resize = (width, height) => send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: true });
  const navigate = async route => { await send('Page.navigate', { url: webBase + route }); await until(() => evaluate('document.readyState === "complete"'), 'page loaded', 180000); };
  const has = label => evaluate(`!!document.querySelector('[aria-label=${JSON.stringify(label)}]')`);
  const tap = async label => {
    await until(() => evaluate(`(()=>{const e=document.querySelector('[aria-label=${JSON.stringify(label)}]');return !!e&&e.getAttribute('aria-disabled')!=='true'&&!e.disabled})()`), 'enabled ' + label);
    // Native DOM click exercises RN Web's keyboard/button handler and its duplicate-submit guard.
    await evaluate(`(()=>{const e=document.querySelector('[aria-label=${JSON.stringify(label)}]');e.scrollIntoView({block:'center'});e.click()})()`);
  };
  const body = () => evaluate('document.body.innerText');
  const input = async (label, value) => {
    await evaluate(`(()=>{const e=document.querySelector('[aria-label=${JSON.stringify(label)}]');e.focus();const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;setter.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  };
  const screenshot = async name => {
    const data = await send('Page.captureScreenshot', { captureBeyondViewport: false });
    await writeFile(path.join(out, name + '.png'), Buffer.from(data.data, 'base64')); result.screenshots.push(name + '.png');
  };
  diagnose = async () => {
    await screenshot('browser-failure');
    const state = await evaluate('JSON.stringify({pathname:location.pathname,text:document.body.innerText,labels:[...document.querySelectorAll("[aria-label]")].map(e=>e.getAttribute("aria-label"))})');
    await writeFile(path.join(out, 'browser-failure-state.json'), state);
  };
  await send('Runtime.enable'); await send('Page.enable'); await send('Network.enable'); await send('Log.enable');
  await send('Emulation.setFocusEmulationEnabled', { enabled: true });
  await send('Page.bringToFront');
  await send('Fetch.enable', { patterns: ['https://api.mathvisionkids.com/api/v1/*', 'http://localhost:8080/api/v1/*'].map(urlPattern => ({ urlPattern, requestStage: 'Request' })) });
  await resize(390, 844);
  // Student Web is a portal-authenticated app: /login without portal tokens redirects.
  // Obtain real credentials from Spring, seed the same web session keys as the SSO
  // handoff, then let AuthProvider verify the profile with /me. Never mock auth.
  const authenticated = await fetch(api + '/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: process.env.QUIZ_QA_EMAIL || 'minh.student@mathvision.local', password: process.env.QUIZ_QA_PASSWORD || 'MathVision123!' }) });
  assert.equal(authenticated.status, 200);
  const tokens = await authenticated.json();
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `if(location.origin===${JSON.stringify(new URL(webBase).origin)}&&!sessionStorage.getItem('portal_access_token')){sessionStorage.setItem('portal_access_token',${JSON.stringify(tokens.accessToken)});sessionStorage.setItem('portal_refresh_token',${JSON.stringify(tokens.refreshToken)});sessionStorage.setItem('portal_session_id',${JSON.stringify(crypto.randomUUID())});}` });
  console.log('Opening authenticated Student', new URL(webBase).host);
  await navigate('/'); await until(() => has('Chụp bài toán'), 'authenticated Home', 120000);
  check('Real JWT verified by Student Web and Quiz shortcut beneath capture', await has('Quiz của em'));
  const request = (route, method = 'GET', data) => evaluate(`(async()=>{const r=await fetch(${JSON.stringify(proxyBase + '/api/v1')}+${JSON.stringify(route)},{method:${JSON.stringify(method)},headers:{'Content-Type':'application/json',Authorization:'Bearer '+sessionStorage.getItem('portal_access_token')},${data === undefined ? '' : 'body:' + JSON.stringify(JSON.stringify(data))}});return {status:r.status,body:await r.json()}})()`);
  const library = (await request('/student/quizzes?group=COMPLETED')).body;
  const item = library.items.find(q => q.topicCode === 'FRACTION_FIND_TOTAL_FROM_REMAINDER');
  assert.ok(item);const totalBefore=(await request('/student/quizzes/pending-count')).body.totalStars;
  const solve = text => {
    const parts=[...text.matchAll(/(\d+)\/(\d+)/g)];assert.equal(parts.length,2);
    const count=text.match(/(?:là|có) (\d+) (?:quyển sách|viên kẹo|viên bi)/u);assert.ok(count);
    const [[a,b],[c,d]]=parts.map(m=>[BigInt(m[1]),BigInt(m[2])]);
    const n=BigInt(count[1])*b*d,den=b*d-a*d-c*b;assert.ok(den>0n);assert.equal(n%den,0n);return String(n/den);
  };
  await navigate('/quiz/'+item.quizId);await until(()=>has('Ôn lại bài cũ'),'completed Quiz replay actions');
  await tap('Ôn lại bài cũ');await until(()=>has('Hoàn thành'),'practice question');
  let q=(await request('/student/quizzes/'+item.quizId)).body;
  const practiceQuestion=q.questionText;const oldAnswer=solve(practiceQuestion);
  check('UI opens PRACTICE with backend mode and preserved best record',q.replayMode==='PRACTICE'&&q.stars===3&&q.correctAnswer===null);
  await input('Đáp án của em, '+q.unit,oldAnswer);await tap('Hoàn thành');await until(()=>has('Về Quiz của em'),'practice result');
  q=(await request('/student/quizzes/'+item.quizId)).body;
  check('UI explicitly labels practice zero stars while API preserves three-star record',q.attempts.at(-1).stars===0&&q.stars===3&&(await body()).includes('Ôn lại bài cũ – Không tính sao'));
  await screenshot('mobile-practice-zero-preserved-best');
  await tap('Thử thách nâng sao');await until(()=>has('Hoàn thành'),'challenge question');
  q=(await request('/student/quizzes/'+item.quizId)).body;const value=solve(q.questionText);
  check('UI Challenge receives a fresh question with hidden answer and stable pending badge',q.replayMode==='CHALLENGE'&&q.questionText!==practiceQuestion&&value!==oldAnswer&&q.correctAnswer===null&&(await request('/student/quizzes/pending-count')).body.pendingCount===0);
  await input('Đáp án của em, '+q.unit,value);await tap('Hoàn thành');await until(()=>has('Về Quiz của em'),'challenge result');
  q=(await request('/student/quizzes/'+item.quizId)).body;
  check('UI distinguishes current earned stars from all-time best',(await body()).includes('Lượt này em nhận '+q.attempts.at(-1).stars+' sao. Kỷ lục của em: 3 sao.'));
  check('Repeated practice/challenge does not inflate total stars',(await request('/student/quizzes/pending-count')).body.totalStars===totalBefore);
  check('Attempt history keeps the previous practice question snapshot',q.attempts.at(-2).questionText===practiceQuestion&&q.attempts.at(-2).mode==='PRACTICE');
  await screenshot('mobile-challenge-best-and-history');
  await navigate('/quiz');await until(async ()=>(await body()).includes('Mỗi câu đố, thêm một khám phá'),'Quiz library');
  await until(async ()=>(await body()).includes('Em đã nhận '+totalBefore+' sao từ Quiz'),'server total stars rendered');
  check('Quiz library displays actual API total stars',(await body()).includes('Em đã nhận '+totalBefore+' sao từ Quiz'));
  check('No uncaught browser exceptions during replay',result.exceptions.length===0);
} catch (error) {
  await diagnose().catch(failure => { result.diagnosticFailure = String(failure); });
  result.failure = String(error.stack || error); console.error(result.failure); process.exitCode = 1;
} finally {
  if (ws?.readyState === WebSocket.OPEN) { try { ws.send(JSON.stringify({ id: 999999, method: 'Browser.close' })); } catch {} ws.close(); }
  browser?.kill();
  for (const server of [files, proxy]) if (server?.listening) { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
  await sleep(500);
  const resolved = path.resolve(profile);
  if (path.dirname(resolved) === path.resolve(tmpdir()) && path.basename(resolved).startsWith('mathvision-quiz-')) await rm(resolved, { recursive: true, force: true, maxRetries: 8, retryDelay: 250 });
  await writeFile(path.join(out, 'browser-results.json'), JSON.stringify(result, null, 2));
}
