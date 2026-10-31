import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import RecognitionResult from '../app/recognition/result';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

const mockRouter={replace:jest.fn()};
const mockDraft = {uri:'file:///private-cropped-line.jpg',source:'CAMERA'};
jest.mock('@expo/vector-icons',()=>({Ionicons:'Ionicons'}));
jest.mock('expo-router',()=>({useRouter:()=>mockRouter}));
jest.mock('react-native-safe-area-context',()=>({SafeAreaView:require('react-native').View}));
jest.mock('../features/recognition/state/recognitionDraftStore',()=>({recognitionDraftStore:{getDraft:()=>mockDraft,clearDraft:jest.fn()},logFlowDomain:jest.fn()}));
jest.mock('../features/recognition/api/RecognitionService',()=>({RecognitionService:{createTrial:jest.fn(),submitFeedback:jest.fn()}}));

it('retries recognition with the same cropped image instead of discarding it and returning home', async()=>{
  (RecognitionService.createTrial as jest.Mock).mockRejectedValueOnce(new Error('unavailable')).mockResolvedValueOnce({trialId:'trial-test',recognizedText:'Có 3 bút.'});
  let view!: TestRenderer.ReactTestRenderer;
  await act(async()=>{view=TestRenderer.create(<RecognitionResult/>);});
  const retry=view.root.findAll(node=>node.props.accessibilityLabel==='Thử lại'&&node.props.onPress)[0];
  await act(async()=>retry.props.onPress());
  expect(RecognitionService.createTrial).toHaveBeenCalledTimes(2);
  expect((RecognitionService.createTrial as jest.Mock).mock.calls[1]).toEqual((RecognitionService.createTrial as jest.Mock).mock.calls[0]);
  expect(recognitionDraftStore.clearDraft).not.toHaveBeenCalled();expect(mockRouter.replace).not.toHaveBeenCalled();
  expect(view.root.findAllByType('Text' as any).map(node=>String(node.props.children)).join(' ')).toContain('Có 3 bút.');
  act(()=>view.unmount());
});
