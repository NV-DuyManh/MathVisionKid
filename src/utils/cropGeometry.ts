export const MIN_CROP_SIZE = 60;

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

export function calculateResizeTL(
  changeX: number, changeY: number,
  box: Rect, bounds: Bounds
): Rect {
  'worklet';
  const rightAnchor = box.x + box.w;
  const bottomAnchor = box.y + box.h;

  let newX = box.x + changeX;
  let newY = box.y + changeY;

  newX = Math.max(bounds.minX, Math.min(newX, rightAnchor - MIN_CROP_SIZE));
  newY = Math.max(bounds.minY, Math.min(newY, bottomAnchor - MIN_CROP_SIZE));

  return { x: newX, y: newY, w: rightAnchor - newX, h: bottomAnchor - newY };
}

export function calculateResizeTR(
  changeX: number, changeY: number,
  box: Rect, bounds: Bounds
): Rect {
  'worklet';
  const leftAnchor = box.x;
  const bottomAnchor = box.y + box.h;

  let newRight = (box.x + box.w) + changeX;
  let newY = box.y + changeY;

  newRight = Math.min(bounds.maxX, Math.max(newRight, leftAnchor + MIN_CROP_SIZE));
  newY = Math.max(bounds.minY, Math.min(newY, bottomAnchor - MIN_CROP_SIZE));

  return { x: leftAnchor, y: newY, w: newRight - leftAnchor, h: bottomAnchor - newY };
}

export function calculateResizeBL(
  changeX: number, changeY: number,
  box: Rect, bounds: Bounds
): Rect {
  'worklet';
  const rightAnchor = box.x + box.w;
  const topAnchor = box.y;

  let newX = box.x + changeX;
  let newBottom = (box.y + box.h) + changeY;

  newX = Math.max(bounds.minX, Math.min(newX, rightAnchor - MIN_CROP_SIZE));
  newBottom = Math.min(bounds.maxY, Math.max(newBottom, topAnchor + MIN_CROP_SIZE));

  return { x: newX, y: topAnchor, w: rightAnchor - newX, h: newBottom - topAnchor };
}

export function calculateResizeBR(
  changeX: number, changeY: number,
  box: Rect, bounds: Bounds
): Rect {
  'worklet';
  const leftAnchor = box.x;
  const topAnchor = box.y;

  let newRight = (box.x + box.w) + changeX;
  let newBottom = (box.y + box.h) + changeY;

  newRight = Math.min(bounds.maxX, Math.max(newRight, leftAnchor + MIN_CROP_SIZE));
  newBottom = Math.min(bounds.maxY, Math.max(newBottom, topAnchor + MIN_CROP_SIZE));

  return { x: leftAnchor, y: topAnchor, w: newRight - leftAnchor, h: newBottom - topAnchor };
}

export function displayRectToSourceRect(
  boxX: number, boxY: number, boxW: number, boxH: number,
  bMinX: number, bMinY: number, imgScale: number,
  actualW: number, actualH: number
): Rect {
  'worklet';
  const realX = Math.max(0, Math.round((boxX - bMinX) * imgScale));
  const realY = Math.max(0, Math.round((boxY - bMinY) * imgScale));
  const realW = Math.max(1, Math.min(actualW - realX, Math.round(boxW * imgScale)));
  const realH = Math.max(1, Math.min(actualH - realY, Math.round(boxH * imgScale)));
  return { x: realX, y: realY, w: realW, h: realH };
}
