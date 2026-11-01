const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const response=await fetch('http://127.0.0.1:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});assert(response.ok);const tokens=await response.json();
 const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:390,height:844}}),errors=[];
 try{await context.addInitScript(({accessToken,refreshToken})=>{sessionStorage.setItem('portal_access_token',accessToken);sessionStorage.setItem('portal_refresh_token',refreshToken);},tokens);const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 await page.goto('http://127.0.0.1:8081/',{timeout:120000});await page.getByRole('button',{name:'Chụp bài toán',exact:true}).waitFor({timeout:60000});await page.evaluate(()=>document.fonts.ready);
 await page.goto('http://127.0.0.1:8081/learning/math-guide?problemText='+encodeURIComponent('Có 12 bút và 8 bút. Hỏi có tất cả bao nhiêu bút?'),{timeout:120000});await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số',exact:true}).waitFor({timeout:60000});
 assert(!await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));const metrics=await page.evaluate(()=>{window.dispatchEvent(new Event('pagehide'));return JSON.parse(localStorage.getItem('mathvision_web_performance_v1')||'null');});assert(metrics&&'lcpMs'in metrics&&'cls'in metrics&&!('url'in metrics));assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(__dirname,'final-smoke.json'),JSON.stringify({evidence:'Real local Student login and actual web routes after both exports and development-server restart; no lesson/model/TTS mocks or new synthesis in this smoke test.',home:true,sourceConfirmation:true,webMeasurementsPersist:true,noHorizontalOverflow:true,errors},null,2));console.log('Current Student web verified after exports.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
