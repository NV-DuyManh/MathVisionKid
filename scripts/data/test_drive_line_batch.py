"""Private-data ledger and label validation; no Drive/network credentials needed."""
import asyncio
import importlib.util
import json
from pathlib import Path

from PIL import Image
import pytest
from unittest.mock import AsyncMock

spec = importlib.util.spec_from_file_location('drive_batch', Path(__file__).with_name('drive_line_batch.py'))
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def prepare(tmp_path, duplicate=False):
    folder = tmp_path/'sample'
    images = folder/'images'
    images.mkdir(parents=True)
    Image.new('RGB', (100, 70), 'white').save(images/'a.jpg')
    records = [{'drive_id':'a', 'name':'a.jpg', 'source_group':'unit'}]
    if duplicate:
        (images/'b.jpg').write_bytes((images/'a.jpg').read_bytes())
        records.append({'drive_id':'b', 'name':'b.jpg', 'source_group':'unit'})
    batch.write_json(folder/'source_selection.json', records)
    source = tmp_path/'detector.py'
    source.write_text('def handwriting_rows(image):\n    return [(5, 10, 90, 30)]\n', encoding='utf-8')
    return folder, source


def test_resume_reloads_reviewed_label_without_redetecting(tmp_path):
    folder, source = prepare(tmp_path)
    first = batch.run_batch(tmp_path, 'sample', source)
    assert first['tested'] == 1 and first['reference_count_pages'] == 0
    label = json.loads((folder/'labels/a.json').read_text())
    assert label['review_status'] == 'needs_review' and label['line_count'] is None
    label.update(review_status='count_verified', line_count=1)
    batch.write_json(folder/'labels/a.json', label)
    second = batch.run_batch(tmp_path, 'sample', source)
    assert second['reference_count_pages'] == second['exact_count_pages'] == 1
    with batch.open_ledger(tmp_path) as db:
        assert batch.select_unseen([{'drive_id':'a'}, {'drive_id':'c'}, {'drive_id':'c'}], db, 10) == [{'drive_id':'c'}]
        assert db.execute('SELECT label_status FROM images').fetchone()[0] == 'count_verified'


def test_aliases_are_marked_and_not_double_counted(tmp_path):
    folder, source = prepare(tmp_path, duplicate=True)
    result = batch.run_batch(tmp_path, 'sample', source)
    assert result['tested'] == 2 and result['unique_pixels'] == 1
    assert json.loads((folder/'results/b.json').read_text())['duplicate_of'] == 'a'


def test_corrupted_image_is_not_marked_tested(tmp_path):
    folder, source = prepare(tmp_path)
    (folder/'images/a.jpg').write_bytes(b'not an image')
    result = batch.run_batch(tmp_path, 'sample', source)
    assert result['failed'] == 1
    with batch.open_ledger(tmp_path) as db:
        assert db.execute('SELECT COUNT(*) FROM images').fetchone()[0] == 0


@pytest.mark.parametrize('changes', [
    {'sha256':'different'}, {'line_count':True},
    {'review_status':'geometry_verified','lines':[{'box':[0,0,101,20]}]},
    {'review_status':'verified','lines':[{'box':[0,0,90,20], 'text':'?', 'uncertain':True}]},
])
def test_invalid_ground_truth_is_rejected(tmp_path, changes):
    p = tmp_path/'label.json'
    label = {'sha256':'known', 'review_status':'count_verified', 'line_count':1}
    label.update(changes)
    batch.write_json(p, label)
    with pytest.raises(ValueError):
        batch.reviewed_label(p, 'known', (100,70))


def test_original_change_invalidates_cached_measurement(tmp_path):
    folder, source = prepare(tmp_path)
    batch.run_batch(tmp_path, 'sample', source)
    Image.new('RGB', (100,70), 'red').save(folder/'images/a.jpg')
    # The existing annotation must be rejected rather than applied to new pixels.
    result = batch.run_batch(tmp_path, 'sample', source)
    assert result['failed'] == 1
    assert 'different image' in json.loads((folder/'results/a.json').read_text())['error']


def test_cloud_resume_does_not_call_provider_twice_or_make_labels(tmp_path, monkeypatch):
    from app.tutoring import notebook
    folder, _ = prepare(tmp_path)
    reading = notebook.NotebookRead(kind='WORK', lines=[notebook.NotebookLine(text='1 + 2 = 3')])
    call = AsyncMock(return_value=reading)
    monkeypatch.setattr(notebook, 'inspect_notebook', call)
    assert asyncio.run(batch.run_cloud_batch(tmp_path, 'sample'))['read'] == 1
    assert asyncio.run(batch.run_cloud_batch(tmp_path, 'sample'))['read'] == 1
    assert call.await_count == 1 and not (folder/'labels').exists()


def test_cloud_unavailability_stops_without_sweeping_images(tmp_path, monkeypatch):
    from app.tutoring import notebook
    from app.tutoring.service import TutorUnavailable
    folder, _ = prepare(tmp_path, duplicate=True)
    call = AsyncMock(side_effect=TutorUnavailable())
    monkeypatch.setattr(notebook, 'inspect_notebook', call)
    summary = asyncio.run(batch.run_cloud_batch(tmp_path, 'sample'))
    assert summary['read'] == 0 and summary['pending'] == 2 and call.await_count == 1
    assert not (folder/'cloud_results/b.json').exists()
