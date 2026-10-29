import {observeLearningPerformance} from '../features/tutoring/webPerformance.web';
it('measures actual browser entries and names max interaction separately from INP',()=>{
  const properties=['window','document','PerformanceObserver','localStorage'] as const;
  const original=new Map(properties.map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]));
  const callbacks=new Map<string,(list:{getEntries:()=>unknown[]})=>void>(),events=new Map<string,()=>void>(),records=new Map<string,string>();
  class Observer{
    static supportedEntryTypes=['largest-contentful-paint','layout-shift','event'];
    constructor(private callback:(list:{getEntries:()=>unknown[]})=>void){}
    observe({type}:{type:string}){callbacks.set(type,this.callback);}
    disconnect(){}
  }
  const target={addEventListener:(name:string,callback:()=>void)=>events.set(name,callback),removeEventListener:jest.fn()};
  const values={window:target,document:{...target,visibilityState:'hidden'},PerformanceObserver:Observer,localStorage:{setItem:(key:string,value:string)=>records.set(key,value)}};
  for(const key of properties)Object.defineProperty(globalThis,key,{configurable:true,value:values[key]});
  try{
    const stop=observeLearningPerformance();
    const emit=(type:string,entries:unknown[])=>callbacks.get(type)!({getEntries:()=>entries});
    emit('largest-contentful-paint',[{startTime:420}]);
    emit('layout-shift',[{startTime:100,value:.9,hadRecentInput:true},{startTime:1000,value:.1,hadRecentInput:false},{startTime:1500,value:.2,hadRecentInput:false},{startTime:4000,value:.4,hadRecentInput:false},{startTime:4500,value:.1,hadRecentInput:false}]);
    emit('event',[{interactionId:1,duration:24},{interactionId:2,duration:40}]);events.get('pagehide')!();
    const result=JSON.parse(records.get('mathvision_web_performance_v1')!);
    expect(result.lcpMs).toBe(420);expect(result.cls).toBeCloseTo(.5);expect(result.maxInteractionMs).toBe(40);expect(result).not.toHaveProperty('inp');expect(result).not.toHaveProperty('url');stop();
  }finally{for(const key of properties){const descriptor=original.get(key);if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete(globalThis as any)[key];}}
});
