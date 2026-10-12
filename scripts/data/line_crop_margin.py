"""Offline crop-margin experiment; never certifies text or changes live detection."""
import math


def pad_line_regions(boxes, width, height):
    """Add bounded context without crossing a neighboring region's midpoint.

    Tall/overlapping blocks stay unchanged. This cannot split merged columns,
    recover absent detections or repair ink already missing from the source.
    """
    if (type(width) is not int or type(height) is not int or width <= 0 or height <= 0
            or len(boxes) > 500 or any(len(b) != 4 or any(type(v) is not int for v in b)
            or not (0 <= b[0] < b[2] <= width and 0 <= b[1] < b[3] <= height) for b in boxes)):
        raise ValueError('Expected bounded, valid source-coordinate regions')
    result = []
    # ponytail: <=500 offline regions; an O(n²) neighbor scan needs no spatial index.
    for index, (x1, y1, x2, y2) in enumerate(boxes):
        w, h = x2-x1, y2-y1
        if h > w*.5:
            result.append((x1, y1, x2, y2))
            continue
        dx, dy = max(2, math.ceil(h*.15)), max(2, math.ceil(h*.2))
        left, top, right, bottom = max(0,x1-dx), max(0,y1-dy), min(width,x2+dx), min(height,y2+dy)
        for other, (a, b, c, d) in enumerate(boxes):
            if other == index:
                continue
            xo, yo = min(x2,c)-max(x1,a), min(y2,d)-max(y1,b)
            if xo > 0 and yo > 0:
                left, top, right, bottom = x1, y1, x2, y2
                break  # Ambiguous overlapping regions need geometry review.
            if (xo <= 0 and yo <= 0 and min(right,c) > max(left,a)
                    and min(bottom,d) > max(top,b)):
                left, top, right, bottom = x1, y1, x2, y2
                break  # A diagonal neighboring stroke must not enter the crop.
            if xo > 0:
                if d <= y1: top = max(top, math.ceil((d+y1)/2))
                if b >= y2: bottom = min(bottom, math.floor((y2+b)/2))
            if yo > 0:
                if c <= x1: left = max(left, math.ceil((c+x1)/2))
                if a >= x2: right = min(right, math.floor((x2+a)/2))
        result.append((left, top, right, bottom))
    return result
