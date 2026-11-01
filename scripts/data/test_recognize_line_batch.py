"""Source integrity, resume invalidation and prediction/label separation."""
import hashlib
import json
import pytest
from PIL import Image
import recognize_line_batch as batch
from recognize_line_batch import run


@pytest.fixture
def provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, 'ROOT', tmp_path)
    runtime = tmp_path / 'ai/runtime'
    hashes = {}
    for name in batch.DETECTOR_SOURCES:
        relative = 'models/ocr/text_detection_cn_ppocrv3_2023may.onnx' if name == 'model' else name
        path = runtime / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixed detector fixture')
        hashes[name] = batch.digest(path)
    return hashes


class Provider:
    def __init__(self):
        self.calls = 0

    def recognize_batch_with_confidence(self, images, batch_size):
        self.calls += 1
        return [('12 : 3 = 5', .99) for _ in images]


def test_hash_checked_resume_never_approves_wrong_arithmetic(tmp_path, provenance):
    source = tmp_path / 'original.png'
    Image.new('RGB', (100, 60), 'white').save(source)
    item = {'drive_id': 'a', 'name': '732.png', 'mounted_source_path': str(source),
            'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    (tmp_path / 'source_selection.json').write_text(json.dumps([item]))
    regions = tmp_path / 'local_regions'
    regions.mkdir()
    region = {'status': 'tested', 'sha256': item['sha256'], 'boxes': [[0, 0, 90, 30]],
              'image_size': [100, 60], 'source_hashes': provenance}
    path = regions / 'a.json'
    path.write_text(json.dumps(region))
    labels = tmp_path / 'labels'
    labels.mkdir()
    approved = labels / 'a.json'
    approved.write_text('{"review_status":"verified","text":"original reference"}')
    before = approved.read_bytes()
    provider = Provider()
    hashes = {'model_sha256': 'm', 'vocab_sha256': 'v', 'provider_sha256': 'p',
              'provider': 'private_experimental_crnn_candidate'}
    assert run(tmp_path, provider, hashes)['regions_recognized'] == 1
    record = json.loads((tmp_path / 'crnn_results/a.json').read_text())
    assert record['lines'][0]['text'] == '12 : 3 = 5'
    assert record['provider'] == hashes['provider']
    assert record['training_eligible'] is False and record['labels_verified'] is False
    run(tmp_path, provider, hashes)
    assert provider.calls == 1
    region['boxes'] = [[0, 0, 80, 30]]
    path.write_text(json.dumps(region))
    run(tmp_path, provider, hashes)
    assert provider.calls == 2
    # A different execution device cannot silently reuse a CPU prediction.
    provider.device = 'cuda:0'
    assert run(tmp_path, provider, hashes)['device'] == 'cuda:0'
    assert provider.calls == 3
    assert json.loads((tmp_path / 'crnn_results/a.json').read_text())['device'] == 'cuda:0'
    run(tmp_path, provider, hashes)
    assert provider.calls == 3
    source.write_bytes(b'changed source')
    assert run(tmp_path, provider, hashes)['execution_failed'] == 1
    failed = json.loads((tmp_path / 'crnn_results/a.json').read_text())
    assert failed['provider'] == hashes['provider']
    assert provider.calls == 3 and approved.read_bytes() == before


@pytest.mark.parametrize('kind', ['missing_hashes', 'missing_dependency', 'changed_detector',
                                 'changed_model', 'wrong_shape', 'outside_path', 'invalid_box'])
def test_stale_or_malformed_geometry_never_reaches_recognizer(tmp_path, provenance, kind):
    source = tmp_path / 'original.png'
    Image.new('RGB', (100, 60), 'white').save(source)
    item = {'drive_id': 'a', 'name': 'a.png', 'mounted_source_path': str(source),
            'sha256': batch.digest(source)}
    (tmp_path / 'source_selection.json').write_text(json.dumps([item]))
    region = {'status': 'tested', 'sha256': item['sha256'], 'boxes': [[0, 0, 90, 30]],
              'image_size': [100, 60], 'source_hashes': dict(provenance)}
    if kind == 'missing_hashes':
        del region['source_hashes']
    elif kind == 'missing_dependency':
        del region['source_hashes']['app/tutoring/rows.py']
    elif kind == 'changed_detector':
        (tmp_path / 'ai/runtime/app/tutoring/rows.py').write_bytes(b'new detector')
    elif kind == 'changed_model':
        (tmp_path / 'ai/runtime/models/ocr/text_detection_cn_ppocrv3_2023may.onnx').write_bytes(b'new model')
    elif kind == 'wrong_shape':
        region['image_size'] = [60, 100]
    elif kind == 'outside_path':
        region['source_hashes']['../../original.png'] = item['sha256']
    else:
        region['boxes'] = [None]
    (tmp_path / 'local_regions').mkdir()
    (tmp_path / 'local_regions/a.json').write_text(json.dumps(region))
    provider = Provider()
    result = run(tmp_path, provider, {'model_sha256': 'm'})
    assert result['execution_failed'] == 1 and provider.calls == 0
    assert result['training_eligible'] is False


def test_new_detector_version_invalidates_resume_even_with_same_box(tmp_path, provenance):
    source = tmp_path / 'original.png'
    Image.new('RGB', (100, 60), 'white').save(source)
    item = {'drive_id': 'a', 'name': 'a.png', 'mounted_source_path': str(source),
            'sha256': batch.digest(source)}
    (tmp_path / 'source_selection.json').write_text(json.dumps([item]))
    region = {'status': 'tested', 'sha256': item['sha256'], 'boxes': [[0, 0, 90, 30]],
              'image_size': [100, 60], 'source_hashes': dict(provenance)}
    (tmp_path / 'local_regions').mkdir()
    path = tmp_path / 'local_regions/a.json'
    path.write_text(json.dumps(region))
    provider = Provider()
    hashes = {'model_sha256': 'm'}
    run(tmp_path, provider, hashes)
    code = tmp_path / 'ai/runtime/app/tutoring/rows.py'
    code.write_bytes(b'updated supported detector')
    assert run(tmp_path, provider, hashes)['execution_failed'] == 1
    assert provider.calls == 1
    region['source_hashes']['app/tutoring/rows.py'] = batch.digest(code)
    path.write_text(json.dumps(region))
    run(tmp_path, provider, hashes)
    assert provider.calls == 2


def test_optional_detector_absence_is_pinned_not_a_skipped_model_check(tmp_path, provenance):
    model = tmp_path / 'ai/runtime/models/ocr/text_detection_cn_ppocrv3_2023may.onnx'
    model.unlink()
    provenance['model'] = 'absent'
    batch.validate_region_provenance({'source_hashes': provenance})
    model.write_bytes(b'a newly installed detector')
    with pytest.raises(ValueError):
        batch.validate_region_provenance({'source_hashes': provenance})
