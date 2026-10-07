"""Optional, pinned local text regions. These are geometry, not verified OCR."""
from functools import lru_cache
import hashlib
import logging
from pathlib import Path
import threading

import cv2
import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[2] / "models/ocr/text_detection_cn_ppocrv3_2023may.onnx"
MODEL_SHA256 = "03f550c6b406fda8bf54bd8327815f6c7e2edd98cea02348c93d879254366587"
_lock = threading.Lock()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model(path, modified, size):
    # A replaced artifact is rechecked; never load arbitrary downloaded weights.
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != MODEL_SHA256:
        raise ValueError("Local text detector checksum mismatch")
    model = cv2.dnn_TextDetectionModel_DB(cv2.dnn.readNet(path))
    model.setInputMean((123.675, 116.28, 103.53))
    model.setInputScale(1.0 / 255.0 / np.array([.229, .224, .225]))
    model.setBinaryThreshold(.3)
    model.setPolygonThreshold(.5)
    model.setMaxCandidates(500)
    model.setUnclipRatio(1.5)
    return model


def merge_fragments(boxes, ink_mask=None, ink_scale=1.0):
    """Join neighbouring words on the same baseline, keeping distant columns."""
    if not boxes:
        return []
    body = float(np.median([y2-y1 for x1,y1,x2,y2 in boxes]))
    rows = []

    def written_gap(left, right, top, bottom):
        if ink_mask is None or left >= right or top >= bottom:
            return False
        left, top = int(left*ink_scale), int(top*ink_scale)
        right, bottom = int(np.ceil(right*ink_scale)), int(np.ceil(bottom*ink_scale))
        columns = np.any(ink_mask[top:bottom, left:right] > 0, axis=0)
        if not columns.size:
            return False
        if columns.mean() < .3:
            return False
        positions = np.r_[-1, np.flatnonzero(columns), len(columns)]
        return np.max(np.diff(positions) - 1) <= max(6, body * .8) * ink_scale

    # ponytail: bounded O(n²) scan over <=500 text candidates; no spatial index.
    for box in sorted(boxes, key=lambda b: ((b[1]+b[3])/2, b[0])):
        x1,y1,x2,y2 = box
        h = y2-y1
        matches = []
        for index, other in enumerate(rows):
            ox1,oy1,ox2,oy2 = other
            oh = oy2-oy1
            overlap = min(y2,oy2)-max(y1,oy1)
            gap = max(0, max(x1,ox1)-min(x2,ox2))
            # Tall vertical arithmetic is not a row to join with prose beside it.
            if (max(h,oh) <= min(h,oh)*2.0
                    and not (h > (x2-x1)*2 and oh > (ox2-ox1)*2)
                    and overlap >= min(h,oh)*.65
                    and abs((y1+y2-oy1-oy2)/2) <= max(h,oh)*.4
                    and (gap <= body*1.5 or written_gap(
                        min(x2,ox2),max(x1,ox1),max(y1,oy1),min(y2,oy2)))):
                matches.append(index)
        if matches:
            parts = [box] + [rows[i] for i in matches]
            merged = (min(b[0] for b in parts), min(b[1] for b in parts),
                      max(b[2] for b in parts), max(b[3] for b in parts))
            rows = [b for i,b in enumerate(rows) if i not in matches]
            rows.append(merged)
        else:
            rows.append(tuple(box))
    # A small duplicate/satellite already enclosed by a complete row is not an
    # additional line. Do not discard fragments extending outside that row.
    rows = list(dict.fromkeys(rows))
    ordered = sorted((box for box in rows if not any(
        other != box and other[0] <= box[0] and other[1] <= box[1]
        and other[2] >= box[2] and other[3] >= box[3] for other in rows)),
        key=lambda b: ((b[1]+b[3])/2,b[0]))
    bands = []
    for box in ordered:
        if (bands and box[3]-box[1] <= body*2
                and all(b[3]-b[1] <= body*2 for b in bands[-1])
                and abs((box[1]+box[3])/2 -
                        np.median([(b[1]+b[3])/2 for b in bands[-1]])) <= body*.4):
            bands[-1].append(box)
        else:
            bands.append([box])
    return [box for band in bands for box in sorted(band,key=lambda b:b[0])]


def split_stacked_writing(bgr,box):
    """Split a tall text region only at blank gaps in strong coloured ink.

    A fraction bar protects the whole expression. Faint/neutral text or touching
    rows retain the learned region instead of guessing boundaries.
    """
    from app.tutoring.rows import _has_stacked_fraction
    x1,y1,x2,y2=box
    crop=bgr[y1:y2,x1:x2]
    hue,saturation,value=cv2.split(cv2.cvtColor(crop,cv2.COLOR_BGR2HSV))
    mask=(((hue>=90)&(hue<=178) | (hue<=12)) &
          (saturation>65)&(value<230)).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
    parts=stats[1:]
    bodies=parts[(parts[:,4]>=12)&(parts[:,3]>=5)&(parts[:,3]<(y2-y1)*.5)]
    if len(bodies)<3:
        return [box]
    body=float(np.percentile(bodies[:,3],65))
    if y2-y1<body*2.5 or _has_stacked_fraction(stats,body):
        return [box]
    keep=np.zeros(count,np.uint8)
    keep[1:]=((parts[:,4]>=8)&(parts[:,3]>=3))
    mask=keep[labels]
    occupied=mask.sum(axis=1)>=max(2,(x2-x1)*.025)
    runs=[]
    for y in np.flatnonzero(occupied):
        if runs and y-runs[-1][1]<=max(4,body*.4):
            runs[-1][1]=int(y)+1
        else:
            runs.append([int(y),int(y)+1])
    if len(runs)<2 or any(bottom-top<body*.45 for top,bottom in runs):
        return [box]
    # Retain the original horizontal extent and bound added whitespace by gaps.
    return [(x1,max(y1,y1+top-3),x2,min(y2,y1+bottom+3)) for top,bottom in runs]


def _infer_regions(bgr):
    if bgr is None or bgr.size == 0:
        return []
    height,width = bgr.shape[:2]
    if min(height,width) < 32:
        return []
    if not MODEL_PATH.is_file():
        return None
    scale = min(1.0, 1280/max(height,width))
    nw,nh = max(1,round(width*scale)), max(1,round(height*scale))
    size = (int(np.ceil(nw/32))*32,int(np.ceil(nh/32))*32)
    image = np.full((size[1],size[0],3),255,np.uint8)
    image[:nh,:nw] = cv2.resize(bgr,(nw,nh))
    try:
        stat = MODEL_PATH.stat()
        # ponytail: one locked OpenCV net for CPU requests; worker-local pools
        # are appropriate only if measured request throughput requires them.
        with _lock:
            model = _load_model(str(MODEL_PATH),stat.st_mtime_ns,stat.st_size)
            model.setInputSize(size)
            polygons,scores = model.detect(image)
    except (OSError,ValueError,cv2.error):
        logger.warning("Local text detector unavailable; using established segmentation")
        return None
    boxes = []
    for polygon,score in zip(polygons,scores):
        if not np.isfinite(score) or not np.isfinite(polygon).all():
            continue
        points = np.clip(np.asarray(polygon,dtype=float)/[nw/width,nh/height],
                         [0,0],[width,height])
        lo = np.floor(points.min(axis=0)).astype(int)
        hi = np.ceil(points.max(axis=0)).astype(int)
        if np.all(hi > lo):
            boxes.append(tuple(map(int,(*lo,*hi))))
    return boxes


def recover_glyph_rows(bgr, regions):
    """Recover spaced notebook glyphs from ink, retaining unrelated model text.

    This is a bounded portrait-only retry for repeated isolated letter bodies.
    Prose, fractions and ambiguous stacked bands keep their learned geometry.
    It supplies candidate boxes, never a transcription or verified annotation.
    """
    from app.tutoring.rows import handwriting_rows, _has_stacked_fraction
    height, width = bgr.shape[:2]
    if height <= width * 1.15:
        return regions
    scale = min(1., 1280 / max(height, width))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    hue, saturation, value = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))
    if np.median(value) < 100 or np.mean(saturation > 90) > .3:
        return regions
    mask = ((hue >= 90) & (hue <= 178) &
            (saturation > max(25, np.median(saturation) + 15)) & (value < 230)).astype(np.uint8)
    rules = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            np.ones((max(30, image.shape[0] // 8), 1), np.uint8))
    rules |= cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                             np.ones((1, max(30, image.shape[1] // 4)), np.uint8))
    mask[rules > 0] = 0
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    parts = stats[1:]
    eligible = parts[(parts[:, 4] >= 25) & (parts[:, 3] >= 7) &
                     (parts[:, 3] < image.shape[0] * .12)]
    narrow = eligible[eligible[:, 2] < image.shape[1] * .12]
    if len(narrow) < 12:
        return regions
    body = float(np.percentile(narrow[:, 3], 65))
    if _has_stacked_fraction(stats, body):
        return regions
    compact = eligible[(eligible[:, 3] >= body * .5) & (eligible[:, 3] <= body * 2.5) &
                       (eligible[:, 2] <= body * 2) & (eligible[:, 2] >= body * .15) &
                       (eligible[:, 4] < eligible[:, 2] * eligible[:, 3] * .7)]
    if len(compact) < 12 or compact[:, 4].sum() < eligible[:, 4].sum() * .5:
        return regions
    cx = (compact[:, 0] + compact[:, 2] / 2) / scale
    cy = (compact[:, 1] + compact[:, 3] / 2) / scale
    bands = []
    for x1, y1, x2, y2 in handwriting_rows(bgr, max_lines=200):
        candidates = compact[(cx >= x1 - body / scale * .5) &
                             (cx <= x2 + body / scale * .5) & (cy >= y1) & (cy <= y2)]
        joined = []
        for part in sorted(candidates, key=lambda p: p[0]):
            if joined and part[0] - (joined[-1][0] + joined[-1][2]) < body * .4:
                previous = joined[-1]
                lo = np.minimum(part[:2], previous[:2])
                hi = np.maximum(part[:2] + part[2:4], previous[:2] + previous[2:4])
                joined[-1] = np.r_[lo, hi - lo, part[4] + previous[4]]
            else:
                joined.append(part)
        if len(joined) < 4:
            continue
        centers = np.array([p[0] + p[2] / 2 for p in joined])
        gaps = np.diff(centers)
        if (np.min(gaps) < body * .9 or np.max(gaps) > np.median(gaps) * 1.7 or
                np.ptp(centers) < image.shape[1] * .35 or
                any(p[2] > body * 2 or p[3] > body * 1.8 for p in joined)):
            continue
        slope, offset = np.polyfit(centers, [p[1] + p[3] / 2 for p in joined], 1)
        if (abs(slope) > .2 or max(abs(p[1] + p[3] / 2 -
                (slope * (p[0] + p[2] / 2) + offset)) for p in joined) > body * .6 or
                max(p[1] + p[3] for p in joined) - min(p[1] for p in joined) > body * 2.5):
            continue
        bands.append(joined)
    if len(bands) < 4:
        return regions
    rows = []
    baselines = np.array([np.median([p[1] + p[3] / 2 for p in band]) for band in bands])
    for index, band in enumerate(bands):
        x1, y1 = min(p[0] for p in band), min(p[1] for p in band)
        x2, y2 = max(p[0] + p[2] for p in band), max(p[1] + p[3] for p in band)
        centers = np.array([p[0] + p[2] / 2 for p in band])
        step = np.median(np.diff(centers))
        slope, offset = np.polyfit(centers, [p[1] + p[3] / 2 for p in band], 1)
        px, py = parts[:, 0] + parts[:, 2] / 2, parts[:, 1] + parts[:, 3] / 2
        possible = ((parts[:, 4] >= 8) & (parts[:, 3] >= body * .3) &
                    (parts[:, 3] <= body * 1.8) & (parts[:, 2] <= body * 2))
        slots = np.r_[centers[0] - step, centers, centers[-1] + step]
        extra = parts[possible &
                      (np.min(abs(px[:, None] - slots), axis=1) <= step * .18) &
                      (abs(py - (slope * px + offset)) <= body * .6)]
        fit_x = list(centers)
        fit_y = [p[1] + p[3] / 2 for p in band]
        growth_slope, growth_offset = slope, offset
        # Follow actual consecutive glyphs beyond a clipped physical band.
        # Stop at the first empty/ambiguous cell; never bridge a missing glyph
        # to another column. Refitting follows modest page curvature.
        for direction in (-1, 1):
            anchor = centers[0] if direction < 0 else centers[-1]
            for _ in range(int(image.shape[1] / step) + 1):
                target = anchor + direction * step
                candidates = parts[possible & (abs(px - target) <= step * .18) &
                                   (abs(py - (growth_slope * px + growth_offset)) <= body * .6)]
                if not len(candidates):
                    break
                lo = candidates[:, :2].min(axis=0)
                hi = (candidates[:, :2] + candidates[:, 2:4]).max(axis=0)
                cw, ch = hi - lo
                if cw > body * 2 or not body * .5 <= ch <= body * 1.8:
                    break
                center = (lo + hi) / 2
                next_x, next_y = fit_x + [center[0]], fit_y + [center[1]]
                next_slope, next_offset = np.polyfit(next_x, next_y, 1)
                if (abs(next_slope) > .2 or np.max(abs(np.array(next_y) -
                        (next_slope * np.array(next_x) + next_offset))) > body * .6):
                    break
                extra = np.concatenate((extra, candidates))
                fit_x, fit_y = next_x, next_y
                growth_slope, growth_offset = next_slope, next_offset
                anchor = center[0]
        if len(extra):
            x1, y1 = min(x1, int(extra[:, 0].min())), min(y1, int(extra[:, 1].min()))
            x2 = max(x2, int((extra[:, 0] + extra[:, 2]).max()))
            y2 = max(y2, int((extra[:, 1] + extra[:, 3]).max()))
        # Detached accents belong to the nearest supported row, above/within its
        # local sloping body. A printed footer below it must not expand the crop.
        marks = parts[(parts[:, 4] >= 8) & (parts[:, 3] >= 2) &
                      (parts[:, 3] <= body * .5) & (parts[:, 2] <= body * .7) &
                      (parts[:, 0] >= x1 - body * .3) &
                      (parts[:, 0] + parts[:, 2] <= x2 + body * .3)]
        mx, my = marks[:, 0] + marks[:, 2] / 2, marks[:, 1] + marks[:, 3] / 2
        owners = np.argmin(abs(my[:, None] - baselines), axis=1)
        near = marks[(abs(my - baselines[index]) <= body * 1.5) &
                     (my <= slope * mx + offset + body * .6) & (owners == index)]
        if len(near):
            x1, y1 = min(x1, int(near[:, 0].min())), min(y1, int(near[:, 1].min()))
            x2 = max(x2, int((near[:, 0] + near[:, 2]).max()))
            y2 = max(y2, int((near[:, 1] + near[:, 3]).max()))
        rows.append((max(0, int((x1 - 4) / scale)), max(0, int((y1 - 4) / scale)),
                     min(width, int(np.ceil((x2 + 4) / scale))),
                     min(height, int(np.ceil((y2 + 4) / scale)))))
    if (any(a[3] > b[1] for a, b in zip(rows, rows[1:])) or
            any((box[3] - box[1]) * scale >= body * 1.8 and
                len(split_stacked_writing(bgr, box)) > 1 for box in rows)):
        return regions
    supported = np.zeros_like(mask)
    for x1, y1, x2, y2 in rows:
        supported[int(y1 * scale):int(np.ceil(y2 * scale)),
                  int(x1 * scale):int(np.ceil(x2 * scale))] = 1
    keep = []
    for box in regions:
        x1, y1, x2, y2 = [round(v * scale) for v in box]
        ink = mask[y1:y2, x1:x2]
        if (ink * supported[y1:y2, x1:x2]).sum() < max(1, ink.sum() * .8):
            keep.append(box)
    return sorted(keep + rows, key=lambda b: ((b[1] + b[3]) / 2, b[0]))


def detect_text_regions(bgr):
    """Return candidates in original pixels, or None when model unavailable.

    No network/download takes place in a student request. Sideways writing is
    considered only when the first pass contains predominantly vertical regions.
    Returned coordinates always refer to the supplied image.
    """
    boxes = _infer_regions(bgr)
    if not boxes:
        return boxes
    height,width = bgr.shape[:2]
    tall = sum(y2-y1 > (x2-x1)*2 for x1,y1,x2,y2 in boxes)
    rotated = False
    if tall >= max(3,len(boxes)*.25):
        upright = cv2.rotate(bgr,cv2.ROTATE_90_CLOCKWISE)
        alternative = _infer_regions(upright)
        def horizontal_evidence(regions, image_width):
            return sum(x2-x1 for x1,y1,x2,y2 in regions
                       if x2-x1 >= max((y2-y1)*3,image_width*.16))
        if (alternative and horizontal_evidence(alternative,height) >
                max(width*2,horizontal_evidence(boxes,width)*1.5)):
            bgr,boxes,rotated = upright,alternative,True
    parts = [part for box in boxes for part in split_stacked_writing(bgr,box)]
    from app.api.generalized import extract_ink_mask
    # Gap evidence does not need full camera resolution. Bound preprocessing to
    # the model's working scale; returned geometry remains in original pixels.
    ink_scale = min(1.0, 1280/max(bgr.shape[:2]))
    ink_image = cv2.resize(bgr, None, fx=ink_scale, fy=ink_scale) if ink_scale < 1 else bgr
    ink_mask, _ = extract_ink_mask(ink_image, *ink_image.shape[:2])
    rows = merge_fragments(parts, ink_mask, ink_scale)
    if rotated:
        return [(y1,height-x2,y2,height-x1) for x1,y1,x2,y2 in rows]
    return recover_glyph_rows(bgr, rows)


def detect_crop_regions(bgr):
    """Provide model context for a tight strip, never reconstruct missing ink."""
    height,width=bgr.shape[:2]
    if min(height,width)<8:
        return []
    border=16
    padded=cv2.copyMakeBorder(bgr,border,border,border,border,
                             cv2.BORDER_CONSTANT,value=(255,255,255))
    regions=detect_text_regions(padded)
    if regions is None:
        return None
    clipped=[]
    for x1,y1,x2,y2 in regions:
        x1,y1=max(0,x1-border),max(0,y1-border)
        x2,y2=min(width,x2-border),min(height,y2-border)
        if x1<x2 and y1<y2:
            clipped.append((x1,y1,x2,y2))
    if clipped:
        return clipped
    from app.tutoring.rows import coloured_strip_regions
    coloured=coloured_strip_regions(bgr)
    return coloured if coloured else _chalk_strip_regions(bgr)


def _chalk_strip_regions(bgr):
    """Retry an empty dark-board strip only where a whole bright row is supported."""
    height,width=bgr.shape[:2]
    if not (8<=height<=128 and width>=height*4):
        return []
    hue,saturation,value=cv2.split(cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV))
    background_hue,background_sat,background_value=[
        float(np.median(channel)) for channel in (hue,saturation,value)]
    if not (35<=background_hue<=125 and background_sat>40 and background_value<155):
        return []
    bright=((saturation<85)&(value>background_value+35)).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(bright,8)
    parts=stats[1:]
    substantial=((parts[:,3]>=height*.2)&(parts[:,3]<=height*.9)
                 &(parts[:,2]<=height*3)&(parts[:,4]>=8))
    bodies=parts[substantial]
    if len(bodies)<3:
        return []
    # Inversion exposes light chalk to the same pinned model. No equalization
    # or fabricated full-source box: dark grids otherwise produce false text.
    gray=255-cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
    first_scale=min(2.,1280/max(height,width))
    centers=bodies[:,1]+bodies[:,3]/2
    # Preserve the first supported result; a bounded larger view may expose
    # faint chalk to the same model without relaxing its ink requirements.
    for scale in dict.fromkeys((first_scale,min(4.,1280/max(height,width)))):
        size=(max(1,round(width*scale)),max(1,round(height*scale)))
        resized=cv2.resize(gray,size)
        scale_x,scale_y=resized.shape[1]/width,resized.shape[0]/height
        border=32
        padded=cv2.copyMakeBorder(resized,border,border,border,border,
                                 cv2.BORDER_CONSTANT,value=255)
        candidates=detect_text_regions(cv2.cvtColor(padded,cv2.COLOR_GRAY2BGR))
        if candidates is None:
            return None
        accepted=[]
        for x1,y1,x2,y2 in candidates:
            x1,y1=max(0,int(np.floor((x1-border)/scale_x))),max(0,int(np.floor((y1-border)/scale_y)))
            x2,y2=min(width,int(np.ceil((x2-border)/scale_x))),min(height,int(np.ceil((y2-border)/scale_y)))
            if x2-x1<width*.45 or y2-y1<height*.3:
                continue
            in_row=(centers>=y1-height*.1)&(centers<=y2+height*.1)
            if np.count_nonzero(in_row)<3:
                continue
            keep=np.zeros(count,np.uint8)
            keep[np.flatnonzero(substantial)+1]=in_row
            supported=keep[labels]
            if supported[y1:y2,x1:x2].sum()/max(1,supported.sum())>=.9:
                if scale>first_scale:
                    nearby=bodies[in_row & (bodies[:,0]+bodies[:,2]>=x1-height*.5)
                                  & (bodies[:,0]<=x2+height*.5)]
                    x1=min(x1,int(nearby[:,0].min()));y1=min(y1,int(nearby[:,1].min()))
                    x2=max(x2,int((nearby[:,0]+nearby[:,2]).max()));y2=max(y2,int((nearby[:,1]+nearby[:,3]).max()))
                accepted.append((x1,y1,x2,y2))
        if accepted:
            return accepted
    return []
