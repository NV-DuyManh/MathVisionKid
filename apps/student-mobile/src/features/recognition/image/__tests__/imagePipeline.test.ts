import { normalizeLocalFileUri, resolveSafeCropImage } from '../imagePipeline';
import { recognitionDraftStore } from '../../state/recognitionDraftStore';
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';

jest.mock('expo-image-manipulator', () => ({ manipulateAsync: jest.fn() }));
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
