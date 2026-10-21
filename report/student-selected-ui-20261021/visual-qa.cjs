const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,base='http://127.0.0.1:8090/study';
const problem='Lan có 36 bút, mẹ cho thêm 27 bút. Hỏi Lan có tất cả bao nhiêu bút?';
const garden='Vườn cây nhà bác Nam có 1/3 số cây là cây táo, 2/5 số cây là cây xoài, còn lại là cây cam. Biết rằng số cây cam có trong vườn là 16 cây. Hỏi trong vườn có tất cả bao nhiêu cây?';
const works=['Số phần cây táo và xoài là:','1/3 + 2/5 = 11/15','Số phần cây cam là:','1 - 11/15 = 4/15'];
const lesson={sessionId:'selected-ui-session-00000001',revision:0,topic:'Phép cộng',goal:'Tìm số bút',feedback:'',outline:['Hiểu đề','Cộng số bút','Kiểm tra lại'],stepIndex:0,completed:[],status:'READY',understandingSteps:0,step:{kind:'MATH',title:'Tính số bút của Lan',explanation:'Gộp số bút ban đầu với số bút mẹ cho thêm.',question:'Lan có tất cả bao nhiêu bút?',choices:[],expression:'36 + 27',unit:'bút',workExcerpt:''}};
(async()=>{
 fs.mkdirSync(path.join(root,'screenshots'),{recursive:true}); const browser=await chromium.launch({headless:true});const rows=[],errors=[];
 try{
  const context=await browser.newContext({deviceScaleFactor:2});let requests=0;
  await context.addInitScript(()=>{
   sessionStorage.setItem('portal_access_token','selected-ui-fixture');
   const owner='selected-ui-pupil',suffix=Array.from(owner).map(c=>c.codePointAt(0).toString(16)).join('_');
   localStorage.setItem('mathvision_lessons_'+suffix,JSON.stringify([
    {id:'saved-fractions',timestamp:Date.now()-1000,problemText:'Bài toán phân số: vườn cây của bác Nam',workText:'1/3 + 2/5 = 11/15',reflection:'Các phần cần cùng kích thước trước khi cộng.',reviewedSteps:3},
    {id:'saved-shape',timestamp:Date.now()-86400000,problemText:'Hình học: tính diện tích tam giác',workText:'12 × 8 : 2 = 48 (cm²)',reflection:'Tìm đáy và chiều cao rồi cùng tính.',reviewedSteps:2},
    {id:'saved-word',timestamp:Date.now()-172800000,problemText:'Bài toán có lời văn: số bút của Lan',workText:'36 + 27 = 63 (bút)',reflection:'',reviewedSteps:2},
    {id:'saved-add',timestamp:Date.now()-259200000,problemText:'Luyện tập phép cộng',workText:'',reflection:'Em nhớ đặt thẳng các hàng.',reviewedSteps:1}
   ]));
   window.__spoken=[];
   window.SpeechSynthesisUtterance=class{constructor(text){this.text=text}};
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{getVoices:()=>[{voiceURI:'vi-fixture',name:'HoaiMy Natural',lang:'vi-VN'}],speak:u=>{window.__spoken.push(u.text);setTimeout(()=>u.onend?.(),15)},cancel:()=>{},addEventListener:()=>{},removeEventListener:()=>{}}});
  });
  let validReview=false;
  await context.route('**/api/v1/**',route=>{
   const url=route.request().url();let data={id:'selected-ui-pupil',name:'Minh',grade:4,role:'STUDENT'};
   if(url.endsWith('/tutor/lesson'))data=lesson;
   if(url.endsWith('/tutor/lesson/answer'))data={...lesson,revision:1,status:'HINT',feedback:'Đặt các chữ số thẳng hàng. Em cộng hàng đơn vị trước rồi cộng hàng chục.'};
   if(url.endsWith('/tutor/lesson/ask')){requests++;data={answer:'Mình gộp hai nhóm bút nên chọn phép cộng.',spokenExplanation:'Em tưởng tượng đặt nhóm ba mươi sáu bút cạnh nhóm hai mươi bảy bút. Để biết tất cả có bao nhiêu bút, mình gộp hai nhóm bằng phép cộng. Em tự cộng từng hàng nhé.',followUp:'Em sẽ bắt đầu cộng ở hàng nào?',guarded:false};}
   if(url.endsWith('/tutor/inspect'))data={kind:'MIXED',problemText:garden,needsProblem:false,lines:works.map((text,i)=>({text,uncertain:false,box:[[110,475,880,565],[365,565,865,700],[110,700,800,800],[365,800,850,945]][i]}))};
   if(url.endsWith('/tutor/work-review')){
    const body=route.request().postDataJSON();
    data={sourceId:body.sourceId,status:validReview?'CORRECT':'NEEDS_REVISION',summary:validReview?'Các phép tính và cách trình bày phù hợp với đề.':'Cùng nhìn lại cách em ghi đơn vị sau phân số.',praise:validReview?'Em đã trình bày rõ và kiểm tra rất cẩn thận!':'',nextAction:validReview?'Em đọc lại cách làm bằng lời nhé.':'Em đối chiếu dòng được đánh dấu rồi tự sửa nhé.',alternative:validReview?'Em có thể dùng sơ đồ đoạn thẳng để kiểm tra.':'',rows:works.map((sourceText,lineIndex)=>({sourceText,lineIndex,status:validReview||lineIndex!==3?'OK':'FIX',feedback:validReview||lineIndex!==3?'Phép tính phù hợp.':'Phân số chỉ phần của cả vườn; em xem lại cách ghi đơn vị.',hints:validReview||lineIndex!==3?[]:['Em phân biệt phần số cây và số cây nhé.']}))};
   }
   return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  async function shot(name,width,height){
   await page.evaluate(()=>document.fonts.ready);await page.waitForFunction(()=>[...document.images].every(i=>i.complete),null,{timeout:10000});await page.waitForTimeout(120);
   const info=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>!i.naturalWidth).length,outside:[...document.querySelectorAll('button,[role=button],[role=radio],[role=tab],input')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height&&r.bottom>0&&r.top<innerHeight&&(r.left< -2||r.right>innerWidth+2)}).map(e=>e.getAttribute('aria-label')||e.textContent)}));
   rows.push({name,width,height,...info});assert(!info.overflow&&!info.broken&&!info.outside.length,JSON.stringify(rows.at(-1)));
   await page.screenshot({path:path.join(root,'screenshots',name+'-'+width+'.png')});
  }
  for(const [width,height]of[[320,740],[390,844],[768,1024],[1024,768],[1440,1000]]){
   await page.setViewportSize({width,height});
   await page.goto(base+'/lessons');await page.getByText('Hôm nay em học gì?',{exact:true}).waitFor();await shot('lessons',width,height);
   await page.getByRole('button',{name:'Chọn Lớp 5',exact:true}).click();await page.getByRole('button',{name:/Mở bài:/}).first().click();await shot('lesson-open',width,height);
   await page.goto(base+'/profile');await page.getByRole('button',{name:/Học tiếp:/}).first().waitFor();await shot('saved',width,height);
   await page.getByRole('tab',{name:'Bài làm',exact:true}).click();await shot('saved-work',width,height);
   await page.getByRole('tab',{name:'Ghi chú',exact:true}).click();await shot('notes',width,height);
   await page.getByRole('button',{name:'Tùy chọn bài 1',exact:true}).click();await page.getByRole('button',{name:'Mở bài học',exact:true}).waitFor();await shot('saved-options',width,height);
   await page.goto(base+'/achievements');await page.getByText('Tuyệt vời!',{exact:true}).waitFor();await shot('achievements',width,height);
   if(await page.getByRole('button',{name:'Xem thành tích của em',exact:true}).count()){await page.getByRole('button',{name:'Xem thành tích của em',exact:true}).click();await shot('achievement-details',width,height);}
   await page.goto(base+'/learning/math-guide?problemText='+encodeURIComponent(problem));await page.getByRole('checkbox').click();await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();await page.getByText('Tính số bút của Lan',{exact:true}).last().waitFor();await shot('step',width,height);
   await page.getByRole('button',{name:'Gợi ý cách làm bước này',exact:true}).click();await page.getByText('PHÉP TÍNH GỢI Ý',{exact:true}).count();await shot('step-hint',width,height);
   await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();await page.getByRole('button',{name:'Nghe giảng kỹ hơn',exact:true}).waitFor();await shot('listening',width,height);
   await page.getByRole('button',{name:'Nghe giảng kỹ hơn',exact:true}).click();await page.getByRole('button',{name:'Em chưa hiểu',exact:true}).waitFor();await shot('listening-checkin',width,height);
   await page.getByRole('button',{name:'Em chưa hiểu',exact:true}).click();await shot('difficulty',width,height);
   const before=requests;await page.getByRole('radio').first().click();assert.equal(requests,before);await shot('difficulty-selected',width,height);
   await page.getByRole('button',{name:'Xem giải thích nhé!',exact:true}).click();await page.getByText('Mình gộp hai nhóm bút nên chọn phép cộng.',{exact:true}).waitFor();await shot('explanation',width,height);
   await page.getByRole('button',{name:'Nghe giảng kỹ hơn',exact:true}).click();await page.getByRole('button',{name:'Em đã hiểu',exact:true}).click();
   assert.equal(await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).count(),0);
  }
  // Real upload, privacy confirmation and crop flow; isolated OCR/review responses only.
  for(const [width,height]of[[390,844],[768,1024],[1440,1000]]){
   await page.setViewportSize({width,height});await page.goto(base+'/camera?mode=MATH_TUTOR');
   const choose=page.waitForEvent('filechooser');await page.getByRole('button',{name:'Chọn ảnh từ thư viện',exact:true}).click();
   await(await choose).setFiles('C:/Users/Admin/AppData/Local/Temp/codex-clipboard-2fd24bf3-ee8e-4d43-baa5-7c4f05a65275.png');
   await page.getByRole('checkbox',{name:'Tôi đã kiểm tra và che thông tin riêng tư trong ảnh',exact:true}).click();
   await page.getByRole('button',{name:'Tiếp tục xem lại',exact:true}).click();
   await page.evaluate(()=>document.fonts.ready);await page.waitForFunction(()=>[...document.images].every(i=>i.complete));await page.waitForTimeout(500);
   await page.getByRole('button',{name:'Xác nhận cắt ảnh',exact:true}).click();
   await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số',exact:true}).waitFor({timeout:20000});
   await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số',exact:true}).click();
   await page.getByRole('checkbox',{name:'Em đã đối chiếu bài làm với ảnh',exact:true}).click();
   validReview=false;await page.getByRole('button',{name:'Nhận xét bài em làm',exact:true}).click();await page.getByText('Cùng sửa từng chỗ nhé',{exact:true}).waitFor();
   await page.getByText('Bài làm của em',{exact:true}).last().scrollIntoViewIfNeeded();await shot('work-revision',width,height);
   const region=page.getByTestId('work-evidence-region-3');assert(await region.count());await region.scrollIntoViewIfNeeded();await shot('work-highlight',width,height);
   validReview=true;await page.getByRole('button',{name:'Nhận xét bài em làm',exact:true}).click();await page.getByText('Em làm tốt rồi!',{exact:true}).waitFor();
   await page.getByText('Bài làm của em',{exact:true}).last().scrollIntoViewIfNeeded();await shot('work-correct',width,height);
   await page.getByRole('button',{name:'Xem nhận xét chi tiết',exact:true}).click();await page.getByRole('button',{name:'Khám phá thêm một cách nghĩ',exact:true}).waitFor();
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(root,'visual-qa.json'),JSON.stringify({fixture:'Actual production Student web export, isolated account and API fixtures; speech completion simulated, photo upload uses user sample. No physical-device or acoustic-quality claim.',rows,errors},null,2));console.log(JSON.stringify({captures:rows.length,errors}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
