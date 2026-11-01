"""Offline specialist comparison. Drive pixels stay in RAM; no model promotion.

Region roles are supplied by the frozen review, not predicted automatically.
References are used only for scoring, never routing or choosing a hypothesis.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'ai-training/datasets/drive_math'


def select_draft(role, hypotheses):
    selected = 'text' if role == 'prose' else 'math'
    if role not in {'prose', 'expression', 'comparison_expression', 'denominator',
                    'numerator', 'numeric_component', 'numeric_field', 'math_expression',
                    'intermediate', 'dividend', 'divisor', 'quotient', 'remainder', 'multiplier'}:
        selected = None
    text = hypotheses.get(selected, '')
    reasons = []
    if selected is None:
        reasons.append('unknown_region_role')
    if not text.strip():
        reasons.append('empty_reading')
    if '[?]' in text or '?' in text:
        reasons.append('unresolved_glyph')
    if len(set(hypotheses.values())) > 1:
        reasons.append('model_disagreement')
    if role in {'numerator', 'denominator'}:
        reasons.append('fraction_tier_requires_linked_layout_review')
    return dict(selected_model=selected, text=text, status='MODEL_DRAFT',
                review_reasons=reasons, training_eligible=False)


def run(output):
    import cv2
    import numpy as np
    import torch
    sys.path.insert(0, str(DATA / 'math_recurrent_20261017'))
    from experiment import (read, sha, fetch, SourceWorker, rectify_cell,
                            line_tensor, decode_ctc, CRNN, metrics, canonical, PHASE)
    output = Path(output)
    if output.exists():
        raise FileExistsError('Preserve existing comparison evidence')
    output.mkdir(parents=True)
    policy_path = DATA / 'math_data_expansion_20261017/policy.json'
    policy = read(policy_path)
    rows = policy['records']
    assert len(rows) == 598 and len({r['id'] for r in rows}) == len(rows)
    forbidden = set(policy['forbidden_source_hashes'])
    splits = {}
    for row in rows:
        assert row['split'] in {'TRAIN', 'DEV'}
        assert row['source']['sha256'] not in forbidden
        assert splits.setdefault(row['source']['sha256'], row['split']) == row['split']
    specs = {
        'text': (ROOT/'ai/runtime/models/ocr/crnn_vi_handwriting_v1/best_cer.pth',
                 ROOT/'ai/runtime/models/ocr/crnn_vi_handwriting_v1/vocab.json', False),
        'legacy': (ROOT/'ai/runtime/models/crnn_mathvision_ocr_v1.pth',
                   ROOT/'ai/runtime/models/vocab_ocr_v1.json', False),
        'math': (Path(policy['parent']), Path(policy['vocab']), True),
        'math_symbols': (DATA/'math_symbol_isolation_20261017/symbol_candidate.pth',
                         Path(policy['vocab']), True),
    }
    torch.set_num_threads(4)
    models, vocabularies, pins = {}, {}, {}
    for name, (checkpoint, vocab_path, aspect) in specs.items():
        vocab = read(vocab_path)
        vocab = vocab.get('vocab', vocab)
        model = CRNN(len(vocab)).eval()
        model.load_state_dict(torch.load(checkpoint, map_location='cpu', weights_only=True))
        models[name], vocabularies[name] = model, vocab
        pins[name] = dict(checkpoint=str(checkpoint), sha256=sha(checkpoint),
                          vocabulary_sha256=sha(vocab_path), classes=len(vocab),
                          input_policy='aspect_preserved' if aspect else 'fixed_64x1024')
    groups, predictions, receipts = {}, [], []
    for row in rows:
        groups.setdefault(row['source']['sha256'], []).append(row)
    prior = {r['id']: r for r in read(PHASE/'math_decode_review_20261013/decode_evaluation.json')['predictions']}
    from PIL import Image
    worker = SourceWorker(timeout=60)
    start = time.monotonic()
    try:
        for source_rows in groups.values():
            source = source_rows[0]['source']
            page = fetch(worker, source)
            page_hash = hashlib.sha256(page.tobytes()).hexdigest()
            for row in source_rows:
                x1, y1, x2, y2 = row['box']
                assert 0 <= x1 < x2 <= page.width and 0 <= y1 < y2 <= page.height
                if 'rectified_cell' in row:
                    crop = Image.fromarray(cv2.cvtColor(rectify_cell(
                        cv2.cvtColor(np.asarray(page), cv2.COLOR_RGB2BGR), row['rectified_cell']), cv2.COLOR_BGR2RGB))
                else:
                    crop = page.crop(row['box'])
                crop_hash = hashlib.sha256(crop.tobytes()).hexdigest()
                if row['id'] in prior:
                    assert hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest() == prior[row['id']]['crop_pixel_sha256']
                else:
                    assert list(page.size) == row['decoded_source_size']
                    assert page_hash == row['decoded_source_pixels_sha256']
                    assert crop_hash == row['crop_pixels_sha256']
                hypotheses = {}
                with torch.inference_mode():
                    tensors = {aspect: line_tensor(crop, aspect).unsqueeze(0) for aspect in (False, True)}
                    for name, model in models.items():
                        logits = model(tensors[specs[name][2]])
                        hypotheses[name] = decode_ctc(logits.argmax(-1).tolist(), vocabularies[name])[0]
                predictions.append(dict(id=row['id'], split=row['split'],
                    reference=row['text'], role=row.get('math_role'), box=row['box'],
                    source_review_status=row['review_status'],
                    source_uncertain=row['uncertain'],
                    source_training_eligible=row['training_eligible'],
                    source_sha256=source['sha256'], drive_id=source['drive_id'],
                    crop_pixels_sha256=crop_hash, crop_size=list(crop.size),
                    hypotheses=hypotheses, draft=select_draft(row.get('math_role'), hypotheses)))
            receipts.append(dict(sha256=source['sha256'], drive_id=source['drive_id']))
            print(f'Drive {len(receipts)}/{len(groups)}; {len(predictions)}/{len(rows)} regions', flush=True)
            del page
    finally:
        worker.close()
    indexed = {r['id']: r for r in rows}
    scores = {}
    for split in ('TRAIN', 'DEV'):
        for scope in ('all', 'prose', 'math', 'fraction_tiers'):
            chosen = [p for p in predictions if p['split'] == split and
                      p['source_review_status'] == 'verified' and not p['source_uncertain'] and
                      (split != 'TRAIN' or p['source_training_eligible']) and
                      (scope == 'all' or scope == 'prose' and p['role'] == 'prose' or
                       scope == 'math' and p['draft']['selected_model'] == 'math' or
                       scope == 'fraction_tiers' and p['role'] in {'numerator', 'denominator'})]
            refs = [indexed[p['id']] for p in chosen]
            scores[f'{split}/{scope}'] = {name: metrics(refs, [p['hypotheses'][name] for p in chosen]) for name in models}
            # Coverage is explicit: unknown roles abstain, never silently choose by reference.
            covered = [p for p in chosen if p['draft']['selected_model'] is not None]
            scores[f'{split}/{scope}']['role_routed'] = dict(
                coverage=len(covered), total=len(chosen),
                **metrics([indexed[p['id']] for p in covered], [p['draft']['text'] for p in covered]))
    for name, (checkpoint, vocab_path, _) in specs.items():
        assert sha(checkpoint) == pins[name]['sha256']
        assert sha(vocab_path) == pins[name]['vocabulary_sha256']
    result = dict(completed=True, duration_seconds=time.monotonic()-start,
        policy_sha256=sha(policy_path), script_sha256=sha(Path(__file__)), models=pins,
        scores=scores, predictions=predictions, source_receipts=receipts,
        source_images_written=0, holdout_accessed=False, training_performed=False,
        production_model_changed=False, draft_labels_training_eligible=0,
        source_quarantined=sum(p['source_uncertain'] or p['source_review_status'] != 'verified' for p in predictions),
        limitations=['Reviewed crops and roles; not automatic end-to-end OCR',
            'Repeated DEV; no independent writer/pretraining guarantee',
            'Greedy CTC comparison; not production beam/pipeline accuracy',
            'Fraction tiers scored separately; not complete 2D fraction recognition',
            'Existing references have no independent teacher attestation'])
    (output/'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # A review queue is not a training manifest, even where old references agree.
    queue = [dict(p, review_priority=(0 if p['source_uncertain'] or p['source_review_status'] != 'verified'
                  else 1 if p['role'] in {'numerator', 'denominator'}
                  else 2 if p['draft']['review_reasons'] else 3)) for p in predictions]
    queue.sort(key=lambda p: (p['review_priority'], p['source_sha256'], p['id']))
    (output/'review-queue.json').write_text(json.dumps(dict(
        kind='SOURCE_REVIEW_QUEUE_NOT_TRAINING_LABELS', training_eligible=0,
        records=queue), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(duration_seconds=result['duration_seconds'], dev=scores['DEV/all']), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run(parser.parse_args().output)
