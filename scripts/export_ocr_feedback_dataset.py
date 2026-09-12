#!/usr/bin/env python3
"""
OCR Feedback Dataset Export Tool for Vietnamese Handwriting Recognition.
Exports only verified training-eligible samples (verdict = CORRECT or CORRECTED, domain = HANDWRITING_TEXT, is_test_data = false).
Generates portable dataset package (manifest.jsonl, manifest.csv, checksums, README, ZIP).
"""

import os
import sys
import json
import csv
import time
import zipfile
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from minio import Minio  # type: ignore

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000").replace("http://", "").replace("https://", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "mathvision")

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fetch_eligible_trials(include_test: bool = False) -> list:
    """
    Fetch all verified line crops from:
      - ocr_trials (OCR Pilot 1 single line)
      - ocr_multiline_lines (OCR Pilot 2 multi-line)
    where:
      - training_eligible = true
      - verdict IN ('CORRECT', 'CORRECTED')
      - privacy_confirmed = true
      - domain = 'HANDWRITING_TEXT'
      - is_test_data = false (unless explicit include_test flag is provided)
      - verified_text_raw is non-empty
    """
    if include_test:
        test_filter = "WHERE (training_eligible = true OR is_test_data = true)"
        ml_test_filter = "WHERE (l.training_eligible = true OR t.is_test_data = true)"
    else:
        test_filter = "WHERE training_eligible = true AND is_test_data = false"
        ml_test_filter = "WHERE l.training_eligible = true AND t.is_test_data = false"

    sql = f"""
    SELECT COALESCE(json_agg(t), '[]'::json) FROM (
        SELECT 
            trial_id::text as sample_id,
            line_image_object_key,
            line_image_sha256 as image_sha256,
            predicted_text,
            verified_text_raw,
            verdict,
            source,
            domain,
            model_name,
            model_version,
            checkpoint_sha256,
            vocab_sha256,
            preprocessing_version,
            is_test_data,
            privacy_confirmed,
            'OCR_PILOT_1' as source_pilot,
            NULL::text as parent_trial_id,
            1 as line_order,
            created_at::text,
            feedback_at::text
        FROM ocr_trials 
        {test_filter}
          AND privacy_confirmed = true
          AND domain = 'HANDWRITING_TEXT'
          AND verdict IN ('CORRECT', 'CORRECTED')
          AND verified_text_raw IS NOT NULL 
          AND length(trim(verified_text_raw)) > 0
        UNION ALL
        SELECT 
            l.line_id::text as sample_id,
            l.line_image_object_key,
            l.line_image_sha256 as image_sha256,
            l.predicted_text,
            l.verified_text_raw,
            l.verdict,
            t.source,
            t.domain as domain,
            l.model_name,
            l.model_version,
            l.checkpoint_sha256,
            l.vocab_sha256,
            l.preprocessing_version,
            t.is_test_data,
            t.privacy_confirmed,
            'OCR_PILOT_2' as source_pilot,
            t.trial_id::text as parent_trial_id,
            l.line_order,
            l.created_at::text,
            l.feedback_at::text
        FROM ocr_multiline_lines l
        JOIN ocr_multiline_trials t ON l.trial_id = t.trial_id
        {ml_test_filter}
          AND t.privacy_confirmed = true
          AND t.domain = 'HANDWRITING_TEXT'
          AND t.status = 'COMPLETED'
          AND l.verdict IN ('CORRECT', 'CORRECTED')
          AND l.verified_text_raw IS NOT NULL 
          AND length(trim(l.verified_text_raw)) > 0
        ORDER BY created_at ASC
    ) t;
    """
    cmd = [
        "docker", "exec", "-i", "mathvision-postgres",
        "psql", "-U", "mathvision", "-d", "mathvision", "-t", "-A", "-c", sql
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = res.stdout.strip()
    if not out:
        return []
    return json.loads(out)

def export_dataset(output_root: Path, mock_samples: list = None, include_test: bool = False) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_dir_name = f"ocr_feedback_export_{timestamp}"
    export_dir = output_root / export_dir_name
    images_dir = export_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    trials = mock_samples if mock_samples is not None else fetch_eligible_trials(include_test=include_test)
    print(f"[EXPORT] Evaluating {len(trials)} candidate verified OCR trials...")

    minio_client = None
    if mock_samples is None:
        try:
            minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
        except Exception as e:
            print(f"[EXPORT] Warning: MinIO client init failed: {e}")

    manifest_rows = []
    checksums = []

    for item in trials:
        sample_id = item["sample_id"]
        verdict = item.get("verdict", "")
        pred = item.get("predicted_text", "")
        raw = item.get("verified_text_raw", "")
        is_test = item.get("is_test_data", False)
        privacy = item.get("privacy_confirmed", True)
        domain = item.get("domain", "HANDWRITING_TEXT")

        # 1. Scope and test exclusion
        if not include_test and is_test:
            print(f"[EXPORT] Skipping sample {sample_id}: flagged as test data (is_test_data=true)")
            continue

        if not privacy:
            print(f"[EXPORT] Skipping sample {sample_id}: privacy not confirmed")
            continue

        if domain != "HANDWRITING_TEXT":
            print(f"[EXPORT] Skipping sample {sample_id}: domain '{domain}' != 'HANDWRITING_TEXT'")
            continue

        if verdict == "SKIPPED":
            print(f"[EXPORT] Skipping sample {sample_id}: verdict is SKIPPED")
            continue

        # 2. Section 14 Guard: If verdict == CORRECT, verify predicted_text == verified_text_raw
        if verdict == "CORRECT":
            if pred != raw:
                print(f"[EXPORT] WARNING: DATA_INTEGRITY_ERROR for sample {sample_id}: verdict is CORRECT but predicted '{pred}' != verified '{raw}'. EXCLUDING from export!")
                continue

        if not raw or not raw.strip():
            print(f"[EXPORT] Skipping sample {sample_id}: verified_text_raw is empty")
            continue

        rel_img_path = f"images/{sample_id}.jpg"
        target_img_path = export_dir / rel_img_path

        img_bytes = None
        if "mock_bytes" in item:
            img_bytes = item["mock_bytes"]
        elif minio_client and "line_image_object_key" in item:
            try:
                response = minio_client.get_object(MINIO_BUCKET, item["line_image_object_key"])
                img_bytes = response.read()
                response.close()
                response.release_conn()
            except Exception as e:
                print(f"[EXPORT] Error fetching image for {sample_id} from MinIO: {e}")

        if not img_bytes:
            print(f"[EXPORT] Skipping sample {sample_id}: no image bytes retrieved")
            continue

        # Verify image checksum integrity against database record
        file_sha = compute_sha256(img_bytes)
        recorded_sha = item.get("image_sha256", "")
        if recorded_sha and file_sha.lower() != recorded_sha.lower():
            print(f"[EXPORT] WARNING: SHA256 mismatch for sample {sample_id}: calculated {file_sha} != recorded {recorded_sha}. EXCLUDING!")
            continue

        with open(target_img_path, "wb") as f:
            f.write(img_bytes)
        checksums.append(f"{file_sha}  {rel_img_path}")

        # De-identified manifest (no PII, no personal names, no school, no JWT, no absolute Windows paths)
        row = {
            "sample_id": sample_id,
            "source_pilot": item.get("source_pilot", "OCR_PILOT_1"),
            "parent_trial_id": item.get("parent_trial_id"),
            "line_order": item.get("line_order", 1),
            "relative_image_path": rel_img_path,
            "predicted_text": pred,
            "verified_text_raw": raw,
            "verdict": verdict,
            "source": item.get("source", "CAMERA"),
            "domain": domain,
            "model_version": item.get("model_version", "1.0.0"),
            "checkpoint_sha256": item.get("checkpoint_sha256", ""),
            "vocab_sha256": item.get("vocab_sha256", ""),
            "preprocessing_version": item.get("preprocessing_version", "v1_resize_64x1024_imagenet"),
            "image_sha256": file_sha,
            "created_at": item.get("created_at", ""),
            "feedback_at": item.get("feedback_at", ""),
        }
        manifest_rows.append(row)

    print(f"[EXPORT] Qualified {len(manifest_rows)} trustworthy handwriting samples.")

    # 1. Write manifest.jsonl
    jsonl_path = export_dir / "manifest.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in manifest_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 2. Write manifest.csv
    csv_path = export_dir / "manifest.csv"
    if manifest_rows:
        keys = list(manifest_rows[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(manifest_rows)

    # 3. Write checksums.sha256
    chk_path = export_dir / "checksums.sha256"
    with open(chk_path, "w", encoding="utf-8") as f:
        f.write("\n".join(checksums) + "\n")

    # 4. Write README.md
    readme_path = export_dir / "README.md"
    readme_content = f"""# MathVision Kids — OCR Human Feedback Training Dataset Export
Export Timestamp: {timestamp}
Domain: VIETNAMESE_HANDWRITING_TEXT
Total Verified Samples: {len(manifest_rows)}

## Provenance
- Target Model: Vietnamese Handwriting CRNN (best_cer.pth)
- Checkpoint SHA256: a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941
- Vocab SHA256: 6af4062e92e22cc91ece5198638e29a6ceec6cb92e3b12bd71deb4b874ac9e0d
- Training Eligibility: Explicit human verification only (verdict in [CORRECT, CORRECTED]), privacy_confirmed=true, is_test_data=false
- De-identification: Line crops only; all personal identifiers, names, emails, and full notebook pages strictly excluded.
- Manifest Files:
  - `manifest.jsonl`: Line-delimited JSON metadata
  - `manifest.csv`: Tabular metadata
  - `checksums.sha256`: SHA256 hashes of all exported line crop images
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 5. Create ZIP package
    zip_filename = f"{export_dir_name}.zip"
    zip_path = output_root / zip_filename
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(export_dir)
                zf.write(full_path, arcname=str(rel_path))

    print(f"[EXPORT] Successfully generated dataset package: {zip_path}")
    print(f"[EXPORT] Export directory: {export_dir}")
    return zip_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export human-verified OCR feedback dataset.")
    parser.add_argument("--out-dir", default="./data/exports", help="Output directory for exports")
    parser.add_argument("--include-test", action="store_true", help="Include test/synthetic data (default False)")
    args = parser.parse_args()

    out_path = Path(args.out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    export_dataset(out_path, include_test=args.include_test)
