const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,{screens}=JSON.parse(fs.readFileSync(path.join(root,'catalog.json'),'utf8'));
const screenUrl=id=>pathToFileURL(path.join(root,'prototype.html')).href+'?theme=4&screen='+id;
const componentSpecs=[['navigation','Thanh điều hướng tím đậm',1440,'home','.sidebar'],['header','Đầu trang và nhận diện',1440,'home','.topbar'],['hero','Thẻ chào và linh vật',1440,'home','[data-component="hero"]'],['streak','Chuỗi học tập',1440,'home','[data-component="streak"]'],['journey','Hành trình uốn cong',1440,'home','[data-component="journey"]'],['utilities','Bốn thẻ tiện ích',1440,'home','[data-component="utilities"]'],['suggestion','Bài học gợi ý',1440,'home','[data-component="suggestions"]'],['bottom-nav','Điều hướng điện thoại',390,'home','.bottom-nav'],['topics','Danh sách chủ đề',768,'lessons','.topic-list'],['badges','Thành tích và huy hiệu',768,'achievements','.badge-grid'],['saved','Bài đã lưu',768,'profile','#profile-list'],['math','Một bước học rõ ràng',768,'math','.focus-main'],['ask','Hỏi bài bằng chữ hoặc giọng nói',390,'ask','.sheet'],['voice','Nghe giảng',390,'voice','.sheet'],['voices','Tối đa hai lựa chọn giọng',390,'voices','.sheet'],['fraction','Phân số tương tác',390,'fraction','.sheet'],['review','Nhận xét và vùng tô vàng',390,'work-review','.sheet'],['solution','Bài giải sau khi học',390,'complete','.sheet']];
(async()=>{const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1,reducedMotion:'reduce'}),page=await context.newPage(),errors=[],checks=[];
page.on('pageerror',e=>errors.push(e.message));
async function open(id,width,height){await page.setViewportSize({width,height});await page.goto(screenUrl(id));await page.evaluate(()=>document.fonts.ready);await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode().catch(()=>{}))));}
try{
for(const width of [320,360,375,390,414,768,1024,1440,1920]){
 const height=width<701?920:width===768?1200:1024;
 for(const s of screens){await open(s.id,width,height);const measure=await page.evaluate(()=>({body:document.body.scrollWidth,html:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length}));checks.push({screen:s.id,width,...measure});
  if(width===390)await page.screenshot({path:path.join(root,'screens',s.id+'-390.png'),fullPage:true});
  if(['home','math','lessons','profile','achievements'].includes(s.id)&&[768,1440].includes(width))await page.screenshot({path:path.join(root,'screens',s.id+'-'+width+'.png'),fullPage:false});
  if(s.id==='home'&&[1024,1920].includes(width))await page.screenshot({path:path.join(root,'screens','home-'+width+'.png'),fullPage:false});
 }
 console.log('Checked',screens.length,'frames at',width);
}
// High-resolution detail shots are browser screenshots of individual coded components.
await context.close();const detailContext=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:2,reducedMotion:'reduce'}),details=await detailContext.newPage();
for(const [id,title,width,screen,selector]of componentSpecs){await details.setViewportSize({width,height:width===390?1000:1024});await details.goto(screenUrl(screen));await details.evaluate(()=>document.fonts.ready);await details.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode().catch(()=>{}))));await details.locator(selector).screenshot({path:path.join(root,'components',id+'.png')});}
await detailContext.close();
const issues=checks.filter(c=>c.body>c.width+1||c.html>c.width+1||c.broken);fs.writeFileSync(path.join(root,'components.json'),JSON.stringify(componentSpecs.map(([id,title,width,screen,selector])=>({id,title,width,screen,selector,file:'components/'+id+'.png'})),null,2));fs.writeFileSync(path.join(root,'visual-qa.json'),JSON.stringify({date:'2026-10-21',scope:'Standalone coded design preview, no product integration',frameCount:screens.length,widths:[320,360,375,390,414,768,1024,1440,1920],views:checks.length,issues,scriptErrors:errors,checks,physicalDevice:false,aiInference:false},null,2));
console.log('QA:',checks.length,'views;',issues.length,'overflow/image issues;',errors.length,'script errors.');if(issues.length||errors.length){console.log(JSON.stringify({issues:issues.slice(0,8),errors:errors.slice(0,3)}));process.exitCode=1;}
}finally{await browser.close()}})().catch(e=>{console.error(e.message);process.exitCode=1});
