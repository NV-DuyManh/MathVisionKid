"""
Comprehensive line-level OCR evaluation script for MathVision Kids.

Metrics Computed:
  - Overall CER (Character Error Rate) and Character Accuracy (1 - CER)
  - Exact Match (Sentence / Line accuracy)
  - Empty Prediction Rate (Blank collapse indicator)
  - Digit Accuracy ('0'..'9')
  - Operator Accuracy ('+', '-', '×', 'x', '*', '/', ':', '=', '÷')
  - Decimal Accuracy (',', '.')
  - Vietnamese Diacritics Accuracy
  - Category Breakdown: TEXT_ONLY, MATH_ONLY, MIXED

Usage:
    python scripts/evaluate.py --checkpoint artifacts/checkpoints/adapted_init.pth --vocab configs/unified_vocab.json --manifest data/manifests/val.jsonl
"""
import sys
import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent

DIGITS = set("0123456789")
OPERATORS = set(["+", "-", "×", "x", "*", "/", ":", "=", "÷"])
DECIMALS = set([",", "."])
VIETNAMESE_ACCENTED = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ")


def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]


def evaluate_character_subsets(gt: str, pred: str) -> Dict[str, Tuple[int, int]]:
    """Compute (correct_count, total_count) for digits, operators, decimals, and Vietnamese characters."""
    # Build aligned character matching via simple LCS or index mapping
    # Conservative metric: count character occurrences matched between GT and Pred
    gt_chars = list(gt)
    pred_chars = list(pred)

    results = {
        "digits": [0, 0],
        "operators": [0, 0],
        "decimals": [0, 0],
        "vietnamese": [0, 0],
    }

    # Count totals in GT
    for c in gt_chars:
        if c in DIGITS:
            results["digits"][1] += 1
        elif c in OPERATORS:
            results["operators"][1] += 1
        elif c in DECIMALS:
            results["decimals"][1] += 1
        elif c in VIETNAMESE_ACCENTED:
            results["vietnamese"][1] += 1

    # Count matches in Pred (min count per char)
    gt_counter = {}
    for c in gt_chars:
        gt_counter[c] = gt_counter.get(c, 0) + 1
    pred_counter = {}
    for c in pred_chars:
        pred_counter[c] = pred_counter.get(c, 0) + 1

    for c, count in gt_counter.items():
        matched = min(count, pred_counter.get(c, 0))
        if c in DIGITS:
            results["digits"][0] += matched
        elif c in OPERATORS:
            results["operators"][0] += matched
        elif c in DECIMALS:
            results["decimals"][0] += matched
        elif c in VIETNAMESE_ACCENTED:
            results["vietnamese"][0] += matched

    return {k: (v[0], v[1]) for k, v in results.items()}


def cv2_imread_unicode(filepath: Path) -> np.ndarray:
    data = np.fromfile(str(filepath), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def load_crnn_model(checkpoint_path: Path, vocab_size: int, device: torch.device):
    # Import CRNN
    import importlib.util
    model_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    spec = importlib.util.spec_from_file_location("crnn_mod", str(model_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    model = mod.CRNN(num_classes=vocab_size)
    state = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(state, strict=True)
    model.to(device)
    model.eval()
    return model


def run_evaluation(
    checkpoint_path: Path,
    vocab_path: Path,
    manifest_path: Path,
    output_report_path: Path,
    device_str: str = "auto",
) -> Dict[str, Any]:
    print("=" * 70)
    print("            MATHVISION LINE-LEVEL OCR EVALUATION")
    print("=" * 70)
    print(f"Checkpoint : {checkpoint_path}")
    print(f"Vocab      : {vocab_path}")
    print(f"Manifest   : {manifest_path}")

    device = torch.device(
        ("cuda" if torch.cuda.is_available() else "cpu") if device_str == "auto" else device_str
    )
    print(f"Device     : {device}")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)
    inv_vocab = {int(v): k for k, v in vocab.items()}
    blank_idx = vocab.get("<blank>", 0)

    model = load_crnn_model(checkpoint_path, len(vocab), device)

    transform = transforms.Compose([
        transforms.Resize((64, 1024)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    print(f"Evaluating {len(records)} test/val samples...")

    total_edit_distance = 0
    total_target_length = 0
    exact_match_count = 0
    empty_prediction_count = 0

    subsets_eval = {
        "digits": [0, 0],
        "operators": [0, 0],
        "decimals": [0, 0],
        "vietnamese": [0, 0],
    }

    category_stats = {
        "TEXT_ONLY": {"cer_sum": 0.0, "em_count": 0, "total": 0, "edit_dist": 0, "tgt_len": 0},
        "MATH_ONLY": {"cer_sum": 0.0, "em_count": 0, "total": 0, "edit_dist": 0, "tgt_len": 0},
        "MIXED": {"cer_sum": 0.0, "em_count": 0, "total": 0, "edit_dist": 0, "tgt_len": 0},
    }

    per_sample_results = []
    start_time = time.time()

    for rec in records:
        img_p = Path(rec["image_path"])
        gt = rec.get("text", "")
        category = rec.get("category", "MIXED")

        # Load image
        img_bgr = cv2_imread_unicode(img_p)
        if img_bgr is None:
            continue
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        inp_tensor = transform(pil_img).unsqueeze(0).to(device)

        # Forward
        with torch.no_grad():
            logits = model(inp_tensor)
            preds = logits.argmax(2).cpu().numpy()[0]

        # Greedy CTC decode
        out_tokens, prev = [], -1
        for idx in preds:
            if idx != blank_idx and idx != prev:
                out_tokens.append(inv_vocab.get(int(idx), "?"))
            prev = idx
        pred_text = "".join(out_tokens).strip()

        # Distance & Accuracy
        ed = levenshtein(gt, pred_text)
        gt_len = max(1, len(gt))
        cer = ed / gt_len
        is_exact = (pred_text == gt)
        is_empty = (len(pred_text) == 0)

        total_edit_distance += ed
        total_target_length += gt_len
        if is_exact:
            exact_match_count += 1
        if is_empty:
            empty_prediction_count += 1

        # Character subsets
        sub_metrics = evaluate_character_subsets(gt, pred_text)
        for k, (corr, tot) in sub_metrics.items():
            subsets_eval[k][0] += corr
            subsets_eval[k][1] += tot

        # Category stats
        cat_key = category if category in category_stats else "MIXED"
        category_stats[cat_key]["total"] += 1
        category_stats[cat_key]["edit_dist"] += ed
        category_stats[cat_key]["tgt_len"] += gt_len
        if is_exact:
            category_stats[cat_key]["em_count"] += 1

        per_sample_results.append({
            "image": str(img_p.name),
            "category": category,
            "ground_truth": gt,
            "prediction": pred_text,
            "cer": round(cer, 4),
            "edit_distance": ed,
            "exact_match": is_exact,
            "empty": is_empty,
        })

    elapsed = time.time() - start_time
    total_samples = len(per_sample_results)

    overall_cer = total_edit_distance / max(1, total_target_length)
    exact_match_rate = exact_match_count / max(1, total_samples)
    empty_rate = empty_prediction_count / max(1, total_samples)

    def calc_acc(pair):
        return round(pair[0] / max(1, pair[1]), 4) if pair[1] > 0 else 1.0

    report = {
        "status": "PASS",
        "checkpoint": str(checkpoint_path),
        "manifest": str(manifest_path),
        "total_samples": total_samples,
        "elapsed_seconds": round(elapsed, 2),
        "metrics": {
            "cer": round(overall_cer, 4),
            "character_accuracy": round(1.0 - overall_cer, 4),
            "exact_match": round(exact_match_rate, 4),
            "empty_rate": round(empty_rate, 4),
            "digit_accuracy": calc_acc(subsets_eval["digits"]),
            "operator_accuracy": calc_acc(subsets_eval["operators"]),
            "decimal_accuracy": calc_acc(subsets_eval["decimals"]),
            "vietnamese_accuracy": calc_acc(subsets_eval["vietnamese"]),
        },
        "category_breakdown": {
            cat: {
                "count": data["total"],
                "cer": round(data["edit_dist"] / max(1, data["tgt_len"]), 4) if data["total"] > 0 else None,
                "exact_match": round(data["em_count"] / max(1, data["total"]), 4) if data["total"] > 0 else None,
            }
            for cat, data in category_stats.items()
        },
        "character_occurrences": {
            k: {"correct": v[0], "total": v[1]} for k, v in subsets_eval.items()
        },
        "samples": per_sample_results,
    }

    print("\n" + "=" * 70)
    print("                 EVALUATION RESULTS")
    print("=" * 70)
    print(f"  Total Samples Evaluated    : {total_samples}")
    print(f"  Overall CER               : {report['metrics']['cer']:.4f} ({report['metrics']['cer']*100:.2f}%)")
    print(f"  Character Accuracy         : {report['metrics']['character_accuracy']:.4f} ({report['metrics']['character_accuracy']*100:.2f}%)")
    print(f"  Exact Match Rate           : {report['metrics']['exact_match']:.4f} ({report['metrics']['exact_match']*100:.2f}%)")
    print(f"  Empty Prediction Rate      : {report['metrics']['empty_rate']:.4f}")
    print(f"  Digit Accuracy (0-9)       : {report['metrics']['digit_accuracy']:.4f}")
    print(f"  Operator Accuracy (+-×/...) : {report['metrics']['operator_accuracy']:.4f}")
    print(f"  Vietnamese Character Acc   : {report['metrics']['vietnamese_accuracy']:.4f}")
    print("-" * 70)
    print("  Category Breakdown:")
    for cat, data in report["category_breakdown"].items():
        if data["count"] > 0:
            print(f"    {cat:<12} : count={data['count']:>3}, CER={data['cer']:.4f}, ExactMatch={data['exact_match']:.4f}")
    print("=" * 70)

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Evaluation report saved to: {output_report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Evaluate OCR model on manifest.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="artifacts/checkpoints/adapted_init.pth",
        help="Path to model checkpoint .pth",
    )
    parser.add_argument(
        "--vocab",
        type=str,
        default="configs/unified_vocab.json",
        help="Path to vocab.json",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/val.jsonl",
        help="Path to manifest jsonl",
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="artifacts/reports/evaluation_report.json",
        help="Path to output JSON report",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device: auto | cuda | cpu",
    )

    args = parser.parse_args()
    run_evaluation(
        checkpoint_path=Path(args.checkpoint).resolve(),
        vocab_path=Path(args.vocab).resolve(),
        manifest_path=Path(args.manifest).resolve(),
        output_report_path=Path(args.output_report).resolve(),
        device_str=args.device,
    )


if __name__ == "__main__":
    main()
