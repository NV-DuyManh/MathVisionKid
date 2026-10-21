const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  await page.goto('file:///'+path.join(__dirname,'index.html').replaceAll('\\','/'));
  for(const label of['Điện thoại','Tablet','Laptop']){
   await page.getByRole('button',{name:label,exact:true}).click();
   for(const item of await page.locator('img').all())await item.scrollIntoViewIfNeeded();
   await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
   assert.equal(await page.evaluate(()=>[...document.images].filter(i=>!i.naturalWidth).length),0,label);
   assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),label);
  }
  await page.getByRole('button',{name:'Điện thoại',exact:true}).click();await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:path.join(__dirname,'gallery-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
  await page.screenshot({path:path.join(__dirname,'gallery-mobile.png')});
  const panels=[['lessons','Bài học'],['achievements','Thành tích'],['saved','Bài đã lưu'],['listening-checkin','Nghe giảng'],['step-hint','Từng bước học'],['difficulty-selected','Chỗ chưa hiểu'],['work-correct','Bài làm của em']];
  await page.setViewportSize({width:1820,height:900});
  await page.setContent('<html lang="vi"><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;padding:35px 32px;background:#F3EEFF;color:#291D55;font-family:Segoe UI,sans-serif}h1{font-size:32px;letter-spacing:-1px;margin:0 0 7px}p{font-size:14px;color:#78688E;margin:0 0 25px}.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:18px}.panel{min-width:0}h2{font-size:14px;margin:0 0 12px;color:#624396}.screen{border:1px solid #E0D5F1;border-radius:21px;overflow:hidden;box-shadow:0 7px 25px #43247E12;background:white}.screen img{display:block;width:100%}.tag{font-size:11px;color:#8A759F;margin-top:20px}</style><h1>MathVisionKid · 7 giao diện đã cập nhật</h1><p>Ảnh chụp giao diện thật từ code dự án · Ưu tiên điện thoại · Trạng thái dữ liệu kiểm thử riêng</p><div class="grid">'+panels.map(([name,title],i)=>'<section class="panel"><h2>0'+(i+1)+' · '+title+'</h2><div class="screen"><img src="file:///'+path.join(__dirname,'screenshots',name+'-390.png').replaceAll('\\','/')+'"></div></section>').join('')+'</div><div class="tag">Bản kiểm tra ngày 21.10.2026 · Web / tablet / laptop có trong bảng đối chiếu · Chưa kiểm tra máy thật</div></html>');
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
  await page.screenshot({path:path.join(__dirname,'overview.png'),fullPage:true});
  fs.writeFileSync(path.join(__dirname,'gallery-qa.json'),JSON.stringify({verified:true,views:['390','768','1440'],brokenImages:0,horizontalOverflow:false},null,2));console.log('Gallery images and all three device selectors verified.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
