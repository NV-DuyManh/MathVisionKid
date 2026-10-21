const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const sample=JSON.parse(fs.readFileSync(path.join(__dirname,'samples.json'),'utf8')).find(s=>s.example==='garden-step');
const base='http://127.0.0.1:8088/study';
const lesson={sessionId:'personal-browser-session-123456',revision:0,topic:'Phân số',goal:'Tìm tổng số cây trong vườn',outline:['Phần táo và xoài','Phần cam','Cả vườn'],stepIndex:0,completed:[],status:'READY',understandingSteps:0,feedback:'',step:{kind:'MATH',title:'Phần táo và xoài',explanation:'Cộng phần cây táo với phần cây xoài.',question:'Tổng hai phân số là bao nhiêu?',expression:'1/3 + 2/5',unit:'',workExcerpt:'',choices:[]}};
(async()=>{
 fs.mkdirSync(path.join(__dirname,'screenshots'),{recursive:true});
 const browser=await chromium.launch({headless:true});const rows=[],errors=[];
 try{
  const context=await browser.newContext({deviceScaleFactor:2});
  await context.addInitScript(()=>sessionStorage.setItem('portal_access_token','isolated-video-qa'));
  let count=0,failNext=false;
  await context.route('**/api/v1/**',route=>{
   const url=route.request().url();let data={id:'isolated-video-pupil',name:'Minh',grade:4,role:'STUDENT'};
   const status={videoId:'v'.repeat(32),status:'READY',progress:100,hasAudio:true,durationSeconds:Math.ceil(sample.videoSeconds),title:lesson.goal};
   if(url.endsWith('/lesson/video/content'))return route.fulfill({status:200,contentType:'video/mp4',body:fs.readFileSync(path.join(__dirname,'garden-step-voiced.mp4'))});
   if(url.endsWith('/lesson/video/status'))data=++count<2?{...status,status:'RENDERING',hasAudio:false,progress:55,durationSeconds:0}:status;
   else if(url.endsWith('/lesson/video')){
    count=0;
    if(failNext){failNext=false;return route.fulfill({status:503,contentType:'application/json',body:'{"message":"private provider error"}'});}
    data={...status,status:'RENDERING',progress:5,hasAudio:false,durationSeconds:0};
   }else if(url.endsWith('/tutor/lesson'))data=lesson;
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  async function shot(name,width,height){
   await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(120);
   const layout=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).length,outside:[...document.querySelectorAll('button,[role=button]')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight&&(r.left< -2||r.right>innerWidth+2)}).length}));
   assert(!layout.overflow&&!layout.broken&&!layout.outside,JSON.stringify({name,width,...layout}));
   rows.push({name,width,height,...layout});await page.screenshot({path:path.join(__dirname,'screenshots',`${name}-${width}.png`)});
  }
  async function open(){
   await page.goto(base+'/learning/math-guide?problemText='+encodeURIComponent('Vườn cây có 1/3 cây táo, 2/5 cây xoài và 16 cây cam. Hỏi cả vườn có bao nhiêu cây?'));
   await page.getByRole('checkbox').click();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
   await page.getByRole('button',{name:'Xem thêm',exact:true}).click();await page.getByRole('button',{name:'Xem video bài này',exact:true}).click();
  }
  for(const [width,height]of[[320,740],[390,844],[768,1024],[1024,768],[1440,1000]]){
   await page.setViewportSize({width,height});await open();
   await page.getByText('Đang dựng video bài của em',{exact:true}).waitFor();await shot('preparing',width,height);
   await page.getByRole('button',{name:'Phát video minh họa',exact:true}).waitFor();await shot('ready',width,height);
   const video=page.locator('video');assert(await video.evaluate(v=>v.paused));
   await page.getByRole('button',{name:'Phát video minh họa',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('video')?.currentTime>.4);
   assert(await video.evaluate(v=>!v.muted&&v.volume>0));
   await page.getByRole('button',{name:'Tạm dừng video',exact:true}).click();assert(await video.evaluate(v=>v.paused));
   await shot('paused',width,height);
   await page.getByRole('button',{name:'Đóng Video bài của em',exact:true}).click();assert.equal(await page.locator('video').count(),0);
  }
  await page.setViewportSize({width:390,height:844});failNext=true;await open();
  await page.getByRole('button',{name:'Thử tạo video lại',exact:true}).waitFor();await shot('retry',390,844);
  assert(!(await page.locator('body').innerText()).includes('private provider'));
  await page.getByRole('button',{name:'Thử tạo video lại',exact:true}).click();await page.getByRole('button',{name:'Phát video minh họa',exact:true}).waitFor();
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(__dirname,'visual-qa.json'),JSON.stringify({fixture:'Real production UI; isolated auth/job status fixtures; real voiced MP4 produced by production renderer. Not live AI or physical device evidence.',rows,errors},null,2));
  console.log(JSON.stringify({captures:rows.length,errors},null,2));
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
