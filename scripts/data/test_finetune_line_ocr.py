"""Data and evaluation guards for experiments; no network or model weights required."""
import copy
import hashlib
import json

from PIL import Image
import pytest

from finetune_line_ocr import distance, gate, load_reviewed, metrics, line_tensor, scoped_metrics


def prepare(tmp_path):
    images = tmp_path / 'cohort/images'
    images.mkdir(parents=True)
    rows = []
    for i, split in enumerate(('TRAIN', 'DEV', 'HOLDOUT')):
        file = images / f'{i}.jpg'
        Image.new('RGB', (100, 70), (255, 200 + i, 160)).save(file)
        rows.append({'id': str(i), 'source_batch': 'cohort', 'source_group': f'page:{i}',
                     'source': {'drive_id': str(i), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()},
                     'box': [0, 0, 100, 40], 'text': '98 : 3 = 32 dư 2', 'split': split,
                     'review_status': 'verified', 'reviewer': 'source review',
                     'uncertain': False, 'training_eligible': split == 'TRAIN', 'layout': 'TEXT_LINE'})
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'records': rows}), encoding='utf-8')
    return manifest, rows


def save(manifest, rows):
    manifest.write_text(json.dumps({'records': rows}), encoding='utf-8')


def test_wrong_written_quotient_is_preserved(tmp_path):
    manifest, rows = prepare(tmp_path)
    rows[0]['text'] = '17843 : 3 = 59947 dư 2'
    save(manifest, rows)
    _, samples = load_reviewed(manifest, tmp_path)
    assert samples[0][0]['text'] == '17843 : 3 = 59947 dư 2'


@pytest.mark.parametrize('change', [
    {'review_status': 'needs_review'}, {'uncertain': True}, {'training_eligible': False},
    {'text': '12[?]'}, {'text': '<blank>'}, {'layout': 'LONG_DIVISION'},
    {'box': [0, 0, 101, 40]}, {'source_batch': '../outside'},
])
def test_unfit_labels_are_rejected(tmp_path, change):
    manifest, rows = prepare(tmp_path)
    rows[0].update(change)
    save(manifest, rows)
    with pytest.raises(ValueError):
        load_reviewed(manifest, tmp_path)


def test_raw_hash_changes_are_rejected(tmp_path):
    manifest, _ = prepare(tmp_path)
    Image.new('RGB', (100, 70), 'black').save(tmp_path / 'cohort/images/0.jpg')
    with pytest.raises(ValueError, match='SHA-256'):
        load_reviewed(manifest, tmp_path)


def test_page_split_leakage_with_different_boxes_is_rejected(tmp_path):
    manifest, rows = prepare(tmp_path)
    rows[1]['source'] = copy.deepcopy(rows[0]['source'])
    rows[1]['box'] = [0, 40, 100, 70]
    save(manifest, rows)
    with pytest.raises(ValueError, match='leakage'):
        load_reviewed(manifest, tmp_path)


def test_pixel_aliases_are_rejected_even_when_file_hashes_differ(tmp_path):
    manifest, rows = prepare(tmp_path)
    source = tmp_path / 'cohort/images/0.jpg'
    alias = tmp_path / 'cohort/images/1.jpg'
    # A JPEG trailing comment changes file bytes but not decoded pixels.
    alias.write_bytes(source.read_bytes() + b'alias metadata')
    rows[1]['source']['sha256'] = hashlib.sha256(alias.read_bytes()).hexdigest()
    save(manifest, rows)
    with pytest.raises(ValueError, match='leakage'):
        load_reviewed(manifest, tmp_path)


def test_metric_does_not_solve_or_discard_wrong_digits():
    rows = [{'text': '17843 : 3 = 59947 dư 2'}]
    result = metrics(rows, ['17843 : 3 = 5947 dư 2'])
    assert result['character_errors'] == result['critical_errors'] == 1
    assert result['exact_lines'] == result['critical_exact_lines'] == 0
    assert distance('015', '15') == 1
    with pytest.raises(ValueError):
        metrics(rows, [])


def test_gate_rejects_numeric_regression_despite_lower_cer():
    old = {'cer': 0.04, 'critical_errors': 0}
    new = {'cer': 0.03, 'critical_errors': 1}
    result = gate({'DEV': old, 'HOLDOUT': old}, {'DEV': old, 'HOLDOUT': new})
    assert not result['experiment_passed']
    assert 'HOLDOUT: digit/operator regression' in result['reasons']
    assert result['production_promoted'] is False


def test_experimental_resize_does_not_stretch_short_fields_or_mutate_source():
    image = Image.new('RGB', (60, 80), 'white')
    original = image.tobytes()
    assert tuple(line_tensor(image).shape) == (3, 64, 1024)
    assert tuple(line_tensor(image, True).shape) == (3, 64, 64)
    assert tuple(line_tensor(Image.new('RGB', (300, 80)), True).shape) == (3, 64, 240)
    assert tuple(line_tensor(Image.new('RGB', (3000, 80)), True).shape) == (3, 64, 1024)
    assert image.tobytes() == original and image.size == (60, 80)


def test_gate_keeps_exact_row_regression_visible_even_when_cer_improves():
    old = {'cer': .04, 'critical_errors': 0, 'exact_lines': 9}
    new = {'cer': .03, 'critical_errors': 0, 'exact_lines': 8}
    result = gate({'DEV': old, 'HOLDOUT': old}, {'DEV': new, 'HOLDOUT': new})
    assert not result['experiment_passed']
    assert 'HOLDOUT: exact-line regression' in result['reasons']


@pytest.mark.parametrize('visual,numeric,defer', [(False, False, False), (True, False, False),
                                               (True, True, False), (True, True, True)])
def test_recurrent_experiment_runs_with_mixed_lengths_and_preserves_cnn(tmp_path, visual, numeric, defer):
    """One real backward pass; synthetic pixels verify plumbing, not accuracy."""
    from argparse import Namespace
    import torch
    from app.ocr.model import CRNN
    from finetune_line_ocr import run

    manifest, rows = prepare(tmp_path)
    for row, width in zip(rows, (60, 100, 80)):
        row.update(text='11', box=[0, 0, width, 40])
        if numeric:
            row['content_kind'] = 'UNSIGNED_NUMERIC_FIELD'
    save(manifest, rows)
    model_dir = tmp_path / 'input_model'
    model_dir.mkdir()
    torch.manual_seed(3)
    initial_vocab = ({'<blank>': 0, **{char: i for i, char in enumerate('0123456789., ', 1)}}
                     if numeric else {'<blank>': 0, '1': 1})
    model = CRNN(len(initial_vocab))
    weights = model_dir / 'best_cer.pth'
    torch.save(model.state_dict(), weights)
    vocab = model_dir / 'vocab.json'
    vocab.write_text(json.dumps(initial_vocab), encoding='utf-8')
    original = hashlib.sha256(weights.read_bytes()).hexdigest()
    output = tmp_path / 'candidate'
    run(Namespace(manifest=manifest, data_root=tmp_path, model_dir=model_dir,
                  output=output, epochs=1, batch_size=2, threads=2,
                  learning_rate=.001, seed=3, preserve_aspect_ratio=True, train_recurrent=True,
                  train_last_visual_block=visual, numeric_fields_only=numeric, defer_holdout=defer,
                  augment_train_contrast=defer))
    candidate = torch.load(output / 'candidate.pth', map_location='cpu', weights_only=True)
    assert all(torch.equal(value, candidate[key]) for key, value in model.state_dict().items()
               if key.startswith('cnn.') and (not visual or int(key.split('.')[1]) < 12))
    if visual:
        assert any(not torch.equal(value, candidate[key]) for key, value in model.state_dict().items()
                   if key.startswith('cnn.12.'))
    assert any(not torch.equal(value, candidate[key]) for key, value in model.state_dict().items()
               if key.startswith('rnn.'))
    evidence = json.loads((output / 'evaluation.json').read_text(encoding='utf-8'))
    assert evidence['settings']['train_recurrent'] is True
    assert evidence['settings']['numeric_fields_only'] is numeric
    if defer:
        assert 'HOLDOUT' not in evidence['predictions'] and 'HOLDOUT' not in evidence['baseline']
        assert evidence['quality_gate']['reasons'] == ['HOLDOUT deferred; development measurements only']
        assert evidence['training_views']['original'] == evidence['training_views']['augmented'] == 1
        assert evidence['candidate']['TRAIN']['lines'] == 1  # Augmentation is not another evaluated source.
        from finetune_line_ocr import evaluate_saved
        replay_args = Namespace(evaluate_candidate=output, output=tmp_path/'evaluation', model_dir=model_dir,
                                manifest=manifest, data_root=tmp_path, threads=2)
        replay = evaluate_saved(replay_args)
        assert replay['candidate']['HOLDOUT']['lines'] == 1
        assert replay['candidate']['DEV'] == evidence['candidate']['DEV']
        assert replay['quality_gate']['production_promoted'] is False
        replay_args.output = model_dir/'evaluation'
        with pytest.raises(ValueError, match='outside candidate and production models'):
            evaluate_saved(replay_args)
        assert not replay_args.output.exists()
        replay_args.threads = 0
        with pytest.raises(ValueError, match='bounded evaluation threads'):
            evaluate_saved(replay_args)
        replay_args.threads = 2
        # Tampering must fail before creating another result or running a model.
        (output/'vocab.json').write_text('{}', encoding='utf-8')
        replay_args.output = tmp_path/'invalid_evaluation'
        with pytest.raises(ValueError, match='hash mismatch'):
            evaluate_saved(replay_args)
        assert not replay_args.output.exists()
    assert evidence['quality_gate']['production_promoted'] is False
    assert evidence['trainer_sha256'] == hashlib.sha256((output / 'trainer_snapshot.py').read_bytes()).hexdigest()
    assert (output / 'manifest_snapshot.json').read_bytes() == manifest.read_bytes()
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == original


def test_scope_metrics_do_not_hide_wrong_quotient_behind_good_prose():
    rows = [{'text': '59947', 'math_role': 'quotient'}, {'text': 'Bài giải'}]
    result = scoped_metrics(rows, ['5947', 'Bài giải'])
    assert result['quotient']['critical_errors'] == 1
    assert result['quotient']['exact_lines'] == 0
    assert result['text_line']['exact_lines'] == 1


def test_manifest_changed_mid_training_emits_no_candidate(tmp_path, monkeypatch):
    from argparse import Namespace
    import torch
    from app.ocr.model import CRNN
    from finetune_line_ocr import run
    manifest, rows = prepare(tmp_path)
    for row in rows:
        row['text'] = '11'
    save(manifest, rows)
    model_dir = tmp_path / 'model'
    model_dir.mkdir()
    torch.save(CRNN(2).state_dict(), model_dir / 'best_cer.pth')
    (model_dir / 'vocab.json').write_text(json.dumps({'<blank>': 0, '1': 1}), encoding='utf-8')
    original_step = torch.optim.Adam.step
    def change_manifest(optimizer, *args, **kwargs):
        value = original_step(optimizer, *args, **kwargs)
        manifest.write_text(manifest.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        return value
    monkeypatch.setattr(torch.optim.Adam, 'step', change_manifest)
    output = tmp_path / 'candidate'
    with pytest.raises(ValueError, match='manifest changed during training'):
        run(Namespace(manifest=manifest, data_root=tmp_path, model_dir=model_dir,
                      output=output, epochs=1, batch_size=2, threads=2,
                      learning_rate=.001, seed=4))
    assert not output.exists()
