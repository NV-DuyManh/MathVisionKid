"""Resumable, local-only Drive-image line audit. Originals and labels stay private.

Discover/download with the Drive connector first, then supply source_selection.json
and images/<drive_id>.jpg under the batch directory. Never promote predictions to
reference labels. 'select' skips tested IDs; content hashes also catch aliases.
"""
import argparse
import asyncio
import csv
import hashlib
import importlib.util
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / 'ai-training/datasets/drive_math'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def open_ledger(data):
    data.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(data / 'ledger.sqlite3')
    db.execute('''CREATE TABLE IF NOT EXISTS images (
        drive_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, pixel_sha256 TEXT NOT NULL,
        name TEXT NOT NULL, source_group TEXT NOT NULL, batch TEXT NOT NULL,
        tested_at TEXT NOT NULL, label_status TEXT NOT NULL DEFAULT 'needs_review')''')
    db.execute('CREATE INDEX IF NOT EXISTS raw_hash ON images(sha256)')
    db.execute('CREATE INDEX IF NOT EXISTS pixel_hash ON images(pixel_sha256)')
    return db


def select_unseen(records, db, limit):
    seen = {row[0] for row in db.execute('SELECT drive_id FROM images')}
    unique = {r['drive_id']: r for r in records if r['drive_id'] not in seen}
    return list(unique.values())[:limit]


def reviewed_label(path, image_hash, image_size):
    """Validate references; count review and box/text review are distinct stages."""
    if not path.exists():
        return None
    label = json.loads(path.read_text(encoding='utf-8'))
    if label.get('sha256') != image_hash:
        raise ValueError('Reference belongs to a different image')
    if label.get('review_status') not in {'count_verified', 'geometry_verified', 'verified'}:
        return None
    count = label.get('line_count')
    if type(count) is not int or count < 0:
        raise ValueError('Invalid reference line count')
    if label['review_status'] in {'geometry_verified', 'verified'}:
        lines = label.get('lines', [])
        if len(lines) != count:
            raise ValueError('Reference count and geometry disagree')
        width, height = image_size
        for row in lines:
            box = row.get('box', [])
            if len(box) != 4 or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
                raise ValueError('Reference box out of bounds')
            if label['review_status'] == 'verified' and (not row.get('text') or row.get('uncertain', False)):
                raise ValueError('Training reference needs verified, unambiguous text')
    return label


def run_batch(data, batch, detector_source, force=False):
    folder = data / batch
    selection = json.loads((folder / 'source_selection.json').read_text(encoding='utf-8'))
    source = detector_source or ROOT / 'ai/runtime/app/tutoring/rows.py'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location('audit_detector', source)
    detector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(detector)
    db = open_ledger(data)
    results = []
    for number, item in enumerate(selection, 1):
        output = folder / 'results' / f"{item['drive_id']}.json"
        record = {**item, 'index': number, 'detector_sha256': digest}
        try:
            path = folder / 'images' / f"{item['drive_id']}.jpg"
            raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            with Image.open(path) as raw:
                image = ImageOps.exif_transpose(raw).convert('RGB')
            pixel_hash = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
            alias = db.execute('SELECT drive_id FROM images WHERE pixel_sha256=? AND drive_id<>?',
                               (pixel_hash, item['drive_id'])).fetchone()
            old = json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
            reusable = (not force and old.get('detector_sha256') == digest
                        and old.get('sha256') == raw_hash and old.get('status') == 'tested')
            if reusable:
                boxes, duration = old['boxes'], old['latency_ms']
            else:
                start = time.perf_counter()
                boxes = detector.handwriting_rows(cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR))
                duration = round((time.perf_counter() - start) * 1000, 2)
            width, height = image.size
            if any(not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height) for x1, y1, x2, y2 in boxes):
                raise ValueError('Detector returned out-of-bounds geometry')
            label_path = folder / 'labels' / f"{item['drive_id']}.json"
            label = reviewed_label(label_path, raw_hash, image.size)
            record.update(status='tested', sha256=raw_hash, pixel_sha256=pixel_hash,
                          image_size=image.size, boxes=boxes, latency_ms=duration,
                          duplicate_of=alias[0] if alias else None,
                          label_status=label['review_status'] if label else 'needs_review',
                          expected_count=label['line_count'] if label else None)
            if not label_path.exists():
                write_json(label_path, {'drive_id': item['drive_id'], 'sha256': raw_hash,
                                       'review_status': 'needs_review', 'line_count': None,
                                       'draft_boxes': boxes, 'lines': [],
                                       'note': 'Predicted boxes are NOT ground truth or training labels.'})
            timestamp = datetime.now(timezone.utc).isoformat()
            db.execute('INSERT OR REPLACE INTO images VALUES (?,?,?,?,?,?,?,?)',
                       (item['drive_id'], raw_hash, pixel_hash, item['name'], item['source_group'],
                        batch, timestamp, record['label_status']))
            db.commit()
        except (OSError, ValueError, KeyError, cv2.error) as exc:
            record.update(status='failed', error=str(exc))
        write_json(output, record)
        results.append(record)
        if number % 20 == 0:
            print(f'{number}/{len(selection)} persisted', flush=True)
    total_images = db.execute('SELECT COUNT(*) FROM images').fetchone()[0]
    db.close()
    tested = [r for r in results if r['status'] == 'tested']
    references = [r for r in tested if r['expected_count'] is not None and not r['duplicate_of']]
    summary = {'batch': batch, 'requested': len(selection), 'tested': len(tested),
               'failed': len(results)-len(tested), 'unique_pixels': len({r['pixel_sha256'] for r in tested}),
               'with_boxes': sum(bool(r['boxes']) for r in tested),
               'reference_count_pages': len(references),
               'exact_count_pages': sum(len(r['boxes']) == r['expected_count'] for r in references),
               'mean_absolute_count_error': float(np.mean([abs(len(r['boxes'])-r['expected_count']) for r in references])) if references else None,
               'p95_latency_ms': float(np.percentile([r['latency_ms'] for r in tested],95)) if tested else None,
               'label_status_counts': {status: sum(r['label_status'] == status for r in tested)
                                       for status in ('needs_review', 'count_verified', 'geometry_verified', 'verified')},
               'detector_sha256': digest, 'training_performed': False}
    write_json(folder / 'summary.json', summary)
    with (folder / 'manifest.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=['index', 'drive_id', 'name', 'source_group',
                                                    'status', 'sha256', 'label_status', 'expected_count', 'detected_count'])
        writer.writeheader()
        for result in results:
            writer.writerow({**{key: result.get(key, '') for key in writer.fieldnames if key != 'detected_count'},
                             'detected_count': len(result.get('boxes', []))})
    write_json(data / 'progress.json', {'images': total_images, 'last_batch': batch, **summary})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'select', 'cloud'])
    parser.add_argument('--data-root', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--batch', default='20261004')
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--detector-source', type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be positive')
    if args.action == 'select':
        if args.selection is None:
            parser.error('select requires --selection containing connector metadata')
        with open_ledger(args.data_root) as db:
            selected = select_unseen(json.loads(args.selection.read_text(encoding='utf-8')), db, args.limit)
        target = args.data_root / args.batch / 'source_selection.json'
        if target.exists():
            parser.error('Batch already exists; choose a new --batch instead of replacing its selection')
        write_json(target, selected)
        print(f'Selected {len(selected)} untested Drive IDs')
    elif args.action == 'cloud':
        asyncio.run(run_cloud_batch(args.data_root, args.batch, args.force))
    else:
        run_batch(args.data_root, args.batch, args.detector_source, args.force)


async def run_cloud_batch(data, batch, force=False):
    """Explicit opt-in to the configured vision APIs; never turn output into labels.

    Run only for an owner-authorized cloud audit. Stop on provider unavailability
    instead of sweeping credentials or pretending a local draft is an OCR result.
    """
    sys.path.insert(0, str(ROOT / 'ai/runtime'))
    from app.tutoring.notebook import inspect_notebook, READ_NOTEBOOK
    from app.tutoring.service import TutorUnavailable
    signature = hashlib.sha256(READ_NOTEBOOK.encode() + (ROOT / 'ai/runtime/app/tutoring/notebook.py').read_bytes()
                               + (ROOT / 'ai/runtime/app/tutoring/rows.py').read_bytes()).hexdigest()
    folder = data / batch
    selection = json.loads((folder / 'source_selection.json').read_text(encoding='utf-8'))
    completed = []
    for number, item in enumerate(selection, 1):
        raw = (folder / 'images' / f"{item['drive_id']}.jpg").read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        target = folder / 'cloud_results' / f"{item['drive_id']}.json"
        previous = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
        if not force and previous.get('signature') == signature and previous.get('sha256') == digest and previous.get('status') == 'read':
            completed.append(previous)
            continue
        record = {**item, 'index': number, 'sha256': digest, 'signature': signature, 'reference_label': False}
        try:
            start = time.perf_counter()
            reading = await inspect_notebook(raw)
            record.update(status='read', latency_ms=round((time.perf_counter()-start)*1000, 2), result=reading.model_dump())
        except TutorUnavailable:
            from app.integrations.groq.line_analyzer import get_pool
            pool = get_pool()
            # Store only error enums/backoff, never credentials or provider bodies.
            entries = pool._entries if pool else []
            record.update(status='provider_unavailable',
                          primary_error_classes=sorted({entry.last_error_class for entry in entries if entry.last_error_class}),
                          retry_not_before=max([time.time()+60] + [entry.cooldown_until for entry in entries]))
            write_json(target, record)
            print(f'{number}/{len(selection)}: provider unavailable; stopped without quota/key sweep', flush=True)
            break
        write_json(target, record)
        completed.append(record)
        print(f'{number}/{len(selection)} cloud result persisted: {reading.kind}, {len(reading.lines)} rows', flush=True)
    summary = {'requested': len(selection), 'read': len(completed),
               'pending': len(selection)-len(completed), 'signature': signature,
               'kind_counts': {kind: sum(r['result']['kind'] == kind for r in completed)
                               for kind in ('PROBLEM', 'WORK', 'MIXED', 'MULTIPLE', 'UNREADABLE')},
               'auto_verified_labels': 0, 'training_performed': False}
    write_json(folder / 'cloud_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    main()
