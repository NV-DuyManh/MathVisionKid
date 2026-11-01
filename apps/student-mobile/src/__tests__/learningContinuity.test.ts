import {Platform} from 'react-native';
import {loadLearningProgress,saveLearningProgress,sameStoredAnswer} from '../features/tutoring/learningProgress';
import {createPlaybackBookmarks} from '../features/tutoring/playbackBookmarks';
import {audioCues} from '../features/tutoring/audioCues';
import {measureVoice,voiceMetrics} from '../features/tutoring/voiceMetrics';
const records=new Map<string,string>();
Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{getItem:(key:string)=>records.get(key)??null,setItem:(key:string,value:string)=>records.set(key,value)}});
const os=Platform.OS;
beforeEach(()=>{Object.defineProperty(Platform,'OS',{configurable:true,value:'web'});records.clear();});
afterAll(()=>Object.defineProperty(Platform,'OS',{configurable:true,value:os}));
const progress=()=>({version:1 as const,at:Date.now(),lessonId:'lesson-1',sessionId:'owned-learning-session-1234',revision:2,stepIndex:2,problemText:'Có 12 bút và 8 bút.',workText:'',attempt:'3/5'});

it('saves only bounded progress for its owner and rejects stale or malformed data',async()=>{
  const row=progress();await saveLearningProgress('a',row);expect(await loadLearningProgress('a')).toEqual(row);expect(await loadLearningProgress('b')).toBeNull();
  await expect(saveLearningProgress('a',{...row,attempt:'x'.repeat(501)})).rejects.toThrow();
  await expect(saveLearningProgress('a',{...row,at:Date.now()-8*86400000})).rejects.toThrow();
  await expect(saveLearningProgress(undefined,row)).rejects.toThrow();
});
it('does not trust an edited stored answer when restoring an approved result',()=>{
  expect(sameStoredAnswer('4/2','2')).toBe(true);expect(sameStoredAnswer('0,5','1/2')).toBe(true);
  expect(sameStoredAnswer('1/0','2')).toBe(false);expect(sameStoredAnswer('999','2')).toBe(false);
});
it('restores position without mixing accounts or scripts and rewinds completed audio',async()=>{
  const a=createPlaybackBookmarks('a');await a.get('script-a');a.set('script-a',7.9,30);await a.flush();
  expect(await createPlaybackBookmarks('a').get('script-a')).toBe(7);
  expect(await createPlaybackBookmarks('b').get('script-a')).toBe(0);
  expect(await createPlaybackBookmarks('a').get('script-b')).toBe(0);
  a.set('script-a',30,30);await a.flush();expect(await createPlaybackBookmarks('a').get('script-a')).toBe(0);
});
it('uses decoded RIFF frame offsets and refuses truncated, reordered or out-of-range cues',()=>{
  const bytes=new Uint8Array(44+32000+60),v=new DataView(bytes.buffer);const tag=(at:number,text:string)=>[...text].forEach((c,i)=>bytes[at+i]=c.charCodeAt(0));
  tag(0,'RIFF');v.setUint32(4,bytes.length-8,true);tag(8,'WAVE');tag(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,16000,true);v.setUint16(32,2,true);v.setUint16(34,16,true);tag(36,'data');v.setUint32(40,32000,true);
  const at=32044;tag(at,'cue ');v.setUint32(at+4,52,true);v.setUint32(at+8,2,true);
  for(let i=0;i<2;i++){const row=at+12+i*24;v.setUint32(row,i,true);tag(row+8,'data');v.setUint32(row+20,i*8000,true);}
  expect(audioCues(bytes)).toEqual([{index:0,start:0,end:.5},{index:1,start:.5,end:1}]);
  expect(audioCues(bytes.subarray(0,bytes.length-1))).toEqual([]);
  v.setUint32(at+56,18000,true);expect(audioCues(bytes)).toEqual([]);
});
it('records each measurement once with no text, identifiers or audio and separates cache/network',async()=>{
  records.set('mathvision_voice_metrics_v1',JSON.stringify([{at:Date.now(),stage:'player',ms:9,outcome:'ready',cache:'ready',voice:'male',platform:'web',privateText:'must-not-be-kept'}]));
  const done=measureVoice('player','vi-VN-NamMinhNeural',{cache:'ready'});done('ready');done('failed');
  const failed=measureVoice('prepare','vi-VN-HoaiMyNeural',{cache:'miss',background:true});failed('failed');
  const report=await voiceMetrics();expect(report.samples).toHaveLength(3);expect(report.groups).toHaveLength(2);
  expect(report.samples[0]).not.toHaveProperty('sessionId');expect(report.samples[0]).not.toHaveProperty('text');
  expect(report.groups.some(row=>row.failures===1&&row.p50===null)).toBe(true);
  expect(JSON.stringify(report)).not.toContain('privateText');
});
