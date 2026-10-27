import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Alert, Platform } from 'react-native';
import * as MediaLibrary from 'expo-media-library/legacy';
import * as ImagePicker from 'expo-image-picker';
import GalleryScreen from '../app/gallery';
import { recognitionDraftStore } from '../features/recognition/state/recognitionDraftStore';
import { normalizeImageDraft } from '../features/recognition/image/imagePipeline';

const mockRouter = { push: jest.fn(), back: jest.fn(), replace: jest.fn() };
let mockBlur: () => void;
let mockFocus: () => void;
jest.mock('expo-router', () => ({ useRouter: () => mockRouter,
  useFocusEffect: (callback: () => (() => void)) => require('react').useEffect(() => {
    mockFocus = () => { mockBlur = callback(); }; mockFocus(); return () => mockBlur();
  }, [callback]),
}));
jest.mock('react-native-safe-area-context', () => ({ useSafeAreaInsets: () => ({ top: 20, bottom: 20 }) }));
jest.mock('expo-media-library/legacy', () => ({ getPermissionsAsync: jest.fn(), getAssetsAsync: jest.fn(), getAssetInfoAsync: jest.fn() }));
jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
jest.mock('../features/recognition/image/imagePipeline', () => ({ normalizeImageDraft: jest.fn(), logStageDiagnostic: jest.fn() }));
const RAW = 'ph://PHOTO/L0/001';
const LOCAL = 'file:///Photos/IMG 1.HEIC';
const JPEG = 'file:///ImageManipulator/normalized.jpg';
const assets = [1, 2].map(id => ({ id: String(id), uri: RAW + id, filename: `IMG${id}.HEIC`, width: 4000, height: 3000 }));
const normalized = { rawUri: LOCAL, uri: JPEG, sourceImageUri: JPEG, originalImageUri: JPEG, originalUri: JPEG,
  width: 1200, height: 900, mimeType: 'image/jpeg', filename: 'normalized.jpg', privacyConfirmed: false, source: 'GALLERY' };
let view: TestRenderer.ReactTestRenderer;
let notice: jest.SpyInstance;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const select = (id = '1') => act(() => view.root.findAll(node => node.props.testID === `gallery-cell-${id}` && node.props.onPress)[0].props.onPress());
const render = async () => { await act(async () => { view = TestRenderer.create(<GalleryScreen />); }); };
beforeEach(() => {
  jest.clearAllMocks(); recognitionDraftStore.clearDraft(); jest.replaceProperty(Platform, 'OS', 'ios');
  notice = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  (MediaLibrary.getPermissionsAsync as jest.Mock).mockResolvedValue({ granted: true });
  (MediaLibrary.getAssetsAsync as jest.Mock).mockResolvedValue({ assets, hasNextPage: false });
  (MediaLibrary.getAssetInfoAsync as jest.Mock).mockResolvedValue({ localUri: LOCAL });
  (normalizeImageDraft as jest.Mock).mockResolvedValue({ ...normalized });
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: false, assets: [{ uri: LOCAL, width: 4000, height: 3000 }] });
});
afterEach(() => { if (view) act(() => view.unmount()); notice.mockRestore(); jest.restoreAllMocks(); });

it('resolves Photos localUri but stores and routes only the normalized JPEG', async () => {
  await render(); select(); await act(async () => button('Dùng ảnh này').props.onPress());
  expect(normalizeImageDraft).toHaveBeenCalledWith(LOCAL, 4000, 3000, 'GALLERY');
  expect(recognitionDraftStore.getDraft()).toMatchObject(normalized);
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/privacy', params: { uri: JPEG } });
});
it('also preserves normalized JPEG in the fallback system picker', async () => {
  (MediaLibrary.getPermissionsAsync as jest.Mock).mockRejectedValueOnce(new Error('unavailable'));
  await render(); await act(async () => button('Chọn ảnh từ thiết bị').props.onPress());
  expect(recognitionDraftStore.getDraft()).toMatchObject(normalized);
  expect(mockRouter.push).toHaveBeenCalledWith({ pathname: '/privacy', params: { uri: JPEG, originalImageUri: JPEG } });
});
it('keeps previous draft on normalization failure and allows retry', async () => {
  recognitionDraftStore.setDraft({ ...normalized, uri: 'file:///previous.jpg' }); const old = recognitionDraftStore.getDraft();
  (normalizeImageDraft as jest.Mock).mockRejectedValueOnce(new Error('IMAGE_FILE_UNREADABLE'));
  await render(); select(); await act(async () => button('Dùng ảnh này').props.onPress());
  expect(mockRouter.push).not.toHaveBeenCalled(); expect(notice).toHaveBeenCalled();
  expect(recognitionDraftStore.getDraft()).toBe(old);
  await act(async () => button('Dùng ảnh này').props.onPress()); expect(mockRouter.push).toHaveBeenCalledTimes(1);
});
it('shows fallback errors and never navigates or discards the previous draft', async () => {
  (MediaLibrary.getPermissionsAsync as jest.Mock).mockRejectedValueOnce(new Error('unavailable'));
  (normalizeImageDraft as jest.Mock).mockRejectedValueOnce(new Error('IMAGE_DECODE_FAILED'));
  await render(); await act(async () => button('Chọn ảnh từ thiết bị').props.onPress());
  expect(notice).toHaveBeenCalled(); expect(mockRouter.push).not.toHaveBeenCalled();
});
it('ignores normalization completing after blur and focus', async () => {
  let finish!: (value: unknown) => void;
  (normalizeImageDraft as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); select(); await act(async () => { button('Dùng ảnh này').props.onPress(); });
  act(() => { mockBlur(); mockFocus(); }); await act(async () => finish(normalized));
  expect(mockRouter.push).not.toHaveBeenCalled(); expect(recognitionDraftStore.getDraft()).toBeNull();
});
it('ignores a normalization result after selecting another photo', async () => {
  let finish!: (value: unknown) => void;
  (normalizeImageDraft as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render(); select(); await act(async () => { button('Dùng ảnh này').props.onPress(); });
  select('2'); await act(async () => finish(normalized));
  expect(mockRouter.push).not.toHaveBeenCalled(); expect(recognitionDraftStore.getDraft()).toBeNull();
});
it('ignores a late fallback picker result after blur and prevents double opening', async () => {
  (MediaLibrary.getPermissionsAsync as jest.Mock).mockRejectedValueOnce(new Error('unavailable'));
  let finish!: (value: unknown) => void;
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await render();
  act(() => { button('Chọn ảnh từ thiết bị').props.onPress(); button('Chọn ảnh từ thiết bị').props.onPress(); mockBlur(); });
  await act(async () => finish({ canceled: false, assets: [{ uri: LOCAL, width: 100, height: 100 }] }));
  expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledTimes(1);
  expect(normalizeImageDraft).not.toHaveBeenCalled(); expect(mockRouter.push).not.toHaveBeenCalled();
});
it('preserves the previous draft when picker is canceled', async () => {
  (MediaLibrary.getPermissionsAsync as jest.Mock).mockRejectedValueOnce(new Error('unavailable'));
  (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValueOnce({ canceled: true });
  recognitionDraftStore.setDraft(normalized as any); const old = recognitionDraftStore.getDraft();
  await render(); await act(async () => button('Chọn ảnh từ thiết bị').props.onPress());
  expect(recognitionDraftStore.getDraft()).toBe(old); expect(mockRouter.push).not.toHaveBeenCalled();
});
