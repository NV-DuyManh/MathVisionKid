import React from 'react';
import TestRenderer, {act} from 'react-test-renderer';
import StudentWebLayout from '../app/_layout.web';
import {observeLearningPerformance} from '../features/tutoring/webPerformance.web';
import {prepareIllustrations} from '../components/ui/AppIllustration';

jest.mock('expo-router',()=>({Stack:'Stack'}));
jest.mock('expo-router/head',()=>({__esModule:true,default:({children}:any)=>children}));
jest.mock('expo-font',()=>({useFonts:()=>[true,null]}));
jest.mock('../components/ui/AppIllustration',()=>({prepareIllustrations:jest.fn(() => new Promise<void>(() => {}))}));
jest.mock('../context/AuthContext',()=>({AuthProvider:({children}:any)=>children}));
jest.mock('../components/ui/WebAlerts.web',()=>({WebAlerts:()=>null}));
jest.mock('../features/tutoring/webPerformance.web',()=>({observeLearningPerformance:jest.fn()}));

it('installs and cleans up field measurements in the actual web root',async()=>{
  const stop=jest.fn();jest.mocked(observeLearningPerformance).mockReturnValue(stop);
  let view!:TestRenderer.ReactTestRenderer;
  try{
    await act(async()=>{view=TestRenderer.create(<StudentWebLayout/>);});
    expect(observeLearningPerformance).toHaveBeenCalledTimes(1);
    expect(view.root.findAllByType('Stack' as any)).toHaveLength(1);
    expect(prepareIllustrations).not.toHaveBeenCalled();
  }
  finally{act(()=>view?.unmount());}
  expect(stop).toHaveBeenCalledTimes(1);
});
