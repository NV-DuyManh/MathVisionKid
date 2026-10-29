// Live public authorization and restoration, no credentials/tokens in output.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base='http://127.0.0.1:8080/api/v1';
async function login(name){const r=await fetch(base+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:name,password:'123'})});assert.equal(r.status,200);return(await r.json()).accessToken;}
async function post(route,body,token){return fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(15000)});}
(async()=>{
 const token=await login('student'),problemText='Có 12 bút xanh và 8 bút đỏ, chia đều cho 5 bạn. Hỏi mỗi bạn được bao nhiêu bút?';
 const initial=await post('/student/tutor/lesson',{problemText,workText:'',problemConfirmed:true,workConfirmed:false,guidedUnderstanding:true,startWithReading:true},token);assert.equal(initial.status,200);const lesson=await initial.json();
 let response;
 for(const answer of lesson.step.choices){
  const r=await post('/student/tutor/lesson/answer',{sessionId:lesson.sessionId,revision:lesson.revision,answer,hint:false},token);assert.equal(r.status,200);response=await r.json();if(response.stepIndex===1)break;
 }
 assert.equal(response.stepIndex,1);
 const request={sessionId:lesson.sessionId,problemText};
 const start=performance.now(),restored=await post('/student/tutor/lesson/resume',request,token),elapsedMs=Math.round(performance.now()-start);assert.equal(restored.status,200);const actual=await restored.json();
 assert.equal(actual.revision,response.revision);assert.equal(actual.stepIndex,1);assert.equal(actual.review.question,lesson.step.question);assert.deepEqual(actual.review.choices,lesson.step.choices);assert.equal(actual.review.studentAnswer,response.completed[0].answer);assert.equal(restored.headers.get('cache-control'),'no-store');assert(!JSON.stringify(actual).includes('correctChoice'));
 const anonymous=(await post('/student/tutor/lesson/resume',request)).status;assert.equal(anonymous,401);
 const teacher=await login('teacher'),forbidden=(await post('/student/tutor/lesson/resume',request,teacher)).status;assert.equal(forbidden,403);
 const different=(await post('/student/tutor/lesson/resume',{...request,problemText:'Một đề khác chưa được xác nhận.'},token)).status;assert.equal(different,400);
 fs.writeFileSync(path.join(__dirname,'backend-flow.json'),JSON.stringify({evidence:'Live local public HTTP with real Student/Teacher authentication, source-only reading lesson; not a test of new model mathematics.',resumeMs:elapsedMs,resumeStatus:restored.status,approvedReviewRestored:true,noFutureAnswerKey:true,noStore:true,anonymousStatus:anonymous,teacherStatus:forbidden,changedSourceStatus:different},null,2));
 console.log('Live owned resume and authorization passed');
})().catch(error=>{console.error(error.message);process.exitCode=1});
