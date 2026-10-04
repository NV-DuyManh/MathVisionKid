import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Image } from 'react-native';
import PrivacyGateScreen from '../app/privacy';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';

const mockRouter = { push: jest.fn(), back: jest.fn(), canGoBack: () => true };
jest.mock('expo-router', () => ({ useLocalSearchParams: () => ({}), useRouter: () => mockRouter }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Icon' }));
jest.mock('react-native-view-shot', () => 'ViewShot');
jest.mock('react-native-reanimated', () => ({
  __esModule: true, default: { View: 'AnimatedView' },
  useSharedValue: (value: unknown) => require('react').useRef({ value }).current,
  useAnimatedStyle: (updater: () => unknown) => updater(), runOnJS: (fn: unknown) => fn,
}));
jest.mock('react-native-gesture-handler', () => ({
  GestureHandlerRootView: 'GestureHandlerRootView', GestureDetector: 'GestureDetector',
  Gesture: { Pan: () => {
    const pan: any = {};
    for (const name of ['minDistance', 'onStart', 'onUpdate', 'onEnd', 'onFinalize']) pan[name] = () => pan;
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
  recognitionDraftStore.setDraft({ rawUri: ORIGINAL, uri: ORIGINAL, width: 1080, height: 2448, mimeType: 'image/jpeg', filename: 'portrait.jpg', mode: 'MATH_TUTOR' });
  jest.spyOn(Image, 'getSize').mockImplementation((_uri, success) => { success(1080, 2448); });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('keeps the original photo full height after returning from a wide crop', async () => {
  await render();
  const before = shot().props.style;
  recognitionDraftStore.updateDraft({ croppedImageUri: 'file:///wide-crop.jpg', uri: 'file:///wide-crop.jpg', width: 900, height: 180, privacyConfirmed: true });
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
  recognitionDraftStore.setDraft({ rawUri: 'file:///landscape.jpg', uri: 'file:///landscape.jpg', width: 1600, height: 400, mimeType: 'image/jpeg', filename: 'new.jpg', mode: 'MATH_TUTOR' });
  act(() => view.update(<PrivacyGateScreen />));
  act(() => callbacks[1](1600, 400));
  expect(shot().props.style).toEqual({ width: 390, height: 97.5 });
  act(() => callbacks[0](1080, 2448));
  expect(shot().props.style).toEqual({ width: 390, height: 97.5 });
});

it('continues with the original photo and its own dimensions after revisiting privacy', async () => {
  recognitionDraftStore.updateDraft({ width: 900, height: 180 });
  await render();
  act(() => button('Tôi đã kiểm tra và che thông tin riêng tư trong ảnh').props.onPress());
  await act(async () => { await button('Tiếp tục xem lại').props.onPress(); });
  expect(recognitionDraftStore.getDraft()).toMatchObject({ privacyImageUri: ORIGINAL, width: 1080, height: 2448, privacyConfirmed: true });
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/crop', params: { retrySubmissionId: undefined } });
});
