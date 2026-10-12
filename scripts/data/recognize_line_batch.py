"""Resumable local CRNN drafts from hash-checked, source-coordinate regions.

Predictions are never reference labels. Reuses the production recognizer without
changing its weights, source photos, or existing reviewed labels.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import time

from PIL import Image, ImageOps
from drive_line_batch import write_json
from source_storage import read_source_bytes
from source_orientation import orient_image, validate_orientation_geometry

ROOT = Path(__file__).resolve().parents[2]
DETECTOR_SOURCES = {'app/api/ocr.py', 'app/api/generalized.py',
                    'app/api/generalized_pipeline.py', 'app/recognition/text_detector.py',
                    'app/tutoring/rows.py', 'model'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_region_provenance(region):
    """A resumable draft must still use the exact detector that produced its crop."""
    hashes = region.get('source_hashes')
    if not isinstance(hashes, dict) or not DETECTOR_SOURCES.issubset(hashes):
        raise ValueError('Regions lack detector provenance; regenerate regions first')
    runtime = (ROOT / 'ai/runtime').resolve()
    for name, expected in hashes.items():
        # The batch detector records its pinned model under this special key.
        relative = Path('models/ocr/text_detection_cn_ppocrv3_2023may.onnx') if name == 'model' else Path(name)
        path = (runtime / relative).resolve()
        if name == 'model' and expected == 'absent' and not path.exists():
            continue
        if (relative.is_absolute() or not path.is_relative_to(runtime) or
                not isinstance(expected, str) or len(expected) != 64):
            raise ValueError('Invalid detector provenance')
        if digest(path) != expected:
            raise ValueError(f'Detector changed: {name}; regenerate regions first')
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def run(folder, provider, model_hashes):
    selection = json.loads((folder / 'source_selection.json').read_text(encoding='utf-8'))
    output = folder / 'crnn_results'
    output.mkdir(exist_ok=True)
    records = []
    for index, item in enumerate(selection, 1):
        path = output / f"{item['drive_id']}.json"
        record = {**item, **model_hashes, 'labels_verified': False,
                  'reference_label': False, 'training_eligible': False,
                  'cloud_calls': 0, 'device': 'cpu',
                  'provider': model_hashes.get('provider', 'crnn_vi_handwriting_v1')}
        try:
            raw = read_source_bytes(folder, item)
            if hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('Source changed')
            region = json.loads((folder / 'local_regions' / f"{item['drive_id']}.json").read_text(encoding='utf-8'))
            if region.get('status') != 'tested' or region.get('sha256') != item['sha256']:
                raise ValueError('Regions do not match verified source bytes')
            validate_orientation_geometry(item, region)
            detector_hash = validate_region_provenance(region)
            boxes = region['boxes']
            signature = {**model_hashes, 'sha256': item['sha256'],
                         'detector_provenance_sha256': detector_hash,
                         'boxes_sha256': hashlib.sha256(json.dumps(boxes).encode()).hexdigest()}
            signature['reviewed_orientation'] = item.get('reviewed_orientation')
            signature['orientation_code_sha256'] = digest(Path(__file__).with_name('source_orientation.py'))
            record.update(signature)
            prior = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
            with Image.open(io.BytesIO(raw)) as source:
                image = orient_image(source, item)
            if region.get('image_size') != list(image.size):
                raise ValueError('Regions do not match the oriented source dimensions')
            if not all(len(b) == 4 and all(type(v) is int for v in b) and
                       0 <= b[0] < b[2] <= image.width and 0 <= b[1] < b[3] <= image.height
                       for b in boxes):
                raise ValueError('Regions exceed source bounds')
            if (prior.get('status') == 'recognized' and
                    all(prior.get(k) == v for k, v in signature.items()) and
                    len(prior.get('lines', [])) == len(boxes) and
                    all(line.get('box') == box for line, box in zip(prior['lines'], boxes))):
                record.update(status='recognized', lines=prior['lines'], latency_ms=prior['latency_ms'])
            else:
                started = time.perf_counter()
                # Process only four crops at a time, including image allocation.
                lines = []
                for start in range(0, len(boxes), 4):
                    chunk = boxes[start:start + 4]
                    predictions = provider.recognize_batch_with_confidence(
                        [image.crop(box) for box in chunk], batch_size=4)
                    if len(predictions) != len(chunk):
                        raise ValueError('Missing line prediction')
                    lines.extend({'box': box, 'text': text, 'raw_score': float(score),
                                  'score_is_accuracy': False}
                                 for box, (text, score) in zip(chunk, predictions))
                record.update(status='recognized', lines=lines,
                              latency_ms=round((time.perf_counter() - started) * 1000, 2))
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
            record.update(status='execution_failed', error_type=type(exc).__name__, error=str(exc))
        write_json(path, record)
        records.append(record)
        print(f"{index}/{len(selection)} {item['name']}: {record['status']}, "
              f"{len(record.get('lines', []))} regions", flush=True)
    done = [r for r in records if r['status'] == 'recognized']
    summary = {'requested': len(selection), 'recognized_images': len(done),
               'execution_failed': len(records) - len(done),
               'regions_recognized': sum(len(r['lines']) for r in done),
               'nonempty_transcripts': sum(bool(line['text'].strip()) for r in done for line in r['lines']),
               'verified_cer': None, 'verified_accuracy': False,
               'training_eligible': False, 'cloud_calls': 0, **model_hashes}
    write_json(folder / 'crnn_summary.json', summary)
    with (folder / 'line_predictions.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['name', 'drive_id', 'line', 'x1', 'y1', 'x2', 'y2', 'ocr_draft', 'raw_score', 'verified'])
        for record in done:
            for number, line in enumerate(record['lines'], 1):
                writer.writerow([record['name'], record['drive_id'], number, *line['box'],
                                 line['text'], line['raw_score'], False])
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    args = parser.parse_args()
    private = (ROOT / 'ai-training/datasets/drive_math').resolve()
    folder = (private / args.batch).resolve()
    if folder == private or not folder.is_relative_to(private):
        parser.error('batch must be inside the private dataset directory')
    sys.path.insert(0, str(ROOT / 'ai/runtime'))
    import torch
    from app.ocr.crnn_provider import CrnnOcrProvider
    torch.set_num_threads(2)
    provider = CrnnOcrProvider(device='cpu')
    if not provider.is_available():
        raise RuntimeError('Existing local CRNN is unavailable')
    hashes = {'model_sha256': digest(provider.weights_path), 'vocab_sha256': digest(provider.vocab_path),
              'provider_sha256': digest(ROOT / 'ai/runtime/app/ocr/crnn_provider.py')}
    summary = run(folder, provider, hashes)
    if hashes['model_sha256'] != digest(provider.weights_path) or hashes['vocab_sha256'] != digest(provider.vocab_path):
        raise RuntimeError('Production weights changed during recognition')
    print(json.dumps(summary, indent=2), flush=True)
    if summary['execution_failed']:
        raise SystemExit(1)
