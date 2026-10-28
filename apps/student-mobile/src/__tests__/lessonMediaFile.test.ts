import { saveNarration } from '../features/tutoring/narrationFile';

const mockFiles: any[] = [];
jest.mock('expo-file-system', () => ({
  Paths: { cache: 'file:///cache/' },
  File: jest.fn().mockImplementation((_directory, name) => {
    let complete = false;
    const file = {
      create: jest.fn(),
      writeSync: jest.fn(() => { complete = true; }),
      // In SDK 58, write() is asynchronous and cannot publish a ready URI yet.
      write: jest.fn(() => new Promise(() => {})),
      delete: jest.fn(),
      get uri() { if (!complete) throw new Error('File not written yet'); return `file:///cache/${name}`; },
    };
    mockFiles.push(file);
    return file;
  }),
}));

beforeEach(() => { mockFiles.length = 0; });

it('finishes writing private WAV bytes before exposing the playback URI', () => {
  const bytes = new Uint8Array([1, 2, 3]);
  const asset = saveNarration(bytes), file = mockFiles[0];
  expect(asset.uri).toMatch(/\.wav$/);
  expect(file.create).toHaveBeenCalledTimes(1);
  expect(file.writeSync).toHaveBeenCalledWith(bytes);
  expect(file.write).not.toHaveBeenCalled();
  asset.dispose(); expect(file.delete).toHaveBeenCalledTimes(1);
});
