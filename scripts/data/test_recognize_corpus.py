"""Protect resumability and source geometry at the corpus boundary."""
import sqlite3
import copy
import pytest
from PIL import Image

from recognize_corpus import open_results, reusable_draft, save_record, source_boxes


def test_resume_rejects_different_frozen_inputs(tmp_path):
    path = tmp_path / 'drafts.sqlite'
    db = open_results(path, 'frozen-model-and-source')
    save_record(db, {'drive_id': 'a', 'status': 'recognized', 'labels_verified': False})
    db.commit()
    db.close()
    with pytest.raises(ValueError, match='Resume inputs changed'):
        open_results(path, 'changed-model')
    db = open_results(path, 'frozen-model-and-source')
    assert db.execute('SELECT COUNT(*) FROM records').fetchone()[0] == 1
    db.close()


def test_supplied_crops_do_not_claim_verified_geometry():
    boxes, kind = source_boxes({'source_type': 'provided_line_crop'}, Image.new('RGB', (80, 20)), None)
    assert boxes == [[0, 0, 80, 20]] and kind.endswith('unverified_geometry')


def test_existing_drafts_without_provenance_cannot_be_adopted(tmp_path):
    path = tmp_path / 'unidentified.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE records (source_id TEXT PRIMARY KEY, status TEXT, payload TEXT)')
        db.execute("INSERT INTO records VALUES ('a', 'recognized', '{}')")
    with pytest.raises(ValueError, match='Resume inputs changed'):
        open_results(path, 'new-fingerprint')


def test_page_requires_matching_oriented_pixels_and_bounded_boxes():
    image = Image.new('RGB', (80, 20))
    item = {'sha256': 'source'}
    region = {'status': 'tested', 'sha256': 'source', 'image_size': [80, 20], 'boxes': [[0, 0, 80, 20]]}
    assert source_boxes(item, image, region)[0] == region['boxes']
    for changed in (dict(region, sha256='changed'), dict(region, image_size=[20, 80]),
                    dict(region, boxes=[[0, 0, 81, 20]]), dict(region, boxes=[[0., 0, 80, 20]])):
        with pytest.raises(ValueError):
            source_boxes(item, image, changed)


@pytest.mark.parametrize('corruption', ['reference', 'verified', 'training', 'nan', 'score_claim',
                                      'pixels', 'text', 'float_box', 'status'])
def test_resume_rejects_approved_or_corrupt_drafts(corruption):
    current = dict(drive_id='a', sha256='frozen', image_size=[80,20], geometry_kind='crop_unverified_geometry')
    saved = dict(current, status='recognized', labels_verified=False, reference_label=False,
                 training_eligible=False, cloud_inference_calls=0,
                 lines=[dict(box=[0,0,80,20], text='8 ÷ 2 = 4', raw_score=.8, score_is_accuracy=False)])
    assert reusable_draft(saved,current,[[0,0,80,20]])
    bad = copy.deepcopy(saved)
    if corruption == 'reference': bad['reference_label'] = True
    elif corruption == 'verified': bad['labels_verified'] = True
    elif corruption == 'training': bad['training_eligible'] = True
    elif corruption == 'nan': bad['lines'][0]['raw_score'] = float('nan')
    elif corruption == 'score_claim': bad['lines'][0]['score_is_accuracy'] = True
    elif corruption == 'pixels': bad['image_size'] = [20,80]
    elif corruption == 'text': bad['lines'][0]['text'] = None
    elif corruption == 'float_box': bad['lines'][0]['box'][0] = 0.0
    elif corruption == 'status': bad['status'] = 'execution_failed'
    assert not reusable_draft(bad,current,[[0,0,80,20]])


def test_valid_empty_region_draft_can_resume_without_becoming_a_label():
    current = dict(drive_id='a', sha256='frozen', image_size=[80,20], geometry_kind='page_unverified_geometry')
    saved = dict(current, status='no_detected_regions', labels_verified=False, reference_label=False,
                 training_eligible=False, cloud_inference_calls=0, lines=[])
    assert reusable_draft(saved,current,[])
    assert not reusable_draft(None,current,[])
