"""Diagnostic YOLO digit reads of frozen numerator/denominator crops.

This tests glyphs only. A digit detector does not establish a fraction layout.
All detections remain drafts, including model consensus.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(output):
    import torch
    from ultralytics import YOLO
    sys.path.insert(0, str(ROOT/'ai-training/datasets/drive_math/math_recurrent_20261017'))
    from experiment import read, sha, fetch, SourceWorker
    output = Path(output)
    if output.exists():
        raise FileExistsError('Preserve existing diagnostic evidence')
    policy_path = ROOT/'ai-training/datasets/drive_math/math_data_expansion_20261017/policy.json'
    comparison_path = ROOT/'ai-training/datasets/drive_math/specialist_comparison_v2_20261022/comparison.json'
    policy, comparison = read(policy_path), read(comparison_path)
    assert sha(policy_path) == comparison['policy_sha256']
    prior = {p['id']: p for p in comparison['predictions']}
    checkpoint = ROOT/'ai/runtime/models/yolov8n_mathvision_det_v1.pt'
    checkpoint_hash = sha(checkpoint)
    torch.set_num_threads(4)
    model = YOLO(str(checkpoint))
    groups = {}
    for row in policy['records']:
        if row.get('math_role') in {'numerator', 'denominator'}:
            assert row['source']['sha256'] not in policy['forbidden_source_hashes']
            groups.setdefault(row['source']['sha256'], []).append(row)
    predictions = []
    worker = SourceWorker(timeout=60)
    try:
        for rows in groups.values():
            page = fetch(worker, rows[0]['source'])
            for row in rows:
                assert 'rectified_cell' not in row
                crop = page.crop(row['box'])
                crop_hash = hashlib.sha256(crop.tobytes()).hexdigest()
                assert crop_hash == prior[row['id']]['crop_pixels_sha256']
                boxes = model(crop, conf=.25, imgsz=640, device='cpu', verbose=False)[0].boxes
                detections = [dict(class_id=int(c), confidence=float(p), xyxy=xy)
                              for c, p, xy in zip(boxes.cls.tolist(), boxes.conf.tolist(), boxes.xyxy.tolist())]
                detections.sort(key=lambda d: d['xyxy'][0])
                # Carry/operator classes cannot silently become digits.
                digits = ''.join(str(d['class_id']) for d in detections) if detections and all(d['class_id'] < 10 for d in detections) else None
                predictions.append(dict(id=row['id'], split=row['split'], role=row['math_role'],
                    reference=row['text'], digit_reading=digits, detections=detections,
                    crop_pixels_sha256=crop_hash, box=row['box'],
                    source_sha256=row['source']['sha256'], drive_id=row['source']['drive_id'],
                    status='MODEL_DRAFT', training_eligible=False))
            print(f'Digit diagnostic: {len(predictions)}/73 components', flush=True)
    finally:
        worker.close()
    assert len(predictions) == 73 and sha(checkpoint) == checkpoint_hash
    dev = [p for p in predictions if p['split'] == 'DEV']
    result = dict(checkpoint_sha256=checkpoint_hash, policy_sha256=sha(policy_path),
        comparison_sha256=sha(comparison_path), script_sha256=sha(Path(__file__)),
        predictions=predictions, dev_components=len(dev),
        dev_exact_components=sum(p['digit_reading'] == p['reference'] for p in dev),
        dev_abstentions=sum(p['digit_reading'] is None for p in dev),
        production_model_changed=False, source_images_written=0, holdout_accessed=False,
        limitations=['Human-reviewed component crops, not 2D fraction recognition',
                     'Digit strings are diagnostics; no decoder routing or label correction',
                     'Detector has no fraction-bar, multiplication or division class'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'predictions'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    run(parser.parse_args().output)
