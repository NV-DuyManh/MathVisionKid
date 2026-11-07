import { saveNarration } from '../features/tutoring/narrationFile';

const mockFiles: any[] = [];
let mockDelayWrite = false;
jest.mock('expo-file-system', () => ({
  Paths: { cache: 'file:///cache/' },
  File: jest.fn().mockImplementation((_directory, name) => {
    let complete = false;
    const file = {
      create: jest.fn(),
      writeSync: jest.fn(() => { throw new Error('Synchronous write blocks the lesson'); }),
      write: jest.fn(() => new Promise<void>(resolve => {
        file.finishWrite = () => { complete = true; resolve(); };
        if (!mockDelayWrite) file.finishWrite();
      })),
      finishWrite: () => {},
      delete: jest.fn(),
      get uri() { if (!complete) throw new Error('File not written yet'); return `file:///cache/${name}`; },
    };
    mockFiles.push(file);
    return file;
  }),
}));

beforeEach(() => { mockFiles.length = 0; mockDelayWrite = false; });

it('yields while writing private WAV bytes and exposes the playback URI only after completion', async () => {
  const bytes = new Uint8Array([1, 2, 3]);
  mockDelayWrite = true;
  const pending = saveNarration(bytes), file = mockFiles[0];
  expect(pending).toBeInstanceOf(Promise);
  let published = false;
  void pending.then(() => { published = true; });
  await Promise.resolve();
  expect(published).toBe(false);
  file.finishWrite();
  const asset = await pending;
  expect(asset.uri).toMatch(/\.wav$/);
  expect(file.create).toHaveBeenCalledTimes(1);
  expect(file.write).toHaveBeenCalledWith(bytes);
  expect(file.writeSync).not.toHaveBeenCalled();
  asset.dispose(); expect(file.delete).toHaveBeenCalledTimes(1);
});
