const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL,fileURLToPath}=require('node:url');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
  for(const link of await page.locator('a').evaluateAll(items=>items.map(a=>a.href)))if(link.startsWith('file:'))assert(fs.existsSync(fileURLToPath(link.split('#')[0])),link);
  await page.screenshot({path:path.join(__dirname,'overview.png')});
  for(const width of ['768','1440','390']){
   await page.locator(`[data-width="${width}"]`).click();
   await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth));
  }
  for(const video of await page.locator('video').all()){
   await video.scrollIntoViewIfNeeded();await video.evaluate(v=>v.play());
   await page.waitForFunction(v=>v.currentTime>.2,await video.elementHandle());
   const playback=await video.evaluate(v=>{v.pause();return {duration:v.duration,time:v.currentTime,muted:v.muted,volume:v.volume}});
   assert(playback.time>0&&playback.duration>15&&!playback.muted&&playback.volume>0,JSON.stringify(playback));
  }
  for(const width of [390,1440]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  assert.deepEqual(errors,[]);console.log('Review verified: local links/images, device switches, 3 voiced MP4 playback, 390/1440 layout.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
