import { normalizeLocalFileUri, resolveSafeCropImage, normalizeImageDraft, inspectReadableImage } from '../imagePipeline';
import { recognitionDraftStore } from '../../state/recognitionDraftStore';
import { Image, Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';

import * as Manipulator from 'expo-image-manipulator';
jest.mock('expo-image-manipulator', () => ({ manipulateAsync: jest.fn(), SaveFormat: { JPEG: 'jpeg' } }));
jest.mock('expo-file-system/legacy', () => ({ getInfoAsync: jest.fn(), copyAsync: jest.fn(), cacheDirectory: 'file:///cache/' }));

describe('uploaded browser image URI handling', () => {
  beforeEach(() => {
    jest.replaceProperty(Platform, 'OS', 'web');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test.each([
    'blob:http://127.0.0.1:8087/owner-photo',
    'data:image/jpeg;base64,aGVsbG8=',
    'file:///cache/ExperienceData/%2540anonymous%2Fphoto.jpg',
    'content://photos/42',
  ])('preserves a usable URI without file-prefixing or decoding: %s', (uri) => {
    expect(normalizeLocalFileUri(uri)).toBe(uri);
  });

  it('keeps a gallery blob displayable when resolving the web crop source', async () => {
    const uri = 'blob:http://127.0.0.1:8087/owner-photo';
    expect(await resolveSafeCropImage(uri)).toEqual({
      originalUri: uri, normalizedUri: uri, exists: true, finalUri: uri,
    });
  });

  it('still normalizes a native local path', () => {
    expect(normalizeLocalFileUri('/cache/photo.jpg')).toBe('file:///cache/photo.jpg');
  });

  test.each(['blob:http://127.0.0.1:8087/owner-photo', 'data:image/jpeg;base64,aGVsbG8='])(
    'preserves the browser image through draft creation and crop updates: %s', (uri) => {
      recognitionDraftStore.setDraft({ rawUri: uri, uri, originalImageUri: uri,
        width: 932, height: 916, mimeType: 'image/jpeg', filename: 'owner.jpg', source: 'GALLERY' });
      expect(recognitionDraftStore.getDraft()?.originalImageUri).toBe(uri);
      recognitionDraftStore.updateDraft({ originalImageUri: uri, croppedImageUri: uri });
      expect(recognitionDraftStore.getDraft()?.originalImageUri).toBe(uri);
      recognitionDraftStore.clearDraft();
    }
  );
});

describe('native cache recovery across application identities', () => {
  afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
  });

  test.each([1, 2])('recovers an image with %i levels of experience-path encoding', async (levels) => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const prefix = 'file:///cache/ExperienceData/';
    const experience = '@anonymous/mathvision-kids-123';
    const original = `${prefix}${experience}/Camera/photo.jpg`;
    let encoded = experience;
    for (let i = 0; i < levels; i++) encoded = encodeURIComponent(encoded);
    const source = `${prefix}${encoded}/Camera/photo.jpg`;
    (FileSystem.getInfoAsync as jest.Mock).mockImplementation(async (uri: string) => ({
      exists: uri === source || uri.startsWith('file:///cache/recognition_crop_'),
    }));
    (FileSystem.copyAsync as jest.Mock).mockResolvedValue(undefined);
    const result = await resolveSafeCropImage(original);
    expect(result.exists).toBe(true);
    expect(result.finalUri).toMatch(/^file:\/\/\/cache\/recognition_crop_/);
    expect(FileSystem.copyAsync).toHaveBeenCalledWith({ from: source, to: result.finalUri });
  });
});


describe('verified iOS JPEG acquisition', () => {
  const RAW = 'file:///cache/ExperienceData/%2540anonymous%2Fkid/Camera/IMG 1.HEIC';
  const JPEG = 'file:///cache/ExperienceData/%2540anonymous%2Fkid/ImageManipulator/stable.jpg';
  beforeEach(() => {
    jest.clearAllMocks(); jest.replaceProperty(Platform, 'OS', 'ios');
    (Manipulator.manipulateAsync as jest.Mock).mockResolvedValue({ uri: JPEG, width: 900, height: 1200 });
    (FileSystem.getInfoAsync as jest.Mock).mockResolvedValue({ exists: true, size: 1234, isDirectory: false });
    jest.spyOn(Image, 'getSize').mockImplementation((_uri, success) => success(1200, 900));
  });
  afterEach(() => { jest.restoreAllMocks(); jest.useRealTimers(); recognitionDraftStore.clearDraft(); });
  test.each(['CAMERA', 'GALLERY'] as const)('keeps decoded JPEG and acquisition provenance for %s', async source => {
    const draft = await normalizeImageDraft(RAW, 4000, 3000, source); recognitionDraftStore.setDraft(draft);
    expect(Manipulator.manipulateAsync).toHaveBeenCalledWith(RAW, [], { compress: 0.95, format: 'jpeg' });
    expect(FileSystem.getInfoAsync).toHaveBeenCalledWith(JPEG);
    expect(Image.getSize).toHaveBeenCalledWith(JPEG, expect.any(Function), expect.any(Function));
    expect(recognitionDraftStore.getDraft()).toMatchObject({ rawUri: RAW, uri: JPEG, originalImageUri: JPEG,
      originalUri: JPEG, sourceImageUri: JPEG, width: 1200, height: 900, mimeType: 'image/jpeg', privacyConfirmed: false });
    recognitionDraftStore.updateDraft({ uri: 'file:///masked.jpg', privacyImageUri: 'file:///masked.jpg', privacyConfirmed: true });
    expect(recognitionDraftStore.getDraft()?.sourceImageUri).toBe(JPEG);
  });
  test.each(['ph://ABC/L0/001', 'assets-library://asset/asset.HEIC?id=123&ext=HEIC'])('preserves iOS asset scheme for conversion: %s', async uri => {
    expect(normalizeLocalFileUri(uri)).toBe(uri); await normalizeImageDraft(uri, 4000, 3000, 'GALLERY');
    expect(Manipulator.manipulateAsync).toHaveBeenCalledWith(uri, [], expect.any(Object));
  });
  it('does not return original URI labelled JPEG when conversion fails', async () => {
    (Manipulator.manipulateAsync as jest.Mock).mockRejectedValueOnce(new Error('HEIC unavailable'));
    await expect(normalizeImageDraft(RAW, 4000, 3000, 'GALLERY')).rejects.toThrow('HEIC unavailable');
    expect(recognitionDraftStore.getDraft()).toBeNull();
  });
  test.each([{ exists: false }, { exists: true, size: 0 }, { exists: true, size: 99, isDirectory: true }])('rejects unusable output %j', async info => {
    (FileSystem.getInfoAsync as jest.Mock).mockResolvedValueOnce(info);
    await expect(normalizeImageDraft(RAW, 4000, 3000, 'CAMERA')).rejects.toThrow();
    expect(Image.getSize).not.toHaveBeenCalled();
  });
  it('rejects an existing file that cannot decode', async () => {
    (Image.getSize as jest.Mock).mockImplementationOnce((_uri, _success, error) => error(new Error('corrupt')));
    await expect(normalizeImageDraft(RAW, 4000, 3000)).rejects.toThrow('IMAGE_DECODE_FAILED');
  });
  it('rejects nonlocal native output rather than using a transient asset', async () => {
    (Manipulator.manipulateAsync as jest.Mock).mockResolvedValueOnce({ uri: 'ph://transient' });
    await expect(normalizeImageDraft(RAW)).rejects.toThrow('IMAGE_NOT_MATERIALIZED');
  });
  it('rejects zero decoder dimensions instead of trusting picker metadata', async () => {
    (Image.getSize as jest.Mock).mockImplementationOnce((_uri, success) => success(0, 0));
    await expect(normalizeImageDraft(RAW, 4000, 3000)).rejects.toThrow('IMAGE_INVALID_DIMENSIONS');
  });
  it('rejects stalled file lookup without starting a late decoder', async () => {
    jest.useFakeTimers(); let finish!: (value: unknown) => void;
    (FileSystem.getInfoAsync as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const result = expect(inspectReadableImage(JPEG)).rejects.toThrow('IMAGE_READ_TIMEOUT');
    await jest.advanceTimersByTimeAsync(10000); await result;
    finish({ exists: true, size: 1234 }); await Promise.resolve();
    expect(Image.getSize).not.toHaveBeenCalled();
  });
  it('notifies subscribers on writes only and supports unsubscribe', () => {
    const listener = jest.fn(); const unsubscribe = recognitionDraftStore.subscribe(listener);
    recognitionDraftStore.getDraft(); recognitionDraftStore.getSnapshot(); expect(listener).not.toHaveBeenCalled();
    recognitionDraftStore.setDraft({ rawUri: RAW, uri: JPEG, sourceImageUri: JPEG, width: 100, height: 100, mimeType: 'image/jpeg', filename: 'input.jpg' });
    recognitionDraftStore.updateDraft({ mode: 'MATH_TUTOR' }); recognitionDraftStore.clearDraft();
    expect(listener).toHaveBeenCalledTimes(3); unsubscribe(); recognitionDraftStore.clearDraft();
    expect(listener).toHaveBeenCalledTimes(3);
  });
});
