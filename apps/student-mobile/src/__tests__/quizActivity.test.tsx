import React from 'react';
import { AppState, Text } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import { useQuizActivity } from '../features/quiz/useQuizActivity';
import { Quiz, quizApi } from '../features/quiz/quizApi';
jest.mock('expo-router',()=>({useFocusEffect:(fn:()=>void)=>require('react').useEffect(fn,[fn])}));
jest.mock('../features/quiz/quizApi',()=>({quizApi:{activity:jest.fn()}}));
const quiz={quizId:'one',status:'IN_PROGRESS',startedAt:'2026-10-31T10:00:00Z',elapsedMillis:2000} as Quiz;
let view:TestRenderer.ReactTestRenderer, state:(state:string)=>void;
function Clock({value=quiz}:{value?:Quiz}) {return <Text>{useQuizActivity(value)}</Text>;}
const elapsed=()=>view.root.findByType(Text).props.children;
beforeEach(()=>{
  jest.useFakeTimers(); jest.clearAllMocks();
  jest.spyOn(AppState,'addEventListener').mockImplementation((_,callback:any)=>{state=callback;return{remove:jest.fn()};});
  (quizApi.activity as jest.Mock).mockImplementation(async(_id,run,active)=>({...quiz,startedAt:run,timerRunning:active}));
});
afterEach(()=>{act(()=>view?.unmount());jest.restoreAllMocks();jest.useRealTimers();});
it('pauses immediately in background, does not heartbeat there, then resumes',async()=>{
  await act(async()=>{view=TestRenderer.create(<Clock/>);});
  act(()=>jest.advanceTimersByTime(2000));expect(elapsed()).toBe(4000);
  await act(async()=>state('background')); const paused=elapsed(),calls=(quizApi.activity as jest.Mock).mock.calls.length;
  act(()=>jest.advanceTimersByTime(86400000)); expect(elapsed()).toBe(paused);expect(quizApi.activity).toHaveBeenCalledTimes(calls);
  expect(quizApi.activity).toHaveBeenLastCalledWith('one',quiz.startedAt,false);
  await act(async()=>state('active'));expect(quizApi.activity).toHaveBeenLastCalledWith('one',quiz.startedAt,true,expect.any(AbortSignal));
});
it('sends a pause when leaving the screen and ignores a late heartbeat response',async()=>{
  let finish!:(value:Quiz)=>void;
  (quizApi.activity as jest.Mock).mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
  await act(async()=>{view=TestRenderer.create(<Clock/>);});
  const signal=(quizApi.activity as jest.Mock).mock.calls[0][3];
  act(()=>view.unmount());expect(signal.aborted).toBe(true);
  expect(quizApi.activity).toHaveBeenLastCalledWith('one',quiz.startedAt,false);
  await act(async()=>finish({...quiz,timerRunning:true}));
});
it('never counts pending/completed library time and bounds a lost connection to one lease',async()=>{
  await act(async()=>{view=TestRenderer.create(<Clock value={{...quiz,status:'READY'}}/>);});
  act(()=>jest.advanceTimersByTime(86400000));expect(elapsed()).toBe(2000);expect(quizApi.activity).not.toHaveBeenCalled();
  await act(async()=>view.update(<Clock/>));
  (quizApi.activity as jest.Mock).mockImplementation(()=>new Promise(()=>{}));
  act(()=>jest.advanceTimersByTime(86400000));expect(elapsed()).toBe(14000);
  await act(async()=>view.update(<Clock value={{...quiz,status:'COMPLETED',elapsedMillis:5000}}/>));
  act(()=>jest.advanceTimersByTime(10000));expect(elapsed()).toBe(5000);
});
