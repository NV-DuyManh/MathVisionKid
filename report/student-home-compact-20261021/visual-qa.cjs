const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const phase=process.argv[2]||'after',base=phase==='before'?'http://127.0.0.1:8090/study':'http://127.0.0.1:8091/study';
(async()=>{
 const browser=await chromium.launch({headless:true});const rows=[],errors=[];
 try{
  const context=await browser.newContext({deviceScaleFactor:2});
  await context.addInitScript(()=>{
   sessionStorage.setItem('portal_access_token','home-compact-qa');
   const suffix=Array.from('home-compact-pupil').map(c=>c.codePointAt(0).toString(16)).join('_');
   localStorage.setItem('mathvision_lessons_'+suffix,JSON.stringify([{id:'saved-fractions',timestamp:Date.now()-1000,problemText:'Bài toán phân số',workText:'1/3 + 2/5 = 11/15',reflection:'Em cần chia các phần bằng nhau.',reviewedSteps:2}]));
  });
  await context.route('**/api/v1/**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'home-compact-pupil',name:'Minh',grade:4,role:'STUDENT'})}));
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  for(const[width,height]of[[320,740],[360,800],[390,844],[414,896],[768,1024],[1024,768],[1440,1000],[1920,1080]]){
   await page.setViewportSize({width,height});await page.goto(base+'/(tabs)');
   await page.getByText('1 ngày liên tiếp!',{exact:true}).waitFor();
   await page.evaluate(()=>document.fonts.ready);await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
   const hero=page.getByRole('heading',{name:'Chào Minh!',exact:true});const box=await hero.boundingBox();assert(box);
   const metrics=await page.evaluate(()=>{
    const find=text=>[...document.querySelectorAll('*')].find(e=>e.childNodes.length===1&&e.textContent===text);
    const bounds=e=>{const r=e?.getBoundingClientRect();return r?{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}:null};
    const capture=document.querySelector('[aria-label="Chụp bài toán"]');
    return{capture:bounds(capture),quick:bounds(find('Tiện ích nhanh')),streak:bounds(find('Chuỗi học tập')),suggestions:bounds(find('Bài học gợi ý cho em')||find('Cùng khám phá nhé!')),
     overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>!i.naturalWidth).length,
     outside:[...document.querySelectorAll('button,[role=button]')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight&&(r.left< -2||r.right>innerWidth+2)}).length};
   });
   assert(!metrics.overflow&&!metrics.broken&&!metrics.outside,JSON.stringify({width,...metrics}));
   if(phase==='after'&&width<768){assert(metrics.streak.y<metrics.suggestions.y,'Learning streak should precede suggestions');if(width>=360)assert(metrics.streak.y<height-130,'Learning streak should be visible on entry');}
   rows.push({width,height,...metrics});
   await page.screenshot({path:path.join(__dirname,'screenshots',phase+'-'+width+'.png')});
   await page.screenshot({path:path.join(__dirname,'screenshots',phase+'-full-'+width+'.png'),fullPage:true});
   if(phase==='after'){
    await page.getByRole('button',{name:'Mở máy tính bỏ túi',exact:true}).click();await page.getByRole('button',{name:'Đóng máy tính',exact:true}).click();
    await page.getByRole('button',{name:'Mẹo chụp bài rõ nét',exact:true}).click();await page.getByRole('button',{name:'Đóng mẹo chụp ảnh',exact:true}).click();
    await page.getByRole('button',{name:'Bảo vệ thông tin riêng tư của em'}).scrollIntoViewIfNeeded();
    const final=await page.getByRole('button',{name:'Bảo vệ thông tin riêng tư của em'}).boundingBox();assert(final&&final.y>=0&&final.y+final.height<=height-(width<768?76:0),'Privacy action must remain reachable above the navigation');
   }
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(__dirname,phase+'-qa.json'),JSON.stringify({fixture:'Actual Student export; isolated auth/local history fixtures. Browser viewport evidence, not physical device evidence.',rows,errors},null,2));
  console.log(JSON.stringify({phase,screenshots:rows.length*2,errors,phone:rows.find(r=>r.width===390)},null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
