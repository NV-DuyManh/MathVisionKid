// Real browser + PostgreSQL QA. No API mocks or fabricated product data.
// Requires the built Student web export and local QA Spring/FastAPI processes.
import { spawn, spawnSync } from 'node:child_process';
import { mkdtemp, readFile, writeFile, mkdir, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';

const root = path.resolve(import.meta.dirname, '../..');
const out = path.resolve(root, process.env.QUIZ_QA_REPORT || 'report/tutor-step3-blocker/browser');
const web = process.env.QUIZ_WEB_EXPORT || 'C:/Users/khatr/tutor-step3-web-20261028';
const api = process.env.QUIZ_QA_API || 'http://127.0.0.1:18080';
const webPort = Number(process.env.QUIZ_WEB_PORT || 8096);
const webBase = process.env.QUIZ_WEB_URL || `http://127.0.0.1:${webPort}`;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
await mkdir(out, { recursive: true });
const result = { environment: 'Chrome headless, real local Spring/FastAPI/PostgreSQL; no physical device', checks: [], screenshots: [], exceptions: [], networkFailures: [], browserLogs: [] };
result.automationErrors = [];
result.cancelledInterceptions = [];
result.tutorResponses = [];
result.preparationRequests = [];
result.reviewMode = process.env.QUIZ_QA_UNASSESSED_WORK === '1'
  ? 'Confirmed complete problem; work refers to an unavailable drawing. Actual existing FastAPI NEEDS_REVIEW fallback; not evidence of cloud grading.'
  : 'Actual cloud WorkReview pipeline';
function check(label, condition) { assert.ok(condition, label); result.checks.push({ label, status: 'PASS' }); console.log('PASS', label); }
// Solve the current public operation exactly; the real Tutor can choose different intermediate steps.
function solveOperation(expression) {
  const source=expression.replace(/[×x]/g,'*').replace(/[÷:]/g,'/').replace(/−/g,'-').replace(/\s/g,'');
  assert.match(source,/^[0-9()+*/.-]+$/);
  const tokens=source.match(/\d+(?:\.\d+)?|[()+*/-]/g); let offset=0;
  const gcd=(a,b)=>b?gcd(b,a%b):a<0n?-a:a;
  const fraction=(n,d=1n)=>{assert.notEqual(d,0n);if(d<0n){n=-n;d=-d;}const g=gcd(n,d);return [n/g,d/g];};
  const add=(a,b,sign=1n)=>fraction(a[0]*b[1]+sign*b[0]*a[1],a[1]*b[1]);
  const multiply=(a,b)=>fraction(a[0]*b[0],a[1]*b[1]);
  const atom=()=>{
    const token=tokens[offset++];
    if(token==='('){const value=sum();assert.equal(tokens[offset++],')');return value;}
    if(token==='-'){const value=atom();return [-value[0],value[1]];}
    assert.match(token||'',/^\d+(?:\.\d+)?$/);
    const [whole,decimal='']=token.split('.');return fraction(BigInt(whole+decimal),10n**BigInt(decimal.length));
  };
  const product=()=>{let value=atom();while(tokens[offset]==='*'||tokens[offset]==='/'){const op=tokens[offset++],right=atom();value=multiply(value,op==='/'?fraction(right[1],right[0]):right);}return value;};
  const sum=()=>{let value=product();while(tokens[offset]==='+'||tokens[offset]==='-'){const sign=tokens[offset++]==='+'?1n:-1n;value=add(value,product(),sign);}return value;};
  const answer=sum();assert.equal(offset,tokens.length);return answer[1]===1n?String(answer[0]):answer.join('/');
}
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
        .catch(error => {
          // Navigating/unmounting may abort an XHR before CDP resumes it.
          // Keep that transport cancellation separate from application exceptions.
          if (String(error).includes('Invalid InterceptionId')) result.cancelledInterceptions.push(String(error));
          else result.automationErrors.push(String(error));
        });
    }
    if (message.method === 'Runtime.exceptionThrown') result.exceptions.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
    if (message.method === 'Network.loadingFailed') result.networkFailures.push({ reason: message.params.errorText, type: message.params.type });
    if (message.method === 'Network.responseReceived') {
      const response=message.params.response;
      const route=new URL(response.url).pathname;
      if(route.includes('/student/tutor/')) result.tutorResponses.push({route,status:response.status});
    }
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
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{const original=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(...args){this.addEventListener('load',()=>{try{if(/\\/student\\/tutor\\/lesson(?:\\/(?:answer|preparation))?$/.test(this.responseURL)){window.__qaTutorStatus=this.status;if(this.status===200)window.__qaTutor=JSON.parse(this.responseText);window.__qaTutorCount=(window.__qaTutorCount||0)+1;}}catch{}});return original.apply(this,args);};})();`});
  await resize(390, 844);
  // Student Web is a portal-authenticated app: /login without portal tokens redirects.
  // Obtain real credentials from Spring, seed the same web session keys as the SSO
  // handoff, then let AuthProvider verify the profile with /me. Never mock auth.
  const qaEmail='quiz-browser-'+crypto.randomUUID()+'@test.invalid';
  const seed=spawnSync('docker',['exec','mathvision-postgres','psql','-U','mathvision','-d','mathvision_tutor_step3_20261028','-v','ON_ERROR_STOP=1','-Atc',`INSERT INTO users(id,email,password_hash,role,display_name,active,created_at,updated_at) SELECT '${crypto.randomUUID()}','${qaEmail}',password_hash,'STUDENT','Bạn học',true,now(),now() FROM users WHERE email='minh.student@mathvision.local'; INSERT INTO students(student_id,grade_level) SELECT id,3 FROM users WHERE email='${qaEmail}';`],{encoding:'utf8',windowsHide:true});
  assert.equal(seed.status,0,'QA account creation');
  const authenticated = await fetch(api + '/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: process.env.QUIZ_QA_EMAIL || qaEmail, password: process.env.QUIZ_QA_PASSWORD || 'MathVision123!' }) });
  assert.equal(authenticated.status, 200);
  const tokens = await authenticated.json();
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `if(location.origin===${JSON.stringify(new URL(webBase).origin)}&&!sessionStorage.getItem('portal_access_token')){sessionStorage.setItem('portal_access_token',${JSON.stringify(tokens.accessToken)});sessionStorage.setItem('portal_refresh_token',${JSON.stringify(tokens.refreshToken)});sessionStorage.setItem('portal_session_id',${JSON.stringify(crypto.randomUUID())});}` });
  console.log('Opening authenticated Student', new URL(webBase).host);
  await navigate('/'); await until(() => has('Chụp bài toán'), 'authenticated Home', 120000);
  check('Real JWT verified by Student Web and Quiz shortcut beneath capture', await has('Quiz của em'));
  const request = (route, method = 'GET', data) => evaluate(`(async()=>{const r=await fetch(${JSON.stringify(proxyBase + '/api/v1')}+${JSON.stringify(route)},{method:${JSON.stringify(method)},headers:{'Content-Type':'application/json',Authorization:'Bearer '+sessionStorage.getItem('portal_access_token')},${data === undefined ? '' : 'body:' + JSON.stringify(JSON.stringify(data))}});return {status:r.status,body:await r.json()}})()`);
  result.runtime=(await request('/student/quizzes/runtime')).body;
  const tree = 'Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây? (2 điểm)';
  const work = '1/3 + 2/5 = 11/15\n1 - 11/15 = 4/15\n16 : (4/15) = 61';
  await navigate('/learning/math-guide?'+new URLSearchParams({problemText:tree}));
  await until(()=>has('Em đã kiểm tra đề bài và các số'),'original confirmed problem');
  check('Before confirmation the full OCR problem is expanded', !await has('Xem đầy đủ'));
  await tap('Em đã kiểm tra đề bài và các số');
  await until(()=>has('Xem đầy đủ'),'confirmed collapsed card');
  check('Confirmation collapses the card and keeps the original text', (await body()).includes('Đã xác nhận'));
  await screenshot('confirmed-problem-collapsed');
  await tap('Xem đầy đủ'); await until(()=>has('Thu gọn'),'expanded confirmed card');
  await screenshot('confirmed-problem-expanded'); await tap('Thu gọn');
  await tap('Bắt đầu từng bước');
  for(let turn=0;turn<24;turn++) {
    await until(()=>evaluate('!!window.__qaTutor'),'real Tutor response',120000);
    const lesson=await evaluate('window.__qaTutor');
    if(lesson.status==='COMPLETE') break;
    if(lesson.status==='PREPARING') { await until(()=>evaluate("window.__qaTutor?.status!=='PREPARING'"),'prepared math without resubmitting reading'); continue; }
    if(await has('Tiếp tục bước tiếp theo')) await tap('Tiếp tục bước tiếp theo');
    if(await has('Bắt đầu giải')) await tap('Bắt đầu giải');
    if(lesson.stepIndex===3 && lesson.step?.kind==='MATH' && !result.firstMathProven) {
      check('Three checked reading answers lead to the first real math question',lesson.revision===3&&lesson.completed.length===3);
      result.firstMathProven=true;
      await screenshot('reading-3-to-first-math');
    }
    const count=await evaluate('window.__qaTutorCount');
    const step=lesson.step, choices=step.choices||[];
    let answer;
    if(choices.length) {
      if(lesson.stepIndex===0) answer=choices.find(v=>v.includes('1/3')&&!v.includes('bao nhiêu'))||choices[0];
      else if(lesson.stepIndex===1) answer=choices.find(v=>v.includes('bao nhiêu'))||choices[0];
      else {const quote=step.question.match(/«(.*?)»/);answer=quote&&!/^(Hỏi|Tính)/i.test(quote[1])?'Đúng':'Sai';if(!choices.includes(answer))answer=choices[0];}
      await tap(answer);
    } else {
      const hint=(step.title+' '+step.question).toLowerCase();
      answer=step.expression?solveOperation(step.expression):/1 phần|một phần/.test(hint)?'4':hint.includes('phần')?(hint.includes('cam')||hint.includes('còn lại')?'4/15':'11/15'):'60';
      if(await has('Tử số câu trả lời')) {
        const [numerator, denominator='1']=answer.split('/');
        await input('Tử số câu trả lời',numerator); await input('Mẫu số câu trả lời',denominator);
      } else await input('Câu trả lời của em',answer);
      await tap('Kiểm tra bước này');
    }
    await until(()=>evaluate(`window.__qaTutorCount>${count}`),'real checked Tutor turn',120000);
    if(await evaluate('window.__qaTutorStatus===503')) {result.transientTutorRetries=(result.transientTutorRetries||0)+1;if(result.transientTutorRetries>3)throw new Error('Tutor cloud unavailable after bounded UI retries');await sleep(15000);continue;}
    const checked=await evaluate('window.__qaTutor');
    result.tutorTurns??=[];result.tutorTurns.push({stepIndex:lesson.stepIndex,answer,status:checked.status});
    assert.notEqual(checked.status,'TRY_AGAIN','QA learner must solve the actual problem');
  }
  check('Actual Tutor reached COMPLETE without forging source state',(await evaluate('window.__qaTutor')).status==='COMPLETE');
  await until(()=>has('Làm ngay'),'automatic Quiz invitation',15000);
  check('Completion automatically shows both Quiz choices',await has('Làm ngay')&&await has('Để khi khác'));
  await evaluate(`document.querySelector('[aria-label="Để khi khác"]').scrollIntoView({block:'center'})`);
  await screenshot('real-lesson-auto-invitation');
  check('Confirmed exact reported text starts background preparation before finishing', result.preparationRequests.some(r => r.problemText === tree && r.confirmed === true));
  await screenshot('mobile-review-invitation'); await tap('Để khi khác');
  await until(() => has('Quiz của em, 1 Quiz chưa hoàn thành'), 'badge 1');

  check('The deferred Quiz persists in PostgreSQL', (await request('/student/quizzes/pending-count')).body.pendingCount === 1);
  await send('Page.reload');
  await until(()=>has('Quiz của em, 1 Quiz chưa hoàn thành'),'badge after reload');
  await screenshot('phone-width-completed-badge');
  await resize(1440,1000);
  await navigate('/quiz');
  await until(()=>has('Bắt đầu'),'saved Quiz library');
  await screenshot('desktop-quiz-library');
  check('No uncaught browser exceptions', result.exceptions.length === 0);
  check('No unexpected automation errors', result.automationErrors.length === 0);
  check('Every actual lesson start, answer and preparation response is HTTP 200',result.tutorResponses
    .filter(r=>/\/lesson(?:\/(?:answer|preparation))?$/.test(r.route)).every(r=>r.status===200));
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
