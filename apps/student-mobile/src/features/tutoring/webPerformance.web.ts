/** Small field measurements, no URLs, account IDs or pupil content. Max interaction
 * duration is labelled explicitly; it is not presented as Google's INP metric. */
export function observeLearningPerformance():()=>void{
  if(typeof window==='undefined'||typeof PerformanceObserver==='undefined')return()=>{};
  let lcp:number|null=null,cls=0,windowScore=0,windowStart=0,lastShift=0,maxInteraction:number|null=null;
  const observers:PerformanceObserver[]=[];
  const watch=(type:string,read:(entry:PerformanceEntry)=>void)=>{
    if(!PerformanceObserver.supportedEntryTypes?.includes(type))return;
    const observer=new PerformanceObserver(list=>list.getEntries().forEach(read));
    try{observer.observe({type,buffered:true,...(type==='event'?{durationThreshold:16}:{})});observers.push(observer);}catch{observer.disconnect();}
  };
  watch('largest-contentful-paint',entry=>{lcp=entry.startTime;});
  watch('layout-shift',entry=>{
    const shift=entry as PerformanceEntry&{hadRecentInput:boolean;value:number};if(shift.hadRecentInput)return;
    if(!windowStart||entry.startTime-lastShift>1000||entry.startTime-windowStart>5000){windowScore=0;windowStart=entry.startTime;}
    windowScore+=shift.value;cls=Math.max(cls,windowScore);lastShift=entry.startTime;
  });
  watch('event',entry=>{if((entry as PerformanceEntry&{interactionId:number}).interactionId)maxInteraction=Math.max(maxInteraction||0,entry.duration);});
  const flush=()=>{try{localStorage.setItem('mathvision_web_performance_v1',JSON.stringify({at:Date.now(),lcpMs:lcp,cls,maxInteractionMs:maxInteraction}));}catch{/* Storage may be unavailable. */}};
  const hidden=()=>{if(document.visibilityState==='hidden')flush();};
  document.addEventListener('visibilitychange',hidden);window.addEventListener('pagehide',flush);
  return()=>{observers.forEach(observer=>observer.disconnect());document.removeEventListener('visibilitychange',hidden);window.removeEventListener('pagehide',flush);flush();};
}
