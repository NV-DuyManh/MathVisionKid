"""
Human Review tool for AI-generated OCR line labels.

Actions:
  - [A]ccept: mark label as VERIFIED
  - [E]dit & Accept: input human corrected text and mark as VERIFIED
  - [R]eject: mark as REJECTED (noise / unreadable crop)
  - [S]kip: leave as NEEDS_REVIEW for later
  - [AUTO / ALL]: Batch accept remaining valid prelabels

Usage:
    python tools/review_labels.py --input data/manifests/validated_prelabels.jsonl --output data/manifests/verified_labels.jsonl
    python tools/review_labels.py --auto_accept   # Non-interactive headless mode for automated pipeline
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def review_labels_cli(
    input_manifest: Path,
    output_verified_manifest: Path,
    auto_accept: bool = False,
) -> List[Dict[str, Any]]:
    print("=" * 70)
    print("             MATHVISION HUMAN REVIEW LABEL TOOL")
    print("=" * 70)
    print(f"Input manifest  : {input_manifest}")
    print(f"Output manifest : {output_verified_manifest}")
    print(f"Mode            : {'Automated / Headless' if auto_accept else 'Interactive CLI'}")

    if not input_manifest.is_file():
        raise FileNotFoundError(f"Input manifest not found: {input_manifest}")

    records = []
    with open(input_manifest, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    print(f"Loaded {len(records)} records for review.")

    verified_records = []
    accepted_all = auto_accept

    for idx, rec in enumerate(records, 1):
        crop_path = rec.get("crop_path", "")
        current_text = rec.get("text", rec.get("raw_prelabel", ""))
        current_status = rec.get("status", "READY_FOR_REVIEW")
        reason = rec.get("validation_reason", "")

        if accepted_all:
            if current_status in ["READY_FOR_REVIEW", "VERIFIED", "RAW_PRELABEL"] and current_text.strip():
                rec["status"] = "VERIFIED"
                rec["reviewed_text"] = current_text
                rec["reviewer"] = "AUTO_ACCEPTED"
                verified_records.append(rec)
            continue

        print("\n" + "-" * 60)
        print(f"[{idx}/{len(records)}] Crop : {crop_path}")
        print(f"Status : {current_status} | Reason: {reason}")
        print(f"AI Text: \"{current_text}\"")
        print("-" * 60)

        choice = input("[A]ccept / [E]dit / [R]eject / [S]kip / [ALL] accept remaining / [Q]uit: ").strip().lower()

        if choice in ["a", ""]:
            rec["status"] = "VERIFIED"
            rec["reviewed_text"] = current_text
            rec["reviewer"] = "HUMAN"
            verified_records.append(rec)
            print("  -> ACCEPTED")

        elif choice == "e":
            new_text = input(f"Enter corrected text (current: \"{current_text}\"): ").strip()
            if new_text:
                rec["status"] = "VERIFIED"
                rec["reviewed_text"] = new_text
                rec["text"] = new_text
                rec["reviewer"] = "HUMAN_EDITED"
                verified_records.append(rec)
                print(f"  -> EDITED & ACCEPTED: \"{new_text}\"")
            else:
                print("  -> Edit cancelled, skipping.")

        elif choice == "r":
            rec["status"] = "REJECTED"
            rec["reviewer"] = "HUMAN"
            print("  -> REJECTED")

        elif choice == "all":
            accepted_all = True
            rec["status"] = "VERIFIED"
            rec["reviewed_text"] = current_text
            rec["reviewer"] = "AUTO_ACCEPTED"
            verified_records.append(rec)
            print("  -> ACCEPTED ALL REMAINING")

        elif choice == "q":
            print("Exiting review tool.")
            break
        else:
            print("  -> SKIPPED")

    output_verified_manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(output_verified_manifest, "w", encoding="utf-8") as f:
        for r in verified_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n" + "=" * 70)
    print(f"Review session completed. Total VERIFIED: {len(verified_records)}")
    print(f"Saved to: {output_verified_manifest}")
    print("=" * 70)
    return verified_records


def main():
    parser = argparse.ArgumentParser(description="Human label review tool.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/manifests/validated_prelabels.jsonl",
        help="Path to validated prelabels manifest",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/manifests/verified_labels.jsonl",
        help="Path to output verified manifest",
    )
    parser.add_argument(
        "--auto_accept",
        action="store_true",
        help="Auto-accept all valid prelabels without prompt",
    )

    args = parser.parse_args()
    review_labels_cli(
        input_manifest=Path(args.input).resolve(),
        output_verified_manifest=Path(args.output).resolve(),
        auto_accept=args.auto_accept,
    )


if __name__ == "__main__":
    main()
