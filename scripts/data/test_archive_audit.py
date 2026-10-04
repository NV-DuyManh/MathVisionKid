"""Offline selection, resume and annotation safety; no model/network needed."""
import hashlib
import io
import json
import zipfile

from PIL import Image
import pytest

import audit_text_regions as audit
import prepare_archive_batch as archive
from review_local_batch import label_flags
from drive_line_batch import write_json, open_ledger


def test_source_label_triage_does_not_confuse_a_math_sentence_with_provider_failure():
    assert label_flags('Không có chữ hoặc biểu thức toán trong ảnh.')==['imported_provider_refusal_or_no_content_claim']
    assert label_flags('Không có học sinh nào vắng mặt.')==[]
    assert label_flags('')==['empty_imported_label']


def test_archive_selects_unlabelled_crops_and_excludes_derived_and_duplicate_pixels(tmp_path):
    buffer=io.BytesIO();Image.new('RGB',(100,50),'red').save(buffer,format='PNG')
    other=io.BytesIO();Image.new('RGB',(100,50),'blue').save(other,format='PNG')
    path=tmp_path/'archives/dataset_clean_full.zip';path.parent.mkdir()
    with zipfile.ZipFile(path,'w') as zipped:
        zipped.writestr('content/dataset_clean/crops/a.png',buffer.getvalue())
        zipped.writestr('content/dataset_clean/crops/b.png',buffer.getvalue())
        zipped.writestr('content/dataset_clean/crops/unlabelled.png',other.getvalue())
        zipped.writestr('content/dataset_clean/debug_vis/a.jpg',buffer.getvalue())
        zipped.writestr('content/dataset_clean/labels.csv','crop_path,filename,label\ncrops/a.png,a.png,original text\n')
    write_json(path.with_suffix('.inventory.json'),{'drive_id':'archive','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    archive.prepare(tmp_path,'sample')
    folder=tmp_path/'sample';items=json.loads((folder/'source_selection.json').read_text())
    assert [x['name'] for x in items]==['a.png','unlabelled.png']
    summary=json.loads((folder/'selection_audit.json').read_text())
    assert len(summary['excluded'])==1 and summary['debug_derivatives_excluded']==1
    assert len(list((folder/'imported_labels').glob('*.json')))==1
    with pytest.raises(ValueError,match='frozen'):archive.prepare(tmp_path,'sample')


def test_local_resume_preserves_accepted_label_and_validates_source_hash(tmp_path,monkeypatch):
    folder=tmp_path/'sample';(folder/'images').mkdir(parents=True)
    path=folder/'images/a.jpg';Image.new('RGB',(100,70),'white').save(path)
    write_json(folder/'source_selection.json',[{'drive_id':'a','name':'a.jpg','source_group':'unit'}])
    reference={'drive_id':'a','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
               'review_status':'count_verified','line_count':0}
    write_json(folder/'labels/a.json',reference)
    calls=[]
    def detect(*args,**kwargs):
        calls.append(kwargs['max_lines']);return [],{'selected_profile':'unit'}
    monkeypatch.setattr(audit,'detect_text_lines',detect)
    audit.run(folder,200,mark_tested=True);audit.run(folder,200,mark_tested=True)
    assert calls==[200]
    assert json.loads((folder/'labels/a.json').read_text())==reference
    assert json.loads((folder/'local_summary.json').read_text())['reused_results']==1
    with open_ledger(tmp_path) as db:assert db.execute('SELECT COUNT(*) FROM images').fetchone()[0]==1
    audit.run(folder,100);assert calls==[200,100]
    write_json(folder/'source_selection.json',[{'drive_id':'a','name':'a.jpg','source_group':'unit','sha256':reference['sha256']}])
    Image.new('RGB',(100,70),'blue').save(path)
    audit.run(folder,100)
    assert json.loads((folder/'local_regions/a.json').read_text())['error_type']=='ValueError'
    assert calls==[200,100]  # Reject changed originals before inference.
    path.write_bytes(b'broken image')
    audit.run(folder,100)
    assert json.loads((folder/'local_summary.json').read_text())['execution_failed']==1
    assert json.loads((folder/'labels/a.json').read_text())==reference
