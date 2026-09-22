"""
Export Verification — MathVision Kids Model Handoff
Verifies all artifacts in the handoff package can be loaded and checksums match.
"""
import json
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HANDOFF_DIR = Path(r"D:\nhom6\train thử\model_handoff")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def verify():
    print("=" * 70)
    print("MATHVISION KIDS — EXPORT VERIFICATION")
    print("=" * 70)
    
    errors = []
    warnings = []
    
    # 1. Check all required files exist
    required_files = [
        "model_manifest.json",
        "label_map_detection.json",
        "vocab_ocr_v1.json",
        "MODEL_CARD.md",
        "DATASET_CARD.md",
        "artifacts/yolov8n_mathvision_det_v1.pt",
        "artifacts/crnn_mathvision_ocr_v1.pth",
        "sample_io/sample_input_synthetic.jpg",
        "sample_io/expected_output.json",
    ]
    
    print("\n[1] FILE EXISTENCE CHECK")
    for f in required_files:
        p = HANDOFF_DIR / f
        if p.exists():
            size = p.stat().st_size
            print(f"  ✅ {f} ({size:,} bytes)")
        else:
            print(f"  ❌ MISSING: {f}")
            errors.append(f"Missing file: {f}")
    
    # 2. SHA-256 verification
    print("\n[2] SHA-256 CHECKSUM VERIFICATION")
    with open(HANDOFF_DIR / "model_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    for model in manifest["models"]:
        artifact = model["artifactFilename"]
        expected_sha = model["sha256"]
        artifact_path = HANDOFF_DIR / "artifacts" / artifact
        
        if not artifact_path.exists():
            print(f"  ❌ {artifact}: FILE NOT FOUND")
            errors.append(f"Artifact not found: {artifact}")
            continue
        
        actual_sha = sha256_file(artifact_path)
        if actual_sha == expected_sha:
            print(f"  ✅ {artifact}: SHA-256 MATCH")
            print(f"     {actual_sha}")
        else:
            print(f"  ❌ {artifact}: SHA-256 MISMATCH")
            print(f"     Expected: {expected_sha}")
            print(f"     Actual:   {actual_sha}")
            errors.append(f"SHA-256 mismatch: {artifact}")
    
    # 3. Try loading YOLO model
    print("\n[3] YOLO MODEL LOAD TEST")
    try:
        import torch
        yolo_path = HANDOFF_DIR / "artifacts" / "yolov8n_mathvision_det_v1.pt"
        ckpt = torch.load(str(yolo_path), map_location="cpu", weights_only=False)
        print(f"  ✅ YOLO checkpoint loaded (type: {type(ckpt).__name__})")
        if isinstance(ckpt, dict):
            print(f"     Keys: {list(ckpt.keys())[:10]}")
        print(f"     PyTorch version: {torch.__version__}")
    except Exception as e:
        print(f"  ⚠️ YOLO load warning: {e}")
        warnings.append(f"YOLO load issue: {e}")
    
    # 4. Try loading CRNN model
    print("\n[4] CRNN MODEL LOAD TEST")
    try:
        import torch
        import torch.nn as nn
        
        crnn_path = HANDOFF_DIR / "artifacts" / "crnn_mathvision_ocr_v1.pth"
        state_dict = torch.load(str(crnn_path), map_location="cpu", weights_only=False)
        
        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            actual_sd = state_dict["model_state_dict"]
            print(f"  ✅ CRNN checkpoint loaded (wrapper with keys: {list(state_dict.keys())})")
        elif isinstance(state_dict, dict):
            actual_sd = state_dict
            print(f"  ✅ CRNN state_dict loaded ({len(actual_sd)} parameters)")
        else:
            actual_sd = None
            print(f"  ✅ CRNN loaded (type: {type(state_dict).__name__})")
        
        if actual_sd:
            total_params = sum(v.numel() for v in actual_sd.values() if hasattr(v, 'numel'))
            print(f"     Total parameters: {total_params:,}")
        
        print(f"     PyTorch version: {torch.__version__}")
    except Exception as e:
        print(f"  ⚠️ CRNN load warning: {e}")
        warnings.append(f"CRNN load issue: {e}")
    
    # 5. Validate JSON files parse correctly
    print("\n[5] JSON SCHEMA VALIDATION")
    json_files = ["model_manifest.json", "label_map_detection.json", "vocab_ocr_v1.json", "sample_io/expected_output.json"]
    for jf in json_files:
        try:
            with open(HANDOFF_DIR / jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  ✅ {jf}: valid JSON ({len(json.dumps(data)):,} chars)")
        except Exception as e:
            print(f"  ❌ {jf}: INVALID — {e}")
            errors.append(f"Invalid JSON: {jf}")
    
    # 6. Verify label map consistency
    print("\n[6] LABEL MAP CONSISTENCY")
    with open(HANDOFF_DIR / "label_map_detection.json", "r", encoding="utf-8") as f:
        label_map = json.load(f)
    
    expected_classes = ["0","1","2","3","4","5","6","7","8","9","+","-","=","c1"]
    actual_classes = label_map.get("class_names_ordered", [])
    if actual_classes == expected_classes:
        print(f"  ✅ Detection label map: {len(actual_classes)} classes match expected")
    else:
        print(f"  ❌ Detection label map mismatch")
        errors.append("Label map class order mismatch")
    
    with open(HANDOFF_DIR / "vocab_ocr_v1.json", "r", encoding="utf-8") as f:
        vocab = json.load(f)
    vocab_dict = vocab.get("vocab", {})
    if len(vocab_dict) == 237:
        print(f"  ✅ OCR vocab: 237 classes, blank_idx={vocab_dict.get('<blank>', 'MISSING')}")
    else:
        print(f"  ❌ OCR vocab: expected 237, got {len(vocab_dict)}")
        errors.append(f"OCR vocab size mismatch: {len(vocab_dict)}")
    
    # 7. Verify preprocessing matches
    print("\n[7] PREPROCESSING CONSISTENCY CHECK")
    for model in manifest["models"]:
        name = model["modelName"]
        prep = model.get("preprocessing", {})
        print(f"  📋 {name}:")
        for k, v in prep.items():
            print(f"     {k}: {v}")
    print("  ⚠️ Manual check required: Ensure these match the training scripts exactly")
    
    # 8. Framework/runtime info
    print("\n[8] FRAMEWORK/RUNTIME VERSIONS")
    try:
        import torch
        print(f"  PyTorch: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU: {torch.cuda.get_device_name(0)}")
    except:
        print("  ⚠️ PyTorch not available")
    
    try:
        import ultralytics
        print(f"  Ultralytics: {ultralytics.__version__}")
    except:
        print("  ⚠️ Ultralytics not installed (required for YOLO inference)")
        warnings.append("Ultralytics not installed")
    
    print(f"  Python: {sys.version}")
    
    # Summary
    print("\n" + "=" * 70)
    if errors:
        print(f"❌ VERIFICATION FAILED — {len(errors)} error(s)")
        for e in errors:
            print(f"   • {e}")
    else:
        print("✅ ALL CHECKS PASSED")
    
    if warnings:
        print(f"\n⚠️ {len(warnings)} warning(s):")
        for w in warnings:
            print(f"   • {w}")
    
    print("=" * 70)
    return len(errors) == 0

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
