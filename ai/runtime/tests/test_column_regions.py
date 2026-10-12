"""A book spread must not become one transcript spanning unrelated columns."""
import numpy as np
import pytest

from app.api import generalized_pipeline as pipeline
from app.schemas.ocr import LineBox
from app.recognition import text_detector
from app.tutoring import rows


LEFT = [(30,y,450,y+40) for y in (80,200,320)]
RIGHT = [(700,y,1130,y+40) for y in (80,200,320)]


@pytest.mark.parametrize('regions,expected', [
    (LEFT+RIGHT,True), (LEFT,False), (LEFT[:2]+RIGHT[:2],False),
    (LEFT+[(470,y,900,y+40) for y in (80,200,320)],False),
    (LEFT+[(700,y,1130,y+40) for y in (140,260,380)],True),
    (LEFT+[(700,y,1130,y+40) for y in (600,720,840)],False),
    ([(30,y,450,y+5) for y in (80,200,320)]+RIGHT,False),
])
def test_column_evidence_requires_repeated_matching_rows_and_a_real_gap(regions,expected):
    assert pipeline._separate_column_evidence(regions,1200) is expected


@pytest.mark.parametrize('limit',[2,200])
def test_spread_uses_independent_columns_and_preserves_limit_cache_and_review(monkeypatch,limit):
    image = np.full((800,1200,3),245,np.uint8)
    physical = [(30,y,1130,y+40) for y in (80,200,320)]
    classical = [LineBox(line_id=f'line_{i}',x=a,y=b,width=c-a,height=d-b,order=i)
                 for i,(a,b,c,d) in enumerate(physical,1)]
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:(classical,{},95,None,40))
    monkeypatch.setattr(rows,'handwriting_rows',lambda *args:physical)
    monkeypatch.setattr(rows,'short_row_candidates',lambda *args:[])
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda *args:LEFT+RIGHT)
    pipeline.clear_detection_cache()
    lines,diag=pipeline.run_generalized_line_detection(image,max_lines=limit)
    assert diag['selected_profile']=='PPOCR_COLUMN_REGIONS'
    assert diag['separate_columns_recovered'] and diag['needs_review']
    assert diag['geometry_verified'] is False
    assert len(lines)==min(6,limit) and diag['region_limit_exceeded']==(limit<6)
    assert all(b.width<600 and 0<=b.x<b.x+b.width<=1200 for b in lines)
    _,cached=pipeline.run_generalized_line_detection(image,max_lines=limit)
    assert cached['cacheHit'] and cached['separate_columns_recovered']


def test_single_column_and_short_exercise_keep_established_rows(monkeypatch):
    physical=[(30,y,1130,y+40) for y in (80,200,320)]
    classical=[LineBox(line_id='line_1',x=30,y=80,width=1100,height=40,order=1)]
    monkeypatch.setattr(pipeline,'_run_single_profile',lambda *args:(classical,{},95,None,40))
    monkeypatch.setattr(rows,'handwriting_rows',lambda *args:physical)
    monkeypatch.setattr(rows,'short_row_candidates',lambda *args:[])
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda *args:LEFT)
    pipeline.clear_detection_cache()
    _,diag=pipeline.run_generalized_line_detection(np.full((800,1200,3),245,np.uint8))
    assert not diag.get('separate_columns_recovered')
    # Even strong columns do not replace geometry on a cropped exercise.
    monkeypatch.setattr(text_detector,'detect_text_regions',lambda *args:LEFT+RIGHT)
    pipeline.clear_detection_cache()
    _,diag=pipeline.run_generalized_line_detection(np.full((400,1200,3),245,np.uint8))
    assert not diag.get('separate_columns_recovered')


def test_column_support_survives_repaired_arithmetic_strokes():
    # Real-photo regression: complete arithmetic strokes remove the tiny false
    # regions that accidentally supplied baseline pairs in the earlier detector.
    left=[(220,142,693,216),(382,212,720,260),(513,262,885,346),
          (534,499,997,575),(403,576,997,655),(166,760,557,828),(444,1222,816,1276)]
    right=[(1192,672,1597,717),(1174,843,1453,888),(1156,953,1428,1028),
           (1163,1070,2031,1135),(1166,1185,2048,1266),(1171,1297,2048,1397)]
    assert pipeline._separate_column_evidence(left+right,2048)
