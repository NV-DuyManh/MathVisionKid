"""Locate coloured handwriting in the displayed image, without model coordinates."""
import cv2
import numpy as np


def _page_angle(bgr):
    """Use long, agreeing notebook rules, never a model's guessed orientation."""
    h, w = bgr.shape[:2]
    scale = min(1.0, 900 / max(h, w))
    small = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 40, 100)
    rules = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                          minLineLength=max(60, round(w*scale*.3)), maxLineGap=10)
    if rules is None:
        return 0.0
    angles, lengths = [], []
    for x1, y1, x2, y2 in rules.reshape(-1, 4):
        angle = np.degrees(np.arctan2(y2-y1, x2-x1))
        if abs(angle) < 12:
            angles.append(angle)
            lengths.append(np.hypot(x2-x1, y2-y1))
    if len(angles) < 4:
        return 0.0
    order = np.argsort(angles)
    angles, lengths = np.array(angles)[order], np.array(lengths)[order]
    angle = float(angles[np.searchsorted(np.cumsum(lengths), lengths.sum()/2)])
    if lengths[abs(angles-angle) < 2].sum() < lengths.sum()*.6:
        return 0.0
    return angle if abs(angle) > 1.5 else 0.0


def handwriting_rows(bgr, max_lines=35):
    height, width = bgr.shape[:2]
    if min(height, width) < 32:
        return []
    # Wide cropped pages suffer most from tilted rules merging nearby rows.
    # Keep complex full-page/column layouts on the established detector path.
    angle = _page_angle(bgr) if width > height*1.2 else 0.0
    if not angle:
        return _straight_rows(bgr, max_lines)
    scale = min(1.0, 1800 / max(height, width))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w/2, h/2), angle, 1)
    aligned = cv2.warpAffine(image, matrix, (w, h), borderValue=(255, 255, 255))
    inverse = cv2.invertAffineTransform(matrix)
    boxes = []
    for x1, y1, x2, y2 in _straight_rows(aligned, max_lines):
        corners = np.array([[x1, y1, 1], [x2, y1, 1], [x2, y2, 1], [x1, y2, 1]]) @ inverse.T / scale
        lo, hi = np.floor(corners.min(axis=0)).astype(int), np.ceil(corners.max(axis=0)).astype(int)
        box = (max(0, int(lo[0])), max(0, int(lo[1])), min(width, int(hi[0])), min(height, int(hi[1])))
        if box[0] < box[2] and box[1] < box[3]:
            boxes.append(box)
    return boxes


def _straight_rows(bgr, max_lines, sparse=False):
    height, width = bgr.shape[:2]
    if min(height, width) < 32:
        return []
    # Work at a bounded resolution; map boxes back to the supplied image.
    scale = min(1.0, 1800 / max(height, width))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    h, w = image.shape[:2]
    cropped_page = w > h*1.2
    hue, saturation, value = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
    mask = ((hue >= 90) & (hue <= 178)
            & (saturation > max(40, float(np.median(saturation)) + 30))
            & (value < 220)).astype(np.uint8)
    if sparse and (not mask.any() or np.median(saturation[mask > 0]) < 80):
        return []  # Faint ink/ruling cannot justify a more permissive retry.
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
              if cv2.contourArea(c) > 30 and 8 < cv2.boundingRect(c)[3] < (min(h*.5, w*.2) if cropped_page else h*.2)
              and cv2.boundingRect(c)[2] < w * .5]
    if len(bodies) < 8:
        return []
    # Detached Vietnamese accents are smaller than letter bodies. A modest
    # upper quantile avoids treating accents as independent writing rows.
    body_height = float(np.percentile(bodies, 60))
    if sparse and _has_stacked_fraction(stats, body_height):
        return []  # A numerator/denominator pair needs one expression region.
    window = max(5, round(body_height * .36)) | 1
    projection = np.convolve(mask.sum(axis=1), np.ones(window) / window, mode="same")
    radius = max(3, round(body_height * .23))
    floor = max(w * (.003 if cropped_page else .008), float(np.percentile(projection, 90)) * (.10 if cropped_page else .15))
    candidates = [y for y in range(radius, h - radius)
                  if projection[y] > floor
                  and projection[y] == np.max(projection[y-radius:y+radius+1])]
    peaks = []
    for y in sorted(candidates, key=lambda y: projection[y], reverse=True):
        if all(abs(y - other) > body_height * (.95 if cropped_page else 1.2) for other in peaks):
            peaks.append(y)
    peaks.sort()
    # Tall glyphs can have two strong ink bands inside the SAME writing row.
    # Require two substantial connected bodies across both peaks; separate
    # fraction tiers and close independent rows have no such shared glyphs.
    parts = stats[keep > 0]
    joined = []
    merged_bodies = {}
    for peak in peaks:
        if joined and peak-joined[-1] <= body_height*1.5:
            shared = parts[(parts[:, 1] <= joined[-1])
                           & (parts[:, 1]+parts[:, 3] > peak)
                           & (parts[:, 2] >= body_height*.3)
                           & (parts[:, 2] <= body_height*4)
                           & (parts[:, 4] >= parts[:, 2]*parts[:, 3]*.12)]
            if len(shared) >= 2:
                previous = joined[-1]
                joined[-1] = max((previous, peak), key=lambda y: projection[y])
                bounds = merged_bodies.pop(previous, (h, 0))
                merged_bodies[joined[-1]] = (min(bounds[0], int(shared[:, 1].min())),
                    max(bounds[1], int((shared[:, 1]+shared[:, 3]).max())))
                continue
        joined.append(peak)
    peaks = joined
    if not 1 <= len(peaks) <= max_lines:
        return []
    gap = float(np.median(np.diff(peaks))) if len(peaks) > 1 else body_height*2
    if not sparse and len(peaks) > 1 and np.max(np.diff(peaks)) > gap * 2.5:
        # ponytail: retry only strong coloured ink; dark/column/fraction layouts
        # need separately verified expression regions before relaxing further.
        return _straight_rows(bgr, max_lines, sparse=True)
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
        row_top, row_bottom = top, bottom
        top = max(top, round(peak-gap * .7))
        bottom = min(bottom, round(peak+gap * .7)+1)
        if peak in merged_bodies:
            first, last = merged_bodies[peak]
            top = max(row_top, min(top, first-4))
            bottom = min(row_bottom, max(bottom, last+5))
        ys, xs = np.nonzero(mask[top:bottom])
        if len(xs) < 30:
            return []
        x1, x2 = max(0, int(xs.min())-6), min(w, int(xs.max())+7)
        y1, y2 = max(top, top+int(ys.min())-4), min(bottom, top+int(ys.max())+5)
        if x2-x1 < body_height * (.8 if cropped_page or sparse else 2):
            return _straight_rows(bgr, max_lines, sparse=True) if not sparse else []
        box = tuple(round(v/scale) for v in (x1, y1, x2, y2))
        # Resizing rounds the working height; the bottom edge can map one pixel
        # past the source. Keep every returned rectangle in source coordinates.
        boxes.append((max(0, box[0]), max(0, box[1]),
                      min(width, box[2]), min(height, box[3])))
        covered += len(xs)
    if covered < np.count_nonzero(mask) * .7:
        return []
    return _attach_stroke_annotations(boxes, labels, stats, keep, body_height, scale)


def _attach_stroke_annotations(boxes, labels, stats, keep, body_height, scale):
    """Keep a detached thin stroke with its sole nearby text row, never erase it.

    Curved arrows can be as tall as letters but have thin column spans. Real
    glyph centers anchor rows; fractions and short words retain their bodies.
    Ambiguous strokes between two rows remain separate candidates for review.
    """
    if len(boxes) < 2:
        return boxes
    primary, strokes = [], []
    for index in range(1, len(stats)):
        x, y, width, height, area = stats[index]
        if not keep[index]:
            continue
        component = labels[y:y+height, x:x+width] == index
        positions = np.arange(height)[:, None]
        occupied = component.any(axis=0)
        spans = (np.max(np.where(component, positions, 0), axis=0)
                 - np.min(np.where(component, positions, height), axis=0) + 1)
        span_ratio = float(np.percentile(spans[occupied], 90) / height)
        center = ((x+width/2)/scale, (y+height/2)/scale)
        if width >= body_height and span_ratio < .4:
            strokes.append(center)
        connected_word = (width >= body_height*2
                          and area >= width*body_height*.2 and span_ratio >= .4)
        if height >= body_height * .25 and (span_ratio >= .65 or connected_word):
            primary.append(center)
    body_counts = [sum(x1 <= x <= x2 and y1 <= y <= y2 for x, y in primary)
                   for x1, y1, x2, y2 in boxes]
    removed = set()
    anchors = boxes
    boxes = list(boxes)
    # ponytail: scan the bounded row list; no diagram classifier or new model.
    for index, (x1, y1, x2, y2) in enumerate(boxes):
        has_stroke = any(x1 <= x <= x2 and y1 <= y <= y2 for x, y in strokes)
        # Connected cursive words can lack isolated glyph centers. Require a
        # thin elongated stroke and a low envelope, including fixed crop padding.
        if (not has_stroke or body_counts[index]
                or y2-y1 > (body_height*1.4+8)/scale
                or x2-x1 < body_height/scale * 2.5):
            continue
        targets = []
        for target, (tx1, ty1, tx2, ty2) in enumerate(anchors):
            if body_counts[target] < 2:
                continue
            overlap = max(0, min(x2, tx2)-max(x1, tx1))/(x2-x1)
            gap = max(0, max(y1, ty1)-min(y2, ty2))
            if overlap >= .8 and gap <= body_height/scale * .7:
                targets.append(target)
        if len(targets) == 1:
            target = targets[0]
            tx1, ty1, tx2, ty2 = boxes[target]
            boxes[target] = (min(x1, tx1), min(y1, ty1),
                             max(x2, tx2), max(y2, ty2))
            removed.add(index)
    return [box for index, box in enumerate(boxes) if index not in removed]


def short_row_candidates(bgr, existing_rows, model_regions):
    """Recover a short missed row only when learned and physical ink agree.

    Keep existing envelopes intact: slanted rows may overlap vertically. A
    model word inside an existing expression is never an additional row.
    """
    if not existing_rows or not model_regions:
        return []
    body = float(np.median([y2-y1 for x1, y1, x2, y2 in model_regions]))
    hue, saturation, value = cv2.split(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))
    mask = ((hue >= 90) & (hue <= 178)
            & (saturation > 65) & (value < 230)).astype(np.uint8)
    added = []
    for box in model_regions:
        x1, y1, x2, y2 = box
        if x2-x1 >= body*2.5 or y2-y1 < body*.5:
            continue
        if any((rx1 <= x1 and ry1 <= y1 and rx2 >= x2 and ry2 >= y2)
               or (max(x1, rx1) < min(x2, rx2)
                   and abs((y1+y2-ry1-ry2)/2) <= body*.6)
               for rx1, ry1, rx2, ry2 in existing_rows + added):
            continue
        _, _, stats, _ = cv2.connectedComponentsWithStats(mask[y1:y2, x1:x2], 8)
        parts = stats[1:]
        bodies = parts[(parts[:, 4] >= 12) & (parts[:, 3] >= body*.3)
                       & (parts[:, 2] >= 2)]
        if len(bodies) < 2:
            continue
        # Include both sides of a nearby fraction bar, not a clipped numerator.
        margin = round(body*2)
        nearby = mask[max(0, y1-margin):min(mask.shape[0], y2+margin),
                      max(0, x1-margin//2):min(mask.shape[1], x2+margin//2)]
        _, _, nearby_stats, _ = cv2.connectedComponentsWithStats(nearby, 8)
        if _has_stacked_fraction(nearby_stats, y2-y1):
            continue
        added.append(_include_detached_marks(bgr, box, existing_rows + added, body))
    return added


def _include_detached_marks(bgr, box, existing_rows, body):
    """Extend an approved short row to faint suffix punctuation or accents.

    Strong bodies still determine eligibility. A low-contrast colon may have
    lower saturation than those bodies; local background contrast locates it.
    Prefix marks beside page edges retain the learned envelope.
    """
    x1, y1, x2, y2 = box
    h, w = bgr.shape[:2]
    margin = round(body * .5)
    left, top = max(0, x1-margin), max(0, y1-margin)
    right, bottom = min(w, x2+margin), min(h, y2+margin)
    hue, sat, value = cv2.split(cv2.cvtColor(bgr[top:bottom, left:right], cv2.COLOR_BGR2HSV))
    mask = ((hue >= 90) & (hue <= 178)
            & (sat > max(30, float(np.median(sat))+15)) & (value < 230)).astype(np.uint8)
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    bounds = list(box)
    # ponytail: scan only the small approved row's neighbourhood, no new model.
    for cx, cy, cw, ch, area in stats[1:]:
        cx, cy = int(cx+left), int(cy+top)
        if area < 8 or max(cw, ch) > body*.35:
            continue
        px, py = cx+cw/2, cy+ch/2
        if x1 <= px <= x2 and y1 <= py <= y2:
            continue
        suffix = y1 <= py <= y2 and x2 < px <= x2+body*.5
        accent = x1 <= px <= x2 and max(y1-py, py-y2, 0) <= body*.3
        if not (suffix or accent):
            continue
        row_distance = abs(py-(y1+y2)/2)
        if any(rx1-body*.5 <= px <= rx2+body*.5
               and abs(py-(ry1+ry2)/2) <= row_distance
               for rx1, ry1, rx2, ry2 in existing_rows):
            continue
        pad = max(4, round(body*.05))
        bounds = [min(bounds[0], max(0, cx-pad)), min(bounds[1], max(0, cy-pad)),
                  max(bounds[2], min(w, cx+int(cw)+pad)),
                  max(bounds[3], min(h, cy+int(ch)+pad))]
    return tuple(bounds)


def coloured_strip_regions(bgr):
    """Recover visible ink in a narrow strip after the learned detector is empty.

    Require multiple substantial bodies, never use ruled paper or isolated
    flecks as evidence. This is a review candidate, not reconstructed writing.
    """
    h, w = bgr.shape[:2]
    if not 8 <= h <= 128 or w < h*5:
        return []
    hue, saturation, value = cv2.split(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))
    mask = ((hue >= 90) & (hue <= 178)
            & (saturation > max(40, float(np.median(saturation))*1.5))
            & (value < 220)).astype(np.uint8)
    rules = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            np.ones((1, max(30, min(w//6, round(h*1.5)))), np.uint8))
    mask[rules > 0] = 0
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    parts = stats[1:]
    bodies = [t for t in parts if t[4] >= 12 and t[2] >= 2 and t[2] <= t[3]*8
              and (t[3] >= h*.45 or (t[3] >= h*.3 and t[2] >= t[3]*1.5
                                     and t[4] >= t[2]*t[3]*.2))
              and not (t[3] >= h*.75 and t[2] <= max(3, t[3]*.12))
              and not (t[2] > t[3]*.6 and t[4] >= t[2]*t[3]*.65)
              and t[0] > w*.03 and t[0]+t[2] < w*.97]
    if len(bodies) < 3:
        return []
    body = float(np.median([t[3] for t in bodies]))
    ordered = sorted(bodies, key=lambda t: t[0])
    if any(right[0]-left[0]-left[2] > body*6 for left, right in zip(ordered, ordered[1:])):
        return []  # Widely scattered texture/columns do not establish one row.
    x1, x2 = min(t[0] for t in bodies), max(t[0]+t[2] for t in bodies)
    top, bottom = min(t[1] for t in bodies), max(t[1]+t[3] for t in bodies)
    # ponytail: inspect bounded connected components; no new model or retry.
    support = [t for t in parts if t[4] >= 8 and t[3] >= 3
               and t[0] >= x1-body*1.5-6 and t[0]+t[2] <= x2+body*1.5+6
               and top-body*.3 <= t[1]+t[3]/2 <= bottom+1]
    x1, x2 = max(0, int(min(t[0] for t in support))-4), min(w, int(max(t[0]+t[2] for t in support))+5)
    y1 = max(0, int(min(t[1] for t in support))-3)
    ink_bottom = int(max(t[1]+t[3] for t in support))
    below = [int(t[1]) for t in parts if t[4] >= 8 and t[3] >= 3
             and t[1] >= ink_bottom and t[0] < x2 and t[0]+t[2] > x1]
    y2 = min(h, ink_bottom+4, min(below) if below else h)
    return [(x1, y1, x2, y2)]


def extend_tiny_row_ends(bgr, boxes, detect):
    """Restore supported horizontal ink of one tiny row, preserving its y bounds."""
    height, width = bgr.shape[:2]
    if not (8 <= height < 32 and width >= height*4 and len(boxes) == 1):
        return boxes, False
    x1, y1, x2, y2 = boxes[0]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if np.median(gray) < 100:
        return boxes, False
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    parts = stats[1:]
    parts = parts[(parts[:, 4] >= 3) & (parts[:, 2] >= 2) & (parts[:, 3] >= 2)
                  & (parts[:, 2] < width*.8)]
    # Mixed ruling/shadow support cannot establish a writing endpoint.
    broad = ((parts[:, 3] >= height*.9) & (parts[:, 2] >= height*2) &
             (parts[:, 4] >= parts[:, 2]*parts[:, 3]*.5))
    ruling = ((parts[:, 3] >= height*.65) & (parts[:, 2] <= max(3, height*.12)))
    if broad.any() and np.count_nonzero(ruling) >= 2:
        return boxes, False
    if len(parts) < 3:
        return boxes, False
    ordered = parts[np.argsort(parts[:, 3])]
    weights = np.cumsum(ordered[:, 4])
    body = float(ordered[np.searchsorted(weights, weights[-1]/2), 3])
    anchors = parts[(parts[:, 4] >= 8) & (parts[:, 3] >= body*.6)]
    if body < max(3, height*.2) or len(anchors) < 3:
        return boxes, False
    xs = anchors[:, 0]+anchors[:, 2]/2
    bottoms = anchors[:, 1]+anchors[:, 3]
    if np.ptp(xs) < width*.4:
        return boxes, False
    slope, offset = np.polyfit(xs, bottoms, 1, w=np.sqrt(anchors[:, 4]))
    near = np.abs(bottoms-(slope*xs+offset)) <= max(2, body*.35)
    if abs(slope) > .15 or anchors[near, 4].sum() < anchors[:, 4].sum()*.95:
        return boxes, False
    if anchors[:, 1].min() < y1 or bottoms.max() > y2:
        return boxes, False
    ink_left = int(anchors[:, 0].min())
    ink_right = int((anchors[:, 0]+anchors[:, 2]).max())
    if x1 <= ink_left+1 and x2 >= ink_right-1:
        return boxes, False
    learned = detect(bgr)
    if not learned or len(learned) != 1:
        return boxes, True
    left, top, right, bottom = learned[0]
    if (left > ink_left+2 or right < ink_right-2 or
            min(y2, bottom)-max(y1, top) < (y2-y1)*.75):
        return boxes, True
    return [[max(0, min(x1, left, ink_left)), y1,
             min(width, max(x2, right, ink_right)), y2]], True


def _has_stacked_fraction(stats, body):
    """Reject sparse retries with ink above AND below a short horizontal bar."""
    parts = stats[1:]
    small = parts[(parts[:, 4] > 8) & (parts[:, 3] > body*.3)
                  & (parts[:, 3] < body*2.5) & (parts[:, 2] < body*3)]
    bars = parts[(parts[:, 2] > body*.35) & (parts[:, 2] < body*3)
                 & (parts[:, 3] < body*.25) & (parts[:, 4] > 8)]
    if not len(small):
        return False
    centers = small[:, 1] + small[:, 3]/2
    for x, y, width, _, _ in bars:
        overlap = (small[:, 0] < x+width) & (small[:, 0]+small[:, 2] > x)
        above = overlap & (y-centers > body*.3) & (y-centers < body)
        below = overlap & (centers-y > body*.3) & (centers-y < body)
        if above.any() and below.any():
            return True
    return False
