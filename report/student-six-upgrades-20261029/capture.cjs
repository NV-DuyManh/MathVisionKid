const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=__dirname,paragraphs=JSON.parse(fs.readFileSync(path.join(out,'real-script.json'),'utf8')).paragraphs;
const problem='Vườn cây có 1/3 số cây là táo, 2/5 số cây là xoài, còn lại là cam. Có 16 cây cam. Hỏi vườn có tất cả bao nhiêu cây?';
const sourceId='six-upgrades-controlled-session-12345';
const steps=[
 {kind:'MATH',title:'Phần cây táo và xoài',explanation:'Cộng hai phần cây đã biết.',question:'Tổng hai phần là bao nhiêu?',expression:'1/3 + 2/5',choices:[],unit:'',workExcerpt:'',guidance:['Cộng một phần ba và hai phần năm.']},
 {kind:'MATH',title:'Phần cây cam',explanation:'Lấy cả vườn trừ phần cây táo và xoài.',question:'Phần cây cam là bao nhiêu?',expression:'1 - 11/15',choices:[],unit:'',workExcerpt:'',guidance:['Lấy một trừ mười một phần mười lăm.']},
 {kind:'MATH',title:'Số cây cả vườn',explanation:'Chia số cây cam cho phần cây cam.',question:'Trong vườn có bao nhiêu cây?',expression:'16 / (4/15)',choices:[],unit:'cây',workExcerpt:'',guidance:['Chia mười sáu cho bốn phần mười lăm.']}
];
const reading={sessionId:sourceId,revision:0,topic:'Cùng hiểu đề',goal:'Tách dữ kiện',outline:['Dữ kiện','Câu hỏi','Cách làm','Phần cây','Số cây'],understandingSteps:3,stepIndex:0,completed:[],status:'READY',feedback:'',step:{kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc dữ kiện trong đề.',question:paragraphs[paragraphs.length-1],guidance:paragraphs.slice(0,-1),choices:['Có 1/3 cây táo, 2/5 cây xoài và 16 cây cam.','Tìm số cây trong vườn.'],expression:'',unit:'',workExcerpt:''}};
function mathLesson(index,completed,status='READY',feedback='') {return{sessionId:sourceId,revision:index,topic:'Phân số',goal:'Tìm số cây',outline:steps.map(s=>s.title),understandingSteps:0,stepIndex:index,step:steps[index]||null,completed,status:index===3?'COMPLETE':status,feedback,...(index===3?{conclusion:'Đáp số: 60 cây.'}:{})};}
async function shot(page,name){await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:path.join(out,'screenshots',name+'.png')});}
async function player(page){await page.getByTestId('narration-player').waitFor({state:'visible'});await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.max)>1);}
(async()=>{
 fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
 const auth=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});assert(auth.ok);const tokens=await auth.json();
 const browser=await chromium.launch({headless:true}),rows=[],errors=[];
 try{for(const [width,height] of [[320,844],[390,844],[768,1024],[1440,900],[844,390]]){
  const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:2,reducedMotion:'reduce'});
  await context.addInitScript(({accessToken,refreshToken})=>{sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);},tokens);
  let mode='reading',current=reading,review=null,completed=[],checkpointCalls=0;
  await context.route('**/api/v1/student/tutor/**',async route=>{
   const url=route.request().url(),body=route.request().postDataJSON();const json=(value,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(value)});
   if(url.endsWith('/lesson/resume'))return json({...current,review});
   if(url.endsWith('/lesson/checkpoint')){checkpointCalls++;return json({expression:'2 - 11/15',question:'Thử cùng cách tính với một số khác nhé.',checked:!!body.answer,correct:body.answer==='19/15',feedback:body.answer?(body.answer==='19/15'?'Đúng rồi! Em đã áp dụng được cách tính với số khác.':'Chưa khớp. Em làm lại cùng thứ tự tính như bước vừa học nhé.') :''});}
   if(url.endsWith('/narration'))return route.fulfill({status:200,contentType:'audio/wav',body:fs.readFileSync(path.join(out,body.voice.includes('HoaiMy')?'female.wav':'male.wav'))});
   if(url.endsWith('/narration/prepare')||url.endsWith('/narration/status'))return json({phase:'ready',mode:'online',percent:100,elapsedMs:0,completedChunks:2,totalChunks:2});
   if(url.endsWith('/lesson/answer')){
    const expected=['11/15','4/15','60'][current.stepIndex];
    if(body.answer!==expected)return json({...current,status:'TRY_AGAIN',feedback:'Em tính lại nhé.'});
    completed=[...completed,{...current.step,answer:expected,solutionSentence:current.step.title+' là:',calculationDetails:[]}];
    review={question:current.step.question,choices:current.step.choices,studentAnswer:expected};current=mathLesson(completed.length,completed,'CORRECT','Đúng bước này rồi!');return json(current);
   }
   if(url.endsWith('/lesson')){current=mode==='reading'?reading:mathLesson(0,[]);return json(current);}
   return json({phase:'preparing'});
  });
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  const open=()=>page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent(problem),{timeout:120000});
  await open();await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();await page.getByTestId('lesson-problem-reference').waitFor();
  await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();await player(page);await page.getByRole('button',{name:'Đọc lời giảng chi tiết'}).click();
  const second=page.getByRole('button',{name:'Nghe đoạn 2: '+paragraphs[1],exact:true});await second.click();await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).waitFor();
  const slider=page.getByRole('slider',{name:'Tua nghe giảng',exact:true});assert(Number(await slider.inputValue())>0);await shot(page,'aligned-'+width);
  await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
  if(width===390){await page.getByRole('button',{name:'Nghe đoạn 1: '+paragraphs[0],exact:true}).focus();await page.keyboard.press('Tab');assert(await second.evaluate(el=>el===document.activeElement));assert.equal(await second.evaluate(el=>getComputedStyle(el).outlineWidth),'2px');await shot(page,'keyboard-cue-390');}
  await page.getByRole('radio',{name:'Giọng nữ',exact:true}).click();await player(page);
  const bounds=await slider.boundingBox();await slider.click({position:{x:bounds.width*.4,y:bounds.height/2}});await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]')?.value)>2);
  await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();await page.getByRole('button',{name:'Hỏi bài',exact:true}).click();
  const draft='Vì sao phải cộng hai phần cây?';await page.getByRole('textbox',{name:'Câu hỏi của em',exact:true}).fill(draft);
  await page.reload();await page.getByTestId('lesson-problem-reference').waitFor();await page.getByText('Đã khôi phục bước đang học của em.',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Hỏi bài',exact:true}).click();assert.equal(await page.getByRole('textbox',{name:'Câu hỏi của em',exact:true}).inputValue(),draft);await shot(page,'draft-restored-'+width);
  await page.getByRole('button',{name:'Đóng Hỏi bài',exact:true}).click();await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();await player(page);
  assert.equal(await page.getByRole('radio',{name:'Giọng nữ',exact:true}).getAttribute('aria-checked'),'true');
  const restoredPosition=Number(await slider.inputValue());assert(restoredPosition>=2);assert.equal(await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).count(),0);await shot(page,'position-restored-'+width);
  await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();await page.goto('http://127.0.0.1:8081/');await page.getByRole('button',{name:'Tiếp tục bài đang học',exact:true}).waitFor();await shot(page,'home-resume-'+width);
  if(width===390){const resume=page.getByRole('button',{name:'Tiếp tục bài đang học',exact:true});await resume.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');assert(await resume.evaluate(el=>el===document.activeElement));assert.equal(await resume.evaluate(el=>getComputedStyle(el).outlineWidth),'2px');await shot(page,'keyboard-home-390');}
  // New isolated source session for the mathematical follow-up fixture.
  mode='math';current=mathLesson(0,[]);review=null;completed=[];
  await page.evaluate(()=>{Object.keys(localStorage).filter(key=>key.startsWith('mathvision_progress_')).forEach(key=>localStorage.removeItem(key));});
  await open();await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).check();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
  await page.getByRole('textbox',{name:'Câu trả lời của em',exact:true}).fill('11/15');await page.getByRole('button',{name:'Kiểm tra bước này',exact:true}).click();await page.getByTestId('checked-student-answer').waitFor();
  await page.reload();await page.getByTestId('checked-student-answer').waitFor();assert.equal(await page.getByTestId('checked-student-answer').getByLabel('11 phần 15',{exact:true}).count(),1);await shot(page,'review-restored-'+width);
  await page.getByRole('button',{name:'Tiếp tục bước tiếp theo',exact:true}).click();await page.getByRole('textbox',{name:'Câu trả lời của em',exact:true}).fill('4/15');await page.getByRole('button',{name:'Kiểm tra bước này',exact:true}).click();
  await page.getByRole('button',{name:'Thử nhanh để nhớ cách làm',exact:true}).click();const checkInput=page.getByRole('textbox',{name:'Kết quả câu thử nhanh',exact:true});await checkInput.fill('18/15');await page.getByRole('button',{name:'Kiểm tra câu thử nhanh',exact:true}).click();await page.getByText('Chưa khớp. Em làm lại cùng thứ tự tính như bước vừa học nhé.',{exact:true}).waitFor();assert.equal(await checkInput.inputValue(),'18/15');await shot(page,'check-retry-'+width);
  await checkInput.fill('19/15');await page.getByRole('button',{name:'Kiểm tra câu thử nhanh',exact:true}).click();await page.getByText('Đúng rồi! Em đã áp dụng được cách tính với số khác.',{exact:true}).waitFor();await shot(page,'check-correct-'+width);
  assert.equal(current.stepIndex,2);assert.equal(checkpointCalls,3);assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1));
  const metrics=await page.evaluate(()=>JSON.parse(localStorage.getItem('mathvision_voice_metrics_v1')||'[]'));
  assert(metrics.some(row=>row.stage==='player'&&row.outcome==='ready'));assert(metrics.every(row=>!('text'in row)&&!('sessionId'in row)));
  rows.push({width,height,realAudioCues:true,paragraphClickPlays:true,draftRestoredAfterImmediateReload:true,voiceKept:true,restoredPosition,noAutoplayOnRestore:true,reviewAndSelectedAnswerRestored:true,homeResumeCard:true,checkpointWrongThenCorrect:true,checkpointDoesNotAdvanceLesson:true,noHorizontalOverflow:true,keyboardFocusVisible:width===390?true:null,voiceMeasurements:metrics.length});
  await context.close();console.log('Verified six upgrades '+width+'x'+height);
 }}catch(error){for(const context of browser.contexts())for(const page of context.pages()){try{await shot(page,'failure');console.log((await page.locator('body').innerText()).slice(0,1000));}catch{}}throw error;}
 finally{await browser.close();}
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual Student web components, controlled lesson/resume/checkpoint API fixtures, local real authentication and real generated WAV with decoded frame cue points. Not physical Android evidence or a model correctness score.',rows,errors},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
