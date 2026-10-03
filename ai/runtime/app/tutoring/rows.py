"""Locate coloured handwriting in the displayed image, without model coordinates."""
import cv2
import numpy as np


def handwriting_rows(bgr, max_lines=35):
    height, width = bgr.shape[:2]
    if min(height, width) < 32:
        return []
    # Work at a bounded resolution; map boxes back to the supplied image.
    scale = min(1.0, 1800 / max(height, width))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    h, w = image.shape[:2]
    hue, saturation, value = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
    mask = ((hue >= 90) & (hue <= 178)
            & (saturation > max(40, float(np.median(saturation)) + 30))
            & (value < 220)).astype(np.uint8)
    # Page edges and long vertical rules must not determine row boundaries.
    margin = max(1, round(w * .03))
    mask[:, :margin] = 0
    mask[:, -margin:] = 0
    mask[:, mask.sum(axis=0) > h * .5] = 0
    rules = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((1, max(30, w//6)), np.uint8))
    rules |= cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((max(30, h//5), 1), np.uint8))
    mask[rules > 0] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros(count, dtype=np.uint8)
    for index in range(1, count):
        _, _, cw, ch, area = stats[index]
        if area >= 25 and ch >= 4 and cw >= 2:
            keep[index] = 1
    mask = keep[labels]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bodies = [cv2.boundingRect(c)[3] for c in contours
              if cv2.contourArea(c) > 30 and 8 < cv2.boundingRect(c)[3] < h * .2
              and cv2.boundingRect(c)[2] < w * .5]
    if len(bodies) < 8:
        return []
    # Detached Vietnamese accents are smaller than letter bodies. A modest
    # upper quantile avoids treating accents as independent writing rows.
    body_height = float(np.percentile(bodies, 60))
    window = max(5, round(body_height * .36)) | 1
    projection = np.convolve(mask.sum(axis=1), np.ones(window) / window, mode="same")
    radius = max(3, round(body_height * .23))
    floor = max(w * .008, float(np.percentile(projection, 90)) * .15)
    candidates = [y for y in range(radius, h - radius)
                  if projection[y] > floor
                  and projection[y] == np.max(projection[y-radius:y+radius+1])]
    peaks = []
    for y in sorted(candidates, key=lambda y: projection[y], reverse=True):
        if all(abs(y - other) > body_height * 1.2 for other in peaks):
            peaks.append(y)
    peaks.sort()
    if not 3 <= len(peaks) <= max_lines:
        return []
    gap = float(np.median(np.diff(peaks)))
    if np.max(np.diff(peaks)) > gap * 2.5:
        return []
    # Partition at valleys between row bodies. Accents and descenders remain
    # inside their row, and no crop can overlap its neighbour.
    cuts = [0]
    for left, right in zip(peaks, peaks[1:]):
        lo = left + round((right-left) * .25)
        hi = right - round((right-left) * .25)
        cuts.append(lo + int(np.argmin(projection[lo:hi+1])))
    cuts.append(h)
    boxes = []
    covered = 0
    for top, bottom, peak in zip(cuts, cuts[1:], peaks):
        # A distant page ornament must not expand a handwriting crop.
        top = max(top, round(peak-gap * .7))
        bottom = min(bottom, round(peak+gap * .7)+1)
        ys, xs = np.nonzero(mask[top:bottom])
        if len(xs) < 30:
            return []
        x1, x2 = max(0, int(xs.min())-6), min(w, int(xs.max())+7)
        y1, y2 = max(top, top+int(ys.min())-4), min(bottom, top+int(ys.max())+5)
        if x2-x1 < body_height * 2:
            return []
        boxes.append(tuple(round(v/scale) for v in (x1, y1, x2, y2)))
        covered += len(xs)
    if covered < np.count_nonzero(mask) * .7:
        return []
    return boxes
