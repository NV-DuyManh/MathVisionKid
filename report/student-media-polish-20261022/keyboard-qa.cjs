const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,base='http://127.0.0.1:8095/study';
const lessonWav=fs.readFileSync(path.join(root,'../student-media-timeline-20261022/samples/lesson.wav')),replyWav=fs.readFileSync(path.join(root,'../student-media-timeline-20261022/samples/reply.wav'));
const videoFile=fs.readdirSync(path.join(root,'../student-personal-video-20261021')).find(p=>p.endsWith('.mp4'));
const video=videoFile?fs.readFileSync(path.join(root,'../student-personal-video-20261021',videoFile)):null;
const problem='Lan có 36 bút, mẹ cho thêm 27 bút. Hỏi Lan có tất cả bao nhiêu bút?';
const lesson={sessionId:'timeline-lesson-session-12345',revision:0,topic:'Phép cộng',goal:'Tìm số bút',feedback:'',outline:['Hiểu đề','Cộng số bút','Kiểm tra'],stepIndex:0,completed:[],status:'READY',understandingSteps:0,step:{kind:'MATH',title:'Tính số bút của Lan',explanation:'Mình gộp hai nhóm bút để tìm số bút của Lan.',guidance:['Em đặt các chữ số thẳng hàng.','Cộng hàng đơn vị trước rồi cộng hàng chục nhé.'],question:'Lan có tất cả bao nhiêu bút?',choices:[],expression:'36 + 27',unit:'bút',workExcerpt:''}};
(async()=>{fs.mkdirSync(path.join(root,'screenshots'),{recursive:true});const browser=await chromium.launch({headless:true,args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']});const rows=[],errors=[],seeks=[];let asks=0,audioRequests=0,failNarration=false,slowNarration=false;
 try{const context=await browser.newContext({deviceScaleFactor:2,permissions:['microphone'],reducedMotion:'reduce'});
 await context.addInitScript(()=>{sessionStorage.setItem('portal_access_token','timeline-fixture');window.__audio=[];const NativeAudio=window.Audio;window.Audio=function(...args){const e=new NativeAudio(...args);window.__audio.push(e);return e};window.Audio.prototype=NativeAudio.prototype;});
 await context.route('**/api/v1/**',async route=>{const url=route.request().url();let data={id:'timeline-pupil',name:'Minh',role:'STUDENT',grade:4};
  if(url.endsWith('/tutor/lesson'))data=lesson;
  if(url.includes('transcribe'))data={text:'Vì sao cộng hàng đơn vị trước?'};
  if(url.endsWith('/tutor/lesson/narration')){audioRequests++;if(failNarration){failNarration=false;return route.fulfill({status:503,contentType:'application/json',body:'{}'});}if(slowNarration)await new Promise(r=>setTimeout(r,1600));const body=route.request().postDataJSON();return route.fulfill({status:200,contentType:'audio/wav',body:body.paragraphs.join(' ').includes('nhớ một')?replyWav:lessonWav});}
  if(url.endsWith('/tutor/lesson/ask')){asks++;data={answer:'Em bắt đầu từ hàng đơn vị để biết có cần nhớ sang hàng chục không.',spokenExplanation:'Em nhìn hàng đơn vị trước nhé. Nếu gộp được một chục, em nhớ một sang hàng chục. Sau đó em cộng hàng chục và phần nhớ.',followUp:'Hàng đơn vị của hai số là những chữ số nào?',guarded:false};}
  if(url.endsWith('/tutor/lesson/video'))data={videoId:'timeline-private-video-0000001',status:'READY',progress:100,durationSeconds:54,hasAudio:true,title:'Cùng nhìn lại cách làm'};
  if(url.endsWith('/tutor/lesson/video/content')){assert(video,'Missing real MP4');return route.fulfill({status:200,contentType:'video/mp4',body:video});}
  return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
 });
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 async function shot(name){await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(100);const m=await page.evaluate(()=>({width:innerWidth,height:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(e=>e.complete&&!e.naturalWidth).length,outside:[...document.querySelectorAll('[role=button],input[type=range]')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight&&(r.left< -1||r.right>innerWidth+1)}).map(e=>e.getAttribute('aria-label'))}));assert(!m.overflow&&!m.broken&&!m.outside.length,JSON.stringify(m));rows.push({name,...m});await page.screenshot({path:path.join(root,'screenshots',`${name}-${m.width}.png`)});}
 async function drag(ratio,kind='audio'){
  const slider=page.getByRole('slider');await slider.scrollIntoViewIfNeeded();const b=await slider.boundingBox();const before=Number(await slider.inputValue()),max=Number(await slider.getAttribute('max'));
  await page.mouse.move(b.x+9+(b.width-18)*before/max,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+9+(b.width-18)*ratio,b.y+b.height/2,{steps:8});await page.mouse.up();await page.waitForTimeout(250);
  await page.waitForFunction(type=>{const e=type==='video'?document.querySelector('video'):window.__audio.at(-1);return Math.abs(e.currentTime-Number(document.querySelector('input[type=range]').value))<.65},kind,{timeout:3000});
  const selected=Number(await slider.inputValue());const actual=await page.evaluate(type=>{const e=type==='video'?document.querySelector('video'):window.__audio.at(-1);return{time:e.currentTime,paused:e.paused,duration:e.duration}},kind);
  assert(Math.abs(actual.time-selected)<.65,JSON.stringify({selected,actual}));seeks.push({kind,ratio,selected,...actual});return actual;
 }

 await page.setViewportSize({width:390,height:844});await page.goto(base+'/learning/math-guide?problemText='+encodeURIComponent(problem));
 await page.getByRole('checkbox').click();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
 const trigger=page.getByRole('button',{name:'Nghe giảng',exact:true});await trigger.focus();await trigger.press('Enter');
 const dialog=page.getByRole('dialog',{name:'Nghe giảng',exact:true});await dialog.waitFor({timeout:5000});
 await page.waitForFunction(()=>window.__audio.at(-1)?.readyState>=2);
 await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).focus();
 const focus=[];for(let i=0;i<16;i++){await page.keyboard.press('Tab');const item=await page.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e);return{label:e.getAttribute('aria-label')||e.textContent,inside:!!e.closest('[role=dialog]'),outline:s.outlineStyle,outlineWidth:s.outlineWidth}});assert(item.inside,JSON.stringify(item));focus.push(item);}
 const slider=page.getByRole('slider');await slider.focus();await slider.press('End');await page.waitForFunction(()=>window.__audio.at(-1).currentTime>9);await slider.press('Home');await page.waitForFunction(()=>window.__audio.at(-1).currentTime<.1);
 await page.getByRole('button',{name:'Tốc độ 1 lần. Bấm để đổi tốc độ',exact:true}).focus();await page.keyboard.press('Enter');await page.waitForFunction(()=>window.__audio.at(-1).playbackRate===.8);
 await page.getByRole('button',{name:'Tốc độ 0.8 lần. Bấm để đổi tốc độ',exact:true}).press('Enter');await page.waitForFunction(()=>window.__audio.at(-1).playbackRate===1.2);
 await page.getByRole('button',{name:'Đọc lời giảng chi tiết',exact:true}).press('Enter');assert.equal(await page.getByText('Em đặt các chữ số thẳng hàng.',{exact:true}).count(),1);
 assert.equal(await page.evaluate(()=>[...document.querySelectorAll('[aria-controls]')].filter(e=>!document.getElementById(e.getAttribute('aria-controls'))).length),0);
 await page.getByRole('button',{name:'Em đã đọc lời giảng',exact:true}).press('Enter');await page.getByRole('button',{name:'Em chưa hiểu',exact:true}).press('Enter');
 const choice=page.getByRole('button',{name:'Vì sao chọn phép tính này?',exact:true});await choice.press('Space');assert.equal(await choice.getAttribute('aria-pressed'),'true');
 await page.keyboard.press('Escape');await dialog.waitFor({state:'detached'});assert(await trigger.evaluate(e=>e===document.activeElement));
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(root,'keyboard-qa.json'),JSON.stringify({focus,errors,keyboardSeek:true,keyboardSpeed:true,keyboardChoice:true,escapeAndFocusRestore:true},null,2));console.log('Keyboard QA passed; named dialog, 16 trapped tab stops, seek/speed/choice, Escape and restored focus.');
 assert.deepEqual(errors,[]);
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
