import { saveLessonMovie } from '../features/tutoring/lessonVideoFile';

const mockFiles: any[] = [];
jest.mock('expo-file-system', () => ({
  Paths: { cache: 'file:///cache/' },
  File: jest.fn().mockImplementation((_directory, name) => {
    let complete = false;
    const file = {
      create: jest.fn(), writeSync: jest.fn(() => { complete = true; }),
      write: jest.fn(() => new Promise(() => {})), delete: jest.fn(),
      get uri() { if (!complete) throw new Error('Movie bytes are not ready'); return `file:///cache/${name}`; },
    };
    mockFiles.push(file);
    return file;
  }),
}));

it('finishes the SDK 58 movie write before publishing its playback URI', () => {
  const bytes = new Uint8Array([1, 2, 3]);
  const asset = saveLessonMovie(bytes), file = mockFiles[0];
  expect(asset.uri).toMatch(/\.mp4$/);
  expect(file.writeSync).toHaveBeenCalledWith(bytes);
  expect(file.write).not.toHaveBeenCalled();
  asset.dispose(); expect(file.delete).toHaveBeenCalledTimes(1);
});
