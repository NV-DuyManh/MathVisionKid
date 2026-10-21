const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,{screens,themes}=JSON.parse(fs.readFileSync(path.join(root,'catalog.json'),'utf8'));
(async()=>{const browser=await chromium.launch({headless:true}),qa=[];let errors=[];
try{const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
for(const theme of themes){const target=path.join(root,'proposals',String(theme.id));fs.mkdirSync(target,{recursive:true});
 for(const width of [390,768,1440]){await page.setViewportSize({width,height:width===768?1024:width===390?844:940});
  for(const screen of screens){await page.goto(pathToFileURL(path.join(root,'prototype.html')).href+'?theme='+theme.id+'&screen='+screen.id);await page.evaluate(()=>document.fonts.ready);await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(img=>img.decode().catch(()=>{}))));
   const measure=await page.evaluate(()=>({viewport:innerWidth,body:document.body.scrollWidth,html:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length}));
   qa.push({theme:theme.id,screen:screen.id,width,...measure});
   if(width===390||screen.id==='home'||screen.id==='math')await page.screenshot({path:path.join(target,`${screen.id}-${width}.png`),fullPage:false});
  }
  console.log('Verified proposal',theme.id,'width',width,'screens',screens.length);
 }
}
const failures=qa.filter(r=>r.body>r.width+1||r.html>r.width+1||r.broken);
fs.writeFileSync(path.join(root,'visual-qa.json'),JSON.stringify({checkedAt:new Date().toISOString(),screens:screens.length,themes:themes.length,widths:[390,768,1440],checks:qa,failures,errors,evidence:'Browser-rendered design prototypes only. No application code or backend/model changed. No physical-device evidence.'},null,2));
console.log('Responsive QA:',qa.length,'views;',failures.length,'overflow/image issues;',errors.length,'script errors.');
if(failures.length||errors.length){console.log(JSON.stringify(failures.slice(0,12)));process.exitCode=1;}
await context.close();
}finally{await browser.close()}})().catch(e=>{console.error(e.message);process.exitCode=1});
