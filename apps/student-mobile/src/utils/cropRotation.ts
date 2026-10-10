import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { normalizeRotation } from './cropRotationGeometry';
export { normalizeRotation, rotatedFrame } from './cropRotationGeometry';

/** Export once on confirmation. Native output dimensions are the crop authority. */
export async function exportCropImage(sourceUri: string, degrees: number, selection: { x: number; y: number; w: number; h: number }) {
  if (Object.values(selection).some(value => !Number.isFinite(value)) || selection.w <= 0 || selection.h <= 0) throw new Error('Invalid crop');
  const context = ImageManipulator.manipulate(sourceUri);
  const angle = normalizeRotation(degrees);
  if (angle) context.rotate(angle);
  const rotated = await context.renderAsync();
  const x = Math.max(0, Math.min(rotated.width - 1, Math.round(selection.x * rotated.width)));
  const y = Math.max(0, Math.min(rotated.height - 1, Math.round(selection.y * rotated.height)));
  const w = Math.max(1, Math.min(rotated.width - x, Math.round(selection.w * rotated.width)));
  const h = Math.max(1, Math.min(rotated.height - y, Math.round(selection.h * rotated.height)));
  const crop = ImageManipulator.manipulate(rotated);
  crop.crop({ originX: x, originY: y, width: w, height: h });
  const image = await crop.renderAsync();
  return image.saveAsync({ format: SaveFormat.JPEG, compress: 0.95 });
}
