"""
Audit vocabulary and build unified vocabulary for MathVision Kids line-level OCR.

Usage:
    python scripts/audit_vocab.py
    python scripts/audit_vocab.py --vocab handoff/staging/ocr_engine_handoff_final/ocr_engine/vocab.json --output configs/unified_vocab.json
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


VIETNAMESE_LOWER = (
    "aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvxyỳýỷỹỵ"
)
VIETNAMESE_UPPER = VIETNAMESE_LOWER.upper()

DIGITS = "0123456789"

MATH_OPERATORS_REQUIRED = [
    "+", "-", "×", "x", "*", "/", ":", "=", "÷", "<", ">", "≤", "≥", "≠", "±"
]

MATH_SPECIALS_REQUIRED = [
    "%", "°", "²", "³", "¹", "⁴"
]

PUNCTUATION_REQUIRED = [
    ".", ",", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "-", "–", "\"", "'", "/", " "
]

# Sample target strings reflecting primary school curriculum
TARGET_TASK_STRINGS = [
    "Thời gian xe chạy là: 7 giờ 45 phút - 6 giờ 30 phút = 1 giờ 15 phút",
    "55 x 3 = 165 (km)",
    "55 × 3 = 165 (km)",
    "Đáp số: 165 km",
    "12,5 + 3,75 = 16,25 (kg)",
    "45 : 5 = 9 (m/s)",
    "Diện tích hình chữ nhật là: 12 x 8 = 96 (cm²)",
    "Thể tích khối hộp là: 5 x 4 x 3 = 60 (m³)",
    "Góc A bằng 45°",
    "Tỉ số phần trăm là: 25%",
    "Phân số: 1/2 + 3/4 = 5/4",
    "Bài giải",
    "Chu vi hình tròn là: 2 x 3,14 x 5 = 31,4 (dm)",
    "Vận tốc ô tô là: 120 : 2 = 60 (km/giờ)",
    "100 ÷ 4 = 25",
]


def audit_vocab(
    vocab_path: Path,
    target_manifests: List[Path],
    output_unified_vocab_path: Path,
    output_report_path: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("        MATHVISION OCR VOCABULARY AUDIT & UNIFICATION")
    print("=" * 70)
    print(f"Source vocab: {vocab_path}")

    if not vocab_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] vocab file not found: {vocab_path}")

    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    old_vocab_size = len(vocab)
    print(f"Current vocabulary size: {old_vocab_size}")

    # 1. Categorize current vocab
    blank_present = "<blank>" in vocab
    digits_present = [d for d in DIGITS if d in vocab]
    viet_lower_present = [c for c in VIETNAMESE_LOWER if c in vocab]
    viet_upper_present = [c for c in VIETNAMESE_UPPER if c in vocab]

    print(f"\n[1] Current Token Coverage:")
    print(f"  Blank token index : {vocab.get('<blank>')}")
    print(f"  Digits present    : {len(digits_present)}/{len(DIGITS)}")
    print(f"  Vietnamese lower  : {len(viet_lower_present)}/{len(VIETNAMESE_LOWER)}")
    print(f"  Vietnamese upper  : {len(viet_upper_present)}/{len(VIETNAMESE_UPPER)}")

    # 2. Gather all target characters required for MathVision Kids
    required_chars: Set[str] = set()
    for s in TARGET_TASK_STRINGS:
        required_chars.update(list(s))
    for op in MATH_OPERATORS_REQUIRED:
        required_chars.update(list(op))
    for sp in MATH_SPECIALS_REQUIRED:
        required_chars.update(list(sp))
    for p in PUNCTUATION_REQUIRED:
        required_chars.update(list(p))
    for c in VIETNAMESE_LOWER:
        required_chars.add(c)
    for c in VIETNAMESE_UPPER:
        required_chars.add(c)
    for d in DIGITS:
        required_chars.add(d)

    # Also scan any provided manifests
    for manifest_path in target_manifests:
        if manifest_path.is_file():
            print(f"Scanning target manifest: {manifest_path}")
            with open(manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        text = record.get("text", "")
                        required_chars.update(list(text))
                    except Exception:
                        pass

    # 3. Check for missing characters
    missing_chars = [c for c in sorted(required_chars) if c not in vocab]
    print(f"\n[2] Required Characters Audit:")
    print(f"  Total required unique characters: {len(required_chars)}")
    print(f"  Missing from current vocab       : {len(missing_chars)}")
    if missing_chars:
        print(f"  Missing character list           : {missing_chars}")
        for c in missing_chars:
            print(f"    - Char '{c}' (U+{ord(c):04X})")
    else:
        print("  ✓ All required characters already exist in current vocab!")

    # 4. Generate Unified Vocab
    # PRESERVE 100% of existing tokens at their exact current indices
    unified_vocab = dict(vocab)
    next_idx = old_vocab_size

    if missing_chars:
        print(f"\n[3] Generating Unified Vocabulary (appending {len(missing_chars)} tokens)...")
        for c in missing_chars:
            unified_vocab[c] = next_idx
            print(f"  Added '{c}' (U+{ord(c):04X}) -> index {next_idx}")
            next_idx += 1
    else:
        print("\n[3] Vocab already complete, keeping existing indices.")

    new_vocab_size = len(unified_vocab)
    print(f"  Final Unified Vocab Size: {new_vocab_size} (Original: {old_vocab_size}, Added: {new_vocab_size - old_vocab_size})")

    # Save unified_vocab.json
    output_unified_vocab_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_unified_vocab_path, "w", encoding="utf-8") as f:
        json.dump(unified_vocab, f, indent=2, ensure_ascii=False)
    print(f"  Unified vocab saved to: {output_unified_vocab_path}")

    # Build audit report
    report = {
        "status": "PASS",
        "original_vocab_size": old_vocab_size,
        "unified_vocab_size": new_vocab_size,
        "blank_index": vocab.get("<blank>"),
        "digits_coverage": f"{len(digits_present)}/{len(DIGITS)}",
        "vietnamese_lower_coverage": f"{len(viet_lower_present)}/{len(VIETNAMESE_LOWER)}",
        "vietnamese_upper_coverage": f"{len(viet_upper_present)}/{len(VIETNAMESE_UPPER)}",
        "missing_characters_count": len(missing_chars),
        "missing_characters": missing_chars,
        "added_tokens_mapping": {c: unified_vocab[c] for c in missing_chars},
        "target_task_symbols": {
            "math_operators": {op: (op in unified_vocab) for op in MATH_OPERATORS_REQUIRED},
            "math_specials": {sp: (sp in unified_vocab) for sp in MATH_SPECIALS_REQUIRED},
            "common_units_supported": True,
        },
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Vocab audit report saved to: {output_report_path}")
    print("=" * 70)
    return report


def main():
    parser = argparse.ArgumentParser(description="Audit and unify OCR vocabulary.")
    parser.add_argument(
        "--vocab",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/vocab.json",
        help="Path to source vocab.json",
    )
    parser.add_argument(
        "--manifests",
        nargs="*",
        default=[],
        help="Optional paths to target .jsonl manifests to scan",
    )
    parser.add_argument(
        "--output_vocab",
        type=str,
        default="configs/unified_vocab.json",
        help="Path to save unified vocab",
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="artifacts/reports/vocab_audit.json",
        help="Path to save audit report JSON",
    )

    args = parser.parse_args()
    manifest_paths = [Path(p).resolve() for p in args.manifests]
    audit_vocab(
        vocab_path=Path(args.vocab).resolve(),
        target_manifests=manifest_paths,
        output_unified_vocab_path=Path(args.output_vocab).resolve(),
        output_report_path=Path(args.output_report).resolve(),
    )


if __name__ == "__main__":
    main()
