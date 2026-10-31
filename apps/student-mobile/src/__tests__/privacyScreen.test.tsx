import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Image, Platform } from 'react-native';
import PrivacyGateScreen from '../app/privacy';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

const mockRouter = { push: jest.fn(), back: jest.fn(), canGoBack: () => true };
let mockFocus: () => void;
let mockBlur: () => void;
jest.mock('expo-router', () => ({
  useLocalSearchParams: () => ({}), useRouter: () => mockRouter,
  useFocusEffect: (callback: () => (() => void)) => require('react').useEffect(() => {
    mockFocus = () => { mockBlur = callback(); }; mockFocus(); return () => mockBlur();
  }, [callback]),
}));
jest.mock('expo-file-system/legacy', () => ({ getInfoAsync: jest.fn(async () => ({ exists: true, size: 1234, isDirectory: false })) }));
import * as FileSystem from 'expo-file-system/legacy';
const mockCapture = jest.fn(async () => 'file:///masked-output.jpg');
const mockPanHandlers: Record<string, (...args: any[]) => void> = {};

jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Icon' }));
jest.mock('react-native-view-shot', () => {
  const React = require('react');
  return React.forwardRef((props: any, ref: any) => {
    React.useImperativeHandle(ref, () => ({ capture: mockCapture }));
    return React.createElement('ViewShot', props);
  });
});
jest.mock('react-native-reanimated', () => ({
  __esModule: true, default: { View: 'AnimatedView' },
  useSharedValue: (value: unknown) => require('react').useRef({ value }).current,
  useAnimatedStyle: (updater: () => unknown) => updater(), runOnJS: (fn: unknown) => fn,
}));
jest.mock('react-native-gesture-handler', () => ({
  GestureHandlerRootView: 'GestureHandlerRootView', GestureDetector: 'GestureDetector',
  Gesture: { Pan: () => {
    const pan: any = {};
    for (const name of ['minDistance', 'onStart', 'onUpdate', 'onEnd', 'onFinalize']) pan[name] = (callback: any) => { mockPanHandlers[name] = callback; return pan; };
    return pan;
  } },
}));

const ORIGINAL = 'file:///portrait.jpg';
let view: TestRenderer.ReactTestRenderer;
const shot = () => view.root.findByType('ViewShot' as any);
const layout = (width = 390, height = 480) => act(() => {
  view.root.findAll(node => typeof node.props.onLayout === 'function')[0].props.onLayout({ nativeEvent: { layout: { width, height } } });
});
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const render = async () => { await act(async () => { view = TestRenderer.create(<PrivacyGateScreen />); }); layout(); };
beforeEach(() => {
  jest.clearAllMocks();
  jest.replaceProperty(Platform, 'OS', 'ios');
  (FileSystem.getInfoAsync as jest.Mock).mockResolvedValue({ exists: true, size: 1234, isDirectory: false });
  recognitionDraftStore.setDraft({ rawUri: ORIGINAL, uri: ORIGINAL, width: 1080, height: 2448, mimeType: 'image/jpeg', filename: 'portrait.jpg', mode: 'MATH_TUTOR' });
  jest.spyOn(Image, 'getSize').mockImplementation((_uri, success) => { success(1080, 2448); });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); jest.useRealTimers(); });
const photo = () => view.root.findAll(node => node.props.accessibilityLabel === 'Ảnh gốc để kiểm tra thông tin riêng tư')[0];
const loading = () => view.root.findAll(node => node.type === 'Text' && node.props.children === 'Đang tải ảnh bài tập...').length > 0;
const failure = () => view.root.findAll(node => node.type === 'Text' && node.props.children === 'Không thể hiển thị ảnh').length > 0;
const loaded = () => act(() => photo().props.onLoad({ nativeEvent: { source: { width: 1080, height: 2448, uri: ORIGINAL } } }));
const confirm = () => act(() => button('Tôi đã kiểm tra và che thông tin riêng tư trong ảnh').props.onPress());

it('keeps the original photo full height after returning from a wide crop', async () => {
  await render();
  const before = shot().props.style;
  act(() => recognitionDraftStore.updateDraft({ croppedImageUri: 'file:///wide-crop.jpg', uri: 'file:///wide-crop.jpg', width: 900, height: 180, privacyConfirmed: true }));
  act(() => view.update(<PrivacyGateScreen />));
  expect(shot().props.style).toEqual(before);
  expect(before.height).toBe(480);
  expect(before.width).toBeCloseTo(480 * 1080 / 2448);
  expect(Image.getSize).toHaveBeenCalledWith(ORIGINAL, expect.any(Function), expect.any(Function));
  const image = view.root.findAll(node => node.props.accessibilityLabel === 'Ảnh gốc để kiểm tra thông tin riêng tư')[0];
  expect(image.props.source.uri).toBe(ORIGINAL);
});

it('also fits the source when the privacy screen is remounted with cropped draft dimensions', async () => {
  recognitionDraftStore.updateDraft({ width: 900, height: 180 });
  await render();
  expect(shot().props.style.height).toBe(480);
  layout(844, 320);
  expect(shot().props.style.height).toBe(320);
  expect(shot().props.style.width).toBeCloseTo(320 * 1080 / 2448);
});

it('ignores a late size callback for a previously selected photo', async () => {
  const callbacks: ((width: number, height: number) => void)[] = [];
  (Image.getSize as jest.Mock).mockImplementation((_uri, success) => { callbacks.push(success); });
  await render();
  act(() => recognitionDraftStore.setDraft({ rawUri: 'file:///landscape.jpg', uri: 'file:///landscape.jpg', width: 1600, height: 400, mimeType: 'image/jpeg', filename: 'new.jpg', mode: 'MATH_TUTOR' }));
  await act(async () => {});
  await act(async () => callbacks[1](1600, 400));
  layout();
  expect(shot().props.style).toEqual({ width: 390, height: 97.5 });
  await act(async () => callbacks[0](1080, 2448));
  expect(shot().props.style).toEqual({ width: 390, height: 97.5 });
});

it('continues with the original photo and its own dimensions after revisiting privacy', async () => {
  recognitionDraftStore.updateDraft({ width: 900, height: 180 });
  await render();
  loaded();
  confirm();
  await act(async () => { await button('Tiếp tục xem lại').props.onPress(); });
  expect(recognitionDraftStore.getDraft()).toMatchObject({ privacyImageUri: ORIGINAL, width: 1080, height: 2448, privacyConfirmed: true });
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/crop', params: { retrySubmissionId: undefined } });
});


it('requires native onLoad and positive layout, not just getSize or a checkbox callback', async () => {
  await render(); expect(loading()).toBe(true); confirm();
  await act(async () => button('Tiếp tục xem lại').props.onPress());
  expect(mockRouter.push).not.toHaveBeenCalled();
  expect(recognitionDraftStore.getDraft()?.privacyConfirmed).not.toBe(true);
  loaded(); confirm(); layout(0, 0);
  await act(async () => button('Tiếp tục xem lại').props.onPress());
  expect(mockRouter.push).not.toHaveBeenCalled();
});
it('keeps cached iOS success terminal when loadStart arrives later or layout changes', async () => {
  await render(); loaded(); expect(loading()).toBe(false);
  act(() => photo().props.onLoadStart()); layout(844, 320);
  act(() => photo().props.onLoadStart());
  expect(loading()).toBe(false); expect(failure()).toBe(false);
  confirm(); expect(button('Tiếp tục xem lại').props.disabled).toBe(false);
});
it('locks an error until retry and ignores events from the failed attempt', async () => {
  await render(); const old = photo().props;
  act(() => old.onError()); act(() => { old.onLoadStart(); old.onLoad(); });
  expect(failure()).toBe(true); expect(loading()).toBe(false);
  expect(button('Tiếp tục xem lại').props.disabled).toBe(true);
  await act(async () => button('Thử tải lại ảnh').props.onPress());
  expect(FileSystem.getInfoAsync).toHaveBeenCalledTimes(2);
  act(() => { old.onError(); old.onLoad(); old.onLoadStart(); });
  expect(loading()).toBe(true); expect(failure()).toBe(false);
  loaded(); expect(loading()).toBe(false);
  expect(recognitionDraftStore.getDraft()?.privacyConfirmed).not.toBe(true);
});
it('rejects an expired cache file and retries without falling back to rawUri', async () => {
  (FileSystem.getInfoAsync as jest.Mock).mockResolvedValueOnce({ exists: false });
  await render(); expect(failure()).toBe(true); expect(photo()).toBeUndefined();
  expect(Image.getSize).not.toHaveBeenCalled();
  await act(async () => button('Thử tải lại ảnh').props.onPress());
  expect(photo().props.source.uri).toBe(ORIGINAL);
  loaded(); expect(failure()).toBe(false);
});
it('fails on getSize error even when draft dimensions are valid', async () => {
  (Image.getSize as jest.Mock).mockImplementation((_uri, _success, error) => error(new Error('decode')));
  await render(); expect(failure()).toBe(true); expect(loading()).toBe(false);
  expect(button('Tiếp tục xem lại').props.disabled).toBe(true);
});
it('fails closed if the decoder never answers and ignores late success', async () => {
  jest.useFakeTimers(); let late!: (w: number, h: number) => void;
  (Image.getSize as jest.Mock).mockImplementation((_uri, success) => { late = success; });
  await render(); await act(async () => jest.advanceTimersByTime(10000));
  expect(failure()).toBe(true); expect(loading()).toBe(false);
  await act(async () => late(1080, 2448)); expect(failure()).toBe(true);
  expect(recognitionDraftStore.getDraft()?.privacyConfirmed).not.toBe(true);
});
it('times out to error if Image never emits success, never to ready', async () => {
  jest.useFakeTimers(); await render(); const old = photo().props;
  await act(async () => jest.advanceTimersByTime(15000)); act(() => old.onLoad());
  expect(failure()).toBe(true); expect(loading()).toBe(false);
  expect(button('Tiếp tục xem lại').props.disabled).toBe(true);
});
it('invalidates events on blur and verifies and confirms again on focus', async () => {
  await render(); loaded(); confirm(); const old = photo().props;
  act(() => mockBlur()); act(() => { old.onError(); old.onLoadStart(); });
  await act(async () => mockFocus()); expect(loading()).toBe(true);
  act(() => { old.onLoad(); old.onError(); });
  expect(loading()).toBe(true); expect(failure()).toBe(false);
  loaded(); expect(button('Tiếp tục xem lại').props.disabled).toBe(true);
  expect(FileSystem.getInfoAsync).toHaveBeenCalledTimes(2);
});
it('subscribes to replacement drafts and ignores old-image events and confirmation', async () => {
  await render(); loaded(); confirm(); const old = photo().props;
  await act(async () => recognitionDraftStore.setDraft({ rawUri: 'ph://RAW', uri: 'file:///new.jpg', sourceImageUri: 'file:///new.jpg',
    width: 100, height: 100, mimeType: 'image/jpeg', filename: 'new.jpg', imageSessionId: 'new-session' }));
  layout(); act(() => { old.onLoad(); old.onError(); old.onLoadStart(); });
  expect(photo().props.source.uri).toBe('file:///new.jpg');
  expect(loading()).toBe(true); expect(failure()).toBe(false);
  loaded(); expect(button('Tiếp tục xem lại').props.disabled).toBe(true);
});
it('preserves masks through retry and commits only the verified masked output', async () => {
  jest.useFakeTimers(); await render(); loaded();
  act(() => { mockPanHandlers.onStart({ x: 30, y: 30 }); mockPanHandlers.onUpdate({ translationX: 60, translationY: 80 }); mockPanHandlers.onEnd(); });
  expect(button('Xóa tất cả vùng che')).toBeDefined();
  act(() => photo().props.onError());
  await act(async () => button('Thử tải lại ảnh').props.onPress()); loaded(); confirm();
  let done!: Promise<void>;
  await act(async () => { done = button('Tiếp tục xem lại').props.onPress(); });
  await act(async () => jest.advanceTimersByTime(120)); await act(async () => done);
  expect(mockCapture).toHaveBeenCalledTimes(1);
  expect(recognitionDraftStore.getDraft()).toMatchObject({ sourceImageUri: ORIGINAL, rawUri: ORIGINAL,
    privacyImageUri: 'file:///masked-output.jpg', uri: 'file:///masked-output.jpg', isMasked: true, privacyConfirmed: true,
    masks: [expect.objectContaining({ x: 30, y: 30, width: 60, height: 80 })] });
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/crop', params: { retrySubmissionId: undefined } });
});
it('does not commit privacy after navigating away during verification', async () => {
  let finish!: (info: unknown) => void;
  await render(); loaded(); confirm();
  (FileSystem.getInfoAsync as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  let done!: Promise<void>;
  act(() => { done = button('Tiếp tục xem lại').props.onPress(); mockBlur(); });
  await act(async () => { finish({ exists: true, size: 1234 }); await done; });
  expect(mockRouter.push).not.toHaveBeenCalled();
  expect(recognitionDraftStore.getDraft()?.privacyConfirmed).not.toBe(true);
});
