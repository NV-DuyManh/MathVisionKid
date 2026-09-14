import cv2
import sys
import numpy as np
from app.api.ocr import detect_text_lines
import os
import sys

# Add tests directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from tests.test_physical_regression import find_fixture_path

def run():
    fixture_path = find_fixture_path()
    if not os.path.exists(fixture_path):
        print("Fixture not found!")
        return
        
    bgr = cv2.imread(fixture_path)
    lines, diag = detect_text_lines(bgr)
    
    print(f"Detected {len(lines)} lines")
    print(diag)
    
    for idx, l in enumerate(lines):
        print(f"Line {idx}: {l}")
        cv2.rectangle(bgr, (l.x, l.y), (l.x+l.width, l.y+l.height), (0, 255, 0), 2)
        
    cv2.imwrite("debug_physical.jpg", bgr)

if __name__ == "__main__":
    run()
