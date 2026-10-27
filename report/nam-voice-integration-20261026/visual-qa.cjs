const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=__dirname,out=path.resolve(root,'../../report/nam-voice-integration-20261026');
const problem='Vườn có 1/3 số cây là cây táo, 2/5 là cây xoài, còn lại 16 cây cam. Hỏi cả vườn có bao nhiêu cây?';
const lesson={sessionId:'voice-lesson-session-12345',revision:0,topic:'Phân số',goal:'Tìm tổng số cây',feedback:'',understandingSteps:3,outline:['Dữ kiện','Câu hỏi','Tóm tắt','Tính phần cây cam','Tìm số cây'],stepIndex:0,completed:[],status:'READY',step:{kind:'UNDERSTAND',title:'Nhận biết dữ kiện',explanation:'Đọc lại nguyên đề. Tách điều đã biết và điều cần tìm trước khi tính.',question:'Câu nào là điều đề đã cho biết?',choices:['Có 1/3 số cây là cây táo','Hỏi cả vườn có bao nhiêu cây?'],expression:'',unit:'',workExcerpt:''}};
(async()=>{
  fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
  const browser=await chromium.launch({headless:true}),rows=[],errors=[];
  try{
    for(const [width,height] of [[320,568],[360,800],[390,844],[768,1024],[844,390],[1440,900]]){
      const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:2,reducedMotion:'reduce'});
      await context.addInitScript(()=>{
        sessionStorage.setItem('portal_access_token','voice-qa-fixture');
        const original=HTMLMediaElement.prototype.play;
        window.__playedAudios=[];
        HTMLMediaElement.prototype.play=function(...args){if(!window.__playedAudios.includes(this))window.__playedAudios.push(this);return original.apply(this,args);};
      });
      const requests=[];
      await context.route('**/api/v1/**',route=>{
        const url=route.request().url();
        if(url.endsWith('/tutor/lesson/narration')){
          const voice=route.request().postDataJSON().voice;requests.push(voice);
          assert(['vi-VN-NamMinhNeural','vi-VN-HoaiMyNeural'].includes(voice));
          return route.fulfill({status:200,contentType:'audio/wav',body:fs.readFileSync(path.join(root,voice+'-1.wav'))});
        }
        const data=url.endsWith('/tutor/lesson')?lesson:{id:'synthetic-voice-pupil',name:'Minh',role:'STUDENT',grade:4};
        return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
      });
      const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
      await page.goto('http://127.0.0.1:8099/learning/math-guide?problemText='+encodeURIComponent(problem));
      await page.getByRole('checkbox',{name:'Em đã kiểm tra đề bài và các số'}).click();
      await page.getByRole('button',{name:'Bắt đầu từng bước',exact:true}).click();
      await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
      const male=page.getByRole('radio',{name:'Nam Minh, giọng nam',exact:true}),female=page.getByRole('radio',{name:'Hoài My, giọng nữ',exact:true});
      await page.waitForFunction(()=>document.querySelector('[role="radio"][aria-checked="true"]'));
      await page.getByRole('button',{name:'Phát lời giảng',exact:true}).waitFor();
      await page.waitForFunction(()=>{const play=document.querySelector('[aria-label="Phát lời giảng"]'),slider=document.querySelector('[aria-label="Tua nghe giảng"]');return play&&play.getAttribute('aria-disabled')!=='true'&&slider&&!slider.disabled&&Number(slider.max)>1;});
      assert.equal(await page.getByRole('radiogroup',{name:'Chọn giọng đọc'}).getByRole('radio').count(),2);
      const boxes=await Promise.all([male.boundingBox(),female.boundingBox()]);
      assert(boxes.every(box=>box.height>=48));assert.equal(await male.getAttribute('aria-checked'),'true');
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert.equal(overflow,false);
      await page.screenshot({path:path.join(out,'screenshots',`voices-male-${width}.png`)});
      if(width===390){
        await page.getByRole('button',{name:'Phát lời giảng',exact:true}).click();
        await page.waitForFunction(()=>window.__playedAudios.some(a=>a.currentTime>.15&&!a.paused));
        await male.focus();await page.keyboard.press('ArrowRight');
        await page.waitForFunction(()=>document.querySelector('[aria-label="Hoài My, giọng nữ"]')?.getAttribute('aria-checked')==='true');
        assert.equal(await page.evaluate(()=>window.__playedAudios.every(a=>a.paused)),true,'Previous voice must stop on switch');
      }else await female.click();
      await page.waitForFunction(()=>{const play=document.querySelector('[aria-label="Phát lời giảng"]'),slider=document.querySelector('[aria-label="Tua nghe giảng"]');return play&&play.getAttribute('aria-disabled')!=='true'&&slider&&!slider.disabled&&Number(slider.max)>6;});
      assert.equal(await female.getAttribute('aria-checked'),'true');
      assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('mathvision.lesson-voice')).voiceId),'vi-VN-HoaiMyNeural');
      await page.screenshot({path:path.join(out,'screenshots',`voices-female-${width}.png`)});
      let playback;
      if(width===390){
        const slider=page.getByRole('slider',{name:'Tua nghe giảng',exact:true});
        await slider.focus();await page.keyboard.press('End');
        await page.waitForFunction(()=>Number(document.querySelector('[aria-label="Tua nghe giảng"]').value)>6);
        await page.keyboard.press('ArrowLeft');
        await page.waitForFunction(()=>{const value=Number(document.querySelector('[aria-label="Tua nghe giảng"]').value);return value>0&&value<6.19;});
        const selected=Number(await slider.inputValue());assert(selected>0&&selected<6.192,JSON.stringify({selected,max:await slider.getAttribute('max'),audios:await page.evaluate(()=>window.__playedAudios.map(a=>({time:a.currentTime,duration:a.duration,paused:a.paused})))}));
        await page.getByRole('button',{name:'Nghe lại từ đầu',exact:true}).click();
        await page.waitForFunction(()=>window.__playedAudios.at(-1).currentTime>.15&&!window.__playedAudios.at(-1).paused);
        playback=await page.evaluate(()=>({time:window.__playedAudios.at(-1).currentTime,duration:window.__playedAudios.at(-1).duration,paused:window.__playedAudios.at(-1).paused}));
        await page.getByRole('button',{name:'Tạm dừng lời giảng',exact:true}).click();
        await page.getByRole('button',{name:'Đóng Nghe giảng',exact:true}).click();
        await page.getByRole('button',{name:'Nghe giảng',exact:true}).click();
        await female.waitFor();await page.waitForFunction(()=>document.querySelector('[aria-label="Hoài My, giọng nữ"]')?.getAttribute('aria-checked')==='true');
        assert.equal(requests.at(-1),'vi-VN-HoaiMyNeural');
      }
      rows.push({width,height,voiceTargets:boxes.map(box=>({width:box.width,height:box.height})),requests,overflow,playback});
      await context.close();
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'visual-qa.json'),JSON.stringify({evidence:'Actual compiled Student UI, fixture authentication/lesson API, real WAV generated by both online voices. Headless browser decoding/playback clock, not physical Android speaker evidence.',rows,errors},null,2));
    console.log(JSON.stringify({viewports:rows.length,screenshots:rows.length*2,errors}));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
