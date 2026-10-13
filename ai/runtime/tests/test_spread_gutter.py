"""A split-spread retry must preserve ink, coordinates and conservative vetoes."""
import cv2
import numpy as np
import pytest

from app.api import generalized_pipeline as pipeline
from app.recognition import text_detector
from app.schemas.ocr import LineBox
from app.tutoring import rows


def spread():
    image=np.full((800,1200,3),245,np.uint8)
    for x in (40,740):
        for y in (150,300,450):
            cv2.putText(image,'abc def',(x,y),cv2.FONT_HERSHEY_SIMPLEX,1.2,(150,40,40),2)
    return image


def regions(image):
    return [(30,y,min(420,image.shape[1]-20),y+40) for y in (100,250,400)]


def test_empty_gutter_retries_independent_columns_in_source_coordinates():
    image=spread();original=image.copy();calls=[]
    def detector(crop):
        calls.append(crop.shape)
        return regions(crop)
    result=pipeline._recover_spread_regions(image,detector)
    assert len(result)==6 and len(calls)==2
    assert calls[0][1]+calls[1][1]==image.shape[1]
    assert all(not (a<550<c) for a,b,c,d in result)
    assert all(0<=a<c<=1200 and 0<=b<d<=800 for a,b,c,d in result)
    assert np.array_equal(image,original)


@pytest.mark.parametrize('kind',['short','dark','blank','single_side','central_ink','neutral'])
def test_unsupported_images_do_not_trigger_half_detection(kind):
    image=spread()
    if kind=='short':image=image[:350]
    elif kind=='dark':image[:]=20
    elif kind=='blank':image[:]=245
    elif kind=='single_side':image[:,600:]=245
    elif kind=='neutral':image=cv2.cvtColor(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),cv2.COLOR_GRAY2BGR)
    else:
        # A word/fraction body covering the possible fold must veto the cut.
        cv2.putText(image,'abcdefghi',(490,350),cv2.FONT_HERSHEY_SIMPLEX,1.3,(150,40,40),3)
    calls=[]
    result=pipeline._recover_spread_regions(image,lambda crop:calls.append(crop.shape))
    assert result is None and not calls


@pytest.mark.parametrize('kind',['missing','one_side','clipped_left','clipped_right','few_rows'])
def test_learned_evidence_and_boundary_veto_preserve_ambiguous_path(kind):
    calls=[]
    def detector(crop):
        number=len(calls);calls.append(crop.shape)
        if kind=='missing':return None
        if kind=='one_side' and number==1:return []
        if kind=='clipped_left' and number==0:
            return [(30,y,crop.shape[1]-1,y+40) for y in (100,250,400)]
        if kind=='clipped_right' and number==1:
            return [(0,y,420,y+40) for y in (100,250,400)]
        return regions(crop)[:2] if kind=='few_rows' else regions(crop)
    assert pipeline._recover_spread_regions(spread(),detector) is None


@pytest.mark.parametrize('limit',[2,200])
@pytest.mark.parametrize('physical_seed',[True,False])
def test_pipeline_fallback_preserves_limits_cache_and_unverified_status(monkeypatch,limit,physical_seed):
    image=spread()
    physical=[(30,y,1170,y+40) for y in (100,250,400)]
    classical=[LineBox(line_id=f'line_{i+1}',x=30,y=y,width=1140,height=40,order=i+1)
               for i,y in enumerate((100,250,400))]
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:(classical,{},95,None,40))
    monkeypatch.setattr(rows,'handwriting_rows',lambda *args:physical if physical_seed else [])
    monkeypatch.setattr(rows,'short_row_candidates',lambda *args:[])
    monkeypatch.setattr(text_detector,'detect_text_regions',
                        lambda crop:regions(crop) if crop.shape[1]<1200 else [])
    pipeline.clear_detection_cache()
    lines,diag=pipeline.run_generalized_line_detection(image,max_lines=limit)
    assert diag['selected_profile']=='PPOCR_COLUMN_REGIONS'
    assert diag['spread_gutter_retried'] and diag['needs_review']
    assert diag['geometry_verified'] is False and diag['region_limit_exceeded']==(limit<6)
    assert len(lines)==min(6,limit)
    _,cached=pipeline.run_generalized_line_detection(image,max_lines=limit)
    assert cached['cacheHit'] and cached['spread_gutter_retried']
