#!/usr/bin/env python3
"""
OCR Feedback Dataset Export Tool for Vietnamese Handwriting Recognition.
Exports only verified training-eligible samples (verdict = CORRECT or CORRECTED).
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

def fetch_eligible_trials() -> list:
    """Fetch all trials where training_eligible = true via postgres docker."""
    sql = """
    SELECT COALESCE(json_agg(t), '[]'::json) FROM (
        SELECT 
            trial_id::text as sample_id,
            line_image_object_key,
            line_image_sha256 as image_sha256,
            predicted_text,
            verified_text_raw,
            verdict,
            source,
            model_version,
            checkpoint_sha256,
            created_at::text,
            feedback_at::text
        FROM ocr_trials 
        WHERE training_eligible = true 
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

def export_dataset(output_root: Path, mock_samples: list = None) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_dir_name = f"ocr_feedback_export_{timestamp}"
    export_dir = output_root / export_dir_name
    images_dir = export_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    trials = mock_samples if mock_samples is not None else fetch_eligible_trials()
    print(f"[EXPORT] Found {len(trials)} training-eligible verified OCR trials.")

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

        if img_bytes:
            with open(target_img_path, "wb") as f:
                f.write(img_bytes)
            file_sha = compute_sha256(img_bytes)
            checksums.append(f"{file_sha}  {rel_img_path}")
        else:
            print(f"[EXPORT] Skipping image download for {sample_id} (no bytes available)")

        row = {
            "sample_id": sample_id,
            "relative_image_path": rel_img_path,
            "predicted_text": item.get("predicted_text", ""),
            "verified_text_raw": item.get("verified_text_raw", ""),
            "verdict": item.get("verdict", ""),
            "source": item.get("source", ""),
            "model_version": item.get("model_version", "1.0.0"),
            "checkpoint_sha256": item.get("checkpoint_sha256", ""),
            "image_sha256": item.get("image_sha256", ""),
            "created_at": item.get("created_at", ""),
            "feedback_at": item.get("feedback_at", ""),
        }
        manifest_rows.append(row)

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
Total Verified Samples: {len(manifest_rows)}

## Provenance
- Target Model: Vietnamese Handwriting CRNN (best_cer.pth)
- Training Eligibility: Explicit human verification only (verdict in [CORRECT, CORRECTED])
- De-identification: Line crops only; all personal identifiers and unmasked regions stripped client-side.
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
    args = parser.parse_args()

    out_root = Path(args.out_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    export_dataset(out_root)
