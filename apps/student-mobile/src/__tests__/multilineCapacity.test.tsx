import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Alert, Image } from 'react-native';
import MultilineReviewScreen from '../app/recognition/multiline-review';
import { RecognitionService } from '../features/recognition/api/RecognitionService';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

const mockRouter = { push: jest.fn(), replace: jest.fn(), back: jest.fn() };
let mockBlur: (() => void) | undefined;
jest.mock('expo-router', () => ({
  useRouter: () => mockRouter, useLocalSearchParams: () => ({}),
  useFocusEffect: (callback: () => (() => void)) => require('react').useEffect(() => {
    mockBlur = callback();
    return mockBlur;
  }, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Icon' }));
jest.mock('../features/recognition/components/RecognitionProgress', () => ({ RecognitionProgress: 'RecognitionProgress' }));
jest.mock('../features/recognition/api/RecognitionService', () => ({
  RecognitionService: { detectLines: jest.fn(), createMultilineTrial: jest.fn() }, normalizeOcrError: jest.fn(),
}));

let view: TestRenderer.ReactTestRenderer;
const lines = (count: number) => Array.from({ length: count }, (_, index) => ({
  line_id: `line_${index + 1}`, order: index + 1, x: 20, y: index * 20, width: 200, height: 15,
}));
const response = (overflow = false) => ({ width: 500, height: 1500, lines: lines(41), diagnostics: { region_limit_exceeded: overflow } });
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const render = async () => { await act(async () => { view = TestRenderer.create(<MultilineReviewScreen />); }); };

beforeEach(() => {
  jest.clearAllMocks();
  recognitionDraftStore.setDraft({ rawUri: 'file:///original.jpg', originalImageUri: 'file:///original.jpg',
    uri: 'file:///masked.jpg', privacyImageUri: 'file:///masked.jpg', croppedImageUri: 'file:///crop.jpg',
    privacyConfirmed: true, isMasked: true, imageSessionId: 'session', width: 500, height: 1500,
    mimeType: 'image/jpeg', filename: 'photo.jpg', mode: 'HANDWRITING_TEXT' });
  jest.spyOn(Image, 'getSize').mockImplementation((_uri, success) => success(500, 1500));
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  (RecognitionService.detectLines as jest.Mock).mockResolvedValue(response());
  (RecognitionService.createMultilineTrial as jest.Mock).mockResolvedValue({ trialId: 'trial' });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); recognitionDraftStore.clearDraft(); });

it('submits every detected row above the old 30-row limit', async () => {
  await render();
  await act(async () => { await button('Nhận diện chữ').props.onPress(); });
  expect((RecognitionService.createMultilineTrial as jest.Mock).mock.calls[0][1]).toHaveLength(41);
  expect((RecognitionService.createMultilineTrial as jest.Mock).mock.calls[0][1][40].line_id).toBe('line_41');
});

it('blocks two presses before rendering, permits retry after cancel, and ignores the old response', async () => {
  const resolve: ((value: unknown) => void)[] = [];
  (RecognitionService.createMultilineTrial as jest.Mock).mockImplementation(() => new Promise(done => resolve.push(done)));
  await render();
  const submit = button('Nhận diện chữ').props.onPress;
  act(() => { void submit(); void submit(); });
  expect(RecognitionService.createMultilineTrial).toHaveBeenCalledTimes(1);
  act(() => view.root.findByType('RecognitionProgress' as any).props.onCancel());
  act(() => { void button('Nhận diện chữ').props.onPress(); });
  expect(RecognitionService.createMultilineTrial).toHaveBeenCalledTimes(2);
  await act(async () => resolve[0]({ trialId: 'cancelled' }));
  expect(mockRouter.push).not.toHaveBeenCalled();
  expect(view.root.findByType('RecognitionProgress' as any)).toBeDefined();
  await act(async () => resolve[1]({ trialId: 'active' }));
  expect(mockRouter.push).toHaveBeenCalledTimes(1);
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/recognition/multiline-result', params: { trialId: 'active' } });
});

it('blocks a truncated page even after deleting rows and keeps the masked crop source', async () => {
  (RecognitionService.detectLines as jest.Mock).mockResolvedValue(response(true));
  await render();
  expect(button('Nhận diện chữ').props.accessibilityState.disabled).toBe(true);
  act(() => button('Xóa dòng').props.onPress());
  await act(async () => { await button('Nhận diện chữ').props.onPress(); });
  expect(RecognitionService.createMultilineTrial).not.toHaveBeenCalled();
  expect(text()).not.toContain('dòng đã sẵn sàng');
  act(() => button('Chọn lại vùng ảnh').props.onPress());
  expect(mockRouter.replace).toHaveBeenCalledWith({ pathname: '/crop', params: {
    uri: 'file:///crop.jpg', originalImageUri: 'file:///original.jpg',
  } });
  expect(recognitionDraftStore.getDraft()?.privacyImageUri).toBe('file:///masked.jpg');
});

it('detects a newly cropped region within the same photo session and clears its old overflow', async () => {
  (RecognitionService.detectLines as jest.Mock).mockResolvedValueOnce(response(true)).mockResolvedValueOnce(response());
  await render();
  recognitionDraftStore.updateDraft({ croppedImageUri: 'file:///smaller-crop.jpg' });
  await act(async () => { view.update(<MultilineReviewScreen />); });
  expect(RecognitionService.detectLines).toHaveBeenLastCalledWith('file:///smaller-crop.jpg', true, true, expect.anything());
  expect(button('Nhận diện chữ').props.disabled).toBe(false);
  expect(button('Chọn lại vùng ảnh')).toBeUndefined();
});

it('ignores an old detection that resolves after a newer crop', async () => {
  let resolveOld: (value: unknown) => void = () => {};
  (RecognitionService.detectLines as jest.Mock).mockReturnValueOnce(new Promise(resolve => { resolveOld = resolve; }))
    .mockResolvedValueOnce(response());
  await render();
  recognitionDraftStore.updateDraft({ croppedImageUri: 'file:///new-crop.jpg' });
  await act(async () => { view.update(<MultilineReviewScreen />); });
  await act(async () => { resolveOld(response(true)); });
  expect(button('Nhận diện chữ').props.disabled).toBe(false);
  expect(button('Chọn lại vùng ảnh')).toBeUndefined();
});

it('keeps a crop-required page blocked when a forced refresh fails', async () => {
  (RecognitionService.detectLines as jest.Mock).mockResolvedValueOnce(response(true))
    .mockRejectedValueOnce(new Error('Network Error'));
  await render();
  act(() => button('Phát hiện lại').props.onPress());
  const actions = (Alert.alert as jest.Mock).mock.calls.at(-1)[2];
  await act(async () => { await actions[1].onPress(); });
  expect(button('Nhận diện chữ').props.disabled).toBe(true);
  expect(button('Chọn lại vùng ảnh')).toBeDefined();
  await act(async () => { await button('Nhận diện chữ').props.onPress(); });
  expect(RecognitionService.createMultilineTrial).not.toHaveBeenCalled();
});

it('ignores a late image-size callback for the previous crop', async () => {
  const sizes: ((width: number, height: number) => void)[] = [];
  (Image.getSize as jest.Mock).mockImplementation((_uri, success) => { sizes.push(success); });
  await render();
  recognitionDraftStore.updateDraft({ croppedImageUri: 'file:///new-crop.jpg' });
  await act(async () => { view.update(<MultilineReviewScreen />); });
  await act(async () => { sizes[1](500, 1500); });
  await act(async () => { sizes[0](1000, 200); });
  expect(RecognitionService.detectLines).toHaveBeenCalledTimes(1);
  expect(RecognitionService.detectLines).toHaveBeenCalledWith('file:///new-crop.jpg', true, true, expect.anything());
});

it('does not start detection from a delayed image-size callback after leaving the screen', async () => {
  let success: ((width: number, height: number) => void) | undefined;
  let failure: ((error: any) => void) | undefined;
  (Image.getSize as jest.Mock).mockImplementation((_uri, onSuccess, onFailure) => {
    success = onSuccess;
    failure = onFailure;
  });
  await render();
  act(() => mockBlur?.());
  await act(async () => { success?.(500, 1500); failure?.(new Error('cancelled image load')); });
  expect(RecognitionService.detectLines).not.toHaveBeenCalled();
  expect(RecognitionService.createMultilineTrial).not.toHaveBeenCalled();
});
