// Actual Student components with deterministic API failures; no phone-device claim.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,problem='Bài 7. Mảnh đất hình chữ nhật nhà bác Tư có chiều dài bằng 15 m, chiều rộng bằng (3)/(5) chiều dài. Bác Tư dùng (1)/(6) diện tích mảnh đất để trồng hoa. Tính diện tích mảnh đất bác Tư dùng để trồng hoa.';
const step={kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc câu cho biết chiều dài và chiều rộng mảnh đất.',guidance:['Chiều dài mảnh đất là 15 mét, chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.'],question:'Câu nào là điều đề đã cho biết?',choices:['Chiều dài 15 m, chiều rộng bằng (3)/(5) chiều dài.','Cần tìm diện tích trồng hoa.'],expression:'',unit:'',workExcerpt:''};
const lesson={sessionId:'audio-refinement-visual-session-12345',revision:0,topic:'Diện tích',goal:'Tìm diện tích trồng hoa',feedback:'',understandingSteps:3,outline:['Hiểu đề','Hiểu câu hỏi','Chọn cách làm','Tính chiều rộng','Tính diện tích'],stepIndex:0,completed:[],status:'READY',step};
const reply={answer:'Chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.',spokenExplanation:'Chiều dài là 15 mét. Chiều rộng bằng ba phần năm chiều dài.',followUp:'Đề đã cho biết chiều dài là bao nhiêu?',guarded:false};
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
 const auth=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});assert.equal(auth.status,200);const tokens=await auth.json();
 const browser=await chromium.launch({headless:true}),rows=[],errors=[];
 try{for(const width of [320,390,768,1440]){
  const context=await browser.newContext({viewport:{width,height:width===1440?900:844},deviceScaleFactor:2,reducedMotion:'reduce'});
  await context.addInitScript(({accessToken,refreshToken})=>{sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);},tokens);
  let ready=false,prepares=0,failedTransfer=false;const requests=[];
  await context.route('**/api/v1/student/tutor/**',async route=>{
   const url=route.request().url(),body=route.request().postDataJSON();requests.push({route:new URL(url).pathname,voice:body?.voice});
   const json=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
   if(url.endsWith('/narration/prepare')||url.endsWith('/narration/status')){
    if(url.endsWith('/narration/prepare')&&++prepares===1)return json({message:'temporary'},503);
    return json({phase:ready?'ready':'synthesizing',mode:'online',percent:ready?100:45,elapsedMs:1000,completedChunks:1,totalChunks:ready?1:2});
   }
   if(url.endsWith('/narration')){
    if(!failedTransfer&&body.voice.includes('NamMinh')){failedTransfer=true;return json({message:'temporary'},502);}
    return route.fulfill({status:200,contentType:'audio/wav',body:fs.readFileSync(path.join(out,body.voice.includes('HoaiMy')?'female.wav':'male.wav'))});
   }
   return json(url.endsWith('/lesson/ask')?reply:url.endsWith('/lesson')?lesson:{phase:'preparing'});
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  const shot=async name=>{await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(out,'screenshots',`${name}-${width}.png`)});};
  await page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent(problem),{timeout:120000});
  await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
  await page.getByTestId('lesson-problem-reference').waitFor();await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
  await page.getByText('Đã tạo 1/2 đoạn giọng đọc.',{exact:true}).waitFor();
  const loading=await page.getByRole('progressbar',{name:'Tiến độ chuẩn bị',exact:true}).boundingBox();await shot('preparing');
  ready=true;await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);
  assert.equal(await page.getByTestId('recovery-notice').count(),0);assert(failedTransfer);
  const play=page.getByRole('button',{name:'Phát lời giảng',exact:true});await page.keyboard.press('Tab');await play.focus();
  assert.equal(await play.evaluate(n=>getComputedStyle(n).outlineWidth),'2px');await page.keyboard.press('Enter');
  await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).waitFor();await shot('playing');
  await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
  assert.notEqual(await play.evaluate(n=>getComputedStyle(n).outlineWidth),'2px');
  const timeline=page.getByTestId('media-timeline'),box=await timeline.boundingBox();
  const controls=await timeline.getByRole('button').evaluateAll(items=>items.map(n=>({label:n.getAttribute('aria-label'),width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height})));
  assert(controls.every(b=>b.height>=44));await shot('player');
  await page.getByRole('radio',{name:'Giọng nữ',exact:true}).click();await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);
  await shot('female');await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
  const beforeReopen=requests.filter(r=>r.route.endsWith('/narration')).length,reopenStart=performance.now();
  await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);
  const reopenReadyMs=Math.round(performance.now()-reopenStart);
  assert.equal(requests.filter(r=>r.route.endsWith('/narration')).length,beforeReopen);
  await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
  await page.getByRole('button',{name:'Hỏi bài',exact:true}).click();await page.getByRole('textbox',{name:'Câu hỏi của em'}).waitFor();await shot('question');
  await page.getByRole('textbox',{name:'Câu hỏi của em'}).fill('Vì sao chiều rộng bằng ba phần năm chiều dài?');await page.getByRole('button',{name:'Gửi câu hỏi',exact:true}).click();
  await page.getByText(reply.answer,{exact:true}).waitFor();await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua lời giải thích"]')?.max)>1);await shot('answer');
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
  rows.push({width,loadingTrackHeight:loading.height,playerHeight:box.height,controls,reopenReadyMs,noReopenDownload:true,prepareTransientRecovered:prepares>2,readyTransferRecovered:failedTransfer,noFailureCard:true,noHorizontalOverflow:true});
  await context.close();console.log('Verified audio refinement '+width);
 }}catch(error){for(const c of browser.contexts())for(const page of c.pages()){await page.screenshot({path:path.join(out,'screenshots','failure.png')});console.log('Failure '+(await page.locator('body').innerText()).slice(0,1000));}throw error;}
 finally{await browser.close();}
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual Student web UI, controlled transient HTTP errors and lesson fixtures, real generated WAV files and local authentication; not physical Android evidence.',rows,errors},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
