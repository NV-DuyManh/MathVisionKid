"""
Script to generate colab/MathVision_OCR_Finetune.ipynb with exactly 24 ordered cells.
"""
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent

cells = []

def add_cell(cell_type, source_lines, header=""):
    full_source = []
    if header:
        full_source.append(f"# {header}\n")
    for line in source_lines:
        full_source.append(line if line.endswith("\n") else line + "\n")
    cells.append({
        "cell_type": cell_type,
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": full_source,
    })

# CELL 1
add_cell("code", [
    "!pip install -q torch torchvision torchaudio opencv-python pillow pyyaml requests",
    "print('✓ Dependencies installed successfully.')",
], "CELL 1: Install dependencies")

# CELL 2
add_cell("code", [
    "import sys, os, torch",
    "print(f'Python Version : {sys.version}')",
    "print(f'PyTorch Version: {torch.__version__}')",
    "print(f'CUDA Available : {torch.cuda.is_available()}')",
    "if torch.cuda.is_available():",
    "    print(f'GPU Device Name: {torch.cuda.get_device_name(0)}')",
    "    print(f'Total VRAM     : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB')",
    "else:",
    "    print('[WARN] No GPU detected. Make sure to select T4 GPU in Runtime > Change runtime type.')",
], "CELL 2: Check Python / PyTorch / CUDA / GPU")

# CELL 3
add_cell("code", [
    "from google.colab import drive",
    "import os",
    "if not os.path.exists('/content/drive/MyDrive'):",
    "    drive.mount('/content/drive')",
    "    print('✓ Google Drive mounted at /content/drive')",
    "else:",
    "    print('✓ Google Drive already mounted at /content/drive')",
], "CELL 3: Mount Google Drive")

# CELL 4
add_cell("code", [
    "!python scripts/discover_drive_dataset.py --drive_root /content/drive/MyDrive/C1SE.01 --config configs/dataset.yaml",
], "CELL 4: Discover C1SE.01")

# CELL 5
add_cell("code", [
    "import json",
    "inv_path = 'artifacts/reports/drive_inventory.json'",
    "with open(inv_path, 'r', encoding='utf-8') as f:",
    "    inv = json.load(f)",
    "print('Drive Inventory Status:', inv.get('status'))",
    "print('Total Images Discovered:', inv.get('total_images_found', 0))",
    "for p in inv.get('existing_paths', []):",
    "    print('  ✓ Existing path:', p)",
    "for p in inv.get('missing_paths', []):",
    "    print('  ✗ Missing path :', p)",
], "CELL 5: Generate drive_inventory.json")

# CELL 6
add_cell("code", [
    "!python scripts/inspect_checkpoint.py --output artifacts/reports/checkpoint_audit.json",
], "CELL 6: Audit model")

# CELL 7
add_cell("code", [
    "!python scripts/audit_vocab.py --output_vocab configs/unified_vocab.json --output_report artifacts/reports/vocab_audit.json",
], "CELL 7: Audit vocab")

# CELL 8
add_cell("code", [
    "!python scripts/segment_lines.py --config configs/crop.yaml --output_crops data/crops --output_debug artifacts/crop_debug",
], "CELL 8: Build line crops")

# CELL 9
add_cell("code", [
    "!python scripts/validate_crops.py --crops_dir data/crops --config configs/crop.yaml --output artifacts/reports/crop_report.json",
], "CELL 9: Run quality gate")

# CELL 10
add_cell("code", [
    "# Prelabel bằng Qwen 3 VL Plus (qwen-vl-plus API / DashScope)",
    "!python labeling/labeling_pipeline.py --crops_dir data/crops --config configs/labeling.yaml --output data/manifests/raw_prelabels.jsonl",
], "CELL 10: Prelabel bằng Qwen 3 VL Plus")

# CELL 11
add_cell("code", [
    "!python scripts/validate_prelabels.py --input data/manifests/raw_prelabels.jsonl --vocab configs/unified_vocab.json --config configs/labeling.yaml --output data/manifests/validated_prelabels.jsonl",
], "CELL 11: Validate labels")

# CELL 12
add_cell("code", [
    "# Human review: automated acceptance for batch pipeline or interactive review",
    "!python tools/review_labels.py --input data/manifests/validated_prelabels.jsonl --output data/manifests/verified_labels.jsonl --auto_accept",
], "CELL 12: Human review")

# CELL 13
add_cell("code", [
    "!python scripts/prepare_dataset.py --input data/manifests/verified_labels.jsonl --output data/manifests/unified_dataset.jsonl",
], "CELL 13: Build verified manifest")

# CELL 14
add_cell("code", [
    "!python scripts/split_dataset.py --input data/manifests/unified_dataset.jsonl --config configs/dataset.yaml --output_dir data/manifests --report artifacts/reports/split_report.json",
], "CELL 14: Split dataset")

# CELL 15
add_cell("code", [
    "import json",
    "with open('artifacts/reports/split_report.json', 'r', encoding='utf-8') as f:",
    "    rep = json.load(f)",
    "audit = rep.get('leakage_audit', {})",
    "print('Zero Leakage Verified:', audit.get('zero_leakage_verified'))",
    "print(f'Train Count: {rep.get(\"train_count\")}, Val Count: {rep.get(\"val_count\")}, Test Count: {rep.get(\"test_count\")}')",
], "CELL 15: Leakage audit")

# CELL 16
add_cell("code", [
    "!python scripts/adapt_checkpoint.py --output_checkpoint artifacts/checkpoints/adapted_init.pth --output_report artifacts/reports/adaptation_report.json",
], "CELL 16: Adapt checkpoint")

# CELL 17
add_cell("code", [
    "!python training/train_finetune.py --smoke_test --config configs/train_finetune.yaml --train_manifest data/manifests/train.jsonl --val_manifest data/manifests/val.jsonl",
], "CELL 17: Smoke training")

# CELL 18
add_cell("code", [
    "!python training/train_finetune.py --config configs/train_finetune.yaml --train_manifest data/manifests/train.jsonl --val_manifest data/manifests/val.jsonl",
], "CELL 18: Full fine-tuning")

# CELL 19
add_cell("code", [
    "!python scripts/evaluate.py --checkpoint artifacts/checkpoints/best_cer.pth --vocab configs/unified_vocab.json --manifest data/manifests/val.jsonl --output_report artifacts/reports/evaluation_report.json",
], "CELL 19: Validation")

# CELL 20
add_cell("code", [
    "import json",
    "with open('artifacts/reports/evaluation_report.json', 'r', encoding='utf-8') as f:",
    "    ev = json.load(f)",
    "metrics = ev.get('metrics', {})",
    "print('=== BASELINE A (best_cer.pth) Benchmark Evaluation ===')",
    "print(f'  Overall CER       : {metrics.get(\"cer\"):.4f}')",
    "print(f'  Exact Match       : {metrics.get(\"exact_match\"):.4f}')",
    "print(f'  Digit Accuracy    : {metrics.get(\"digit_accuracy\"):.4f}')",
    "print(f'  Operator Accuracy : {metrics.get(\"operator_accuracy\"):.4f}')",
    "print(f'  Vietnamese Acc    : {metrics.get(\"vietnamese_accuracy\"):.4f}')",
], "CELL 20: Benchmark baseline")

# CELL 21
add_cell("code", [
    "!python scripts/export_model.py",
], "CELL 21: Export best model")

# CELL 22
add_cell("code", [
    "import os, shutil, glob",
    "from datetime import datetime",
    "drive_base = '/content/drive/MyDrive/MathVisionKid_AI/checkpoints'",
    "if os.path.exists('/content/drive/MyDrive'):",
    "    ts = datetime.now().strftime('%Y%m%d_%H%M%S')",
    "    run_dir = os.path.join(drive_base, f'run_{ts}')",
    "    os.makedirs(run_dir, exist_ok=True)",
    "    export_dir = 'artifacts/export/ocr_vi_math_line_v1'",
    "    for item in os.listdir(export_dir):",
    "        src = os.path.join(export_dir, item)",
    "        dst = os.path.join(run_dir, item)",
    "        if os.path.isfile(src):",
    "            shutil.copy2(src, dst)",
    "    print(f'✓ Best model and manifests backed up to Drive: {run_dir}')",
    "else:",
    "    print('[LOCAL NOTE] Drive not mounted, backup simulated locally.')",
], "CELL 22: Backup checkpoint về Drive")

# CELL 23
add_cell("code", [
    "import sys, glob",
    "sys.path.insert(0, 'artifacts/export/ocr_vi_math_line_v1')",
    "from predict import predict_text, predict_batch",
    "crops = glob.glob('data/crops/*.png')",
    "if crops:",
    "    print('Testing single inference on first crop:', crops[0])",
    "    res = predict_text(crops[0])",
    "    print(f'  -> Recognized Text: \"{res}\"')",
    "    print('Testing batch inference on 3 crops...')",
    "    b_res = predict_batch(crops[:3], batch_size=2)",
    "    for i, t in enumerate(b_res):",
    "        print(f'  [{i+1}] \"{t}\"')",
    "else:",
    "    print('No crop images found to test inference.')",
], "CELL 23: Test inference")

# CELL 24
add_cell("code", [
    "import json",
    "with open('artifacts/reports/model_selection.json', 'r', encoding='utf-8') as f:",
    "    sel = json.load(f)",
    "print('=================================================================')",
    "print('                FINAL MODEL SELECTION REPORT')",
    "print('=================================================================')",
    "selected = sel.get('selected_model', {})",
    "print(f'Model Name : {selected.get(\"baseline_name\")}')",
    "print(f'Checkpoint : {selected.get(\"checkpoint\")}')",
    "print(f'Parameters : {selected.get(\"parameters\"):,}')",
    "print('Metrics    :', selected.get('metrics'))",
    "print('Reason     :', selected.get('selection_reason'))",
    "print('=================================================================')",
], "CELL 24: Generate final report")

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

out_p = _ROOT / "colab" / "MathVision_OCR_Finetune.ipynb"
out_p.parent.mkdir(parents=True, exist_ok=True)
with open(out_p, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print(f"✓ Successfully created notebook with {len(cells)} cells at: {out_p}")
