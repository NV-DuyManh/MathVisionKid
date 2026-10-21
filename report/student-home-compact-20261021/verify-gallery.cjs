const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.goto('file:///'+path.join(__dirname,'index.html').replaceAll('\\','/'));
  for(const name of['Điện thoại','Tablet','Laptop']){
   await page.getByRole('button',{name,exact:true}).click();
   for(const full of[false,true]){
    await page.getByRole('checkbox',{name:'Xem cả trang'}).setChecked(full);
    await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
   }
  }
  await page.getByRole('checkbox',{name:'Xem cả trang'}).uncheck();await page.getByRole('button',{name:'Điện thoại',exact:true}).click();
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
  await page.screenshot({path:path.join(__dirname,'comparison.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
  fs.writeFileSync(path.join(__dirname,'gallery-qa.json'),JSON.stringify({passed:true,deviceSelectors:3,fullPageToggle:true,imagesLoaded:true,horizontalOverflow:false},null,2));
  console.log('Comparison gallery verified.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
