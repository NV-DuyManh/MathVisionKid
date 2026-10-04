import { displayRectToSourceRect, calculateResize, closestCropHandle, MIN_CROP_SIZE, CropHandle } from '../cropGeometry';

describe('continuous crop resizing', () => {
  const box = { x: 100, y: 120, w: 160, h: 100 };
  const bounds = { minX: 0, minY: 0, maxX: 500, maxY: 400 };
  const handles: CropHandle[] = ['top', 'right', 'bottom', 'left', 'tl', 'tr', 'bl', 'br'];

  it('crops a single narrow text line instead of imposing a 60px minimum', () => {
    const result = calculateResize('bottom', 0, -95, box, bounds);
    expect(result.w).toBe(160);
    expect(result.h).toBe(MIN_CROP_SIZE);
    expect(result.h).toBeLessThanOrEqual(8);
  });

  it.each([
    ['top', 0, 160, { x: 100, y: 220, w: 160, h: 60 }],
    ['bottom', 0, -160, { x: 100, y: 60, w: 160, h: 60 }],
    ['left', 200, 0, { x: 260, y: 120, w: 40, h: 100 }],
    ['right', -200, 0, { x: 60, y: 120, w: 40, h: 100 }],
    ['tl', 200, 130, { x: 260, y: 220, w: 40, h: 30 }],
    ['tr', -200, 130, { x: 60, y: 220, w: 40, h: 30 }],
    ['bl', 200, -130, { x: 260, y: 90, w: 40, h: 30 }],
    ['br', -200, -130, { x: 60, y: 90, w: 40, h: 30 }],
  ])('keeps following %s across the opposite anchor and back in the same gesture', (handle, dx, dy, expected) => {
    expect(calculateResize(handle as CropHandle, dx as number, dy as number, box, bounds)).toEqual(expected);
    expect(calculateResize(handle as CropHandle, 0, 0, box, bounds)).toEqual(box);
  });

  it('crosses a zero-height selection continuously without a jump or invalid crop', () => {
    let previous = calculateResize('top', 0, 90, box, bounds);
    for (let dy = 91; dy <= 110; dy++) {
      const result = calculateResize('top', 0, dy, box, bounds);
      expect(result.h).toBeGreaterThanOrEqual(MIN_CROP_SIZE);
      expect(Math.abs(result.y - previous.y)).toBeLessThanOrEqual(1);
      expect(Math.abs(result.h - previous.h)).toBeLessThanOrEqual(1);
      previous = result;
    }
  });

  it.each(handles)('keeps %s resizing inside the image for large displacements', handle => {
    for (const dx of [-1000, -165, 0, 165, 1000]) for (const dy of [-1000, -105, 0, 105, 1000]) {
      const result = calculateResize(handle, dx, dy, box, bounds);
      expect(result.x).toBeGreaterThanOrEqual(bounds.minX);
      expect(result.y).toBeGreaterThanOrEqual(bounds.minY);
      expect(result.x + result.w).toBeLessThanOrEqual(bounds.maxX);
      expect(result.y + result.h).toBeLessThanOrEqual(bounds.maxY);
      expect(result.w).toBeGreaterThan(0);
      expect(result.h).toBeGreaterThan(0);
      if (handle === 'top' || handle === 'bottom') expect([result.x, result.w]).toEqual([box.x, box.w]);
      if (handle === 'left' || handle === 'right') expect([result.y, result.h]).toEqual([box.y, box.h]);
    }
  });

  it('still selects the nearest edge when thin selections make touch targets overlap', () => {
    const thin = { x: 80, y: 100, w: 200, h: 8 };
    expect(closestCropHandle(180, 99, thin)).toBe('top');
    expect(closestCropHandle(180, 109, thin)).toBe('bottom');
    expect(closestCropHandle(280, 104, thin)).toBe('right');
    expect(closestCropHandle(79, 104, thin)).toBe('left');
    expect(closestCropHandle(80, 100, thin)).toBe('tl');
    expect(closestCropHandle(280, 108, thin)).toBe('br');
  });

  it('fits an image smaller than the minimum visual span', () => {
    const tiny = { x: 10, y: 20, w: 4, h: 3 };
    const tinyBounds = { minX: 10, minY: 20, maxX: 14, maxY: 23 };
    for (const handle of handles) expect(calculateResize(handle, 100, -100, tiny, tinyBounds)).toEqual(tiny);
  });
});

describe('cropGeometry - displayRectToSourceRect', () => {
  const bMinX = 10, bMinY = 20;
  const actualW = 1000, actualH = 2000;

  it('CROP-01/02: portrait/landscape clean mapping', () => {
    const res = displayRectToSourceRect(110, 120, 100, 100, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res).toEqual({ x: 200, y: 200, w: 200, h: 200 });
  });

  it('CROP-04/06: clamps left/top edge (negative values)', () => {
    const res = displayRectToSourceRect(0, 0, 100, 100, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res.x).toBe(0);
    expect(res.y).toBe(0);
  });

  it('CROP-05/07: clamps right/bottom edge (overflow values)', () => {
    const res = displayRectToSourceRect(510, 1020, 100, 100, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res.x).toBeLessThan(actualW);
    expect(res.y).toBeLessThan(actualH);
    expect(res.x + res.w).toBeLessThanOrEqual(actualW);
    expect(res.y + res.h).toBeLessThanOrEqual(actualH);
  });

  it('CROP-08: all-four-edge clamp (box much larger than image)', () => {
    const res = displayRectToSourceRect(0, 0, 1000, 2000, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res.x).toBe(0);
    expect(res.y).toBe(0);
    expect(res.w).toBe(actualW);
    expect(res.h).toBe(actualH);
  });

  it('CROP-09: fractional coordinates correctly clamped', () => {
    const res = displayRectToSourceRect(500.5, 1000.7, 50, 50, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res.x + res.w).toBeLessThanOrEqual(actualW);
    expect(res.y + res.h).toBeLessThanOrEqual(actualH);
    expect(Number.isInteger(res.x)).toBe(true);
    expect(Number.isInteger(res.y)).toBe(true);
    expect(Number.isInteger(res.w)).toBe(true);
    expect(Number.isInteger(res.h)).toBe(true);
  });

  it('CROP-10: minimum-size rectangle enforced', () => {
    const res = displayRectToSourceRect(100, 100, 0.1, 0.2, bMinX, bMinY, 2.0, actualW, actualH);
    expect(res.w).toBe(1);
    expect(res.h).toBe(1);
  });

  it('CROP-11: stale/out-of-range input corrected deterministically', () => {
    const res = displayRectToSourceRect(2000, 3000, 100, 100, bMinX, bMinY, 2.0, actualW, actualH);
    // Origin clamped to actualW - 1
    expect(res.x).toBe(actualW - 1);
    expect(res.y).toBe(actualH - 1);
    expect(res.w).toBe(1);
    expect(res.h).toBe(1);
    expect(res.x + res.w).toBe(actualW);
    expect(res.y + res.h).toBe(actualH);
  });
});
