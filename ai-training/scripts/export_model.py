"""
Export the best fine-tuned MathVision Kids Line OCR model package.

Target Directory:
  artifacts/export/ocr_vi_math_line_v1/

Exported Package Contents:
  - best_cer.pth (Weights)
  - model.py (Architecture)
  - vocab.json (Vocabulary mapping)
  - predict.py (Standalone inference module)
  - config.yaml (Training/inference configuration)
  - model_manifest.json (Metadata, checksums, and contracts)
  - requirements.txt (Dependencies)
  - sample_predictions.json (Sample inference verification)
  - evaluation_report.json (Validation metrics)

Usage:
    python scripts/export_model.py
"""
import sys
import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def export_model_package(
    checkpoint_src: Path,
    vocab_src: Path,
    config_src: Path,
    eval_report_src: Path,
    export_dir: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("        MATHVISION OCR MODEL EXPORT & PACKAGING")
    print("=" * 70)
    print(f"Export directory: {export_dir}")

    export_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy Model Checkpoint
    ckpt_dest = export_dir / "best_cer.pth"
    if not checkpoint_src.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_src}")
    shutil.copy2(checkpoint_src, ckpt_dest)

    # 2. Copy Vocab
    vocab_dest = export_dir / "vocab.json"
    shutil.copy2(vocab_src, vocab_dest)

    # 3. Copy Architecture model.py
    model_src = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    model_dest = export_dir / "model.py"
    shutil.copy2(model_src, model_dest)

    # 4. Copy Standalone predict.py
    predict_src = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "predict.py"
    predict_dest = export_dir / "predict.py"
    shutil.copy2(predict_src, predict_dest)

    # 5. Copy Config
    config_dest = export_dir / "config.yaml"
    if config_src.is_file():
        shutil.copy2(config_src, config_dest)

    # 6. Copy Requirements
    req_src = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "requirements.txt"
    req_dest = export_dir / "requirements.txt"
    if req_src.is_file():
        shutil.copy2(req_src, req_dest)

    # 7. Copy Evaluation Report
    eval_dest = export_dir / "evaluation_report.json"
    if eval_report_src.is_file():
        shutil.copy2(eval_report_src, eval_dest)

    # 8. Compute Checksums
    checksums = {}
    for f in export_dir.iterdir():
        if f.is_file():
            checksums[f.name] = compute_sha256(f)

    # 9. Load Vocab for stats
    with open(vocab_dest, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    # 10. Generate Model Manifest
    manifest = {
        "manifestVersion": "1.2.0",
        "model_name": "MathVision-Kids-Vietnamese-Math-Line-OCR",
        "model_version": "1.0.0",
        "status": "production_candidate",
        "task": "line_level_optical_character_recognition",
        "supported_domains": [
            "Vietnamese handwriting (primary school students)",
            "Accented Vietnamese text (câu lời giải, đáp số)",
            "Arithmetic operations (+, -, ×, x, :, /, =)",
            "Decimal numbers (commas, periods)",
            "Measurement units (m, cm, km, kg, g, giờ, phút, giây, ...)",
            "Exponents and symbols (%, °, ², ³)",
        ],
        "architecture": "CRNN (4-block Conv2d + GroupNorm + BiLSTM(128) + Linear)",
        "framework": "PyTorch",
        "input_channels": 3,
        "input_height": 64,
        "input_width": 1024,
        "vocab_size": len(vocab),
        "blank_index": vocab.get("<blank>", 0),
        "artifacts_sha256": checksums,
        "export_date": "2026-09-21",
    }

    manifest_dest = export_dir / "model_manifest.json"
    with open(manifest_dest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n✓ Exported Package Contents:")
    for fn, sha in checksums.items():
        print(f"  - {fn:<25} : {sha}")

    print(f"\nModel manifest saved to: {manifest_dest}")
    print("=" * 70)
    return manifest


def main():
    export_model_package(
        checkpoint_src=Path("artifacts/checkpoints/best_cer.pth").resolve(),
        vocab_src=Path("configs/unified_vocab.json").resolve(),
        config_src=Path("configs/train_finetune.yaml").resolve(),
        eval_report_src=Path("artifacts/reports/evaluation_report.json").resolve(),
        export_dir=Path("artifacts/export/ocr_vi_math_line_v1").resolve(),
    )


if __name__ == "__main__":
    main()
