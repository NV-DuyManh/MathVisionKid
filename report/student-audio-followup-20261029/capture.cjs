// Real Student components; controlled HTTP fixtures, not provider or Android timing.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,problem='Bài 7. Mảnh đất hình chữ nhật nhà bác Tư có chiều dài bằng 15 m, chiều rộng bằng (3)/(5) chiều dài. Bác Tư dùng (1)/(6) diện tích mảnh đất để trồng hoa. Tính diện tích mảnh đất bác Tư dùng để trồng hoa.';
const step={kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc câu cho biết chiều dài và chiều rộng mảnh đất.',guidance:['Chiều dài mảnh đất là 15 mét, chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.'],question:'Câu nào là điều đề đã cho biết?',choices:['Chiều dài 15 m, chiều rộng bằng (3)/(5) chiều dài.','Cần tìm diện tích trồng hoa.'],expression:'',unit:'',workExcerpt:''};
const lesson={sessionId:'audio-followup-visual-session-12345',revision:0,topic:'Diện tích',goal:'Tìm diện tích trồng hoa',feedback:'',understandingSteps:3,outline:['Hiểu đề','Hiểu câu hỏi','Chọn cách làm','Tính chiều rộng','Tính diện tích'],stepIndex:0,completed:[],status:'READY',step};
const reply={answer:'Chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.',spokenExplanation:'Chiều dài là 15 mét. Chiều rộng bằng ba phần năm chiều dài.',followUp:'Đề đã cho biết chiều dài là bao nhiêu?',guarded:false};
const wav={male:fs.readFileSync(path.join(out,'../student-audio-refinement-20261029/male.wav')),female:fs.readFileSync(path.join(out,'../student-audio-refinement-20261029/female.wav'))};
async function visiblePlayer(page,title='Nghe giảng') {
 const player=page.getByTestId('narration-player');await player.waitFor({state:'visible'});
 await page.waitForFunction(name=>{const n=document.querySelector(`[aria-label="Tua ${name.toLowerCase()}"]`);return n&&!n.disabled&&Number(n.max)>1;},title);
}
async function shot(page,name){await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(out,'screenshots',name+'.png')});}
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
 const auth=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});assert.equal(auth.status,200);const tokens=await auth.json();
 const browser=await chromium.launch({headless:true}),rows=[],errors=[];
 try{for(const [width,height] of [[320,844],[390,844],[768,1024],[1440,900],[844,390]]){
  const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:2,reducedMotion:'reduce'});
  await context.addInitScript(({accessToken,refreshToken})=>{
   sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);
   window.preparationAudit={enabled:false,visible:false,overlap:false};
   const visible=n=>n&&getComputedStyle(n).display!=='none'&&getComputedStyle(n).visibility!=='hidden'&&n.getBoundingClientRect().height>0;
   new MutationObserver(()=>{if(!window.preparationAudit.enabled)return;const preparing=visible(document.querySelector('[data-testid="narration-preparation"]')),player=visible(document.querySelector('[data-testid="narration-player"]'));
    window.preparationAudit.visible ||= !!preparing;window.preparationAudit.overlap ||= !!(preparing&&player);
   }).observe(document,{subtree:true,attributes:true,childList:true});
  },tokens);
  let ready=false,fail=false;const requests=[];
  await context.route('**/api/v1/student/tutor/**',async route=>{
   const url=route.request().url(),body=route.request().postDataJSON();requests.push({route:new URL(url).pathname,voice:body?.voice});
   const json=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
   if(url.endsWith('/narration/prepare')||url.endsWith('/narration/status'))return json({phase:fail?'failed':ready?'ready':'synthesizing',mode:'online',percent:ready?100:45,elapsedMs:1000,completedChunks:ready?1:1,totalChunks:ready?1:2});
   if(url.endsWith('/narration'))return route.fulfill({status:200,contentType:'audio/wav',body:body.voice.includes('HoaiMy')?wav.female:wav.male});
   return json(url.endsWith('/lesson/ask')?reply:url.endsWith('/lesson')?lesson:{phase:'preparing'});
  });
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent(problem),{timeout:120000});
  await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
  await page.getByTestId('lesson-problem-reference').waitFor();await shot(page,'lesson-'+width);
  const open=page.getByRole('button',{name:'Nghe giảng',exact:true});await open.focus();await open.click();
  await page.getByTestId('narration-preparation').waitFor({state:'visible'});await page.getByText('Đã tạo 1/2 đoạn giọng đọc.',{exact:true}).waitFor();await shot(page,'preparing-'+width);
  await page.evaluate(()=>{window.preparationAudit.enabled=true;});ready=true;await visiblePlayer(page);
  assert.equal((await page.evaluate(()=>window.preparationAudit)).overlap,false);
  const play=page.getByRole('button',{name:'Phát lời giảng',exact:true});await page.keyboard.press('Tab');await play.focus();assert.equal(await play.evaluate(n=>getComputedStyle(n).outlineWidth),'2px');
  await page.keyboard.press('Enter');await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).waitFor();await shot(page,'playing-'+width);await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
  const timeline=page.getByTestId('media-timeline'),playerBox=await timeline.boundingBox();
  const controls=await timeline.getByRole('button').evaluateAll(nodes=>nodes.map(n=>({label:n.getAttribute('aria-label'),height:n.getBoundingClientRect().height})));assert(controls.every(n=>n.height>=44));
  await page.getByRole('radio',{name:'Giọng nữ',exact:true}).click();await visiblePlayer(page);await shot(page,'player-'+width);
  const dialog=page.getByRole('dialog');for(let i=0;i<14;i++){await page.keyboard.press('Tab');assert(await dialog.evaluate(n=>n.contains(document.activeElement)));}
  await page.keyboard.press('Escape');await page.getByRole('button',{name:'Đóng Nghe giảng'}).waitFor({state:'detached'});
  assert(await open.evaluate(n=>n===document.activeElement));
  const before=requests.filter(r=>r.route.endsWith('/narration')).length;
  await page.evaluate(()=>{window.preparationAudit={enabled:true,visible:false,overlap:false};});const start=performance.now();await open.click();await visiblePlayer(page);const cachedReopenMs=Math.round(performance.now()-start);
  await page.waitForTimeout(250);const cachedAudit=await page.evaluate(()=>window.preparationAudit);assert.equal(cachedAudit.visible,false);assert.equal(cachedAudit.overlap,false);
  assert.equal(requests.filter(r=>r.route.endsWith('/narration')).length,before);await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
  await page.getByRole('button',{name:'Hỏi bài',exact:true}).click();const input=page.getByRole('textbox',{name:'Câu hỏi của em'});await input.fill('Vì sao chiều rộng bằng ba phần năm chiều dài?');await shot(page,'question-'+width);
  const mediaBefore=requests.filter(r=>r.route.endsWith('/lesson/media/prepare')).length;
  await page.getByRole('button',{name:'Gửi câu hỏi',exact:true}).click();await page.getByText(reply.answer,{exact:true}).waitFor();await visiblePlayer(page,'Lời giải thích');await shot(page,'answer-'+width);
  assert.equal(requests.filter(r=>r.route.endsWith('/lesson/media/prepare')).length,mediaBefore);
  const replyPlayerHeight=Math.round((await page.getByTestId('media-timeline').boundingBox()).height);
  assert(replyPlayerHeight<playerBox.height);
  for(const label of ['Lùi 10 giây','Tiến 10 giây','Tốc độ 1 lần. Bấm để đổi tốc độ'])assert(await page.getByRole('button',{name:label,exact:true}).count());
  assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
  // A fresh page drops its private in-memory audio assets, exercising a real failure UI.
  fail=true;await page.reload();await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
  await page.getByTestId('lesson-problem-reference').waitFor();await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
  const recovery=page.getByTestId('recovery-notice');await recovery.waitFor();const errorBox=await recovery.boundingBox();
  assert.equal(await recovery.getByRole('button').count(),2);assert(errorBox.height<210);
  assert((await recovery.getByRole('button').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().height))).every(n=>n>=44));await shot(page,'recovery-'+width);
  fail=false;await page.getByRole('button',{name:'Tải lại lời giảng',exact:true}).click();await visiblePlayer(page);assert.equal(await recovery.count(),0);
  await shot(page,'recovered-'+width);
  rows.push({width,height,cachedReopenMs,cachedPreparationNeverVisible:!cachedAudit.visible,noExtraCachedDownload:true,noPreparationPlayerOverlap:true,replyDoesNotPrepareWholeLesson:true,keyboardTrap:true,escapeCloses:true,focusRestored:true,playerHeight:Math.round(playerBox.height),replyPlayerHeight,recoveryHeight:Math.round(errorBox.height),compactRecoveryAndRetry:true,controls,noHorizontalOverflow:true});
  await context.close();console.log('Verified follow-up '+width+'x'+height);
 }}catch(error){for(const c of browser.contexts())for(const page of c.pages()){await shot(page,'failure');console.log('Failure '+(await page.locator('body').innerText()).slice(0,1000));}throw error;}
 finally{await browser.close();}
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual Student web UI, controlled lesson and narration responses, real generated WAV and local authentication. Browser timings cover cached player readiness only; not provider speed or physical Android evidence.',rows,errors},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
