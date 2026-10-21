const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({headless:true}),page=await browser.newPage({viewport:{width:2280,height:1200},deviceScaleFactor:1});try{for(let i=0;i<5;i++){
await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href+'?print=1&theme='+i);await page.evaluate(()=>document.fonts.ready);await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode().catch(()=>{}))));await page.screenshot({path:path.join(__dirname,'boards',`board-${i}-full.png`),fullPage:true});console.log('Exported board',i,'height',await page.evaluate(()=>document.documentElement.scrollHeight));
await page.setViewportSize({width:2280,height:1560});await page.screenshot({path:path.join(__dirname,'boards',`board-${i}-preview.png`),fullPage:false});await page.setViewportSize({width:2280,height:1200});
}}finally{await browser.close()}})().catch(e=>{console.error(e.message);process.exitCode=1});
