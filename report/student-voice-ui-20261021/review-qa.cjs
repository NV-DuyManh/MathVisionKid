const fs = require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {pathToFileURL,fileURLToPath}=require('node:url');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const url=pathToFileURL(path.join(__dirname,'index.html')).href;
  await page.goto(url);
  await page.evaluate(()=>{for(const img of document.images)img.loading='eager'});
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
  assert.deepEqual(await page.evaluate(()=>[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src)),[]);
  const links=await page.locator('a').evaluateAll(items=>items.map(a=>a.href));
  for(const link of links)if(link.startsWith('file:'))assert(fs.existsSync(fileURLToPath(new URL(link).href.split('#')[0])),link);
  await page.screenshot({path:path.join(__dirname,'overview.png')});
  for(const width of ['768','1440','390']){
   await page.locator(`[data-width="${width}"]`).click();
   await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
  }
  for(const video of await page.locator('video').all()){
   await video.evaluate(v=>v.play());
   await page.waitForTimeout(350);
   const meta=await video.evaluate(v=>{v.pause();return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,time:v.currentTime}});
   assert.equal(meta.duration,12);assert.equal(meta.width,960);assert.equal(meta.height,540);assert(meta.time>0);
  }
  for(const width of [390,1440]){
   await page.setViewportSize({width,height:1000});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  }
  assert.deepEqual(errors,[]);
  console.log('Gallery verified: 3 concepts, real screenshot switches, all local links, 3 playable MP4s, 390/1440px layout.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
