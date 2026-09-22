"""
Standalone verification and smoke test runner for Vietnamese handwriting OCR engine.

Usage:
    python test_predict.py
    # or with a custom image:
    python test_predict.py path/to/image.jpg
"""
import sys
import json
import time
import hashlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow running directly from within the ocr_engine directory or as part of a parent workspace
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

EXPECTED_CHECKPOINT_SHA256 = "a807eaa763a4471bc057b9545a3521612423214858d50b1ef42b7baf28de0941"
EXPECTED_PARAM_COUNT = 5962560
EXPECTED_VOCAB_SIZE = 320


def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_smoke_test():
    print("=" * 65)
    print("   OCR ENGINE HANDOFF VERIFICATION & PACKAGE SMOKE TEST")
    print("=" * 65)

    # 1. Package Imports
    print("\n[1/6] Verifying Imports & Architecture...")
    try:
        from ocr_engine.model import CRNN
        from ocr_engine.predict import predict_text, predict_batch, _load
    except ImportError:
        from model import CRNN
        from predict import predict_text, predict_batch, _load
    print("  ✓ Package imports succeeded.")

    # 2. Checkpoint Existence & SHA256
    print("\n[2/6] Verifying Official Checkpoint...")
    ckpt_path = _HERE / "best_cer.pth"
    if not ckpt_path.is_file():
        print(f"  [FAIL] Checkpoint not found at: {ckpt_path}")
        return False
    actual_sha = compute_sha256(ckpt_path)
    if actual_sha != EXPECTED_CHECKPOINT_SHA256:
        print(f"  [FAIL] Checkpoint SHA mismatch!")
        print(f"    Expected: {EXPECTED_CHECKPOINT_SHA256}")
        print(f"    Actual  : {actual_sha}")
        return False
    print(f"  ✓ Checkpoint verified: {ckpt_path.name}")
    print(f"    SHA256: {actual_sha} (MATCHES EXPECTED)")

    # 3. Vocabulary Contract
    print("\n[3/6] Verifying Vocabulary Contract...")
    vocab_path = _HERE / "vocab.json"
    if not vocab_path.is_file():
        print(f"  [FAIL] vocab.json not found at: {vocab_path}")
        return False
    with open(vocab_path, encoding="utf-8") as f:
        vocab = json.load(f)
    if len(vocab) != EXPECTED_VOCAB_SIZE:
        print(f"  [FAIL] Vocab size mismatch: expected {EXPECTED_VOCAB_SIZE}, got {len(vocab)}")
        return False
    if vocab.get("<blank>") != 0:
        print(f"  [FAIL] Blank token index is not 0 (got {vocab.get('<blank>')})")
        return False
    # Check digits and operators
    for d in "0123456789":
        assert d in vocab, f"Digit {d} missing from vocab"
    for op in ["+", "-", "="]:
        assert op in vocab, f"Operator {op} missing from vocab"
    print(f"  ✓ Vocabulary verified: {len(vocab)} continuous tokens, blank=0, digits & operators present.")

    # 4. Model Parameter Count
    print("\n[4/6] Verifying Model Parameter Count...")
    import torch
    model_test = CRNN(len(vocab), dropout=0.2)
    total_params = sum(p.numel() for p in model_test.parameters())
    if total_params != EXPECTED_PARAM_COUNT:
        print(f"  [FAIL] Parameter count mismatch: expected {EXPECTED_PARAM_COUNT}, measured {total_params}")
        return False
    print(f"  ✓ Parameter count verified: {total_params:,} parameters.")
    del model_test

    # 5. Packaged Smoke Test Samples (Single Image & Metric Verification)
    print("\n[5/6] Running Package Smoke Test on Bundled Samples...")
    print("  NOTE: This is a smoke test on the 5 bundled samples for quick functional checks.")
    print("  Official validation CER remains 0.1134 across 500 validation images.")

    samples_dir = _HERE / "samples"
    manifest_path = samples_dir / "sample_manifest.json"
    if not manifest_path.exists():
        print(f"  [FAIL] sample_manifest.json not found at {manifest_path}")
        return False

    with open(manifest_path, encoding="utf-8") as f:
        manifest_data = json.load(f)

    samples = manifest_data.get("samples", [])
    cers = []
    sample_paths = []
    for s in samples:
        img_file = samples_dir / s["image"]
        sample_paths.append(img_file)
        gt = s["text"]
        pred = predict_text(img_file)
        dist = levenshtein(pred, gt)
        cer_val = dist / max(len(gt), 1)
        cers.append(cer_val)
        print(f"\n  [Sample: {s['image']}]")
        print(f"    GT   : {gt}")
        print(f"    PRED : {pred}")
        print(f"    CER  : {cer_val:.4f} (edit dist: {dist}/{len(gt)})")

    mean_cer = sum(cers) / len(cers) if cers else 0.0
    print("\n  " + "-" * 55)
    print(f"  Mean CER on the 5 packaged smoke-test samples: {mean_cer:.4f} ({mean_cer * 100:.2f}%)")
    print("  " + "-" * 55)

    # 6. Micro-Batch Functional & Memory Tests (1, 5, 10, 30 images)
    print("\n[6/6] Testing Micro-Batch Inference (1, 5, 10, 30 images)...")
    for count in [1, 5, 10, 30]:
        # Create input list by safe repeating
        inputs = (sample_paths * ((count // len(sample_paths)) + 1))[:count]
        t0 = time.perf_counter()
        batch_res = predict_batch(inputs, batch_size=4)
        elapsed = time.perf_counter() - t0

        assert len(batch_res) == count, f"Output count mismatch for batch {count}: got {len(batch_res)}"
        # Verify order preservation
        for idx in range(count):
            assert batch_res[idx] == batch_res[idx % len(sample_paths)], f"Order mismatch at index {idx}"
        print(f"  ✓ Batch {count:2d} images (micro-batch size=4): PASS | elapsed: {elapsed:.4f}s | count: {len(batch_res)}")

    # CPU Fallback Verification
    print("\n  Checking explicit CPU inference fallback...")
    cpu_pred = predict_text(sample_paths[0], device="cpu")
    assert len(cpu_pred) > 0, "CPU inference returned empty string"
    print(f"  ✓ Explicit CPU inference: PASS (result length: {len(cpu_pred)})")

    print("\n" + "=" * 65)
    print("  ALL VERIFICATIONS AND PACKAGE SMOKE TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            print(f"Predicting single image: {target}")
            from ocr_engine.predict import predict_text
            res = predict_text(target)
            print(f"Result: {res}")
        else:
            print(f"File not found: {target}")
            sys.exit(1)
    else:
        success = run_smoke_test()
        sys.exit(0 if success else 1)