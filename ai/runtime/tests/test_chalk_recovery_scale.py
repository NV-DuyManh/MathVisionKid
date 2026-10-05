"""Bounded chalk recovery keeps supported rows and source geometry intact."""
import cv2
import numpy as np
import pytest
from app.recognition import text_detector as trial

def board(width=400):
    image=np.full((40,width,3),(55,90,45),np.uint8)
    cv2.putText(image,'Luyen chu lam dep',(20,29),cv2.FONT_HERSHEY_SIMPLEX,.65,(240,240,240),2)
    return image

def whole_source(pixels,original_size):
    height,width=original_size;scale_x=(pixels.shape[1]-64)/width;scale_y=(pixels.shape[0]-64)/height
    return [(32,32,32+width*scale_x,32+height*scale_y)]

def test_first_accepted_row_is_preserved_without_a_second_inference(monkeypatch):
    image=board();calls=[]
    def infer(pixels):
        calls.append(pixels.shape[:2]);assert len(calls)==1
        return whole_source(pixels,image.shape[:2])
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    assert trial._chalk_strip_regions(image)==[(0,0,400,40)]
    assert calls==[(144,864)]

def test_empty_first_scale_retries_larger_without_escaping_source(monkeypatch):
    image=board();calls=[]
    def infer(pixels):
        calls.append(pixels.shape[:2])
        return [] if len(calls)==1 else whole_source(pixels,image.shape[:2])
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    assert trial._chalk_strip_regions(image)==[(0,0,400,40)]
    assert calls==[(144,864),(192,1344)]

def test_second_scale_restores_nearby_visible_prefix_and_vertical_ink(monkeypatch):
    image=board();calls=[]
    def infer(pixels):
        calls.append(pixels.shape[:2])
        if len(calls)==1:return []
        sx=(pixels.shape[1]-64)/400;sy=(pixels.shape[0]-64)/40
        return [(32+25*sx,32+12*sy,32+385*sx,32+36*sy)]
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    box=trial._chalk_strip_regions(image)[0]
    foreground=cv2.inRange(image,np.array([240,240,240]),np.array([240,240,240]))
    ys,xs=np.nonzero(foreground)
    assert box[0]<=xs.min() and box[1]<=ys.min()
    assert box[2]>xs.max() and box[3]>ys.max()
    assert 0<=box[0]<box[2]<=400 and 0<=box[1]<box[3]<=40

def test_repeated_long_side_cap_does_not_run_a_duplicate_retry(monkeypatch):
    image=board(800);calls=[]
    def infer(pixels):calls.append(pixels.shape[:2]);return []
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    assert trial._chalk_strip_regions(image)==[]
    assert calls==[(128,1344)]

@pytest.mark.parametrize('unavailable_on',[1,2])
def test_model_unavailability_stays_unavailable(monkeypatch,unavailable_on):
    calls=[]
    def infer(pixels):calls.append(pixels.shape[:2]);return None if len(calls)==unavailable_on else []
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    assert trial._chalk_strip_regions(board()) is None
    assert len(calls)==unavailable_on

def test_second_scale_fragment_does_not_become_a_full_row(monkeypatch):
    calls=[]
    def infer(pixels):calls.append(pixels.shape[:2]);return [(60,60,100,80)]
    monkeypatch.setattr(trial,'detect_text_regions',infer)
    assert trial._chalk_strip_regions(board())==[]
    assert len(calls)==2
