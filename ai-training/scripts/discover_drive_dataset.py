"""
Discover dataset stored in Google Drive or local filesystem.

Usage:
    python scripts/discover_drive_dataset.py
    python scripts/discover_drive_dataset.py --drive_root /content/drive/MyDrive/C1SE.01 --config configs/dataset.yaml
"""
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_CANDIDATE_PATHS = [
    "Chữ Viết Tay Về Toán/Lớp 4",
    "Chữ Viết Tay Về Toán/Lớp 5",
    "Chữ Viết Tay Về Toán/NEW/IMG",
    "Chữ Viết Tay Về Toán/Sưu tập Tùm Lum",
    "Ảnh",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def try_mount_colab_drive():
    """Attempt to mount Google Drive if running in a Colab environment."""
    try:
        from google.colab import drive
        print("[Colab Detected] Checking Google Drive mount...")
        if not os.path.exists("/content/drive/MyDrive"):
            print("Mounting Google Drive at /content/drive...")
            drive.mount("/content/drive")
            print("✓ Google Drive mounted successfully.")
        else:
            print("✓ Google Drive is already mounted at /content/drive.")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[WARN] Colab drive mount attempt failed: {e}")
        return False


def discover_dataset(
    drive_root_str: str,
    candidate_subdirs: List[str],
    output_report_path: Path,
    mount_if_colab: bool = True,
) -> Dict[str, Any]:
    print("=" * 70)
    print("       MATHVISION GOOGLE DRIVE DATASET DISCOVERY")
    print("=" * 70)

    is_colab = False
    if mount_if_colab:
        is_colab = try_mount_colab_drive()

    drive_root = Path(drive_root_str)
    print(f"Target Drive Root : {drive_root}")
    print(f"Environment       : {'Google Colab' if is_colab else 'Local Machine'}")

    # Check if root path exists
    if not drive_root.exists():
        print("\n" + "!" * 70)
        print(f"NOTICE: Drive root does NOT exist: {drive_root}")
        print("LOCAL_PIPELINE_READY")
        print("REAL_DATA_STATUS=WAITING_FOR_DRIVE")
        print("!" * 70)

        report = {
            "status": "WAITING_FOR_DRIVE",
            "environment": "colab" if is_colab else "local",
            "drive_root": str(drive_root),
            "root_exists": False,
            "total_images_found": 0,
            "existing_paths": [],
            "missing_paths": [str(drive_root / sub) for sub in candidate_subdirs],
            "folders": {},
            "message": "Drive root not mounted or missing. Use Colab or provide a valid local path for fixture mode.",
        }

        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report written to : {output_report_path}")
        return report

    # Root exists -> scan candidate paths
    print(f"\n[1] Scanning candidate subdirectories under {drive_root}...")
    existing_paths = []
    missing_paths = []
    folder_inventory = {}
    all_image_records = []

    for sub in candidate_subdirs:
        sub_path = drive_root / sub
        if sub_path.exists() and sub_path.is_dir():
            existing_paths.append(str(sub_path))
            print(f"  ✓ Found existing directory : {sub}")
            # Discover images recursively
            img_files = []
            for ext in IMAGE_EXTENSIONS:
                img_files.extend(list(sub_path.rglob(f"*{ext}")))
                img_files.extend(list(sub_path.rglob(f"*{ext.upper()}")))

            # Deduplicate by absolute path
            img_paths = sorted(list(set(img_files)))
            img_count = len(img_paths)
            print(f"    -> Images discovered: {img_count}")

            folder_inventory[sub] = {
                "path": str(sub_path),
                "image_count": img_count,
                "sample_files": [str(p.name) for p in img_paths[:5]],
            }

            for p in img_paths:
                all_image_records.append({
                    "source_path": str(p),
                    "relative_to_root": str(p.relative_to(drive_root)),
                    "filename": p.name,
                    "folder": sub,
                })
        else:
            missing_paths.append(str(sub_path))
            print(f"  ✗ Path not found (optional) : {sub}")

    # Also check if root itself has images directly
    direct_images = []
    for ext in IMAGE_EXTENSIONS:
        direct_images.extend(list(drive_root.glob(f"*{ext}")))
        direct_images.extend(list(drive_root.glob(f"*{ext.upper()}")))
    if direct_images:
        direct_imgs = sorted(list(set(direct_images)))
        print(f"  ✓ Found {len(direct_imgs)} images directly in root directory.")
        folder_inventory["<root>"] = {
            "path": str(drive_root),
            "image_count": len(direct_imgs),
            "sample_files": [str(p.name) for p in direct_imgs[:5]],
        }

    total_images = len(all_image_records) + len(direct_images)
    print("\n" + "=" * 70)
    print("                 DATASET DISCOVERY SUMMARY")
    print("=" * 70)
    print(f"  Total Candidate Subdirs Checked : {len(candidate_subdirs)}")
    print(f"  Existing Subdirs Found         : {len(existing_paths)}")
    print(f"  Missing Subdirs                : {len(missing_paths)}")
    print(f"  Total Images Discovered        : {total_images}")
    print("=" * 70)

    report = {
        "status": "DISCOVERED" if total_images > 0 else "EMPTY_DIRECTORY",
        "environment": "colab" if is_colab else "local",
        "drive_root": str(drive_root),
        "root_exists": True,
        "total_images_found": total_images,
        "existing_paths": existing_paths,
        "missing_paths": missing_paths,
        "folders": folder_inventory,
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Discovery report saved to: {output_report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Discover dataset on Google Drive or local path.")
    parser.add_argument(
        "--drive_root",
        type=str,
        default="/content/drive/MyDrive/C1SE.01",
        help="Root path to dataset on Drive or local",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/dataset.yaml",
        help="Path to dataset YAML config",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/reports/drive_inventory.json",
        help="Path to output inventory JSON",
    )
    parser.add_argument(
        "--no_mount",
        action="store_true",
        help="Disable automatic colab drive mounting attempt",
    )

    args = parser.parse_args()

    candidate_paths = DEFAULT_CANDIDATE_PATHS
    if os.path.exists(args.config):
        try:
            import yaml
            with open(args.config, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            if "drive" in cfg and "candidate_subdirs" in cfg["drive"]:
                candidate_paths = cfg["drive"]["candidate_subdirs"]
        except Exception as e:
            print(f"[WARN] Could not parse config {args.config}: {e}")

    discover_dataset(
        drive_root_str=args.drive_root,
        candidate_subdirs=candidate_paths,
        output_report_path=Path(args.output).resolve(),
        mount_if_colab=not args.no_mount,
    )


if __name__ == "__main__":
    main()
