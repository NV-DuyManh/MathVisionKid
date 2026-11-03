import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { QuizHelp } from '../features/quiz/QuizHelp';
import { quizApi, Quiz } from '../features/quiz/quizApi';
import { TutorService } from '../features/tutoring/api/TutorService';
jest.mock('../features/tutoring/LessonQuestion',()=>({LessonQuestion:'LessonQuestion'}));
jest.mock('../features/quiz/quizApi',()=>({quizApi:{help:jest.fn()},quizError:()=> 'Em thử lại nhé.'}));
jest.mock('../features/tutoring/api/TutorService',()=>({TutorService:{startLesson:jest.fn()}}));
const quiz={quizId:'owned-quiz',startedAt:'run-one',questionText:'Tính: 12 + 8'} as Quiz;
let view:TestRenderer.ReactTestRenderer;
beforeEach(()=>{jest.clearAllMocks();(quizApi.help as jest.Mock).mockResolvedValue({...quiz,solutionViewed:true});(TutorService.startLesson as jest.Mock).mockResolvedValue({sessionId:'real-server-session',revision:0,stepIndex:0});});
afterEach(()=>act(()=>view?.unmount()));
it('records help before using a real question session and passes the exact owned question',async()=>{
  const assisted=jest.fn();
  await act(async()=>{view=TestRenderer.create(<QuizHelp quiz={quiz} onAssisted={assisted} onReturn={()=>{}}/>);});
  expect(assisted).toHaveBeenCalledWith(expect.objectContaining({solutionViewed:true}));
  expect(TutorService.startLesson).toHaveBeenCalledWith(quiz.questionText,'',expect.objectContaining({problemConfirmed:true}),expect.any(AbortSignal));
  expect(view.root.findByType('LessonQuestion' as any).props.sessionId).toBe('real-server-session');
});
it('does not open a tutor session if ownership/help authorization fails',async()=>{
  (quizApi.help as jest.Mock).mockRejectedValue(new Error('404 private detail'));
  await act(async()=>{view=TestRenderer.create(<QuizHelp quiz={quiz} onAssisted={()=>{}} onReturn={()=>{}}/>);});
  expect(TutorService.startLesson).not.toHaveBeenCalled();
  expect(JSON.stringify(view.toJSON())).not.toContain('404 private detail');
});
it('cancels preparation and never publishes its late session after closing',async()=>{
  let finish!:(value:unknown)=>void;
  (TutorService.startLesson as jest.Mock).mockImplementation(()=>new Promise(resolve=>{finish=resolve;}));
  await act(async()=>{view=TestRenderer.create(<QuizHelp quiz={quiz} onAssisted={()=>{}} onReturn={()=>{}}/>);});
  const signal=(TutorService.startLesson as jest.Mock).mock.calls[0][3];
  act(()=>view.unmount());expect(signal.aborted).toBe(true);
  await act(async()=>finish({sessionId:'late',revision:0,stepIndex:0}));
});
it('removes the previous question session immediately when the quiz question changes',async()=>{
  const assisted=jest.fn(),onReturn=jest.fn();
  await act(async()=>{view=TestRenderer.create(<QuizHelp quiz={quiz} onAssisted={assisted} onReturn={onReturn}/>);});
  let finish!:(value:unknown)=>void;
  (TutorService.startLesson as jest.Mock).mockImplementationOnce(()=>new Promise(resolve=>{finish=resolve;}));
  const next={...quiz,questionText:'Tính: 18 - 5'};
  await act(async()=>view.update(<QuizHelp quiz={next} onAssisted={assisted} onReturn={onReturn}/>));
  expect(view.root.findAllByType('LessonQuestion' as any)).toHaveLength(0);
  expect(TutorService.startLesson).toHaveBeenLastCalledWith(next.questionText,'',expect.anything(),expect.any(AbortSignal));
  await act(async()=>finish({sessionId:'next-question-session',revision:0,stepIndex:0}));
  expect(view.root.findByType('LessonQuestion' as any).props.sessionId).toBe('next-question-session');
});
