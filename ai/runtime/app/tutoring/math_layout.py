"""Bounded ink evidence for a single school calculation; no symbol recognition."""
import base64
import io

import cv2
import numpy as np
from PIL import Image, ImageDraw


def _ink(bgr):
    scale = min(1., 1000 / max(bgr.shape[:2]))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    hue, saturation, value = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
    mask = (((hue >= 90) | (hue <= 12)) &
            (saturation > max(55, float(np.median(saturation)) + 30)) & (value < 230)).astype(np.uint8)*255
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    return image, mask, stats[1:]


def isolated_fraction(bgr):
    """A tight numerator/bar/denominator crop can be math without a question."""
    image, _, parts = _ink(bgr)
    h, w = image.shape[:2]
    bodies = parts[(parts[:, 4] > 12) & (parts[:, 3] >= 8) & (parts[:, 3] < h*.5)]
    if not len(bodies):
        return False
    body = float(np.percentile(bodies[:, 3], 65))
    digits = bodies[bodies[:, 3] > body*.5]
    if not 2 <= len(digits) <= 6:
        return False
    bars = 0
    for x, y, width, height, area in parts:
        if not (body*.5 < width < body*3 and height < body*.3 and area > 8):
            continue
        cx, cy = digits[:, 0]+digits[:, 2]/2, digits[:, 1]+digits[:, 3]/2
        if (np.all((cx >= x-body*.3) & (cx <= x+width+body*.3))
                and ((y-cy > body*.3) & (y-cy < body*3)).any()
                and ((cy-y > body*.3) & (cy-y < body*3)).any()
                and np.ptp(digits[:, 1]+digits[:, 3]/2) < body*5
                and w < body*8 and h < body*12):
            bars += 1
    return bars == 1


def fraction_expression(bgr):
    """Support a bounded reread when several complete fraction bars are visible.

    This is ink evidence, not a math classification or a symbol transcription.
    Whole pages and a single subtraction/division bar do not qualify.
    """
    image, _, parts = _ink(bgr)
    h, w = image.shape[:2]
    bodies = parts[(parts[:, 4] > 12) & (parts[:, 3] >= 8) & (parts[:, 3] < h*.5)]
    if not len(bodies):
        return False
    body = float(np.percentile(bodies[:, 3], 65))
    if h > body*14 or w > body*40:
        return False
    digits = bodies[bodies[:, 3] > body*.5]
    cy = digits[:, 1]+digits[:, 3]/2
    bars = 0
    for x, y, width, height, area in parts:
        if not (body*.5 < width < body*3 and height < body*.3 and area > 8):
            continue
        overlap = (digits[:, 0] < x+width) & (digits[:, 0]+digits[:, 2] > x)
        if ((overlap & (y-cy > body*.3) & (y-cy < body*3)).any()
                and (overlap & (cy-y > body*.3) & (cy-y < body*3)).any()):
            bars += 1
    return bars >= 2


def division_panels(bgr):
    """Separate LEFT dividend/working and RIGHT divisor/quotient by ink bracket.

    Only a single bracket near the top of a tight crop is accepted. Neutral ink,
    multiple brackets and unsupported layouts keep the ordinary reading path.
    These panels guide transcription; they never justify a student line box.
    """
    image, mask, parts = _ink(bgr)
    h, w = image.shape[:2]
    bodies = parts[(parts[:, 4] > 10) & (parts[:, 3] >= 7) &
                   (parts[:, 3] < h*.24) & (parts[:, 2] < w*.25)]
    if len(bodies) < 5:
        return None
    body = float(np.median(bodies[:, 3]))
    lines = cv2.HoughLinesP(mask, 1, np.pi/180, threshold=max(12, int(body)),
                           minLineLength=max(15, body*.9), maxLineGap=max(4, round(body*.4)))
    if lines is None:
        return None
    vertical = [l for l in lines.reshape(-1, 4) if abs(l[2]-l[0]) < abs(l[3]-l[1])*.25]
    horizontal = [l for l in lines.reshape(-1, 4) if abs(l[3]-l[1]) < abs(l[2]-l[0])*.3]
    candidates = []
    cx, cy = bodies[:, 0]+bodies[:, 2]/2, bodies[:, 1]+bodies[:, 3]/2
    for x1, y1, x2, y2 in vertical:
        x, top, bottom = (x1+x2)/2, min(y1, y2), max(y1, y2)
        if bottom-top < body*1.8:
            continue
        for left, hy1, right, hy2 in horizontal:
            y = (hy1+hy2)/2
            if (abs(min(left, right)-x) > body*.4 or max(left, right)-x < body*1.4
                    or y > h*.4 or not top+body*.6 < y < bottom+body*.15):
                continue
            above = (cy > y-body*2.5) & (cy < y+body*.3)
            if not ((above & (cx < x-body*.3)).any()
                    and (above & (cx > x+body*.3) & (cx < max(left, right)+body)).any()
                    and ((cy > y+body*.25) & (cy < y+body*2.5) &
                         (cx > x+body*.3) & (cx < max(left, right)+body*3)).any()):
                continue
            if not any(abs(x-ox) < body*.7 and abs(y-oy) < body*1.4 for ox, oy in candidates):
                candidates.append((x, y))
    if len(candidates) != 1:
        return None
    x, y = candidates[0]
    if not w*.3 < x < w*.75:
        return None
    # Retain slanted digit bodies at the top left; never crop at a flat bar height.
    rectangles = [(0, 0, round(x-body*.15), min(h, round(y+body*.6))),
                  (round(x+body*.15), 0, w, round(y)),
                  (round(x+body*.15), round(y), w, min(h, round(y+body*3))),
                  (0, round(y+body*.6), round(x-body*.15), h)]
    labels = ('DIVIDEND (top left)', 'DIVISOR (top right)',
              'QUOTIENT (right below bar)', 'WRITTEN WORKING ROWS (left, top to bottom)')
    panels = [image[t:b, l:r] for l, t, r, b in rectangles]
    canvas = Image.new('RGB', (max(p.shape[1] for p in panels)+24,
                               sum(p.shape[0]+45 for p in panels)), 'white')
    draw = ImageDraw.Draw(canvas)
    offset = 0
    for label, panel in zip(labels, panels):
        draw.text((12, offset+8), label, fill='black')
        canvas.paste(Image.fromarray(cv2.cvtColor(panel, cv2.COLOR_BGR2RGB)), (12, offset+30))
        offset += panel.shape[0]+45
    stream = io.BytesIO()
    canvas.save(stream, 'JPEG', quality=95)
    return base64.b64encode(stream.getvalue()).decode('ascii')
