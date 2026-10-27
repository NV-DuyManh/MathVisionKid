import React from 'react';
import TestRenderer, {act} from 'react-test-renderer';
import {PersonalLessonVideo} from '../features/tutoring/PersonalLessonVideo';
import {lessonVideoApi} from '../features/tutoring/lessonVideoApi';
import {saveLessonMovie} from '../features/tutoring/lessonVideoFile';
import {TaskProgress} from '../components/ui/TaskProgress';
const mockDispose=jest.fn();
jest.mock('../features/tutoring/LessonClip',()=>({LessonClip:'LessonClip'}));
jest.mock('../features/tutoring/lessonVideoApi',()=>({lessonVideoApi:{prepare:jest.fn(),status:jest.fn(),download:jest.fn()}}));
jest.mock('../features/tutoring/lessonVideoFile',()=>({saveLessonMovie:jest.fn()}));
const ready={videoId:'v'.repeat(32),status:'READY',progress:100,durationSeconds:35,hasAudio:true,title:'Tìm số cây'};
const lesson={sessionId:'video-lesson-session-12345',revision:2,status:'READY'} as any;
let view:TestRenderer.ReactTestRenderer;
beforeEach(()=>{jest.clearAllMocks();(lessonVideoApi.prepare as jest.Mock).mockResolvedValue(ready);(lessonVideoApi.download as jest.Mock).mockResolvedValue(new Uint8Array([1]));(saveLessonMovie as jest.Mock).mockReturnValue({uri:'file:///private-lesson.mp4',dispose:mockDispose});});
afterEach(()=>{if(view)act(()=>view.unmount());});
it('automatically prepares this lesson revision and renders a voiced movie without autoplay',async()=>{
 await act(async()=>{view=TestRenderer.create(<PersonalLessonVideo scope="pupil-a" lesson={lesson}/>)});
 expect(lessonVideoApi.prepare).toHaveBeenCalledWith({sessionId:lesson.sessionId,revision:2},expect.any(AbortSignal));
 expect(lessonVideoApi.download).toHaveBeenCalledWith(ready.videoId,expect.any(AbortSignal));
 const clip=view.root.findByType('LessonClip' as any);
 expect(clip.props.source).toBe('file:///private-lesson.mp4');expect(clip.props.narrated).toBe(true);
 act(()=>view.unmount());expect(mockDispose).toHaveBeenCalledTimes(1);
});
it('drops late responses and aborts when the lesson owner or revision changes',async()=>{
 let resolve:any;const task=new Promise(r=>resolve=r);(lessonVideoApi.prepare as jest.Mock).mockReturnValueOnce(task);
 await act(async()=>{view=TestRenderer.create(<PersonalLessonVideo scope="pupil-a" lesson={lesson}/>)});
 const signal=(lessonVideoApi.prepare as jest.Mock).mock.calls[0][1];
 await act(async()=>view.update(<PersonalLessonVideo scope="pupil-b" lesson={{...lesson,revision:3}}/>));
 expect(signal.aborted).toBe(true);
 await act(async()=>resolve({...ready,videoId:'old'.repeat(10)}));
 expect(lessonVideoApi.download).toHaveBeenCalledTimes(1);
});
it('offers retry and hides provider details when video preparation fails',async()=>{
 (lessonVideoApi.prepare as jest.Mock).mockRejectedValueOnce(new Error('ffmpeg missing localhost:8000 secret'));
 await act(async()=>{view=TestRenderer.create(<PersonalLessonVideo scope="pupil-a" lesson={lesson}/>)});
 expect(JSON.stringify(view.toJSON())).not.toMatch(/localhost|ffmpeg|secret/);
 const retry=view.root.findAll(n=>n.props.accessibilityLabel==='Thử tạo video lại'&&n.props.onPress)[0];
 await act(async()=>retry.props.onPress());
 expect(view.root.findByType('LessonClip' as any).props.narrated).toBe(true);
});

it('advances from real rendering to download and never reports ready while bytes are still pending',async()=>{
 jest.useFakeTimers();
 let finish!:(value:Uint8Array)=>void;
 (lessonVideoApi.prepare as jest.Mock).mockResolvedValueOnce({...ready,status:'RENDERING',progress:45,hasAudio:false,durationSeconds:0});
 (lessonVideoApi.status as jest.Mock).mockResolvedValueOnce(ready);
 (lessonVideoApi.download as jest.Mock).mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
 try {
  await act(async()=>{view=TestRenderer.create(<PersonalLessonVideo scope="pupil-a" lesson={lesson}/>)});
  expect(view.root.findByType(TaskProgress).props.activeStep).toBe(0);
  await act(async()=>{jest.advanceTimersByTime(1000);});
  expect(view.root.findByType(TaskProgress).props.activeStep).toBe(1);
  expect(view.root.findAllByType('LessonClip' as any)).toHaveLength(0);
  expect(view.root.findAllByType('Text' as any).map(node=>String(node.props.children)).join(' ')).not.toContain('100%');
  await act(async()=>finish(new Uint8Array([1])));
  expect(view.root.findByType('LessonClip' as any).props.preparationSteps).toEqual(['Dựng hình và lời giảng','Tải video về','Mở trình phát']);
 } finally {jest.useRealTimers();}
});
