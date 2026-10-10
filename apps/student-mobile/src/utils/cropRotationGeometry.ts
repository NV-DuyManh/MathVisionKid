export function normalizeRotation(degrees: number): number {
  'worklet';
  if (!Number.isFinite(degrees)) throw new Error('Invalid rotation');
  return ((degrees + 180) % 360 + 360) % 360 - 180;
}

/** Geometry only: safe to run on the UI thread while the user drags. */
export function rotatedFrame(width: number, height: number, degrees: number, viewportW: number, viewportH: number) {
  'worklet';
  const radians = normalizeRotation(degrees) * Math.PI / 180;
  const c = Math.abs(Math.cos(radians)), s = Math.abs(Math.sin(radians));
  const rotatedW = width * c + height * s, rotatedH = width * s + height * c;
  const scale = Math.min(viewportW / Math.max(1, rotatedW), viewportH / Math.max(1, rotatedH));
  const w = rotatedW * scale, h = rotatedH * scale;
  return { x: (viewportW - w) / 2, y: (viewportH - h) / 2, w, h, scale };
}
