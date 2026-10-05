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


def _chalk_board(width=400):
    image=np.full((40,width,3),(55,90,45),np.uint8)
    for x in (30,width//2,width-50):
        cv2.putText(image,'a',(x,29),cv2.FONT_HERSHEY_SIMPLEX,.8,(240,240,240),2)
    return image


def test_chalk_retry_maps_context_back_and_rejects_a_partial_word_row(monkeypatch):
    image=_chalk_board()
    def infer(pixels):
        assert pixels.shape[:2]==(144,864)
        assert np.all(pixels[0]==255)
        # Bright chalk becomes dark; original board becomes a light background.
        assert pixels[80,110,0]<pixels[80,100,0]
        return [(22,30,852,115),(32,32,470,112)]
    monkeypatch.setattr(text_detector,'detect_text_regions',infer)
    assert text_detector._chalk_strip_regions(image)==[(0,0,400,40)]


def test_chalk_retry_maps_each_axis_at_the_actual_resize_ratio(monkeypatch):
    image=_chalk_board(789)
    def infer(pixels):
        assert pixels.shape[:2]==(129,1344)
        return [(32,32,1312,97)]
    monkeypatch.setattr(text_detector,'detect_text_regions',infer)
    assert text_detector._chalk_strip_regions(image)==[(0,0,789,40)]


@pytest.mark.parametrize('crop_entry', [False, True], ids=['helper', 'crop-entry'])
def test_extremely_wide_chalk_strip_clamps_resize_height_and_preserves_bounds(monkeypatch,crop_entry):
    image=np.full((16,50000,3),(55,90,45),np.uint8)
    for x in (1000,25000,48000):
        cv2.rectangle(image,(x,5),(x+6,10),(240,240,240),-1)
    calls=[]
    def infer(pixels):
        calls.append(pixels.shape[:2])
        if pixels.shape[:2]==(48,50032):
            return []
        assert pixels.shape[:2]==(65,1344)
        return [(32,32,1312,33)]
    monkeypatch.setattr(text_detector,'detect_text_regions',infer)
    detect=text_detector.detect_crop_regions if crop_entry else text_detector._chalk_strip_regions
    assert detect(image)==[(0,0,50000,16)]
    assert calls==([(48,50032),(65,1344)] if crop_entry else [(65,1344)])


@pytest.mark.parametrize('image',[
    np.full((40,400,3),245,np.uint8),
    np.full((40,400,3),(55,90,45),np.uint8),
    np.full((200,800,3),(55,90,45),np.uint8),
    np.full((40,100,3),(55,90,45),np.uint8),
])
def test_chalk_retry_does_not_call_model_for_paper_blank_board_or_ineligible_shape(monkeypatch,image):
    def unexpected(pixels):raise AssertionError('No supported chalk row')
    monkeypatch.setattr(text_detector,'detect_text_regions',unexpected)
    assert text_detector._chalk_strip_regions(image)==[]


def test_chalk_retry_rejects_board_grid_and_one_glyph_before_inference(monkeypatch):
    image=np.full((40,400,3),(55,90,45),np.uint8)
    for x in range(0,400,30):
        cv2.line(image,(x,0),(x,39),(240,240,240),1)
    cv2.line(image,(0,20),(399,20),(240,240,240),1)
    def unexpected(pixels):raise AssertionError('Grid is not three glyph bodies')
    monkeypatch.setattr(text_detector,'detect_text_regions',unexpected)
    assert text_detector._chalk_strip_regions(image)==[]
    image=np.full((40,400,3),(55,90,45),np.uint8)
    cv2.putText(image,'a',(30,29),cv2.FONT_HERSHEY_SIMPLEX,.8,(240,240,240),2)
    assert text_detector._chalk_strip_regions(image)==[]


@pytest.mark.parametrize('established,coloured',[
    ([(30,20,400,48)],[]),
    ([],[(10,3,300,35)]),
    (None,[]),
])
def test_chalk_branch_preserves_model_availability_and_existing_crop_regions(monkeypatch,established,coloured):
    from app.tutoring import rows
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda pixels:established)
    monkeypatch.setattr(rows,'coloured_strip_regions',lambda pixels:coloured)
    def unexpected(pixels):raise AssertionError('Established result must be preserved')
    monkeypatch.setattr(text_detector,'_chalk_strip_regions',unexpected)
    expected=None if established is None else ([(14,4,384,32)] if established else coloured)
    assert text_detector.detect_crop_regions(_chalk_board())==expected


def test_chalk_branch_runs_only_after_both_empty_passes_and_preserves_retry_unavailable(monkeypatch):
    from app.tutoring import rows
    monkeypatch.setattr(rows,'coloured_strip_regions',lambda pixels:[])
    calls=[]
    def infer(pixels):
        calls.append(pixels.shape[:2])
        return [] if len(calls)==1 else [(32,32,832,112)]
    monkeypatch.setattr(text_detector,'detect_text_regions',infer)
    assert text_detector.detect_crop_regions(_chalk_board())==[(0,0,400,40)]
    assert calls==[(72,432),(144,864)]
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda pixels:None)
    assert text_detector._chalk_strip_regions(_chalk_board()) is None
