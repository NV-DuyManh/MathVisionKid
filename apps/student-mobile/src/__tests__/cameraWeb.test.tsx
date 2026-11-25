import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { pickWebPhoto } from '../features/recognition/image/pickWebPhoto';
import { useCameraPermissions } from 'expo-camera';
import { Text } from 'react-native';
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
jest.mock('../features/recognition/image/pickWebPhoto', () => ({ pickWebPhoto: jest.fn() }));
jest.mock('../features/recognition/image/imagePipeline', () => ({ normalizeImageDraft: jest.fn() }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: 'AppButton' }));
let view: TestRenderer.ReactTestRenderer;
let blur: () => void;
const push = jest.fn();
const requestPermission = jest.fn();
const getPermission = jest.fn().mockResolvedValue({ granted: true });
const button = (label: string) => view.root.findAll(node => (node.props.title === label || node.props.accessibilityLabel === label) && typeof node.props.onPress === 'function')[0];
const preview = () => view.root.findByType('CameraView' as any);
const ready = () => act(() => preview().props.onCameraReady());
const failCamera = () => act(() => preview().props.onMountError({ message: 'No camera' }));
const originalUrlMethods = Object.getOwnPropertyDescriptors(URL);
beforeAll(() => {
  Object.defineProperties(URL, {
    createObjectURL: { configurable: true, value: jest.fn(() => 'blob:photo') },
    revokeObjectURL: { configurable: true, value: jest.fn() },
  });
});
afterAll(() => {
  for (const name of ['createObjectURL', 'revokeObjectURL'] as const) {
    const descriptor = originalUrlMethods[name];
    if (descriptor) Object.defineProperty(URL, name, descriptor);
    else Reflect.deleteProperty(URL, name);
  }
});
beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft();
  (useRouter as jest.Mock).mockReturnValue({ push, back: jest.fn(), replace: jest.fn(), canGoBack: () => true });
  (useLocalSearchParams as jest.Mock).mockReturnValue({ mode: 'MATH_TUTOR', problemText: 'Question retained' });
  (useFocusEffect as jest.Mock).mockImplementation(callback => {
    React.useEffect(() => { blur = callback(); return blur; }, [callback]);
  });
  (useCameraPermissions as jest.Mock).mockReturnValue([{ granted: true, status: 'granted' }, requestPermission, getPermission]);
  (normalizeImageDraft as jest.Mock).mockResolvedValue({ uri: 'blob:normalized', width: 100, height: 80, isMasked: false });
  mockTakePicture.mockResolvedValue({ uri: 'data:image/jpeg;base64,photo', width: 1920, height: 1080 });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.useRealTimers(); });
const render = async () => { await act(async () => { view = TestRenderer.create(<WebCameraScreen />); }); };
it('opens the rear live preview by default and enables the shutter only when ready', async () => {
  await render();
  expect(preview().props.facing).toBe('back');
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  expect(pickWebPhoto).not.toHaveBeenCalled();
  ready();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(false);
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeUndefined();
});
it('captures the live photo, retains lesson context and stops preview before privacy', async () => {
  const lessonContext = { purpose: 'ADD_PROBLEM' as const, workText: 'Pupil work retained' };
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30, lessonContext });
  await render(); ready();
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(mockTakePicture).toHaveBeenCalledWith({ quality: 1, base64: false });
  expect(pickWebPhoto).not.toHaveBeenCalled();
  expect(normalizeImageDraft).toHaveBeenCalledWith('data:image/jpeg;base64,photo', 1920, 1080, 'CAMERA');
  expect(recognitionDraftStore.getDraft()).toMatchObject({ lessonContext, mode: 'MATH_TUTOR', problemText: 'Question retained', isMasked: false });
  expect(push).toHaveBeenCalledWith('/privacy');
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
});
it('keeps the image on normalization failure and allows a fresh live attempt', async () => {
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30 });
  const stored = recognitionDraftStore.getDraft();
  (normalizeImageDraft as jest.Mock).mockRejectedValueOnce(new Error('Image load timed out'));
  await render(); ready();
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(recognitionDraftStore.getDraft()).toEqual(stored);
  expect(push).not.toHaveBeenCalled();
  expect(view.root.findAllByType(Text).some(node =>
    node.props.accessibilityRole === 'alert' && node.props.children.startsWith('Chưa chụp được ảnh'),
  )).toBe(true);
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(false);
  await act(async () => button('Chụp ảnh bài toán').props.onPress());
  expect(push).toHaveBeenCalledWith('/privacy');
});
it('offers the rear system camera while the preview is starting or unavailable', async () => {
  (pickWebPhoto as jest.Mock).mockResolvedValue(new Blob(['photo'], { type: 'image/jpeg' }));
  await render();
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeDefined();
  failCamera();
  expect(button('Chụp ảnh bài toán').props.disabled).toBe(true);
  await act(async () => button('Chụp bằng máy ảnh điện thoại').props.onPress());
  expect(pickWebPhoto).toHaveBeenCalledWith(true);
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:photo');
  expect(push).toHaveBeenCalledWith('/privacy');
});

it('restarts a granted preview without opening a competing permission stream', async () => {
  await render();
  failCamera();
  await act(async () => button('Thử mở lại máy ảnh').props.onPress());
  expect(requestPermission).not.toHaveBeenCalled();
  expect(preview()).toBeDefined();
});
it('keeps gallery and the camera permission action available before permission is granted', async () => {
  (useCameraPermissions as jest.Mock).mockReturnValue([null, requestPermission, getPermission]);
  requestPermission.mockResolvedValue({ granted: false });
  await render();
  expect(view.root.findAllByType('CameraView' as any)).toHaveLength(0);
  expect(button('Chọn ảnh từ thư viện').props.disabled).toBe(false);
  await act(async () => button('Cho phép mở máy ảnh').props.onPress());
  expect(requestPermission).toHaveBeenCalledTimes(1);
  expect(button('Chụp bằng máy ảnh điện thoại')).toBeDefined();
});
it('keeps the library usable if the browser cannot query camera permission', async () => {
  getPermission.mockRejectedValueOnce(new Error('NotSupportedError'));
  (useCameraPermissions as jest.Mock).mockReturnValue([null, requestPermission, getPermission]);
  (pickWebPhoto as jest.Mock).mockResolvedValue(new Blob(['photo'], { type: 'image/jpeg' }));
  await render();
  expect(useCameraPermissions).toHaveBeenCalledWith({ get: false });
  expect(getPermission).toHaveBeenCalledTimes(1);
  await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(push).toHaveBeenCalledWith('/privacy');
});
it('keeps the previous image and navigation unchanged on library cancellation', async () => {
  recognitionDraftStore.setDraft({ uri: 'blob:old', width: 20, height: 30 });
  const stored = recognitionDraftStore.getDraft();
  (pickWebPhoto as jest.Mock).mockResolvedValue(undefined);
  await render();
  await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(recognitionDraftStore.getDraft()).toEqual(stored);
  expect(normalizeImageDraft).not.toHaveBeenCalled(); expect(push).not.toHaveBeenCalled();
});
it('keeps the library usable while a browser permission prompt is unanswered', async () => {
  let finish!: (value: unknown) => void;
  (useCameraPermissions as jest.Mock).mockReturnValue([null, requestPermission, getPermission]);
  requestPermission.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  (pickWebPhoto as jest.Mock).mockResolvedValue(undefined);
  await render();
  act(() => button('Cho phép mở máy ảnh').props.onPress());
  expect(button('Chọn ảnh từ thư viện').props.disabled).toBe(false);
  await act(async () => button('Chọn ảnh từ thư viện').props.onPress());
  expect(pickWebPhoto).toHaveBeenCalledTimes(1);
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
