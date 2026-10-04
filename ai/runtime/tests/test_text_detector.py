import cv2
import numpy as np
import pytest

from app.recognition import text_detector


def test_fragments_merge_without_joining_rows_or_columns():
    boxes = [(20,20,70,40),(75,21,130,41),(260,20,320,40),
             (20,55,70,75),(80,56,130,76),(180,18,210,115)]
    assert text_detector.merge_fragments(boxes) == [
        (20,20,130,41),(260,20,320,40),(20,55,130,76),(180,18,210,115)]


@pytest.mark.parametrize('ink_scale', [1.0, .5, .25])
def test_model_gap_merges_only_when_source_has_continuing_letter_bodies(ink_scale):
    boxes = [(20,20,90,40), (190,20,260,40), (400,20,470,40),
             (210,25,220,32), (20,70,90,90)]
    mask = np.zeros((100,500), np.uint8)
    for x in range(90,190,15):
        mask[22:38,x:x+9] = 255
    mask = cv2.resize(mask, None, fx=ink_scale, fy=ink_scale,
                      interpolation=cv2.INTER_NEAREST)
    assert text_detector.merge_fragments(boxes, mask, ink_scale) == [
        (20,20,260,40), (400,20,470,40), (20,70,90,90)]


def test_tall_digit_region_splits_rows_but_preserves_a_stacked_fraction():
    image=np.full((300,160,3),248,np.uint8)
    for y in (60,130,200,270):
        cv2.putText(image,'05',(30,y),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    assert len(text_detector.split_stacked_writing(image,(20,20,100,290)))==4
    fraction=np.full((180,160,3),248,np.uint8)
    cv2.putText(fraction,'12',(30,60),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    cv2.line(fraction,(28,75),(76,75),(140,40,20),2)
    cv2.putText(fraction,'34',(30,115),cv2.FONT_HERSHEY_SIMPLEX,1,(140,40,20),2)
    assert text_detector.split_stacked_writing(fraction,(20,20,100,140))==[(20,20,100,140)]


def test_missing_or_invalid_optional_weights_leave_fallback_available(tmp_path,monkeypatch):
    path=tmp_path/'model.onnx'
    monkeypatch.setattr(text_detector,'MODEL_PATH',path)
    image=np.full((100,200,3),255,np.uint8)
    assert text_detector.detect_text_regions(image) is None
    path.write_bytes(b'not a verified artifact')
    assert text_detector.detect_text_regions(image) is None


def test_input_padding_maps_polygons_back_to_exact_source_bounds(tmp_path,monkeypatch):
    path=tmp_path/'model.onnx';path.write_bytes(b'pretend verified weights')
    monkeypatch.setattr(text_detector,'MODEL_PATH',path)
    class Model:
        def setInputSize(self,size):self.size=size
        def detect(self,image):
            assert image.shape[:2]==(self.size[1],self.size[0])
            return np.array([[[0,0],[1280,0],[1280,800],[0,800]]]),np.array([.9])
    monkeypatch.setattr(text_detector,'_load_model',lambda *args:Model())
    assert text_detector.detect_text_regions(np.full((1580,2745,3),255,np.uint8)) == [(0,0,2745,1580)]


def test_portrait_api_uses_regions_and_does_not_cache_a_different_limit(monkeypatch):
    from app.api.generalized_pipeline import run_generalized_line_detection,clear_detection_cache
    monkeypatch.setattr(text_detector,'detect_text_regions',
                        lambda image:[(10,20,90,40),(10,70,90,90)])
    clear_detection_cache()
    image=np.full((300,200,3),245,np.uint8)
    one,diag=run_generalized_line_detection(image,max_lines=1)
    both,second=run_generalized_line_detection(image,max_lines=2)
    assert len(one)==1 and diag['region_limit_exceeded']
    assert len(both)==2 and not second['region_limit_exceeded']
    assert not second['cacheHit'] and not second['geometry_verified']
    cached,third=run_generalized_line_detection(image,max_lines=2)
    assert len(cached)==2 and third['cacheHit']


def test_cache_distinguishes_identical_pixel_bytes_in_different_source_shapes(monkeypatch):
    from app.api import generalized_pipeline as pipeline
    from app.api.ocr import LineBox
    from app.tutoring import rows
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda image:[(10,20,90,40)])
    classical=[LineBox(line_id='line_1',x=30,y=70,width=100,height=20,order=1)]
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:(classical,{},95,None,12))
    monkeypatch.setattr(rows,'handwriting_rows',lambda *args:[])
    pipeline.clear_detection_cache()
    _,portrait=pipeline.run_generalized_line_detection(np.full((300,200,3),245,np.uint8))
    lines,landscape=pipeline.run_generalized_line_detection(np.full((200,300,3),245,np.uint8))
    assert portrait['selected_profile']=='PPOCR_TEXT_REGIONS'
    assert not landscape['cacheHit'] and lines[0].y > 40


def test_sideways_rows_map_back_to_original_pixels(monkeypatch):
    image=np.full((400,300,3),255,np.uint8)
    vertical=[(20,10,40,240),(70,10,90,240),(120,10,140,240)]
    horizontal=[(20,20,370,40),(20,70,370,90),(20,120,370,140)]
    def infer(pixels):
        return vertical if pixels.shape[:2]==(400,300) else horizontal
    monkeypatch.setattr(text_detector,'_infer_regions',infer)
    assert text_detector.detect_text_regions(image)==[
        (20,30,40,380),(70,30,90,380),(120,30,140,380)]


def test_vertical_arithmetic_does_not_rotate_without_strong_text_evidence(monkeypatch):
    image=np.full((400,300,3),255,np.uint8)
    vertical=[(20,10,40,240),(70,10,90,240),(120,10,140,240)]
    def infer(pixels):
        return vertical if pixels.shape[:2]==(400,300) else [(20,20,70,40)]
    monkeypatch.setattr(text_detector,'_infer_regions',infer)
    assert text_detector.detect_text_regions(image)==vertical


def test_tight_crop_padding_is_removed_without_inventing_outside_pixels(monkeypatch):
    image=np.full((23,400,3),245,np.uint8)
    def regions(pixels):
        assert pixels.shape[:2]==(55,432)
        return [(10,10,450,70),(1,1,8,8)]
    monkeypatch.setattr(text_detector,'detect_text_regions',regions)
    assert text_detector.detect_crop_regions(image)==[(0,0,400,23)]


@pytest.mark.parametrize('shape,profile,clipped', [
    ((23,400),'PPOCR_CROP_FALLBACK',True),
    ((33,201),'PPOCR_EMPTY_FALLBACK',True),
    ((191,933),'PPOCR_EMPTY_FALLBACK',False),
])
def test_crop_api_fallback_runs_only_when_established_path_is_empty(monkeypatch,shape,profile,clipped):
    from app.api import generalized_pipeline as pipeline
    from app.tutoring import rows
    from app.api.ocr import LineBox
    image=np.full((*shape,3),245,np.uint8)
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:([],{},0,None,12))
    monkeypatch.setattr(rows,'handwriting_rows',lambda *args:[])
    calls=[]
    def detect(pixels):calls.append(True);return [(20,0,shape[1]-20,shape[0])]
    monkeypatch.setattr(text_detector,'detect_crop_regions',detect)
    pipeline.clear_detection_cache()
    boxes,diag=pipeline.run_generalized_line_detection(image,max_lines=200)
    assert len(boxes)==1 and diag['source_text_may_be_clipped']==clipped
    assert diag['selected_profile']==profile and not diag['geometry_verified']
    assert diag['needs_review']
    established=[LineBox(line_id='line_1',x=20,y=1,width=200,height=20,order=1)]
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:(established,{},95,None,12))
    pipeline.clear_detection_cache();pipeline.run_generalized_line_detection(image)
    assert len(calls)==1
