import sys
import os
import cv2
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from app.api.generalized_pipeline import run_generalized_line_detection, compute_strong_body_bands
from app.api.generalized import extract_ink_mask

def create_blank_bgr(w=800, h=600):
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    return img

def create_mock_row(img, y, h, w_offset=50, w_len=700, ink_color=(0,0,0)):
    for x in range(w_offset, w_offset + w_len, 25):
        cv2.circle(img, (x + np.random.randint(-5, 5), y + h//2 + np.random.randint(-3, 3)), np.random.randint(2, 6), ink_color, -1)
        cv2.line(img, (x, y + h//4), (x+10, y + h - h//4), ink_color, 2)
    return img

img = create_blank_bgr()
img = create_mock_row(img, y=100, h=30)
img = create_mock_row(img, y=150, h=30)
cv2.line(img, (400, 100), (400, 180), (0,0,0), 3)

lines, diag = run_generalized_line_detection(img)
print('Lines:', len(lines))
for l in lines:
    print('  ', l)

# Also debug the crop directly
height, width = img.shape[:2]
final_mask, _ = extract_ink_mask(img, height, width)
raw_cnts, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
median_h = float(np.median(heights)) if heights else 15.0

print(f"Median H: {median_h}")
for multiplier in [0.015, 0.03, 0.05, 0.08, 0.12, 0.15]:
    bands = compute_strong_body_bands(final_mask, median_h, width, height, thresh_multiplier=multiplier)
    print(f"Mult {multiplier}: {bands}")
