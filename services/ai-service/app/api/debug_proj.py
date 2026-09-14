import cv2
import sys
import numpy as np
import os
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from app.api.generalized import extract_ink_mask
from app.api.generalized_pipeline import compute_strong_body_bands

def find_fixture_path():
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../scratch/OWNER_GRAPH_HANDWRITING_PHYSICAL_FIXTURE.png")),
        r"C:\Users\Admin\.gemini\antigravity-ide\brain\52d84899-536e-42a4-a843-a17129ed4141\scratch\OWNER_GRAPH_HANDWRITING_PHYSICAL_FIXTURE.png",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def run():
    fixture_path = find_fixture_path()
    bgr = cv2.imread(fixture_path)
    height, width = bgr.shape[:2]
    
    final_mask, chromatic_mask = extract_ink_mask(bgr, height, width)
    
    # Just grab the top half of the image which contains the first two rows
    crop = final_mask[0:int(height/2), :]
    
    ink_per_row = np.sum(crop > 0, axis=1)
    
    raw_cnts, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    heights = [cv2.boundingRect(c)[3] for c in raw_cnts if cv2.contourArea(c) > 5]
    median_h = float(np.median(heights)) if heights else 15.0
    
    smooth_window = max(3, int(median_h * 0.4))
    smoothed_proj = np.convolve(ink_per_row, np.ones(smooth_window) / smooth_window, mode='same')
    
    bands = compute_strong_body_bands(crop, median_h, crop.shape[1], crop.shape[0])
    print(f"Median H: {median_h}")
    print(f"Bands: {bands}")
    print(f"Strong thresh: {max(15.0, crop.shape[1] * 0.02)}")
    
    plt.figure()
    plt.plot(smoothed_proj)
    plt.axhline(y=max(15.0, crop.shape[1] * 0.02), color='r', linestyle='-')
    plt.savefig("debug_proj.png")
    
if __name__ == "__main__":
    run()
