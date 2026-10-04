import { ImageManipulator } from 'expo-image-manipulator';
import { normalizeRotation, rotatedFrame, exportCropImage } from '../cropRotation';
jest.mock('expo-image-manipulator', () => ({ ImageManipulator: { manipulate: jest.fn() }, SaveFormat: { JPEG: 'jpeg' } }));

it('keeps fine angles and full turns valid', () => {
  expect(normalizeRotation(360)).toBe(0);
  expect(normalizeRotation(-450)).toBe(-90);
  expect(normalizeRotation(270.5)).toBe(-89.5);
  expect(normalizeRotation(-0.5)).toBe(-0.5);
  expect(() => normalizeRotation(NaN)).toThrow();
});

it.each([0, -45, -7.5, 45, 90, 180, 270, 360])('fits a rotated photo in the viewport without exporting a file: %s degrees', angle => {
  (ImageManipulator.manipulate as jest.Mock).mockClear();
  const frame = rotatedFrame(4000, 3000, angle, 360, 500);
  expect(frame.x).toBeGreaterThanOrEqual(-1e-8);
  expect(frame.y).toBeGreaterThanOrEqual(-1e-8);
  expect(frame.x + frame.w).toBeLessThanOrEqual(360.00001);
  expect(frame.y + frame.h).toBeLessThanOrEqual(500.00001);
  expect(frame.w > 0 && frame.h > 0).toBe(true);
  expect(ImageManipulator.manipulate).not.toHaveBeenCalled();
});

it('uses native rotated dimensions, keeps the masked source, and saves only the final crop', async () => {
  const rotate = jest.fn();
  const cropped = { width: 1600, height: 800, saveAsync: jest.fn().mockResolvedValue({ uri: 'file:///final.jpg', width: 1600, height: 800 }) };
  const rotated = { width: 2000, height: 1000, saveAsync: jest.fn() };
  const crop = jest.fn();
  (ImageManipulator.manipulate as jest.Mock).mockReturnValueOnce({ rotate, renderAsync: async () => rotated })
    .mockReturnValueOnce({ crop, renderAsync: async () => cropped });
  const result = await exportCropImage('file:///privacy-masked.jpg', 90.5, { x: 0.1, y: 0.1, w: 0.8, h: 0.8 });
  expect(rotate).toHaveBeenCalledWith(90.5);
  expect(crop).toHaveBeenCalledWith({ originX: 200, originY: 100, width: 1600, height: 800 });
  expect(rotated.saveAsync).not.toHaveBeenCalled();
  expect(cropped.saveAsync).toHaveBeenCalledWith({ format: 'jpeg', compress: 0.95 });
  expect(result.uri).toBe('file:///final.jpg');
  expect((ImageManipulator.manipulate as jest.Mock).mock.calls.slice(-2)).toEqual([['file:///privacy-masked.jpg'], [rotated]]);
});

it('propagates a failed masked export without an unmasked fallback', async () => {
  (ImageManipulator.manipulate as jest.Mock).mockClear().mockReturnValue({ rotate: jest.fn(), renderAsync: async () => { throw new Error('Cannot read masked source'); } });
  await expect(exportCropImage('file:///privacy-masked.jpg', -90, { x: 0, y: 0, w: 1, h: 1 })).rejects.toThrow();
  expect(ImageManipulator.manipulate).toHaveBeenCalledTimes(1);
  expect(ImageManipulator.manipulate).toHaveBeenCalledWith('file:///privacy-masked.jpg');
});

it('exports a nonempty narrow crop without an arbitrary ten-pixel rejection', async () => {
  const rotated = { width: 1080, height: 2448 };
  const crop = jest.fn();
  const saveAsync = jest.fn().mockResolvedValue({ uri: 'file:///narrow.jpg', width: 1080, height: 5 });
  (ImageManipulator.manipulate as jest.Mock).mockReturnValueOnce({ renderAsync: async () => rotated })
    .mockReturnValueOnce({ crop, renderAsync: async () => ({ saveAsync }) });
  const result = await exportCropImage('file:///masked.jpg', 0, { x: 0, y: 0.5, w: 1, h: 5 / 2448 });
  expect(crop).toHaveBeenCalledWith({ originX: 0, originY: 1224, width: 1080, height: 5 });
  expect(result.height).toBe(5);
});
