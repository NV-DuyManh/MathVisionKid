import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from labeling.qwen3vl_backend import Qwen3VLPlusPrelabeler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_prelabeling_pipeline(
    crops_dir: Path,
    config_path: Path,
    output_manifest_path: Path,
) -> List[Dict[str, Any]]:
    print("=" * 70)
    print("         MATHVISION QWEN 3 VL PLUS PRELABELING PIPELINE")
    print("=" * 70)
    print(f"Crops directory : {crops_dir}")
    print(f"Config path     : {config_path}")

    config = {}
    if config_path.is_file():
        import yaml
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    # Find crop images
    crop_paths = []
    for ext in [".png", ".jpg", ".jpeg", ".bmp"]:
        crop_paths.extend(list(crops_dir.glob(f"*{ext}")))
    crop_paths = sorted(crop_paths)

    print(f"Discovered {len(crop_paths)} line crops to transcribe.")
    if not crop_paths:
        print("[WARN] No crops found in directory. Exiting.")
        return []

    # Initialize backend
    prelabeler = Qwen3VLPlusPrelabeler(config)
    prelabeler.load_model()

    records = []
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_manifest_path, "w", encoding="utf-8") as out_f:
            for idx, crop_p in enumerate(crop_paths, 1):
                raw_text = prelabeler.transcribe_crop(crop_p)
                print(f"  [{idx:03d}/{len(crop_paths):03d}] {crop_p.name} -> \"{raw_text}\"")

                rec = {
                    "crop_path": str(crop_p),
                    "filename": crop_p.name,
                    "raw_prelabel": raw_text,
                    "model": prelabeler.model_id,
                    "status": "RAW_PRELABEL",
                }
                records.append(rec)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()

    finally:
        # Guarantee memory cleanup
        prelabeler.cleanup()

    print(f"\n✓ Generated {len(records)} raw prelabels -> {output_manifest_path}")
    print("=" * 70)
    return records


def main():
    parser = argparse.ArgumentParser(description="Run Qwen2-VL batch prelabeling on line crops.")
    parser.add_argument("--crops_dir", type=str, default="data/crops", help="Path to crops directory")
    parser.add_argument("--config", type=str, default="configs/labeling.yaml", help="Path to labeling config")
    parser.add_argument(
        "--output",
        type=str,
        default="data/manifests/raw_prelabels.jsonl",
        help="Path to output raw prelabels jsonl",
    )

    args = parser.parse_args()
    run_prelabeling_pipeline(
        crops_dir=Path(args.crops_dir).resolve(),
        config_path=Path(args.config).resolve(),
        output_manifest_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
