import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import * as ImagePicker from 'expo-image-picker';
import { useCameraPermissions } from 'expo-camera';
import { Alert } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import WebCameraScreen from '../app/camera.web';
import { normalizeImageDraft } from '../features/recognition/image/imagePipeline';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
const mockTakePicture = jest.fn();
jest.mock('expo-router', () => ({ useRouter: jest.fn(), useLocalSearchParams: jest.fn(), useFocusEffect: jest.fn() }));
jest.mock('expo-camera', () => {
  const React = require('react');
  return {
    useCameraPermissions: jest.fn(),
    CameraView: React.forwardRef((props: any, ref: any) => {
      React.useImperativeHandle(ref, () => ({ takePictureAsync: mockTakePicture }));
      return React.createElement('CameraView', props);
    }),
  };
});
jest.mock('expo-image-picker', () => ({ launchCameraAsync: jest.fn(), launchImageLibraryAsync: jest.fn(), CameraType: { back: 'back' } }));
jest.mock('../features/recognition/image/imagePipeline', () => ({ normalizeImageDraft: jest.fn() }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: 'AppButton' }));
let view: TestRenderer.ReactTestRenderer;
let blur: () => void;
const push = jest.fn();
const requestPermission = jest.fn();
const button = (label: string) => view.root.findAll(node => (node.props.title === label || node.props.accessibilityLabel === label) && typeof node.props.onPress === 'function')[0];
const preview = () => view.root.findByType('CameraView' as any);
const ready = () => act(() => preview().props.onCameraReady());
const failCamera = () => act(() => preview().props.onMountError({ message: 'No camera' }));
beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft();
  (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn(), replace: jest.fn(), canGoBack: () => true });
  (useLocalSearchParams as jest.Mock).mockReturnValue({ mode: 'MATH_TUTOR', problemText: 'Question retained' });
  (useFocusEffect as jest.Mock).mockImplementation(callback => {
    React.useEffect(() => { blur = callback(); return blur; }, [callback]);
  });
  (useCameraPermissions as jest.Mock).mockReturnValue([{ granted: true, status: 'granted' }, requestPermission]);
  (normalizeImageDraft as jest.Mock).mockResolvedValue({ uri: 'blob:normalized', width: 100, height: 80, isMasked: false });
  mockTakePicture.mockResolvedValue({ uri: 'data:image/jpeg;base64,photo', width: 1920, height: 1080 });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.useRealTimers(); });
const render = async () => { await act(async () => { view = TestRenderer.create(<WebCameraScreen />); }); };
it('opens the rear live preview by default and enables the shutter only when ready', async () => {
  await render();
  expect(preview().props.facing).toBe('back');
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  expect(ImagePicker.launchCameraAsync).not.toHaveBeenCalled();
  ready();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(false);
});
it('captures the live photo, retains lesson context and stops preview before privacy', async () => {
  const lessonContext = { purpose: 'ADD_PROBLEM' as const, workText: 'Pupil work retained' };
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30, lessonContext });
  await render(); ready();
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(mockTakePicture).toHaveBeenCalledWith({ quality: 1, base64: false });
  expect(ImagePicker.launchCameraAsync).not.toHaveBeenCalled();
  expect(normalizeImageDraft).toHaveBeenCalledWith('data:image/jpeg;base64,photo', 1920, 1080, 'CAMERA');
  expect(recognitionDraftStore.getDraft()).toMatchObject({ lessonContext, mode: 'MATH_TUTOR', problemText: 'Question retained', isMasked: false });
  expect(push).toHaveBeenCalledWith('/privacy');
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
});
it('keeps the image on normalization failure and allows a fresh live attempt', async () => {
  const notice = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30 });
  const stored = recognitionDraftStore.getDraft();
  (normalizeImageDraft as jest.Mock).mockRejectedValueOnce(new Error('Image load timed out'));
  await render(); ready();
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(recognitionDraftStore.getDraft()).toEqual(stored);
  expect(push).not.toHaveBeenCalled(); expect(notice).toHaveBeenCalled();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(false);
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(push).toHaveBeenCalledWith('/privacy'); notice.mockRestore();
});
it('offers the system camera only after a preview error and retains the rear capture preference', async () => {
  (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue({ canceled: false, assets: [{ uri: 'blob:photo', width: 4000, height: 3000 }] });
  await render();
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeUndefined();
  failCamera();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  await act(async () => button('Chụp bằng máy ảnh điện thoại').props.onPress());
  expect(ImagePicker.launchCameraAsync).toHaveBeenCalledWith(expect.objectContaining({ cameraType: 'back', allowsEditing: false }));
  expect(push).toHaveBeenCalledWith('/privacy');
});
it('keeps gallery and the camera permission action available before permission is granted', async () => {
  (useCameraPermissions as jest.Mock).mockReturnValue([null, requestPermission]);
  requestPermission.mockResolvedValue({ granted: false });
  await render();
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
  expect(button('Chọn ảnh từ thư viện').props.disabled).toBe(false);
  await act(async () => button('Cho phép mở máy ảnh').props.onPress());
  expect(requestPermission).toHaveBeenCalledTimes(1);
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeDefined();
});
it('keeps the previous image and navigation unchanged on library cancellation', async () => {
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30 });
  const stored = recognitionDraftStore.getDraft();
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });
  await render();
  await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(recognitionDraftStore.getDraft()).toEqual(stored);
  expect(normalizeImageDraft).not.toHaveBeenCalled(); expect(push).not.toHaveBeenCalled();
});
it('keeps the library usable while a browser permission prompt is unanswered', async () => {
  let finish!: (value: unknown) => void;
  (useCameraPermissions as jest.Mock).mockReturnValue([null, requestPermission]);
  requestPermission.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });
  await render();
  act(() => button('Cho phép mở máy ảnh').props.onPress());
  expect(button('Chọn ảnh từ thư viện').props.disabled).toBe(false);
  await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1);
  await act(async () => finish({ granted: false }));
});
it('ignores a second shutter tap while a photo is being captured', async () => {
  let finish!: (value: unknown) => void;
  mockTakePicture.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); ready();
  act(() => { button('Chụp ảnh bài toán').props.onPress(); button('Chụp ảnh bài toán').props.onPress(); });
  expect(mockTakePicture).toHaveBeenCalledTimes(1);
  await act(async () => finish({ uri: 'blob:photo', width: 200, height: 100 }));
  expect(push).toHaveBeenCalledTimes(1);
});
it('stops the preview on navigation away and ignores a late capture result', async () => {
  let finish!: (value: unknown) => void;
  mockTakePicture.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); ready();
  act(() => { button('Chụp ảnh bài toán').props.onPress(); blur(); });
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
  await act(async () => finish({ uri: 'blob:late', width: 200, height: 100 }));
  expect(normalizeImageDraft).not.toHaveBeenCalled(); expect(push).not.toHaveBeenCalled();
});
it('replaces an indefinitely starting preview with retry and capture fallback', async () => {
  jest.useFakeTimers();
  await render();
  act(() => jest.advanceTimersByTime(15000));
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
  expect(button('Thử mở lại máy ảnh')).toBeDefined();
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeDefined();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
});
