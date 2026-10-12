"""Guard reviewed rotations, coordinate frames and resumable corpus drafts."""
import hashlib
from pathlib import Path

from PIL import Image
import pytest

import source_orientation as orientation
from recognize_corpus import reusable_draft, source_boxes


def item(angle=270):
    return {'sha256': 'original', 'reviewed_orientation': {
        'clockwise_degrees': angle, 'sha256': 'original', 'status': 'verified',
        'reviewer': 'visual review'}}


@pytest.mark.parametrize('angle,expected', [(0,(1,0)), (90,(1,1)), (180,(1,1)), (270,(0,1))])
def test_rotation_keeps_exact_source_pixels_without_modifying_input(angle, expected):
    image = Image.new('RGB', (3,2), 'white')
    image.putpixel((1,0), (11,22,33))
    before = image.tobytes()
    result = orientation.orient_image(image, item(angle))
    assert image.tobytes() == before
    assert result.getpixel(expected) == (11,22,33)
    assert result.size == ((2,3) if angle in (90,270) else (3,2))


def test_exif_is_applied_once_before_reviewed_rotation():
    image = Image.new('RGB', (3,2), 'white')
    image.putpixel((1,0), (11,22,33))
    image.getexif()[274] = 6
    result = orientation.orient_image(image, item(270))
    assert result.size == (3,2) and result.getpixel((1,0)) == (11,22,33)
    assert image.getexif()[274] == 6


@pytest.mark.parametrize('change', [
    {'clockwise_degrees': 45}, {'clockwise_degrees': True}, {'clockwise_degrees': 90.0},
    {'sha256': 'different'}, {'status': 'predicted'}, {'reviewer': ''}, {'reviewer': None},
])
def test_rejects_guessed_unbound_or_malformed_orientation(change):
    source = item()
    source['reviewed_orientation'].update(change)
    with pytest.raises(ValueError, match='visual review'):
        orientation.orient_image(Image.new('RGB', (3,2)), source)


def test_same_dimensions_cannot_hide_opposite_rotations_or_changed_code():
    source = item()
    image = Image.new('RGB', (20,80))
    region = {'status': 'tested', 'sha256': 'original', 'image_size': [20,80],
              'boxes': [[0,0,20,80]], 'reviewed_orientation': source['reviewed_orientation'],
              'orientation_code_sha256': hashlib.sha256(Path(orientation.__file__).read_bytes()).hexdigest()}
    assert source_boxes(source, image, region)[0] == region['boxes']
    with pytest.raises(ValueError, match='different orientation'):
        source_boxes(item(90), image, region)
    region['orientation_code_sha256'] = 'stale'
    with pytest.raises(ValueError, match='preprocessing changed'):
        source_boxes(source, image, region)


def test_changed_review_invalidates_resumed_text_even_when_box_and_shape_match():
    current = dict(drive_id='a', sha256='original', image_size=[20,80], geometry_kind='page',
                   reviewed_orientation=item()['reviewed_orientation'])
    saved = dict(current, status='recognized', labels_verified=False, reference_label=False,
                 training_eligible=False, cloud_inference_calls=0,
                 lines=[dict(box=[0,0,20,80], text='12', raw_score=.9, score_is_accuracy=False)])
    assert reusable_draft(saved, current, [[0,0,20,80]])
    current['reviewed_orientation'] = item(90)['reviewed_orientation']
    assert not reusable_draft(saved, current, [[0,0,20,80]])


def test_detection_resume_invalidates_opposite_direction_without_writing_previews(tmp_path, monkeypatch):
    import json
    import audit_text_regions as audit
    from app.schemas.ocr import LineBox
    source = tmp_path / 'synthetic.png'
    Image.new('RGB', (80,20), 'white').save(source)
    row = item(90)
    row.update(drive_id='a', name='synthetic.png', mounted_source_path=str(source),
               sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    row['reviewed_orientation']['sha256'] = row['sha256']
    selection = tmp_path / 'source_selection.json'
    selection.write_text(json.dumps([row]))
    calls = []
    def detect(pixels, **kwargs):
        calls.append(pixels.shape)
        return [LineBox(line_id='line_1', x=0,y=0,width=20,height=80,order=1)], {}
    monkeypatch.setattr(audit, 'detect_text_lines', detect)
    audit.run(tmp_path, 200, write_overlays=False, write_drafts=False)
    audit.run(tmp_path, 200, write_overlays=False, write_drafts=False)
    assert len(calls) == 1
    row['reviewed_orientation']['clockwise_degrees'] = 270
    selection.write_text(json.dumps([row]))
    audit.run(tmp_path, 200, write_overlays=False, write_drafts=False)
    assert len(calls) == 2 and calls[0] == calls[1]
    assert not (tmp_path/'local_overlays').exists() and not (tmp_path/'labels').exists()
