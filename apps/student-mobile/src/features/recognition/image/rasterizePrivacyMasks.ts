import type { ContainerBounds, MaskRect } from '../../../utils/privacyGeometry';

export async function rasterizePrivacyMasks(uri: string, masks: readonly MaskRect[], preview: ContainerBounds) {
  const photo = new Image();
  photo.src = uri;
  await photo.decode();
  const canvas = document.createElement('canvas');
  canvas.width = photo.naturalWidth;
  canvas.height = photo.naturalHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx || !canvas.width || !canvas.height || !(preview.width > 0 && preview.height > 0)) {
    throw new Error('MASK_IMAGE_UNAVAILABLE');
  }
  ctx.drawImage(photo, 0, 0);
  ctx.fillStyle = '#000';
  const scaleX = canvas.width / preview.width;
  const scaleY = canvas.height / preview.height;
  for (const { x, y, width, height } of masks) {
    const left = Math.max(0, Math.floor(x * scaleX));
    const top = Math.max(0, Math.floor(y * scaleY));
    const right = Math.min(canvas.width, Math.ceil((x + width) * scaleX));
    const bottom = Math.min(canvas.height, Math.ceil((y + height) * scaleY));
    if (!(right > left && bottom > top)) throw new Error('INVALID_MASK_BOUNDS');
    ctx.fillRect(left, top, right - left, bottom - top);
  }
  const result = canvas.toDataURL('image/jpeg', 0.95);
  if (!result.startsWith('data:image/jpeg;')) throw new Error('MASK_EXPORT_FAILED');
  return result;
}
