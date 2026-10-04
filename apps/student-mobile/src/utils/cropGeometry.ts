export const MIN_CROP_SIZE = 8;
export type CropHandle = 'tl' | 'tr' | 'bl' | 'br' | 'top' | 'right' | 'bottom' | 'left';

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export function calculateDrag(
  changeX: number, changeY: number,
  box: Rect, bounds: Bounds
): Rect {
  'worklet';
  const newX = Math.max(bounds.minX, Math.min(box.x + changeX, bounds.maxX - box.w));
  const newY = Math.max(bounds.minY, Math.min(box.y + changeY, bounds.maxY - box.h));
  return { x: newX, y: newY, w: box.w, h: box.h };
}

function resizeSpan(moving: number, anchor: number, min: number, max: number) {
  'worklet';
  moving = Math.max(min, Math.min(max, moving));
  const size = Math.max(Math.min(MIN_CROP_SIZE, max - min), Math.abs(moving - anchor));
  // A small centered span bridges the crossing without an abrupt jump or zero-sized crop.
  const position = Math.max(min, Math.min(max - size, (moving + anchor - size) / 2));
  return { position, size };
}

/** Keep the opposite anchor fixed for the whole gesture; crossing it changes sides. */
export function calculateResize(handle: CropHandle, changeX: number, changeY: number, box: Rect, bounds: Bounds): Rect {
  'worklet';
  const left = handle === 'left' || handle === 'tl' || handle === 'bl';
  const right = handle === 'right' || handle === 'tr' || handle === 'br';
  const top = handle === 'top' || handle === 'tl' || handle === 'tr';
  const bottom = handle === 'bottom' || handle === 'bl' || handle === 'br';
  const horizontal = left || right ? resizeSpan((left ? box.x : box.x + box.w) + changeX, left ? box.x + box.w : box.x, bounds.minX, bounds.maxX) : { position: box.x, size: box.w };
  const vertical = top || bottom ? resizeSpan((top ? box.y : box.y + box.h) + changeY, top ? box.y + box.h : box.y, bounds.minY, bounds.maxY) : { position: box.y, size: box.h };
  return { x: horizontal.position, y: vertical.position, w: horizontal.size, h: vertical.size };
}

export function cropHandlePoint(handle: CropHandle, box: Rect) {
  'worklet';
  return {
    x: box.x + (handle === 'left' || handle === 'tl' || handle === 'bl' ? 0 : handle === 'right' || handle === 'tr' || handle === 'br' ? box.w : box.w / 2),
    y: box.y + (handle === 'top' || handle === 'tl' || handle === 'tr' ? 0 : handle === 'bottom' || handle === 'bl' || handle === 'br' ? box.h : box.h / 2),
  };
}

/** Disambiguate overlapping 48px touch targets when the crop becomes very thin. */
export function closestCropHandle(x: number, y: number, box: Rect): CropHandle {
  'worklet';
  const handles: CropHandle[] = ['top', 'right', 'bottom', 'left', 'tl', 'tr', 'bl', 'br'];
  let closest: CropHandle = 'top', distance = Infinity;
  for (const handle of handles) {
    const point = cropHandlePoint(handle, box);
    const candidate = (point.x - x) ** 2 + (point.y - y) ** 2;
    if (candidate < distance) { closest = handle; distance = candidate; }
  }
  return closest;
}

export function displayRectToSourceRect(
  boxX: number, boxY: number, boxW: number, boxH: number,
  bMinX: number, bMinY: number, imgScale: number,
  actualW: number, actualH: number
): Rect {
  'worklet';
  let realX = Math.round((boxX - bMinX) * imgScale);
  let realY = Math.round((boxY - bMinY) * imgScale);
  let realW = Math.round(boxW * imgScale);
  let realH = Math.round(boxH * imgScale);

  // Clamp origins securely to [0, max-1]
  realX = Math.max(0, Math.min(actualW - 1, realX));
  realY = Math.max(0, Math.min(actualH - 1, realY));

  // Clamp dimensions securely to remaining space [1, max-origin]
  realW = Math.max(1, Math.min(actualW - realX, realW));
  realH = Math.max(1, Math.min(actualH - realY, realH));

  return { x: realX, y: realY, w: realW, h: realH };
}
