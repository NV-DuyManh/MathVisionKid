"""Data and evaluation guards for experiments; no network or model weights required."""
import copy
import hashlib
import json

from PIL import Image
import pytest

from finetune_line_ocr import checkpoint_key, distance, expand_head, gate, load_reviewed, metrics, line_tensor, scoped_metrics


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


def test_metric_counts_numerals_hallucinated_in_prose_without_reference_digits():
    rows = [{'text': 'cá mà'}, {'text': '8 : 2 = 4'}]
    result = metrics(rows, ['cá m0', '8 : 2 = 4'])
    assert result['critical_errors'] == result['unexpected_critical_errors'] == 1
    assert result['unexpected_critical_lines'] == 1
    assert result['critical_lines'] == result['critical_exact_lines'] == 1
    assert result['critical_chars'] == 5
    assert result['critical_cer'] == .2
    plain = metrics(rows[:1], ['cá m0'])
    assert plain['critical_errors'] == 1 and plain['critical_cer'] is None


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


def test_gate_rejects_prose_regression_hidden_by_aggregate_math_gain():
    old = {'cer': .04, 'critical_errors': 0, 'exact_lines': 9}
    new = {'cer': .02, 'critical_errors': 0, 'exact_lines': 10}
    scope_old = {'cer': .01, 'critical_errors': 0, 'exact_lines': 5}
    scope_new = {'cer': .03, 'critical_errors': 1, 'exact_lines': 4}
    scopes = {'HOLDOUT': {'baseline': {'prose': scope_old}, 'candidate': {'prose': scope_new}}}
    result = gate({'DEV': old, 'HOLDOUT': old}, {'DEV': new, 'HOLDOUT': new}, scopes)
    assert not result['experiment_passed']
    assert 'HOLDOUT/prose: character regression' in result['reasons']
    assert 'HOLDOUT/prose: digit/operator regression' in result['reasons']
    assert 'HOLDOUT/prose: exact-line regression' in result['reasons']
    scopes['HOLDOUT']['candidate']['prose'] = scope_old
    assert gate({'DEV': old, 'HOLDOUT': old}, {'DEV': new, 'HOLDOUT': new}, scopes)['experiment_passed']


def test_checkpoint_selection_preserves_prose_before_aggregate_math_gain():
    baseline = {'prose': {'cer': .04, 'critical_errors': 1, 'exact_lines': 3}}
    worse = {'prose': {'cer': .04, 'critical_errors': 1, 'exact_lines': 1}}
    safe_dev = {'cer': .07, 'critical_errors': 15, 'exact_lines': 20}
    unsafe_dev = {'cer': .02, 'critical_errors': 5, 'exact_lines': 30}
    assert checkpoint_key(safe_dev, baseline, baseline) < checkpoint_key(unsafe_dev, baseline, worse)
    better_safe_dev = dict(safe_dev, critical_errors=10)
    assert checkpoint_key(better_safe_dev, baseline, baseline) < checkpoint_key(safe_dev, baseline, baseline)


def test_multiplication_transfer_preserves_probability_mass_and_original_head():
    import torch
    torch.manual_seed(9)
    old = torch.nn.Linear(4, 3)
    initial = {k: v.clone() for k, v in old.state_dict().items()}
    vocabulary = {'<blank>': 0, 'x': 1, 'a': 2}
    transferred = expand_head(old, vocabulary, ['×'], True)
    features = torch.randn(6, 4)
    baseline = old(features).softmax(-1)
    actual = transferred(features).softmax(-1)
    assert torch.allclose(actual[:, 0], baseline[:, 0], atol=1e-7)
    assert torch.allclose(actual[:, 2], baseline[:, 2], atol=1e-7)
    assert torch.allclose(actual[:, 1] + actual[:, 3], baseline[:, 1], atol=1e-7)
    assert all(torch.equal(v, initial[k]) for k, v in old.state_dict().items())
    cold = expand_head(old, vocabulary, ['×'])
    assert torch.equal(cold.weight[:3], old.weight)
    assert torch.equal(cold.bias[:3], old.bias)
    assert torch.count_nonzero(cold.weight[3]) == 0 and cold.bias[3].item() == -12
    with pytest.raises(ValueError, match='new TRAIN'):
        expand_head(old, vocabulary, [], True)
    with pytest.raises(ValueError, match='existing x'):
        expand_head(old, {'<blank>': 0, 'z': 1, 'a': 2}, ['×'], True)


@pytest.mark.parametrize('replay', [0, 4, True])
def test_unbounded_or_noninteger_prose_replay_rejected_before_training(tmp_path, replay):
    from argparse import Namespace
    from finetune_line_ocr import run
    manifest, _ = prepare(tmp_path)
    with pytest.raises(ValueError, match='Prose replay'):
        run(Namespace(manifest=manifest, prose_replay=replay))


@pytest.mark.parametrize('weight', [-1, 3, float('nan'), float('inf'), True])
def test_invalid_prose_anchor_rejected_before_training(tmp_path, weight):
    from argparse import Namespace
    from finetune_line_ocr import run
    manifest, _ = prepare(tmp_path)
    with pytest.raises(ValueError, match='Prose anchor weight'):
        run(Namespace(manifest=manifest, prose_anchor_weight=weight))


@pytest.mark.parametrize('visual,numeric,defer', [(False, False, False), (True, False, False),
                                               (True, True, False), (True, True, True),
                                               (True, False, True)])
def test_recurrent_experiment_runs_with_mixed_lengths_and_preserves_cnn(tmp_path, monkeypatch, visual, numeric, defer):
    """One real backward pass; synthetic pixels verify plumbing, not accuracy."""
    from argparse import Namespace
    import torch
    from app.ocr.model import CRNN
    from finetune_line_ocr import run

    manifest, rows = prepare(tmp_path)
    for row, width in zip(rows, (60, 100, 80)):
        row.update(text='11', box=[0, 0, width, 40])
        if defer:
            row['math_role'] = 'prose'
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
    if defer:
        import finetune_line_ocr as trainer
        transform = trainer.line_tensor
        holdout_pixels = Image.open(tmp_path/'cohort/images/2.jpg').convert('RGB').crop(rows[2]['box']).tobytes()
        def reject_holdout_transform(crop, preserve=False):
            assert crop.tobytes() != holdout_pixels, 'HOLDOUT must never enter neural preprocessing during development'
            return transform(crop, preserve)
        monkeypatch.setattr(trainer, 'line_tensor', reject_holdout_transform)
    run(Namespace(manifest=manifest, data_root=tmp_path, model_dir=model_dir,
                  output=output, epochs=1, batch_size=2, threads=2,
                  learning_rate=.001, seed=3, preserve_aspect_ratio=True, train_recurrent=True,
                  train_last_visual_block=visual, numeric_fields_only=numeric, defer_holdout=defer,
                  augment_train_contrast=defer, prose_replay=2 if defer else 1,
                  prose_anchor_weight=1.0 if defer and not numeric else 0.0))
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
    assert evidence['history'][0]['dev_scopes']
    assert evidence['selected_scope_regressions'] == evidence['history'][0]['scope_regressions']
    if defer:
        assert 'HOLDOUT' not in evidence['predictions'] and 'HOLDOUT' not in evidence['baseline']
        assert evidence['quality_gate']['reasons'] == ['HOLDOUT deferred; development measurements only']
        assert evidence['training_views']['original'] == evidence['training_views']['augmented'] == 1
        assert evidence['training_views']['sampled_per_epoch'] == 4
        assert evidence['training_views']['prose_anchor_views'] == (0 if numeric else 2)
        assert evidence['candidate']['DEV']['lines'] == 1
        assert evidence['candidate']['TRAIN']['lines'] == 1  # Augmentation is not another evaluated source.
        from finetune_line_ocr import evaluate_saved
        monkeypatch.setattr(trainer, 'line_tensor', transform)
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
