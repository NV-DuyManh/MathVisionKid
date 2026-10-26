"""
Inspect checkpoint and verify compatibility with model architecture and vocabulary.

Usage:
    python scripts/inspect_checkpoint.py
    python scripts/inspect_checkpoint.py --checkpoint path/to/best_cer.pth --output artifacts/reports/checkpoint_audit.json
"""
import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any

import torch

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def inspect_checkpoint(
    checkpoint_path: Path,
    model_source_path: Path,
    vocab_path: Path,
    output_report_path: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("      MATHVISION OCR CHECKPOINT INSPECTION & AUDIT")
    print("=" * 70)
    print(f"Checkpoint : {checkpoint_path}")
    print(f"Model file : {model_source_path}")
    print(f"Vocab file : {vocab_path}")

    # 1. Existence and Hash Checks
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] Checkpoint file does not exist: {checkpoint_path}")
    if not model_source_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] Model source file does not exist: {model_source_path}")
    if not vocab_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] Vocab file does not exist: {vocab_path}")

    ckpt_sha = compute_sha256(checkpoint_path)
    model_sha = compute_sha256(model_source_path)
    vocab_sha = compute_sha256(vocab_path)
    ckpt_size_bytes = checkpoint_path.stat().st_size

    print(f"\n[1] Checksum Verification:")
    print(f"  Checkpoint SHA256 : {ckpt_sha} ({ckpt_size_bytes:,} bytes)")
    print(f"  Model Src SHA256  : {model_sha}")
    print(f"  Vocab SHA256      : {vocab_sha}")

    # 2. Vocabulary Inspection
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    vocab_size = len(vocab)
    blank_index = vocab.get("<blank>")
    print(f"\n[2] Vocabulary Contract:")
    print(f"  Total tokens      : {vocab_size}")
    print(f"  Blank index       : {blank_index}")
    if blank_index is None or blank_index != 0:
        raise ValueError(f"[FAIL FAST] Expected blank token '<blank>' at index 0, got {blank_index}")

    # 3. Load Checkpoint Tensor State
    print(f"\n[3] Loading Checkpoint State Dict:")
    try:
        state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    except Exception as e:
        raise RuntimeError(f"[FAIL FAST] Failed to load checkpoint {checkpoint_path}: {e}")

    keys_info = {}
    total_params = 0
    classifier_weight_key = None
    classifier_bias_key = None
    classifier_dim = None

    for k, v in state_dict.items():
        shape = list(v.shape)
        dtype_str = str(v.dtype)
        num_el = v.numel()
        total_params += num_el
        keys_info[k] = {
            "shape": shape,
            "dtype": dtype_str,
            "num_elements": num_el,
        }
        print(f"  Key: {k:<30} Shape: {str(shape):<20} Params: {num_el:>10,}")

        # Detect classifier layer
        if k == "fc.weight":
            classifier_weight_key = k
            classifier_dim = shape[0]
        elif k == "fc.bias":
            classifier_bias_key = k

    print(f"\n  Total Checkpoint Parameters: {total_params:,}")
    print(f"  Classifier layer detected  : {classifier_weight_key} -> output dim = {classifier_dim}")

    if classifier_dim != vocab_size:
        raise ValueError(
            f"[FAIL FAST] Classifier dimension mismatch: checkpoint output is {classifier_dim} "
            f"but vocab size is {vocab_size}!"
        )

    # 4. Check Architecture Compatibility with model.py
    print(f"\n[4] Instantiating CRNN Architecture from {model_source_path.name}:")
    import importlib.util
    spec = importlib.util.spec_from_file_location("model_module", str(model_source_path))
    model_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_mod)

    if not hasattr(model_mod, "CRNN"):
        raise AttributeError(f"[FAIL FAST] Class 'CRNN' not found in {model_source_path}")

    model_instance = model_mod.CRNN(num_classes=vocab_size)
    model_param_count = sum(p.numel() for p in model_instance.parameters())
    print(f"  Model instantiated successfully. Parameter count: {model_param_count:,}")

    if model_param_count != total_params:
        raise ValueError(
            f"[FAIL FAST] Architecture parameter count mismatch! Model: {model_param_count:,}, Checkpoint: {total_params:,}"
        )

    # Load weights with strict=True
    try:
        model_instance.load_state_dict(state_dict, strict=True)
        print("  ✓ model.load_state_dict(state_dict, strict=True) SUCCEEDED perfectly!")
    except Exception as e:
        raise RuntimeError(f"[FAIL FAST] Failed to load state_dict into CRNN model with strict=True: {e}")

    # 5. Dummy Forward Pass
    print(f"\n[5] Forward Pass Verification with Synthetic Input [B=2, C=3, H=64, W=1024]:")
    dummy_input = torch.randn(2, 3, 64, 1024)
    model_instance.eval()
    with torch.no_grad():
        output = model_instance(dummy_input)
    # Output shape: [B, W_feat, num_classes] where W_feat = 1024 // 8 = 128
    print(f"  Input shape  : {list(dummy_input.shape)}")
    print(f"  Output shape : {list(output.shape)} (Expected: [2, 128, {vocab_size}])")
    assert output.shape == (2, 128, vocab_size), f"Unexpected output shape: {output.shape}"
    print("  ✓ Forward pass shape contract verified!")

    audit_result = {
        "status": "PASS",
        "checkpoint_file": str(checkpoint_path),
        "checkpoint_sha256": ckpt_sha,
        "checkpoint_size_bytes": ckpt_size_bytes,
        "model_source_file": str(model_source_path),
        "model_source_sha256": model_sha,
        "vocab_file": str(vocab_path),
        "vocab_sha256": vocab_sha,
        "architecture": "CRNN (4-block Conv2d + GroupNorm + BiLSTM + Linear)",
        "parameter_count": total_params,
        "vocab_size": vocab_size,
        "blank_index": blank_index,
        "classifier_layer": "fc",
        "classifier_dimension": classifier_dim,
        "input_channels": 3,
        "input_height": 64,
        "input_width": 1024,
        "output_shape_for_1024": [1, 128, vocab_size],
        "state_dict_keys": keys_info,
        "compatibility": {
            "strict_load": True,
            "forward_pass_pass": True,
            "weights_only_safe": True,
        },
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(audit_result, f, indent=2, ensure_ascii=False)

    print(f"\n[6] Audit report written to: {output_report_path}")
    print("=" * 70)
    print("               CHECKPOINT INSPECTION PASSED!")
    print("=" * 70)
    return audit_result


def main():
    parser = argparse.ArgumentParser(description="Inspect OCR checkpoint and verify architecture.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/best_cer.pth",
        help="Path to .pth checkpoint file",
    )
    parser.add_argument(
        "--model_file",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/model.py",
        help="Path to model.py source file",
    )
    parser.add_argument(
        "--vocab_file",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/vocab.json",
        help="Path to vocab.json file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/reports/checkpoint_audit.json",
        help="Path to output JSON audit report",
    )

    args = parser.parse_args()
    inspect_checkpoint(
        checkpoint_path=Path(args.checkpoint).resolve(),
        model_source_path=Path(args.model_file).resolve(),
        vocab_path=Path(args.vocab_file).resolve(),
        output_report_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
