"""Conservative pixel evidence for a row of clearly partitioned, shaded circles."""
import asyncio
import re

import cv2
import numpy as np


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


async def clarify_circles(questions, pixels, timeout_seconds):
    candidates = [(index, match) for index, question in enumerate(questions)
        for match in re.finditer(r'\[[^\[\]]*hình tròn[^\[\]]*\]', question.problemText, re.I)]
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
    count = int(stated_count[1]) if stated_count else max(numbered, default=0)
    if count != len(facts):
        return questions  # A missed/faint circle must not disappear from the task.
    question = questions[index]
    description = ' '.join(f'Hình {i}: chia {total} phần bằng nhau, {shaded} phần tô màu, {plain} phần không tô màu.'
        for i, (total, shaded, plain) in enumerate(facts, 1))
    text = question.problemText[:match.start()] + '[' + description + ']' + question.problemText[match.end():]
    if len(text) > 4000:
        return questions
    result = list(questions)
    # The bounded visual measurement does not certify the rest of the OCR.
    # Keep the photograph, printed choices and explicit pupil confirmation.
    result[index] = question.model_copy(update={'problemText': text, 'uncertain': True})
    return result
