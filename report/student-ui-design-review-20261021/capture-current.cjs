const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,origin='https://mathvisionkid-portal.vercel.app',project=path.resolve(root,'../..');
const problem='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn nhà bác Nam có tất cả bao nhiêu cây?';
const screens=[['login','/login'],['home','/'],['lessons','/lessons'],['achievements','/achievements'],['profile','/profile'],['camera','/camera?mode=MATH_TUTOR'],['gallery','/gallery'],['privacy','/privacy'],['crop','/crop'],['preview','/preview'],['processing','/processing'],['line-crop','/recognition/line-crop'],['multiline-review','/recognition/multiline-review'],['multiline-result','/recognition/multiline-result'],['recognition-result','/recognition/result'],['history','/recognition/analytics'],['history-detail','/recognition/trial-analytics'],['correct','/results/correct'],['error-hint','/results/error-hint'],['quality','/results/quality-failure?issue=BLUR'],['scope','/results/out-of-scope'],['review-required','/results/review-required'],['token','/results/token-confirmation'],['source','/learning/math-guide?problemText='+encodeURIComponent(problem)]];
(async()=>{
 fs.mkdirSync(path.join(root,'current'),{recursive:true});
 const credentials=JSON.parse(fs.readFileSync(path.join(project,'infra/local-runtime/pc-preview/demo-accounts.json'),'utf8'));
 const account=credentials.accounts.find(a=>a.role==='STUDENT');
 const response=await fetch(origin+'/api/v1/auth/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:account.email,password:credentials.password}),signal:AbortSignal.timeout(30000)});
 if(!response.ok)throw Error('Current site login status '+response.status);
 const {accessToken}=await response.json();
 const browser=await chromium.launch({headless:true});const records=[];
 try{
  for(const width of [1440,390]){
   const context=await browser.newContext({viewport:{width,height:width===390?844:1000},reducedMotion:'reduce'});
   await context.addInitScript(token=>sessionStorage.setItem('portal_access_token',token),accessToken);
   const page=await context.newPage();
   for(const [id,route] of screens){
    if(width===390&&!['login','home','lessons','achievements','profile','camera','source'].includes(id))continue;
    try{
     await page.goto(origin+'/study'+route,{waitUntil:'domcontentloaded',timeout:30000});
     await page.waitForTimeout(900);await page.evaluate(()=>document.fonts.ready);
     // Personal email is masked for the review artifact only; the live application is unchanged.
     await page.locator('body').evaluate(body=>{const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT);while(walker.nextNode()){const n=walker.currentNode;if(n.nodeValue&&/\b[^\s@]+@[^\s@]+\.[^\s@]+\b/.test(n.nodeValue))n.nodeValue=n.nodeValue.replace(/\b[^\s@]+@[^\s@]+\.[^\s@]+\b/g,'[đã ẩn email]');}});
     const text=(await page.locator('body').innerText()).slice(0,3500);
     const buttons=await page.getByRole('button').allTextContents();
     await page.screenshot({path:path.join(root,'current',`${id}-${width}.png`),fullPage:false});
     records.push({id,width,route,status:'captured',file:`current/${id}-${width}.png`,text,buttons,evidence:'Actual published frontend. Direct route; missing-input states are preserved, not fabricated.'});
     console.log('Captured',id,width);
    }catch(error){records.push({id,width,route,status:'unavailable',error:error.message.split('\n')[0]});console.log('Unavailable',id,width);}
   }
   await context.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(root,'current-captures.json'),JSON.stringify({capturedAt:new Date().toISOString(),origin,records},null,2));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
