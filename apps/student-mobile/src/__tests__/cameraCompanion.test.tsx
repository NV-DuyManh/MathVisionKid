import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import * as ImagePicker from 'expo-image-picker';
import { Alert } from 'react-native';
import { useCameraPermissions } from 'expo-camera';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import CameraScreen from '../app/camera';
import { normalizeImageDraft } from '../features/recognition/image/imagePipeline';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

const mockTakePicture = jest.fn();
jest.mock('expo-router', () => ({ useRouter: jest.fn(), useLocalSearchParams: jest.fn(), useFocusEffect: jest.fn() }));
jest.mock('expo-camera', () => {
  const React = require('react');
  return { useCameraPermissions: jest.fn(), CameraView: React.forwardRef((props: any, ref: any) => {
    React.useImperativeHandle(ref, () => ({ takePictureAsync: mockTakePicture }));
    return React.createElement('CameraView', props);
  }) };
});
jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
jest.mock('../features/recognition/image/imagePipeline', () => ({ normalizeImageDraft: jest.fn(), logStageDiagnostic: jest.fn() }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView', useSafeAreaInsets: () => ({ top: 20, bottom: 20 }) }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: 'AppButton' }));
jest.mock('../components/domain/ScanFrame', () => ({ ScanFrame: 'ScanFrame' }));
let view: TestRenderer.ReactTestRenderer;
let blur: () => void;
let focus: () => void;
const push = jest.fn();
const button = (name: string) => view.root.findAll(node => (node.props.accessibilityLabel === name || node.props.title === name) && node.props.onPress)[0];
const preview = () => view.root.findByType('CameraView' as any);
beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft();
  (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn(), canGoBack: () => true });
  (useLocalSearchParams as jest.Mock).mockReturnValue({ mode: 'MATH_TUTOR' });
  (useCameraPermissions as jest.Mock).mockReturnValue([{ granted: true }, jest.fn()]);
  (useFocusEffect as jest.Mock).mockImplementation(callback => React.useEffect(() => {
    focus = () => { blur = callback(); }; focus(); return () => blur?.();
  }, [callback]));
  mockTakePicture.mockResolvedValue({ uri: 'file:///new-work.jpg', width: 1000, height: 800 });
  (normalizeImageDraft as jest.Mock).mockResolvedValue({ uri: 'file:///normalized.jpg', sourceImageUri: 'file:///normalized.jpg', originalImageUri: 'file:///normalized.jpg', rawUri: 'file:///new-work.jpg', width: 1000, height: 800, privacyConfirmed: false });
});
afterEach(() => { if (view) act(() => view.unmount()); });
const render = async () => { await act(async () => { view = TestRenderer.create(<CameraScreen />); }); };

it('waits for the native preview and preserves the original problem when taking its companion photo', async () => {
  const lessonContext = { purpose: 'ADD_WORK' as const, problemText: 'Có 12 bút và 5 bút.', workText: '',
    problemConfirmed: true, workConfirmed: false, lessonId: 'lesson_companion', uncertainWork: false };
  recognitionDraftStore.setDraft({ uri: 'file:///old.jpg', width: 1000, height: 800, mode: 'MATH_TUTOR', lessonContext });
  await render();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(mockTakePicture).not.toHaveBeenCalled();
  act(() => preview().props.onCameraReady());
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(recognitionDraftStore.getDraft()!.lessonContext).toEqual(lessonContext);
  expect(push).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
});

it('ignores rapid repeat taps and late photos after blur and refocus', async () => {
  let finish: (value: any) => void = () => {};
  mockTakePicture.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); act(() => preview().props.onCameraReady());
  const oldPreview = preview().props;
  act(() => { button('Chụp ảnh bài toán').props.onPress(); button('Chụp ảnh bài toán').props.onPress(); });
  expect(mockTakePicture).toHaveBeenCalledTimes(1);
  act(() => blur());
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
  act(() => focus());
  act(() => { oldPreview.onCameraReady(); oldPreview.onMountError({ message: 'late preview callback' }); });
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(1);
  await act(async () => finish({ uri: 'file:///late.jpg', width: 100, height: 100 }));
  expect(normalizeImageDraft).not.toHaveBeenCalled();
  expect(push).not.toHaveBeenCalled();
  act(() => preview().props.onCameraReady());
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(push).toHaveBeenCalledTimes(1);
});

it('keeps the gallery available after a preview error and ignores an abandoned picker result', async () => {
  let finish: (value: any) => void = () => {};
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  act(() => preview().props.onMountError({ message: 'private camera detail' }));
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  expect(button('Chọn ảnh từ thư viện').props.disabled).toBe(false);
  act(() => { void button('Chọn ảnh từ thư viện').props.onPress(); });
  act(() => blur());
  await act(async () => finish({ canceled: false, assets: [{ uri: 'file:///late-library.jpg', width: 100, height: 100 }] }));
  expect(recognitionDraftStore.getDraft()).toBeNull();
  expect(push).not.toHaveBeenCalled();
});


it('keeps the normalized JPEG after capture and never routes the original camera cache URI', async () => {
  await render(); act(() => preview().props.onCameraReady());
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(recognitionDraftStore.getDraft()).toMatchObject({ rawUri: 'file:///new-work.jpg', uri: 'file:///normalized.jpg',
    sourceImageUri: 'file:///normalized.jpg', originalImageUri: 'file:///normalized.jpg', privacyConfirmed: false });
  expect(push).toHaveBeenCalledWith({ pathname: '/privacy', params: { uri: 'file:///normalized.jpg' } });
});
it('keeps normalized JPEG when choosing the library from camera', async () => {
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: false, assets: [{ uri: 'ph://HEIC', width: 4000, height: 3000 }] });
  await render(); await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(normalizeImageDraft).toHaveBeenCalledWith('ph://HEIC', 4000, 3000, 'GALLERY');
  expect(recognitionDraftStore.getDraft()?.uri).toBe('file:///normalized.jpg');
});
it('preserves previous draft on conversion failure and permits retry', async () => {
  const notice = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  recognitionDraftStore.setDraft({ uri: 'file:///previous.jpg', width: 100, height: 100 });
  const previous = recognitionDraftStore.getDraft();
  (normalizeImageDraft as jest.Mock).mockRejectedValueOnce(new Error('IMAGE_DECODE_FAILED'));
  await render(); act(() => preview().props.onCameraReady());
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(push).not.toHaveBeenCalled(); expect(notice).toHaveBeenCalled(); expect(recognitionDraftStore.getDraft()).toBe(previous);
  await act(async () => button('Chụp ảnh bài toán').props.onPress()); expect(push).toHaveBeenCalledTimes(1); notice.mockRestore();
});
it('ignores normalization completing after camera blur and refocus', async () => {
  let finish!: (value: unknown) => void;
  (normalizeImageDraft as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); act(() => preview().props.onCameraReady());
  await act(async () => { button('Chụp ảnh bài toán').props.onPress(); });
  act(() => { blur(); focus(); });
  await act(async () => finish({ uri: 'file:///abandoned-normalized.jpg', width: 100, height: 100 }));
  expect(push).not.toHaveBeenCalled(); expect(recognitionDraftStore.getDraft()).toBeNull();
});
