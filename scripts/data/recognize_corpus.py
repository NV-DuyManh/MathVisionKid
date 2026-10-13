"""Stream a frozen CRNN over supplied crops and hash-verified page regions.

SQLite keeps bounded-memory, resumable drafts; predictions never become labels.
No network inference, training, production installation or source edits occur.
"""
import argparse
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import sqlite3
import sys
import time

from PIL import Image, ImageOps, __version__ as PIL_VERSION
from finetune_line_ocr import decode_ctc, digest, line_tensor
from line_crop_margin import pad_line_regions
from recognize_line_batch import validate_region_provenance
from source_storage import read_source_bytes
from source_orientation import orient_image, validate_orientation_geometry

ROOT = Path(__file__).resolve().parents[2]
CROP_TYPES = {'supplied_image_crop', 'provided_line_crop'}


def source_boxes(item, image, region):
    if item.get('source_type') in CROP_TYPES:
        return [[0, 0, image.width, image.height]], 'supplied_crop_unverified_geometry'
    if (region is None or region.get('status') != 'tested'
            or region.get('sha256') != item['sha256']
            or region.get('image_size') != list(image.size)):
        raise ValueError('Page regions must match the current oriented source')
    validate_orientation_geometry(item, region)
    boxes = region['boxes']
    if len(boxes) > 200:
        raise ValueError('Too many page regions')
    # Validates exact integer coordinates even when margins are disabled.
    pad_line_regions(boxes, image.width, image.height)
    return boxes, 'detected_page_regions_unverified_geometry'


def open_results(path, fingerprint):
    connection = sqlite3.connect(path)
    connection.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
    connection.execute('CREATE TABLE IF NOT EXISTS records '
                       '(source_id TEXT PRIMARY KEY, status TEXT, payload TEXT)')
    prior = connection.execute("SELECT value FROM metadata WHERE key='fingerprint'").fetchone()
    if ((prior and prior[0] != fingerprint)
            or (not prior and connection.execute('SELECT COUNT(*) FROM records').fetchone()[0])):
        connection.close()
        raise ValueError('Resume inputs changed; use a new output database')
    connection.execute("INSERT OR IGNORE INTO metadata VALUES ('fingerprint', ?)", (fingerprint,))
    connection.commit()
    return connection


def save_record(connection, record):
    connection.execute('INSERT OR REPLACE INTO records VALUES (?, ?, ?)',
                       (record['drive_id'], record['status'], json.dumps(record, ensure_ascii=False)))


def reusable_draft(saved, current, boxes):
    """Resume only structurally valid, explicitly unverified source drafts."""
    if not isinstance(saved, dict):
        return False
    if any(saved.get(k) != current[k] for k in ('drive_id', 'sha256', 'image_size', 'geometry_kind')):
        return False
    if saved.get('reviewed_orientation') != current.get('reviewed_orientation'):
        return False
    if (any(saved.get(k) is not False for k in ('labels_verified', 'reference_label', 'training_eligible'))
            or saved.get('cloud_inference_calls') != 0
            or saved.get('status') != ('recognized' if boxes else 'no_detected_regions')):
        return False
    lines = saved.get('lines')
    if not isinstance(lines, list) or len(lines) != len(boxes):
        return False
    for line, box in zip(lines, boxes):
        if (not isinstance(line, dict) or line.get('box') != list(box)
                or any(type(v) is not int for v in line['box'])
                or not isinstance(line.get('text'), str)
                or line.get('score_is_accuracy') is not False):
            return False
        score = line.get('raw_score')
        if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
            return False
    return True


def run(args):
    import torch
    import torchvision
    sys.path.insert(0, str(ROOT / 'ai/runtime'))
    from app.ocr.model import CRNN
    torch.set_num_threads(args.threads)
    folder, model_dir, output = args.batch.resolve(), args.candidate.resolve(), args.output.resolve()
    private = (ROOT / 'ai-training/datasets/drive_math').resolve()
    if not folder.is_relative_to(private) or not output.is_relative_to(private):
        raise ValueError('Sources and drafts must stay inside the private dataset')
    evidence = json.loads((model_dir / 'evaluation.json').read_text(encoding='utf-8'))
    if evidence.get('settings', {}).get('numeric_fields_only') is True:
        raise ValueError('Numeric-fields-only candidates cannot recognize general text/math corpora')
    weights, vocabulary = model_dir / 'candidate.pth', model_dir / 'vocab.json'
    paired = {'model_sha256': digest(weights), 'vocab_sha256': digest(vocabulary)}
    if (paired['model_sha256'] != evidence['candidate_sha256']
            or paired['vocab_sha256'] != evidence['candidate_vocab_sha256']):
        raise ValueError('Frozen checkpoint and vocabulary do not match training evidence')
    selection = folder / 'source_selection.json'
    items = json.loads(selection.read_text(encoding='utf-8'))
    if len({i['drive_id'] for i in items}) != len(items):
        raise ValueError('Source IDs must be unique')
    region_paths = {}
    region_hashes = {}
    detector_regions = {}
    for directory in args.regions:
        for path in sorted(directory.glob('*.json')):
            if path.stem in region_paths:
                raise ValueError('Duplicate page geometry')
            region_paths[path.stem] = path
            region_hashes[path.stem] = digest(path)
            region = json.loads(path.read_text(encoding='utf-8'))
            signature = json.dumps(region.get('source_hashes'), sort_keys=True)
            if signature not in detector_regions:
                validate_region_provenance(region)
                detector_regions[signature] = region
    provenance = {**paired, 'selection_sha256': digest(selection),
                  'region_files': region_hashes, 'margins': args.margins,
                  'runtime': {'python': platform.python_version(), 'torch': str(torch.__version__),
                              'torchvision': torchvision.__version__, 'pillow': PIL_VERSION,
                              'device': 'cpu', 'threads': args.threads, 'batch_size': args.batch_size},
                  'aspect_ratio': evidence['settings']['preserve_aspect_ratio'],
                  'code': {str(p.relative_to(ROOT)): digest(p) for p in (
                      Path(__file__), ROOT / 'scripts/data/finetune_line_ocr.py',
                      ROOT / 'scripts/data/source_storage.py', ROOT / 'scripts/data/line_crop_margin.py',
                      ROOT / 'scripts/data/source_orientation.py',
                      ROOT / 'scripts/data/recognize_line_batch.py', ROOT / 'ai/runtime/app/ocr/model.py',
                      ROOT / 'ai/runtime/app/ocr/crnn_provider.py')}}
    fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    db = open_results(output / 'predictions.sqlite', fingerprint)
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    vocab = json.loads(vocabulary.read_text(encoding='utf-8'))
    model = CRNN(len(vocab)).eval()
    model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True))
    pending = []
    started = time.monotonic()

    def flush():
        # Exact widths: no extra CNN padding that would alter GroupNorm/CTC.
        groups = defaultdict(list)
        for record, tensors in pending:
            record['lines'] = [None] * len(tensors)
            for number, (box, tensor) in enumerate(tensors):
                groups[tensor.shape[-1]].append((record, number, box, tensor))
        with torch.inference_mode():
            for group in groups.values():
                for first in range(0, len(group), args.batch_size):
                    chunk = group[first:first + args.batch_size]
                    logits = model(torch.stack([row[3] for row in chunk]))
                    texts = decode_ctc(logits.argmax(-1).tolist(), vocab)
                    scores = logits.softmax(-1).max(-1).values.mean(-1).tolist()
                    for (record, number, box, _), text, score in zip(chunk, texts, scores):
                        width, height = box[2]-box[0], box[3]-box[1]
                        record['lines'][number] = {'box': box, 'text': text, 'raw_score': score,
                                                  'score_is_accuracy': False,
                                                  'needs_layout_review': height > width*.5 or (
                                                      record['geometry_kind'].startswith('detected_page')
                                                      and height > record['image_size'][1]*.12),
                                                  'resize_width_capped': round(width*64/height/8)*8 > 1024}
        for record, _ in pending:
            record['status'] = 'recognized' if record['lines'] else 'no_detected_regions'
            save_record(db, record)
        db.commit()
        pending.clear()

    for index, item in enumerate(items, 1):
        record = {'drive_id': item['drive_id'], 'name': item['name'], 'sha256': item['sha256'],
                  'reviewed_orientation': item.get('reviewed_orientation'),
                  'labels_verified': False, 'reference_label': False, 'training_eligible': False,
                  'cloud_inference_calls': 0}
        try:
            raw = read_source_bytes(folder, item)
            if hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('Source bytes changed')
            prior = db.execute('SELECT status, payload FROM records WHERE source_id=?', (item['drive_id'],)).fetchone()
            with Image.open(io.BytesIO(raw)) as source:
                image = orient_image(source, item)
            path = region_paths.get(item['drive_id'])
            region = json.loads(path.read_text(encoding='utf-8')) if path else None
            boxes, record['geometry_kind'] = source_boxes(item, image, region)
            if item.get('source_type') not in CROP_TYPES:
                if digest(path) != region_hashes[item['drive_id']]:
                    raise ValueError('Page geometry changed during recognition')
                if args.margins:
                    boxes = pad_line_regions(boxes, image.width, image.height)
            record['image_size'] = list(image.size)
            if prior and prior[0] in {'recognized', 'no_detected_regions'}:
                saved = json.loads(prior[1])
                if reusable_draft(saved, record, boxes):
                    continue  # Verify current source/geometry before reusing a draft.
            pending.append((record, [(list(box), line_tensor(image.crop(box), provenance['aspect_ratio']))
                                     for box in boxes]))
            if sum(len(tensors) for _, tensors in pending) >= 128:
                flush()
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
            flush()
            record.update(status='execution_failed', error_type=type(exc).__name__, error=str(exc))
            save_record(db, record)
            db.commit()
        if index % 250 == 0:
            flush()
            counts = dict(db.execute('SELECT status, COUNT(*) FROM records GROUP BY status'))
            print(json.dumps({'processed': index, 'requested': len(items), 'status': counts,
                              'elapsed_seconds': round(time.monotonic()-started)}, ensure_ascii=False), flush=True)
    flush()
    for region in detector_regions.values():
        validate_region_provenance(region)
    counts, lines, nonempty = {}, 0, 0
    with (output / 'predictions.jsonl').open('w', encoding='utf-8') as stream:
        for status, payload in db.execute('SELECT status, payload FROM records ORDER BY source_id'):
            counts[status] = counts.get(status, 0) + 1
            row = json.loads(payload)
            lines += len(row.get('lines', []))
            nonempty += sum(bool(line['text'].strip()) for line in row.get('lines', []))
            stream.write(payload + '\n')
    if (digest(weights) != paired['model_sha256'] or digest(vocabulary) != paired['vocab_sha256']
            or digest(selection) != provenance['selection_sha256']
            or any(digest(ROOT / path) != sha for path, sha in provenance['code'].items())
            or any(digest(region_paths[key]) != sha for key, sha in region_hashes.items())):
        raise ValueError('Frozen inputs changed; output cannot be certified')
    summary = {'requested': len(items), 'status': counts, 'regions_recognized': lines,
               'nonempty_transcripts': nonempty, 'verified_cer': None, 'verified_accuracy': False,
               'training_eligible': False, 'production_promoted': False, 'cloud_inference_calls': 0,
               'fingerprint': fingerprint, **paired}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    db.close()
    print(json.dumps(summary, indent=2), flush=True)
    return 1 if counts.get('execution_failed') or len(items) != sum(counts.values()) else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--regions', type=Path, nargs='*', default=[])
    parser.add_argument('--margins', action='store_true')
    parser.add_argument('--threads', type=int, choices=range(1, 9), default=2)
    parser.add_argument('--batch-size', type=int, choices=range(1, 5), default=4)
    raise SystemExit(run(parser.parse_args()))
