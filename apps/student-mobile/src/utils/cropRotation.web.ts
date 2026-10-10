import { normalizeRotation } from './cropRotationGeometry';
export { normalizeRotation, rotatedFrame } from './cropRotationGeometry';

/** Draw only the final crop: avoid full-size PNG round trips on phone browsers. */
export async function exportCropImage(sourceUri: string, degrees: number, selection: { x: number; y: number; w: number; h: number }) {
  if (!sourceUri || Object.values(selection).some(v => !Number.isFinite(v)) || selection.w <= 0 || selection.h <= 0) throw new Error('Invalid crop');
  const angle = normalizeRotation(degrees) * Math.PI / 180;
  const source = await new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    const timer = setTimeout(() => { image.onload = image.onerror = null; image.src = ''; reject(new Error('Image load timed out')); }, 15000);
    image.crossOrigin = 'anonymous';
    image.onload = () => { clearTimeout(timer); image.onload = image.onerror = null; image.naturalWidth && image.naturalHeight ? resolve(image) : reject(new Error('Empty image')); };
    image.onerror = () => { clearTimeout(timer); reject(new Error('Cannot load crop source')); };
    image.src = sourceUri;
  });
  const c = Math.abs(Math.cos(angle)), s = Math.abs(Math.sin(angle));
  const rotatedW = Math.max(1, Math.round(source.naturalWidth * c + source.naturalHeight * s));
  const rotatedH = Math.max(1, Math.round(source.naturalHeight * c + source.naturalWidth * s));
  const x = Math.max(0, Math.min(rotatedW - 1, Math.round(selection.x * rotatedW)));
  const y = Math.max(0, Math.min(rotatedH - 1, Math.round(selection.y * rotatedH)));
  const w = Math.max(1, Math.min(rotatedW - x, Math.round(selection.w * rotatedW)));
  const h = Math.max(1, Math.min(rotatedH - y, Math.round(selection.h * rotatedH)));
  // Bound the final canvas below common phone limits; never resize a small crop up.
  const scale = Math.min(1, 3200 / Math.max(w, h));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(w * scale)); canvas.height = Math.max(1, Math.round(h * scale));
  const width = canvas.width, height = canvas.height;
  try {
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Cannot create crop canvas');
    context.fillStyle = '#fff'; context.fillRect(0, 0, canvas.width, canvas.height);
    context.scale(scale, scale);
    context.translate(rotatedW / 2 - x, rotatedH / 2 - y);
    context.rotate(angle);
    context.drawImage(source, -source.naturalWidth / 2, -source.naturalHeight / 2);
    const blob = await new Promise<Blob>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Crop save timed out')), 15000);
      try {
        canvas.toBlob(value => { clearTimeout(timer); value ? resolve(value) : reject(new Error('Cannot save crop')); }, 'image/jpeg', 0.95);
      } catch (failure) { clearTimeout(timer); reject(failure); }
    });
    return { uri: URL.createObjectURL(blob), width, height };
  } finally { canvas.width = canvas.height = 0; }
}
