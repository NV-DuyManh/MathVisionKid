// Live owned HTTP flow. Keep credentials/tokens in memory; persist timings only.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const base='http://127.0.0.1:8080/api/v1',out=__dirname;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const login=await fetch(base+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'student',password:'123'})});
 if(!login.ok)throw new Error('Login HTTP '+login.status);const{accessToken}=await login.json();
 const post=(route,body)=>fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+accessToken},body:JSON.stringify(body),signal:AbortSignal.timeout(65000)});
 const began=performance.now();const response=await post('/student/tutor/lesson',{problemText:'Vườn cây có 1/3 số cây là táo, 2/5 số cây là xoài, còn lại là cam. Có 16 cây cam. Hỏi vườn có tất cả bao nhiêu cây?',workText:'',problemConfirmed:true,workConfirmed:false,guidedUnderstanding:true,startWithReading:true});
 const result={evidence:'Live local HTTP services and real provider audio; not physical-device latency or human listening evaluation.',lessonOpenMs:Math.round(performance.now()-began),lessonStatus:response.status,voices:[]};
 if(!response.ok){fs.writeFileSync(path.join(out,'live-probe.json'),JSON.stringify(result,null,2));throw new Error('Lesson HTTP '+response.status);}
 const lesson=await response.json(),paragraphs=[...new Set([...(lesson.step.guidance?.length?lesson.step.guidance:[lesson.step.explanation]),lesson.step.question].map(p=>p.trim()).filter(Boolean))];
 result.scriptCharacters=paragraphs.join(' ').length;
 fs.writeFileSync(path.join(out,'real-script.json'),JSON.stringify({paragraphs},null,2));
 result.voices=await Promise.all(['vi-VN-NamMinhNeural','vi-VN-HoaiMyNeural'].map(async(voice,index)=>{
  const body={sessionId:lesson.sessionId,revision:lesson.revision,paragraphs,voice},start=performance.now(),deadline=start+60000;
  let started=false,prepareMs,phase='waiting',status;
  try{
   while(performance.now()<deadline){
    const t=performance.now(),r=await post('/student/tutor/lesson/narration/'+(started?'status':'prepare'),body);status=r.status;
    if(status===429){await sleep(500);continue;}if(!r.ok)throw new Error('HTTP '+status);
    const state=await r.json();if(!started){prepareMs=Math.round(performance.now()-t);started=true;}
    phase=state.phase;if(phase==='ready')break;if(phase==='failed')throw new Error('Job failed');await sleep(300);
   }
   if(phase!=='ready')throw new Error('Deadline');
   const readyMs=Math.round(performance.now()-start),audio=await post('/student/tutor/lesson/narration',body);if(!audio.ok)throw new Error('Audio HTTP '+audio.status);
   const bytes=Buffer.from(await audio.arrayBuffer());fs.writeFileSync(path.join(out,index?'female.wav':'male.wav'),bytes);
   let cuePoints=0;for(let offset=12;offset+8<=bytes.length;){const size=bytes.readUInt32LE(offset+4);if(bytes.toString('ascii',offset,offset+4)==='cue ')cuePoints=bytes.readUInt32LE(offset+8);offset+=8+size+size%2;}
   if(cuePoints!==paragraphs.length)throw new Error('Missing exact paragraph cue points');
   const cachedStart=performance.now(),cached=await post('/student/tutor/lesson/narration',body),again=Buffer.from(await cached.arrayBuffer());
   return{voice:index?'Giọng nữ':'Giọng nam',success:true,cuePoints,prepareMs,readyMs,totalMs:Math.round(performance.now()-start),bytes:bytes.length,cachedReadMs:Math.round(performance.now()-cachedStart),sameAudio:crypto.createHash('sha256').update(bytes).digest('hex')===crypto.createHash('sha256').update(again).digest('hex')};
  }catch(error){return{voice:index?'Giọng nữ':'Giọng nam',success:false,prepareMs,elapsedMs:Math.round(performance.now()-start),phase,httpStatus:status,category:error.message};}
 }));
 fs.writeFileSync(path.join(out,'live-probe.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 if(result.voices.some(v=>!v.success))process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1;});
