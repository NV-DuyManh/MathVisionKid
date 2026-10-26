"""
Validate AI prelabels for hallucinations, descriptions, out-of-vocab tokens, and conversational noise.

Validation Rules:
  - Reject empty texts
  - Flag descriptions / refusals / conversational preambles ("Đây là...", "Không thể đọc...") -> NEEDS_REVIEW
  - Flag excessive character lengths (> max_characters_per_line) -> NEEDS_REVIEW
  - Flag abnormal repetitions (e.g. char repeated > 5 times) -> NEEDS_REVIEW
  - Flag out-of-vocab characters -> NEEDS_REVIEW with character list
  - Valid outputs -> READY_FOR_REVIEW

Usage:
    python scripts/validate_prelabels.py --input data/manifests/raw_prelabels.jsonl --config configs/labeling.yaml
"""
import sys
import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_BANNED_PHRASES = [
    "đây là",
    "hình ảnh",
    "không thể",
    "không đọc",
    "bài toán",
    "lời giải",
    "kết quả là",
    "chính xác là",
    "xin lỗi",
    "tôi không",
    "chữ viết",
    "trong ảnh",
    "hiển thị",
]


def validate_text(
    text: str,
    vocab_set: set,
    v_cfg: Dict[str, Any],
) -> Tuple[str, str, List[str]]:
    """Validate a single transcribed string. Returns (status, reason, out_of_vocab_chars)."""
    text = text.strip()

    # 1. Empty check
    if not text:
        return "REJECTED", "EMPTY_TEXT", []

    # 2. Length checks
    max_len = v_cfg.get("max_characters_per_line", 150)
    min_len = v_cfg.get("min_characters_per_line", 1)
    if len(text) > max_len:
        return "NEEDS_REVIEW", f"EXCESSIVELY_LONG (length={len(text)}>{max_len})", []
    if len(text) < min_len:
        return "REJECTED", "TOO_SHORT", []

    # 3. Conversational / Hallucination / Description check
    lower_text = text.lower()
    banned = v_cfg.get("banned_phrases", DEFAULT_BANNED_PHRASES)
    for phrase in banned:
        if phrase in lower_text:
            return "NEEDS_REVIEW", f"DESCRIPTION_OR_CONVERSATIONAL ('{phrase}' detected)", []

    # 4. Abnormal character repetition check (e.g. "aaaaaa", "111111", "......")
    max_repeat = v_cfg.get("max_char_repeat", 5)
    repeat_pattern = re.compile(rf"(.)\1{{{max_repeat},}}")
    if repeat_pattern.search(text):
        match = repeat_pattern.search(text).group(0)
        return "NEEDS_REVIEW", f"ABNORMAL_REPETITION ('{match[:6]}...')", []

    # 5. Out-of-vocab characters check
    if vocab_set:
        oov_chars = [c for c in text if c not in vocab_set]
        if oov_chars:
            unique_oov = sorted(list(set(oov_chars)))
            return "NEEDS_REVIEW", f"OUT_OF_VOCAB_CHARS ({unique_oov})", unique_oov

    return "READY_FOR_REVIEW", "PASSED_VALIDATION_RULES", []


def run_label_validation(
    input_manifest: Path,
    vocab_path: Path,
    config_path: Path,
    output_validated_manifest: Path,
    output_report_path: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("          MATHVISION PRELABEL VALIDATION PIPELINE")
    print("=" * 70)
    print(f"Input manifest   : {input_manifest}")
    print(f"Vocab path       : {vocab_path}")

    v_cfg = {}
    if config_path.is_file():
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            v_cfg = yaml.safe_load(f).get("validation", {})

    vocab_set = set()
    if vocab_path.is_file():
        with open(vocab_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
            vocab_set = set(v_data.keys())
        print(f"Loaded vocabulary with {len(vocab_set)} tokens.")

    if not input_manifest.is_file():
        raise FileNotFoundError(f"Input manifest not found: {input_manifest}")

    records = []
    with open(input_manifest, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    print(f"Validating {len(records)} raw prelabel records...")

    ready_count = 0
    needs_review_count = 0
    rejected_count = 0
    validated_records = []

    output_validated_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(output_validated_manifest, "w", encoding="utf-8") as out_f:
        for rec in records:
            raw_text = rec.get("raw_prelabel", rec.get("text", ""))
            status, reason, oov = validate_text(raw_text, vocab_set, v_cfg)

            if status == "READY_FOR_REVIEW":
                ready_count += 1
            elif status == "NEEDS_REVIEW":
                needs_review_count += 1
            else:
                rejected_count += 1

            validated_rec = dict(rec)
            validated_rec["status"] = status
            validated_rec["validation_reason"] = reason
            validated_rec["out_of_vocab_chars"] = oov
            validated_rec["text"] = raw_text

            validated_records.append(validated_rec)
            out_f.write(json.dumps(validated_rec, ensure_ascii=False) + "\n")

    print("\n" + "=" * 70)
    print("              VALIDATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total Evaluated       : {len(records)}")
    print(f"  Ready for Review      : {ready_count}")
    print(f"  Needs Human Review    : {needs_review_count}")
    print(f"  Rejected (Empty/Junk) : {rejected_count}")
    print("=" * 70)

    report = {
        "status": "PASS",
        "total_evaluated": len(records),
        "ready_for_review_count": ready_count,
        "needs_review_count": needs_review_count,
        "rejected_count": rejected_count,
        "validated_manifest": str(output_validated_manifest),
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Validation report saved to: {output_report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Validate prelabels for quality and vocabulary compliance.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/manifests/raw_prelabels.jsonl",
        help="Path to raw prelabels jsonl",
    )
    parser.add_argument(
        "--vocab",
        type=str,
        default="configs/unified_vocab.json",
        help="Path to unified vocab json",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/labeling.yaml",
        help="Path to labeling config YAML",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/manifests/validated_prelabels.jsonl",
        help="Path to output validated labels jsonl",
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="artifacts/reports/label_validation_report.json",
        help="Path to output report json",
    )

    args = parser.parse_args()
    run_label_validation(
        input_manifest=Path(args.input).resolve(),
        vocab_path=Path(args.vocab).resolve(),
        config_path=Path(args.config).resolve(),
        output_validated_manifest=Path(args.output).resolve(),
        output_report_path=Path(args.output_report).resolve(),
    )


if __name__ == "__main__":
    main()
