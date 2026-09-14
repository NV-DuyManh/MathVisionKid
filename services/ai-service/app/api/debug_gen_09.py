import sys
import os
import cv2
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from app.api.generalized_pipeline import run_generalized_line_detection

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
img = create_mock_row(img, y=200, h=30)
cv2.line(img, (400, 100), (400, 230), (0,0,0), 3)

lines, diag = run_generalized_line_detection(img)
print('Lines:', len(lines))
for l in lines:
    print('  ', l)
