import os
import cv2
import glob
import zipfile
import hashlib
import numpy as np
import csv
from pathlib import Path
import sys

sys.path.append("E:/MathVisionKid/services/ai-service")
from app.api.ocr import run_classical_line_detection, correct_skew
from app.ocr.crnn_provider import CrnnOcrProvider
from PIL import Image

def get_sha256(filepath):
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def estimate_blur(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def estimate_brightness(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def main():
    BASE_DIR = "E:/MathVisionKid"
    DATA_DIR = os.path.join(BASE_DIR, "data", "hwtext_v1")
    ZIP_PATH = os.path.join(BASE_DIR, "rename.zip")
    
    DIRS = ["source", "work/crops", "work/overlays", "labels", "splits", "diagnostics", "quarantine_math"]
    for d in DIRS:
        os.makedirs(os.path.join(DATA_DIR, d), exist_ok=True)
        
    print("1. INTAKE & DEDUPE")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(os.path.join(DATA_DIR, "source"))
        
    source_files = glob.glob(os.path.join(DATA_DIR, "source", "**", "*.jpg"), recursive=True)
    
    source_records = []
    seen_hashes = set()
    
    for idx, filepath in enumerate(source_files):
        filename = os.path.basename(filepath)
        file_sha256 = get_sha256(filepath)
        
        if file_sha256 in seen_hashes:
            continue
        seen_hashes.add(file_sha256)
        
        # Infer group P_YYYYMMDD_HHMMSS
        parts = filename.split('_')
        if len(parts) >= 3 and parts[0] == "P":
            source_group = f"P_{parts[1]}_{parts[2]}"
        else:
            source_group = "UNKNOWN"
            
        img = cv2.imread(filepath)
        h, w = img.shape[:2]
        
        blur_score = estimate_blur(img)
        brightness = estimate_brightness(img)
        
        quality_status = "reject" if blur_score < 50 else "usable"
        
        source_records.append({
            "source_image_id": f"IMG_{idx:04d}",
            "filename": filename,
            "filepath": filepath,
            "source_group": source_group,
            "sha256": file_sha256,
            "width": w,
            "height": h,
            "blur_score": blur_score,
            "brightness": brightness,
            "quality_status": quality_status,
            "notes": ""
        })
        
    with open(os.path.join(DATA_DIR, "source_manifest.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=source_records[0].keys())
        writer.writeheader()
        writer.writerows(source_records)
    print(f"Unique source images: {len(source_records)}")
    
    print("2. SEGMENTATION & CLASSIFY")
    try:
        provider = CrnnOcrProvider()
    except Exception as e:
        print(f"Failed to load CRNN: {e}")
        provider = None
        
    line_candidates = []
    
    for record in source_records:
        if record["quality_status"] == "reject":
            continue
            
        img = cv2.imread(record["filepath"])
        crops = run_classical_line_detection(img)
        overlay = img.copy()
        
        for c_idx, box in enumerate(crops):
            pad = 5
            x1 = max(0, box.x - pad)
            y1 = max(0, box.y - pad)
            x2 = min(img.shape[1], box.x + box.width + pad)
            y2 = min(img.shape[0], box.y + box.height + pad)
            
            crop_img = img[y1:y2, x1:x2]
            if crop_img.size == 0: continue
            
            crop_filename = f"{record['source_image_id']}_L{c_idx:02d}.jpg"
            crop_path = os.path.join(DATA_DIR, "work/crops", crop_filename)
            cv2.imwrite(crop_path, crop_img)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            prelabel = ""
            if provider:
                pil_img = Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB))
                prelabel = provider.recognize_line(pil_img)
                
            math_chars = set("+-*/=><")
            has_math = any(c in math_chars for c in prelabel)
            has_digits = any(c.isdigit() for c in prelabel)
            has_alpha = any(c.isalpha() for c in prelabel)
            
            if has_math or (has_digits and not has_alpha):
                provisional_class = "MATH_DOMINANT"
            elif has_alpha and has_digits:
                provisional_class = "TEXT_WITH_CONTEXTUAL_NUMBERS"
            elif has_alpha and not has_digits:
                provisional_class = "TEXT_ONLY"
            else:
                provisional_class = "REJECT"
                
            line_candidates.append({
                "line_id": crop_filename.split('.')[0],
                "source_image_id": record["source_image_id"],
                "source_group": record["source_group"],
                "x": x1, "y": y1, "w": x2-x1, "h": y2-y1,
                "detector_version": "v1.1",
                "crop_path": f"work/crops/{crop_filename}",
                "quality_score": record["blur_score"],
                "provisional_class": provisional_class,
                "raw_prelabel": prelabel,
                "verified_text": "",
                "label_status": "PRELABELED",
                "review_status": "PENDING"
            })
            
        cv2.imwrite(os.path.join(DATA_DIR, "work/overlays", record["filename"]), overlay)
        
    if line_candidates:
        with open(os.path.join(DATA_DIR, "line_candidates.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=line_candidates[0].keys())
            writer.writeheader()
            writer.writerows(line_candidates)
            
        annotation_queue = [x for x in line_candidates if x["provisional_class"] in ["TEXT_ONLY", "TEXT_WITH_CONTEXTUAL_NUMBERS"]]
        if annotation_queue:
            with open(os.path.join(DATA_DIR, "annotation_queue.tsv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=annotation_queue[0].keys(), delimiter="\t")
                writer.writeheader()
                writer.writerows(annotation_queue)
                
        print(f"Total lines: {len(line_candidates)}")
        from collections import Counter
        print(Counter(x["provisional_class"] for x in line_candidates))

if __name__ == "__main__":
    main()
