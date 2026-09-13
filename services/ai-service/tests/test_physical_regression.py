import pytest
import cv2
import os
import sys

from app.api.ocr import run_grid_handwriting_detection

def test_physical_graph_handwriting_fixture_detects_four_rows():
    fixture_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\52d84899-536e-42a4-a843-a17129ed4141\scratch\OWNER_GRAPH_HANDWRITING_PHYSICAL_FIXTURE.png"
    if not os.path.exists(fixture_path):
        pytest.skip("Fixture not found locally")
        
    bgr_image = cv2.imread(fixture_path)
    assert bgr_image is not None
    height = bgr_image.shape[0]
    
    lines, diagnostics = run_grid_handwriting_detection(bgr_image)
    
    assert diagnostics["chromatic_cluster_found"] is True
    assert diagnostics["final_boxes"] == 4
    assert len(lines) == 4
    
    # strictly ascending y
    for i in range(1, 4):
        assert lines[i].y > lines[i-1].y
        
    # check no line is a giant box (> 40% height)
    for l in lines:
        assert l.height < height * 0.4
