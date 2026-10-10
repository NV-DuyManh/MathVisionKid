import { exportCropImage } from '../cropRotation.web';

const full = { x: 0, y: 0, w: 1, h: 1 };
const oldImage = global.Image, oldDocument = global.document, oldUrl = URL.createObjectURL;
let photo: any, canvas: any, context: any;
beforeEach(() => {
  jest.useFakeTimers();
  context = { fillRect: jest.fn(), scale: jest.fn(), translate: jest.fn(), rotate: jest.fn(), drawImage: jest.fn() };
  canvas = { width: 0, height: 0, getContext: () => context,
    toBlob: jest.fn((done: (blob: Blob | null) => void) => done(new Blob(['jpeg']))) };
  global.Image = class {
    naturalWidth = 6000; naturalHeight = 4000; onload: any; onerror: any; crossOrigin = ''; src = '';
    constructor() { photo = this; }
  } as any;
  global.document = { createElement: jest.fn(() => canvas) } as any;
  URL.createObjectURL = jest.fn(() => 'blob:final-crop');
});
afterEach(() => { jest.useRealTimers(); global.Image = oldImage; global.document = oldDocument; URL.createObjectURL = oldUrl; });

it('bounds a high resolution photo to a single final canvas and releases it', async () => {
  const result = exportCropImage('blob:masked-source', 0, full);
  expect(photo.src).toBe('blob:masked-source');
  photo.onload();
  await expect(result).resolves.toEqual({ uri: 'blob:final-crop', width: 3200, height: 2133 });
  expect(context.drawImage).toHaveBeenCalledWith(photo, -3000, -2000);
  expect(document.createElement).toHaveBeenCalledTimes(1);
  expect(canvas.width + canvas.height).toBe(0);
});
it('keeps a thin region nonempty without scaling it up', async () => {
  const result = exportCropImage('blob:masked-source', 0, { x: 0, y: 0.2, w: 0.1, h: 0.001 });
  photo.onload();
  await expect(result).resolves.toMatchObject({ width: 600, height: 4 });
});
it('fails a stalled image load within a bounded time without reading another source', async () => {
  const result = exportCropImage('blob:masked-source', 0, full);
  const rejection = expect(result).rejects.toThrow('Image load timed out');
  jest.advanceTimersByTime(15000);
  await rejection;
  expect(photo.src).toBe('');
  expect(document.createElement).not.toHaveBeenCalled();
});
it('fails a stalled encoder and releases its canvas instead of waiting indefinitely', async () => {
  canvas.toBlob.mockImplementation(() => {});
  const result = exportCropImage('blob:masked-source', 90, full);
  const rejection = expect(result).rejects.toThrow('Crop save timed out');
  photo.onload(); await Promise.resolve();
  jest.advanceTimersByTime(15000);
  await rejection;
  expect(canvas.width + canvas.height).toBe(0);
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});
it('propagates an empty encoding without creating a fallback or an invalid upload', async () => {
  canvas.toBlob.mockImplementation((done: (blob: Blob | null) => void) => done(null));
  const result = exportCropImage('blob:masked-source', 0, full);
  const rejection = expect(result).rejects.toThrow('Cannot save crop');
  photo.onload(); await rejection;
  expect(URL.createObjectURL).not.toHaveBeenCalled();
  expect(canvas.width + canvas.height).toBe(0);
});
