// Actual Student UI. Only lesson/error API responses are controlled fixtures.
// Uses real local authentication and an existing generated Vietnamese WAV.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,problem='Bài 7. Mảnh đất hình chữ nhật nhà bác Tư có chiều dài bằng 15 m, chiều rộng bằng (3)/(5) chiều dài. Bác Tư dùng (1)/(6) diện tích mảnh đất để trồng hoa. Tính diện tích mảnh đất bác Tư dùng để trồng hoa.';
const step={kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc câu cho biết chiều dài và chiều rộng mảnh đất.',guidance:['Chiều dài mảnh đất là 15 mét, chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.'],question:'Câu nào là điều đề đã cho biết?',choices:['Chiều dài 15 m, chiều rộng bằng (3)/(5) chiều dài.','Cần tìm diện tích trồng hoa.'],expression:'',unit:'',workExcerpt:''};
const lesson={sessionId:'compact-error-visual-lesson-session-12345',revision:0,topic:'Diện tích',goal:'Tìm diện tích trồng hoa',feedback:'',understandingSteps:3,outline:['Hiểu đề','Hiểu câu hỏi','Chọn cách làm','Tính chiều rộng','Tính diện tích'],stepIndex:0,completed:[],status:'READY',step};
const reply={answer:'Chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.',spokenExplanation:'Chiều dài là 15 mét. Chiều rộng bằng ba phần năm chiều dài.',followUp:'Đề đã cho biết chiều dài là bao nhiêu?',guarded:false};
const screenshot=async(page,name)=>{await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(out,'screenshots',name+'.png')});};
async function noticeMetrics(page){
 const card=page.getByTestId('recovery-notice');await card.waitFor();
 const bounds=await card.boundingBox(),buttons=card.getByRole('button'),sizes=await buttons.evaluateAll(nodes=>nodes.map(n=>{const b=n.getBoundingClientRect();return{label:n.textContent.trim(),height:b.height,width:b.width};}));
 assert(sizes.length>0&&sizes.length<=2);assert(sizes.every(b=>b.height>=44));
 assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
 return{height:Math.round(bounds.height),width:Math.round(bounds.width),actions:sizes};
}
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
 const auth=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});
 assert.equal(auth.status,200);const tokens=await auth.json();
 const browser=await chromium.launch({headless:true}),rows=[],errors=[];
 try{
  for(const width of [320,390,768,1440]){
   const context=await browser.newContext({viewport:{width,height:width===1440?900:844},deviceScaleFactor:2,reducedMotion:'reduce'});
   await context.addInitScript(({accessToken,refreshToken})=>{sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);
    Object.defineProperty(speechSynthesis,'getVoices',{configurable:true,value:()=>[]});},tokens);
   let allowAudio=false,allowAsk=false,allowLesson=false;const requests=[];
   await context.route('**/api/v1/student/tutor/**',async route=>{
    const url=route.request().url(),body=route.request().postDataJSON();requests.push({url:new URL(url).pathname,voice:body?.voice,question:body?.question});
    const json=(data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
    if(url.endsWith('/narration'))return route.fulfill({status:200,contentType:'audio/wav',body:fs.readFileSync(path.join(out,'../student-learning-voice-polish-20261029/male.wav'))});
    if(url.endsWith('/narration/prepare')||url.endsWith('/narration/status'))return json({phase:allowAudio?'ready':'failed',mode:'online',percent:allowAudio?100:10,elapsedMs:0,completedChunks:allowAudio?1:0,totalChunks:1});
    if(url.endsWith('/lesson/ask'))return allowAsk?json(reply):json({message:'Service unavailable'},503);
    if(url.endsWith('/lesson'))return allowLesson?json(lesson):json({message:'Service unavailable'},503);
    return json({phase:'preparing'});
   });
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent(problem),{timeout:120000});
   await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();
   await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
   const lessonError=await noticeMetrics(page);await screenshot(page,'lesson-error-'+width);
   assert((await page.locator('body').innerText()).replace(/\s+/g,' ').includes('Mảnh đất hình chữ nhật'));
   allowLesson=true;await page.getByRole('button',{name:'Bắt đầu lại bài học',exact:true}).click();
   await page.getByTestId('lesson-problem-reference').waitFor();
   await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
   const voiceError=await noticeMetrics(page);assert.equal(await page.getByTestId('recovery-notice').getByRole('button').count(),2);
   assert.equal(await page.getByText(/giọng dự phòng/i).count(),0);await screenshot(page,'voice-error-'+width);
   const transcript=page.getByRole('button',{name:'Đọc lời giảng chi tiết'});await transcript.click();
   assert.equal(await transcript.getAttribute('aria-expanded'),'true');await transcript.click();
   // Missing local voice must also offer a compact recovery, without substituting English.
   await page.getByRole('button',{name:'Dùng giọng đọc trên thiết bị',exact:true}).click();
   await page.getByText('Chưa có giọng Việt trên thiết bị',{exact:true}).waitFor();
   const deviceError=await noticeMetrics(page);await screenshot(page,'device-error-'+width);
   allowAudio=true;const retry=page.getByRole('button',{name:'Quay lại giọng đã chọn',exact:true});
   await retry.focus();assert.equal(await retry.evaluate(n=>n===document.activeElement),true);
   const focus=await retry.evaluate(n=>({style:getComputedStyle(n).outlineStyle,width:getComputedStyle(n).outlineWidth}));
   assert.equal(focus.style,'solid');assert(parseFloat(focus.width)>=2);
   await page.keyboard.press('Enter');
   await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);
   await page.getByRole('button',{name:'Phát lời giảng',exact:true}).click();
   await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
   await screenshot(page,'voice-recovered-'+width);
   await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
   await page.getByRole('button',{name:'Hỏi bài',exact:true}).click();
   const input=page.getByRole('textbox',{name:'Câu hỏi của em'}),question='Vì sao chiều rộng bằng ba phần năm chiều dài?';
   await input.fill(question);await page.getByRole('button',{name:'Gửi câu hỏi',exact:true}).click();
   const questionError=await noticeMetrics(page);assert.equal(await input.inputValue(),question);
   await screenshot(page,'question-error-'+width);
   await page.getByRole('button',{name:'Sửa câu hỏi',exact:true}).click();assert.equal(await input.evaluate(n=>n===document.activeElement),true);
   allowAsk=true;await page.getByRole('button',{name:'Gửi lại câu hỏi',exact:true}).click();
   await page.getByText(reply.answer,{exact:true}).waitFor();
   const asks=requests.filter(r=>r.url.endsWith('/lesson/ask'));assert.equal(asks.length,2);assert(asks.every(r=>r.question===question));
   await screenshot(page,'question-recovered-'+width);
   rows.push({width,lessonError,voiceError,deviceError,questionError,keyboardFocus:focus,exactQuestionRetained:true,retryRecoveredAudio:true,playPauseWorked:true,transcriptAccessible:true,noHorizontalOverflow:true});
   await context.close();console.log('Verified compact error UI '+width);
  }
 }catch(error){for(const c of browser.contexts())for(const p of c.pages()){await screenshot(p,'failure');console.log('Failure '+p.url()+' '+(await p.locator('body').innerText()).slice(0,1400));}throw error;}
 finally{await browser.close();}
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual Student web components, controlled lesson/error responses, real local authentication and real generated WAV; not physical Android evidence.',rows,errors},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
