const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto('file:///'+path.join(__dirname,'index.html').replaceAll('\\','/'));
  const gallery=page.locator('#gallery');
  for(const label of ['Điện thoại 390','Điện thoại nhỏ 320','Tablet 768','Desktop 1440','Điện thoại ngang']){
   await page.getByRole('button',{name:label,exact:true}).click();
   await page.waitForFunction(()=>[...document.querySelectorAll('#gallery img')].every(img=>img.complete&&img.naturalWidth>0));
  }
  await page.getByRole('button',{name:'Điện thoại 390',exact:true}).click();
  await page.getByRole('button',{name:'Phóng lớn Nghe giảng',exact:true}).click();assert(await page.getByRole('dialog').isVisible());
  await page.keyboard.press('Escape');assert(!await page.getByRole('dialog').isVisible());
  await page.screenshot({path:path.join(__dirname,'gallery.png'),fullPage:true});
  await page.goto('http://127.0.0.1:8081/login',{timeout:120000});
  await page.getByLabel('Tài khoản email hoặc mã học sinh',{exact:true}).fill('student');await page.getByLabel('Mật khẩu',{exact:true}).fill('123');
  await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();
  await page.waitForURL(url=>!url.pathname.includes('login'),{timeout:30000});
  await page.getByRole('button',{name:'Chụp bài toán',exact:true}).waitFor();
  await page.reload();await page.getByRole('button',{name:'Chụp bài toán',exact:true}).waitFor();
  assert(!page.url().includes('/login'));assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(__dirname,'gallery-qa.json'),JSON.stringify({galleryWidths:5,allImagesLoaded:true,enlargeAndEscape:true,realStudentLogin:true,sessionSurvivesReload:true,postExportDevelopmentPageLoads:true,errors},null,2));
  console.log('Gallery, real Student login and post-export dev page passed');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
