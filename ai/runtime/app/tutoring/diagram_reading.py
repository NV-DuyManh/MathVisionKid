"""Conservative pixel evidence for clearly partitioned, shaded school diagrams."""
import asyncio
import re

import cv2
import numpy as np


_SHADING_WORDS = frozenset(('hình vẽ gồm là một hai ba bốn năm sáu bảy tám thứ nhất đầu tiên cuối '
    'tròn ngũ giác đều mỗi được chia thành làm phần bằng nhau tô màu không chưa hoàn toàn cả '
    'và có còn lại tất tam trong đó cam').split())


def _counts_only(text):
    return (not re.search(r'[/=×÷+%<>]', text)
            and set(re.findall(r'[^\W\d_]+', text.lower())) <= _SHADING_WORDS)


def _replace_description(source, match, description):
    replacement = '['+description+']'
    remaining = source[:match.start()]+source[match.end():]
    choices = list(re.finditer(r'(?<!\w)([A-D])[.)]\s*', remaining))
    if [choice[1] for choice in choices] == list('ABCD') and match.start() >= choices[-1].end():
        # A provider may append a picture description after D. It belongs to
        # the shared stem, never to the final answer choice.
        split = choices[0].start()
        return remaining[:split].rstrip()+'\n'+replacement+'\n'+remaining[split:].strip()
    return source[:match.start()]+replacement+source[match.end():]


async def clarify_diagrams(questions, pixels, timeout_seconds):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + min(4., timeout_seconds)
    for clarify in (clarify_circles, clarify_pentagons):
        remaining = deadline-loop.time()
        if remaining <= 0:
            break
        questions = await clarify(questions, pixels, remaining)
    return questions


def _circle_row(bgr):
    scale = min(1., 1400 / max(bgr.shape[:2]))
    image = cv2.resize(bgr, None, fx=scale, fy=scale) if scale < 1 else bgr
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 140)
    distance = cv2.distanceTransform(255-edges, cv2.DIST_L2, 3)
    found = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 45,
        param1=120, param2=45, minRadius=20, maxRadius=100)
    circles = []
    angles = np.linspace(0, 2*np.pi, 360, endpoint=False)
    for x, y, radius in ([] if found is None else found[0]):
        if min(x, y, image.shape[1]-1-x, image.shape[0]-1-y) < radius*1.3:
            continue  # Leave enough room to sample the surrounding paper.
        xs = np.rint(x + radius*np.cos(angles)).astype(int)
        ys = np.rint(y + radius*np.sin(angles)).astype(int)
        if np.mean(distance[ys, xs] < 2.8) >= .92:
            circles.append((float(x), float(y), float(radius)))
    if not 2 <= len(circles) <= 8:
        return None
    circles.sort()
    radii = [circle[2] for circle in circles]
    radius = float(np.median(radii))
    if (max(radii)-min(radii) > radius*.18
            or np.ptp([circle[1] for circle in circles]) > radius*.2
            or any(b[0]-a[0] < radius*2.2 for a, b in zip(circles, circles[1:]))):
        return None
    return gray, circles


def circle_facts(pixels):
    located = _circle_row(pixels)
    if located is None:
        return None
    gray, circles = located
    angles = np.linspace(0, 2*np.pi, 360, endpoint=False)
    facts = []
    for x, y, radius in circles:
        def samples(rays, radii):
            xs = np.rint(x + np.cos(rays[:, None])*radii).astype(int)
            ys = np.rint(y + np.sin(rays[:, None])*radii).astype(int)
            return gray[ys, xs].astype(float)
        paper = samples(angles, np.linspace(1.12, 1.25, 4)*radius)
        background = float(np.median(paper))
        if background < 225 or np.percentile(paper, 90)-np.percentile(paper, 10) > 12:
            return None
        boundary = np.mean(samples(angles, np.linspace(.3, .82, 24)*radius) < 100, axis=1) > .55
        starts = np.flatnonzero(boundary & ~np.roll(boundary, 1))
        ends = np.flatnonzero(boundary & ~np.roll(boundary, -1))
        if not 2 <= len(starts) <= 12:
            return None
        peaks = []
        for start in starts:
            end = next((int(value) for value in ends if value >= start), int(ends[0])+360)
            if end-start > 18:
                return None
            peaks.append(((int(start)+end)/2) % 360)
        peaks.sort()
        gaps = np.diff([*peaks, peaks[0]+360])
        if np.max(np.abs(gaps-360/len(peaks))) > min(9, 360/len(peaks)*.15):
            return None  # Unequal/skewed drawing cannot establish equal sectors.
        shaded = 0
        for start, gap in zip(peaks, gaps):
            rays = np.deg2rad(np.linspace(start+gap*.3, start+gap*.7, 15))
            interior = samples(rays, np.linspace(.35, .75, 16)*radius)
            difference = background-interior
            if np.mean(difference > 14) >= .8:
                shaded += 1
            elif np.mean(np.abs(difference) < 8) < .8:
                return None  # Faint/overwritten fill remains unknown.
        facts.append((len(peaks), shaded, len(peaks)-shaded))
    return facts


def pentagon_facts(pixels):
    """Measure one aligned row of regular pentagons with five visible radii.

    Reject skew, missing dividers and ambiguous fill. Printed answers and the
    model's suggested shape/sector counts are never inputs to this measurement.
    """
    scale = min(1., 1400 / max(pixels.shape[:2]))
    image = cv2.resize(pixels, None, fx=scale, fy=scale) if scale < 1 else pixels
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contours, _ = cv2.findContours(cv2.Canny(gray, 40, 100), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    shapes = []
    for contour in contours:
        vertices = cv2.approxPolyDP(contour, .025*cv2.arcLength(contour, True), True)
        if len(vertices) != 5 or not cv2.isContourConvex(vertices) or cv2.contourArea(vertices) < 1000:
            continue
        points = vertices[:, 0, :].astype(float)
        center = points.mean(axis=0)
        radii = np.linalg.norm(points-center, axis=1)
        radius = float(np.median(radii))
        if not 20 < radius < 130 or np.ptp(radii) > radius*.18:
            continue
        angles = np.sort(np.mod(np.arctan2(points[:, 1]-center[1], points[:, 0]-center[0]), 2*np.pi))
        gaps = np.diff(np.r_[angles, angles[0]+2*np.pi])
        if np.max(np.abs(gaps-2*np.pi/5)) > .16:
            continue
        if min(*center, image.shape[1]-1-center[0], image.shape[0]-1-center[1]) < radius*1.3:
            continue
        if any(np.linalg.norm(center-item[0]) < radius*.4 for item in shapes):
            continue  # Inner/outer edges of the same outline are one shape.
        shapes.append((center, radius, angles))
    if not 2 <= len(shapes) <= 8:
        return None
    shapes.sort(key=lambda item: item[0][0])
    radius = float(np.median([item[1] for item in shapes]))
    if (np.ptp([item[1] for item in shapes]) > radius*.18
            or np.ptp([item[0][1] for item in shapes]) > radius*.2
            or any(b[0][0]-a[0][0] < radius*2 for a, b in zip(shapes, shapes[1:]))):
        return None
    facts = []
    for center, radius, angles in shapes:
        def samples(rays, radii):
            xs = np.rint(center[0]+np.cos(np.asarray(rays)[:, None])*radii).astype(int)
            ys = np.rint(center[1]+np.sin(np.asarray(rays)[:, None])*radii).astype(int)
            return gray[ys, xs].astype(float)
        paper = samples(np.linspace(0, 2*np.pi, 360, endpoint=False), np.linspace(1.12, 1.25, 4)*radius)
        background = float(np.median(paper))
        if background < 225 or np.percentile(paper, 90)-np.percentile(paper, 10) > 12:
            return None
        for angle in angles:
            radii = np.linspace(.3, .7, 20)*radius
            line = samples(np.linspace(angle-.12, angle+.12, 9), radii).min(axis=0)
            neighbours = samples([angle-.24, angle+.24], radii)
            # A divider is either a dark stroke or a clear filled/white edge.
            supported = (neighbours.max(axis=0)-line > 15) | (np.ptp(neighbours, axis=0) > 30)
            if np.mean(supported) < .65:
                return None
        shaded = 0
        for start, gap in zip(angles, np.diff(np.r_[angles, angles[0]+2*np.pi])):
            interior = samples(np.linspace(start+gap*.3, start+gap*.7, 15), np.linspace(.3, .65, 16)*radius)
            difference = background-interior
            if np.mean(difference > 14) >= .8:
                shaded += 1
            elif np.mean(np.abs(difference) < 4) < .8:
                return None
        facts.append((5, shaded, 5-shaded))
    return facts


async def clarify_pentagons(questions, pixels, timeout_seconds):
    # Replace only counts/shading prose. Dimensions, vertex labels or other
    # visible annotations must not disappear when a shape description is refined.
    candidates = [(index, match) for index, question in enumerate(questions)
        for match in re.finditer(r'\[[^\[\]]+\]|^Hình[^\n]+', question.problemText, re.M)
        if re.search(r'\bngũ giác\b', match[0], re.I) and re.search(r'\btô màu\b', match[0], re.I)
        and _counts_only(match[0])
        and not re.search(r'\bmàu\s+(?:cam|xanh|đỏ|vàng|tím|nâu|đen|trắng|hồng)\b',
                          question.problemText[:match.start()]+question.problemText[match.end():], re.I)]
    if len(candidates) != 1:
        return questions
    try:
        facts = await asyncio.wait_for(asyncio.to_thread(pentagon_facts, pixels), min(2., timeout_seconds))
    except TimeoutError:
        return questions
    if facts is None:
        return questions
    index, match = candidates[0]
    question = questions[index]
    description = ' '.join(f'Hình {i}: hình ngũ giác chia {total} phần bằng nhau, '
        f'{shaded} phần tô màu, {plain} phần không tô màu.'
        for i, (total, shaded, plain) in enumerate(facts, 1))
    text = _replace_description(question.problemText, match, description)
    if len(text) > 4000:
        return questions
    result = list(questions)
    result[index] = question.model_copy(update={'problemText': text, 'uncertain': True})
    return result


async def clarify_circles(questions, pixels, timeout_seconds):
    candidates = [(index, match) for index, question in enumerate(questions)
        for match in re.finditer(r'\[[^\[\]]+\]', question.problemText)
        if _counts_only(match[0]) and (re.search(r'\bhình tròn\b', match[0], re.I) or (
            re.search(r'\bhình tròn\b', question.problemText[:match.start()], re.I)
            and re.match(r'\[\s*Hình\s+1\s*:', match[0], re.I)
            and re.search(r'\bphần tô màu\b', match[0], re.I)))]
    if len(candidates) != 1:
        return questions
    try:
        facts = await asyncio.wait_for(asyncio.to_thread(circle_facts, pixels), min(2., timeout_seconds))
    except TimeoutError:
        return questions
    if facts is None:
        return questions
    index, match = candidates[0]
    stated_count = re.search(r'\b(\d+)\s+hình tròn\b', match[0], re.I)
    numbered = [int(value) for value in re.findall(r'\bhình\s+(\d+)\s*:', match[0], re.I)]
    count = int(stated_count[1]) if stated_count else len(numbered)
    if count != len(facts) or (numbered and numbered != list(range(1, count+1))):
        return questions  # Incomplete or misordered figures cannot be matched to the source.
    question = questions[index]
    description = ' '.join(f'Hình {i}: chia {total} phần bằng nhau, {shaded} phần tô màu, {plain} phần không tô màu.'
        for i, (total, shaded, plain) in enumerate(facts, 1))
    text = _replace_description(question.problemText, match, description)
    if len(text) > 4000:
        return questions
    result = list(questions)
    # The bounded visual measurement does not certify the rest of the OCR.
    # Keep the photograph, printed choices and explicit pupil confirmation.
    result[index] = question.model_copy(update={'problemText': text, 'uncertain': True})
    return result
