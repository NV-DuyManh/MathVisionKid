// Actual app components. Deterministic lesson fixtures isolate visual/interaction QA.
// Authentication and the two generated WAV samples use the running local services.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,problem='Bài 7. Mảnh đất hình chữ nhật nhà bác Tư có chiều dài bằng 15 m, chiều rộng bằng (3)/(5) chiều dài. Bác Tư dùng (1)/(6) diện tích mảnh đất để trồng hoa. Tính diện tích mảnh đất bác Tư dùng để trồng hoa.';
const first={kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc câu cho biết chiều dài và chiều rộng mảnh đất.',guidance:['Đề cho biết chiều dài mảnh đất là 15 mét, chiều rộng bằng ba phần năm chiều dài. Em tìm câu ghi đúng hai dữ kiện này nhé.'],question:'Câu nào là điều đề đã cho biết?',choices:['Chiều dài 15 m, chiều rộng bằng (3)/(5) chiều dài.','Cần tìm diện tích trồng hoa.'],expression:'',unit:'',workExcerpt:''};
const lesson={sessionId:'polish-visual-lesson-session-12345',revision:0,topic:'Diện tích',goal:'Tìm diện tích trồng hoa',feedback:'',understandingSteps:3,outline:['Hiểu đề','Hiểu câu hỏi','Chọn cách làm','Tính chiều rộng','Tính diện tích'],stepIndex:0,completed:[],status:'READY',step:first};
const correct={...lesson,revision:1,status:'CORRECT',feedback:'Em chọn đúng dữ kiện rồi!',stepIndex:1,completed:[{kind:'UNDERSTAND',title:first.title,answer:first.choices[0],explanation:first.explanation,expression:'',unit:'',solutionSentence:'',calculationDetails:[]}],step:{...first,title:'Hiểu câu hỏi',question:'Đề muốn tìm điều gì?',choices:['Diện tích trồng hoa.','Chiều dài mảnh đất.']}};
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
 const auth=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});
 assert.equal(auth.status,200);const tokens=await auth.json();
 const browser=await chromium.launch({headless:true}),rows=[],errors=[];
 try {
  for (const width of [320,390,768,1440]) {
   const context=await browser.newContext({viewport:{width,height:width===1440?900:844},deviceScaleFactor:2,reducedMotion:'reduce'});
   await context.addInitScript(({accessToken,refreshToken})=>{sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);},tokens);
   const requests=[];
   await context.route('**/api/v1/student/tutor/**',async route=>{
    const url=route.request().url(),body=route.request().postDataJSON();requests.push({url:new URL(url).pathname,voice:body?.voice});
    if(url.endsWith('/narration'))return route.fulfill({status:200,contentType:'audio/wav',body:fs.readFileSync(path.join(out,body.voice.includes('HoaiMy')?'female.wav':'male.wav'))});
    const reply=body?.answer===first.choices[1]?{...lesson,revision:1,status:'TRY_AGAIN',feedback:'Em chọn lại câu nói về dữ kiện nhé.'}:{...correct,revision:2};
    const data=url.endsWith('/narration/prepare')||url.endsWith('/narration/status')?{phase:'ready',mode:'online',percent:100,elapsedMs:0,completedChunks:1,totalChunks:1}:url.endsWith('/lesson/answer')?reply:url.endsWith('/lesson')?lesson:{phase:'preparing'};
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
   });
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
   await page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent(problem),{timeout:120000});
   await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();
   await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
   const panel=page.getByTestId('lesson-problem-reference');await panel.waitFor();
   await page.evaluate(()=>document.fonts.ready);
   const panelSize=await panel.boundingBox();const bodySize=await page.getByTestId('lesson-problem-content').boundingBox();
   assert(bodySize.height<=125);assert((await page.getByTestId('stacked-fraction').count())>=2);
   assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
   await page.screenshot({path:path.join(out,'screenshots',`lesson-${width}.png`)});
   await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
   await page.getByRole('radio',{name:'Giọng nam',exact:true}).waitFor();
   assert.equal(await page.getByRole('radio').count(),2);assert(!await page.getByText(/Nam Minh|Hoài My/).count());
   await page.getByRole('radio',{name:'Giọng nữ',exact:true}).click();
   await page.waitForFunction(()=>{
    const slider=document.querySelector('[aria-label="Tua nghe giảng"]');
    const play=document.querySelector('[aria-label="Phát lời giảng"]');
    return slider&&Number(slider.max)>1&&play&&play.getAttribute('aria-disabled')!=='true';
   });
   await page.getByRole('button',{name:'Phát lời giảng',exact:true}).click();
   await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).waitFor();
   await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
   await page.screenshot({path:path.join(out,'screenshots',`voice-${width}.png`)});
   const downloadsBeforeRetry=requests.filter(r=>r.url.endsWith('/narration')).length;
   await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
   await page.getByRole('button',{name:first.choices[1],exact:true}).click();
   await page.getByText('Em vừa chọn · Chưa đúng',{exact:true}).waitFor();
   assert.equal(await page.getByRole('button',{name:first.choices[1],exact:true}).isEnabled(),true);
   await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
   await page.getByRole('radio',{name:'Giọng nữ',exact:true}).waitFor();
   await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);
   assert.equal(requests.filter(r=>r.url.endsWith('/narration')).length,downloadsBeforeRetry,'Same issued words after a retry must reuse the downloaded audio');
   await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
   await page.screenshot({path:path.join(out,'screenshots',`wrong-${width}.png`)});
   await page.getByRole('button',{name:first.choices[0],exact:true}).click();
   await page.getByTestId('correct-answer-feedback').waitFor();
   assert.equal(requests.filter(r=>r.url.endsWith('/lesson/answer')).length,2);
   for(const choice of first.choices)assert.equal(await page.getByRole('button',{name:choice,exact:true}).isDisabled(),true);
   await page.getByText('Em đã chọn · Đúng',{exact:true}).waitFor();
   await page.screenshot({path:path.join(out,'screenshots',`success-${width}.png`)});
   await page.getByRole('button',{name:'Tiếp tục bước tiếp theo',exact:true}).click();
   await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
   assert.equal(await page.getByRole('radio',{name:'Giọng nữ',exact:true}).getAttribute('aria-checked'),'true');
   rows.push({width,panelHeight:panelSize.height,bodyHeight:bodySize.height,overflow:false,manualContinue:true,femaleVoiceRetained:true,audioLoadedAndPlayPause:true,wrongChoiceRetainedAndRetryable:true,correctChoiceRetainedAndLocked:true,noDuplicateDownloadForSameRetrySpeech:true});
   await context.close();console.log('Verified viewport '+width);
  }
 } catch(error) {
  for(const context of browser.contexts())for(const page of context.pages()) {
   await page.screenshot({path:path.join(out,'screenshots','failure.png')});
   console.log('Failure page: '+page.url()+' '+(await page.locator('body').innerText()).slice(0,1500));
  }
  throw error;
 } finally {await browser.close();}
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual project web UI; deterministic lesson API fixtures; real local authentication and real generated audio files. Not physical Android evidence.',rows,errors},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
