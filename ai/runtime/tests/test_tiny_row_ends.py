"""Physical endpoint checks and the final production-pipeline integration."""
import cv2
import numpy as np
import pytest
from app.tutoring.rows import extend_tiny_row_ends
def printed():
    im=np.full((24,390,3),255,np.uint8)
    cv2.putText(im,'END OF PRINTED ROW 24',(4,19),cv2.FONT_HERSHEY_SIMPLEX,.5,(30,30,30),1,cv2.LINE_AA)
    return im
def test_extends_only_x_preserves_every_other_coordinate():
    im=printed();before=[[70,0,180,24]]
    after,called=extend_tiny_row_ends(im,before,lambda _: [(2,0,389,24)])
    assert called and after==[[2,0,389,24]]
    assert before==[[70,0,180,24]]
@pytest.mark.parametrize('result',[None,[],[(2,0,150,24),(160,0,389,24)]])
def test_no_model_agreement_preserves_rows(result):
    before=[[70,0,180,24]];after,called=extend_tiny_row_ends(printed(),before,lambda _:result)
    assert called and after==before
def test_model_cannot_change_vertical_bounds():
    before=[[70,0,180,24]]
    assert extend_tiny_row_ends(printed(),before,lambda _: [(2,2,389,22)])[0]==[[2,0,389,24]]
@pytest.mark.parametrize('result',[[(60,0,150,24)],[(2,8,389,15)]])
def test_model_must_cover_physical_ink_and_overlap_original_y(result):
    before=[[70,0,180,24]]
    assert extend_tiny_row_ends(printed(),before,lambda _:result)[0]==before
def must_not_call(_):raise AssertionError('unsupported input must not call model')
@pytest.mark.parametrize('before',[[],[[1,0,389,24]],[[2,0,160,24],[170,0,389,24]],[[70,10,180,15]]])
def test_no_unneeded_model_calls(before):
    assert extend_tiny_row_ends(printed(),before,must_not_call)==(before,False)
@pytest.mark.parametrize('shape',[(7,390),(32,390),(1000,1400),(24,30)])
def test_bounded_shape_only(shape):
    before=[[0,0,10,shape[0]]];im=np.full((*shape,3),255,np.uint8)
    assert extend_tiny_row_ends(im,before,must_not_call)==(before,False)
def test_two_physical_rows_never_join_even_with_one_original_box():
    im=np.full((31,390,3),255,np.uint8)
    for y in [12,28]:cv2.putText(im,'ROW TWO ROW TWO',(3,y),cv2.FONT_HERSHEY_SIMPLEX,.35,(20,20,20),1)
    before=[[60,0,180,31]]
    assert extend_tiny_row_ends(im,before,must_not_call)==(before,False)
def test_fraction_numerator_denominator_are_not_flattened():
    im=np.full((31,390,3),255,np.uint8)
    for x in range(20,370,45):
        cv2.putText(im,'3',(x,11),cv2.FONT_HERSHEY_SIMPLEX,.35,(20,20,20),1)
        cv2.line(im,(x-2,15),(x+10,15),(20,20,20),1)
        cv2.putText(im,'5',(x,29),cv2.FONT_HERSHEY_SIMPLEX,.35,(20,20,20),1)
    before=[[100,0,240,31]]
    assert extend_tiny_row_ends(im,before,must_not_call)==(before,False)
@pytest.mark.parametrize('kind',['blank','specks','rule','fabric'])
def test_no_ink_noise_and_patterns(kind):
    im=np.full((24,390,3),255,np.uint8)
    if kind=='specks':
        for x in range(4,380,10):cv2.circle(im,(x,12),1,(20,20,20),-1)
    if kind=='rule':cv2.line(im,(0,12),(389,12),(30,30,30),1)
    if kind=='fabric':
        for y in range(0,24,5):
            for x in range(0,390,5):cv2.rectangle(im,(x,y),(x+2,y+2),(30,30,30),-1)
    before=[[70,0,180,24]]
    assert extend_tiny_row_ends(im,before,must_not_call)==(before,False)
def test_clipped_neighbor_never_changes_existing_vertical_extent_or_count():
    im=printed()
    cv2.putText(im,'CLIPPED NEIGHBOUR',(3,30),cv2.FONT_HERSHEY_SIMPLEX,.5,(30,30,30),1)
    before=[[70,0,180,24]]
    after,called=extend_tiny_row_ends(im,before,lambda _: [(2,0,389,24)])
    assert called and len(after)==1
    assert after[0][1::2]==before[0][1::2]


def shadowed_ruled_crop(mirrored=False):
    image = np.full((24, 298, 3), 220, np.uint8)
    cv2.putText(image, '60 (cm)', (3, 20), cv2.FONT_HERSHEY_SIMPLEX,
                .5, (40, 40, 40), 1, cv2.LINE_AA)
    for x in (104, 135):
        cv2.line(image, (x, 0), (x, 23), (120, 120, 120), 2)
    cv2.rectangle(image, (155, 0), (294, 23), (100, 100, 100), -1)
    before = [[0, 0, 80, 24]]
    if mirrored:
        image = cv2.flip(image, 1)
        before = [[218, 0, 298, 24]]
    return image, before


@pytest.mark.parametrize('mirrored', [False, True])
def test_shadow_and_vertical_ruling_cannot_support_endpoint_growth(mirrored):
    image, before = shadowed_ruled_crop(mirrored)
    assert extend_tiny_row_ends(image, before, must_not_call) == (before, False)


def test_genuine_wide_extent_has_no_growth_cap():
    before = [[0, 0, 30, 24]]
    assert extend_tiny_row_ends(printed(), before,
                              lambda _: [(2, 0, 389, 24)]) == ([[0, 0, 389, 24]], True)


def stub_classical(monkeypatch, candidates):
    from app.api import generalized_pipeline as pipeline
    from app.tutoring import rows
    monkeypatch.setattr(pipeline, '_run_single_profile',
                        lambda *args: (candidates, {'geometry_verified': True}, 95, None, 12))
    monkeypatch.setattr(rows, 'handwriting_rows', lambda *args: [])
    pipeline.clear_detection_cache()
    return pipeline


def test_pipeline_repairs_final_padded_row_and_caches_review_diagnostics(monkeypatch):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    candidate = LineBox(line_id='line_1', x=70, y=0, width=110, height=24, order=1)
    pipeline = stub_classical(monkeypatch, [candidate])
    calls = []
    def detect(image):
        calls.append(image.shape)
        return [(2, 2, 389, 22)]
    monkeypatch.setattr(text_detector, 'detect_crop_regions', detect)
    image = printed()
    lines, diag = pipeline.run_generalized_line_detection(image)
    assert len(lines) == 1
    row = lines[0]
    assert (row.x, row.y, row.width, row.height, row.order, row.line_id) == (2, 0, 387, 24, 1, 'line_1')
    assert diag['tiny_row_ends_recovered'] == 1
    assert diag['needs_review'] and not diag['geometry_verified']
    assert diag['source_text_may_be_clipped']
    cached, second = pipeline.run_generalized_line_detection(image)
    assert cached == lines and second['cacheHit']
    assert second['tiny_row_ends_recovered'] == 1 and len(calls) == 1


@pytest.mark.parametrize('mirrored', [False, True])
def test_pipeline_keeps_existing_row_when_shadow_grid_support_is_ambiguous(monkeypatch, mirrored):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    image, before = shadowed_ruled_crop(mirrored)
    x1, y1, x2, y2 = before[0]
    candidate = LineBox(line_id='line_1', x=x1, y=y1, width=x2-x1, height=y2-y1, order=1)
    pipeline = stub_classical(monkeypatch, [candidate])
    monkeypatch.setattr(text_detector, 'detect_crop_regions', must_not_call)
    lines, diagnostics = pipeline.run_generalized_line_detection(image)
    assert len(lines) == 1 and lines[0].line_id == 'line_1' and lines[0].order == 1
    assert (lines[0].y, lines[0].height) == (0, 24)
    expected_x = 213 if mirrored else 0
    assert (lines[0].x, lines[0].width) == (expected_x, 85)
    assert 'tiny_row_ends_recovered' not in diagnostics


@pytest.mark.parametrize('model_result', [None, [], [(2, 0, 160, 24), (170, 0, 389, 24)]])
def test_pipeline_preserves_padded_result_without_model_agreement(monkeypatch, model_result):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    candidate = LineBox(line_id='line_1', x=70, y=0, width=110, height=24, order=1)
    pipeline = stub_classical(monkeypatch, [candidate])
    monkeypatch.setattr(text_detector, 'detect_crop_regions', lambda _: model_result)
    lines, diag = pipeline.run_generalized_line_detection(printed())
    assert [(r.x, r.y, r.width, r.height) for r in lines] == [(65, 0, 120, 24)]
    assert 'tiny_row_ends_recovered' not in diag and diag['geometry_verified']


def test_pipeline_does_not_join_two_existing_rows(monkeypatch):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    candidates = [LineBox(line_id=f'line_{i+1}', x=70, y=y, width=110, height=6, order=i+1)
                  for i, y in enumerate([2, 17])]
    pipeline = stub_classical(monkeypatch, candidates)
    monkeypatch.setattr(text_detector, 'detect_crop_regions', must_not_call)
    lines, diag = pipeline.run_generalized_line_detection(printed())
    assert len(lines) == 2 and 'tiny_row_ends_recovered' not in diag


def test_pipeline_refuses_two_physical_rows_in_one_classical_region(monkeypatch):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    image = np.full((31, 390, 3), 255, np.uint8)
    for y in [12, 28]:
        cv2.putText(image, 'ROW TWO ROW TWO', (3, y), cv2.FONT_HERSHEY_SIMPLEX, .35, (20,20,20), 1)
    pipeline = stub_classical(monkeypatch, [LineBox(line_id='line_1', x=70, y=0, width=110, height=31, order=1)])
    monkeypatch.setattr(text_detector, 'detect_crop_regions', must_not_call)
    lines, diag = pipeline.run_generalized_line_detection(image)
    assert [(r.x, r.y, r.width, r.height) for r in lines] == [(65, 0, 120, 31)]
    assert 'tiny_row_ends_recovered' not in diag


def test_pipeline_does_not_retry_already_covered_printed_ink(monkeypatch):
    from app.schemas.ocr import LineBox
    from app.recognition import text_detector
    pipeline = stub_classical(monkeypatch, [LineBox(line_id='line_1', x=0, y=0, width=390, height=24, order=1)])
    monkeypatch.setattr(text_detector, 'detect_crop_regions', must_not_call)
    lines, diag = pipeline.run_generalized_line_detection(printed())
    assert [(r.x, r.y, r.width, r.height) for r in lines] == [(0, 0, 390, 24)]
    assert 'tiny_row_ends_recovered' not in diag


def test_empty_pipeline_only_uses_its_existing_empty_fallback(monkeypatch):
    from app.recognition import text_detector
    pipeline = stub_classical(monkeypatch, [])
    calls = []
    def detect(image):
        calls.append(True)
        return []
    monkeypatch.setattr(text_detector, 'detect_crop_regions', detect)
    lines, diag = pipeline.run_generalized_line_detection(np.full((24, 390, 3), 255, np.uint8))
    assert lines == [] and len(calls) == 1
    assert 'tiny_row_ends_recovered' not in diag
