"""
Adapt base OCR checkpoint to expanded unified vocabulary.

Logic:
  - For layers with identical keys and shapes: copy weights directly.
  - For classifier layer (fc.weight, fc.bias):
      * Copy weights for existing class indices (0..old_vocab_size-1).
      * Initialize weights for newly added class indices (old_vocab_size..new_vocab_size-1).
  - Verifies model integrity via strict loading and forward pass.
  - Outputs artifacts/checkpoints/adapted_init.pth and artifacts/reports/adaptation_report.json.
"""
import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any, List

import torch
import torch.nn as nn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def adapt_checkpoint(
    checkpoint_path: Path,
    old_vocab_path: Path,
    new_vocab_path: Path,
    model_source_path: Path,
    output_checkpoint_path: Path,
    output_report_path: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("        MATHVISION OCR CHECKPOINT ADAPTATION")
    print("=" * 70)
    print(f"Base Checkpoint : {checkpoint_path}")
    print(f"Old Vocab       : {old_vocab_path}")
    print(f"New Vocab       : {new_vocab_path}")

    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] Base checkpoint not found: {checkpoint_path}")
    if not old_vocab_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] Old vocab not found: {old_vocab_path}")
    if not new_vocab_path.is_file():
        raise FileNotFoundError(f"[FAIL FAST] New vocab not found: {new_vocab_path}")

    old_ckpt_sha = compute_sha256(checkpoint_path)

    with open(old_vocab_path, "r", encoding="utf-8") as f:
        old_vocab = json.load(f)
    with open(new_vocab_path, "r", encoding="utf-8") as f:
        new_vocab = json.load(f)

    old_vocab_size = len(old_vocab)
    new_vocab_size = len(new_vocab)
    print(f"\n[1] Vocabularies:")
    print(f"  Old Vocab Size : {old_vocab_size}")
    print(f"  New Vocab Size : {new_vocab_size}")

    # Load old state dict
    old_state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

    # Import CRNN model definition
    import importlib.util
    spec = importlib.util.spec_from_file_location("model_module", str(model_source_path))
    model_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_mod)
    CRNN = model_mod.CRNN

    # Instantiate new model with new vocab size
    new_model = CRNN(num_classes=new_vocab_size)
    new_state = new_model.state_dict()

    matched_keys: List[str] = []
    skipped_keys: List[str] = []
    newly_initialized_keys: List[str] = []
    classifier_changed = False

    adapted_state = {}

    print(f"\n[2] Weight Transfer Logic:")
    for key, new_tensor in new_state.items():
        if key in old_state:
            old_tensor = old_state[key]
            if old_tensor.shape == new_tensor.shape:
                # Direct exact shape match -> copy weight
                adapted_state[key] = old_tensor.clone()
                matched_keys.append(key)
                print(f"  [MATCH]   {key:<30} shape: {list(old_tensor.shape)}")
            else:
                # Shape mismatch (typically classifier head: fc.weight, fc.bias)
                skipped_keys.append(key)
                print(f"  [ADAPT]   {key:<30} old shape: {list(old_tensor.shape)} -> new shape: {list(new_tensor.shape)}")
                if key == "fc.weight":
                    classifier_changed = True
                    # Initialize full tensor like new_tensor
                    adapted_weight = new_tensor.clone()
                    # Copy old classes weights
                    adapted_weight[:old_vocab_size, :] = old_tensor[:old_vocab_size, :].clone()
                    # Initialize new classes with matching variance
                    with torch.no_grad():
                        weight_std = old_tensor.std().item()
                        nn.init.normal_(adapted_weight[old_vocab_size:, :], mean=0.0, std=weight_std)
                    adapted_state[key] = adapted_weight
                    newly_initialized_keys.append(f"{key}[{old_vocab_size}:{new_vocab_size}]")
                    print(f"            Preserved {old_vocab_size} rows, initialized {new_vocab_size - old_vocab_size} new rows (std={weight_std:.4f})")

                elif key == "fc.bias":
                    classifier_changed = True
                    adapted_bias = new_tensor.clone()
                    adapted_bias[:old_vocab_size] = old_tensor[:old_vocab_size].clone()
                    with torch.no_grad():
                        bias_mean = old_tensor.mean().item()
                        adapted_bias[old_vocab_size:].fill_(bias_mean)
                    adapted_state[key] = adapted_bias
                    newly_initialized_keys.append(f"{key}[{old_vocab_size}:{new_vocab_size}]")
                    print(f"            Preserved {old_vocab_size} biases, initialized {new_vocab_size - old_vocab_size} new biases (mean={bias_mean:.4f})")
                else:
                    # Generic fallback: keep random init for unknown shape change
                    adapted_state[key] = new_tensor.clone()
                    newly_initialized_keys.append(key)
        else:
            newly_initialized_keys.append(key)
            adapted_state[key] = new_tensor.clone()
            print(f"  [NEW]     {key:<30} newly initialized")

    # Load adapted state dict into new model with strict=True
    print(f"\n[3] Strict Validation of Adapted Model:")
    new_model.load_state_dict(adapted_state, strict=True)
    print("  ✓ Strict loading of adapted state dict SUCCEEDED!")

    # Forward pass test
    dummy_input = torch.randn(2, 3, 64, 1024)
    new_model.eval()
    with torch.no_grad():
        out = new_model(dummy_input)
    assert out.shape == (2, 128, new_vocab_size), f"Forward pass shape mismatch: {out.shape}"
    print(f"  ✓ Forward pass verified: input [2, 3, 64, 1024] -> output {list(out.shape)}")

    # Save adapted checkpoint
    output_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(adapted_state, output_checkpoint_path)
    new_ckpt_sha = compute_sha256(output_checkpoint_path)
    print(f"\n[4] Output Artifacts:")
    print(f"  Adapted checkpoint saved to : {output_checkpoint_path}")
    print(f"  Adapted checkpoint SHA256   : {new_ckpt_sha}")

    report = {
        "status": "PASS",
        "old_checkpoint_sha256": old_ckpt_sha,
        "adapted_checkpoint_sha256": new_ckpt_sha,
        "old_vocab_size": old_vocab_size,
        "new_vocab_size": new_vocab_size,
        "added_classes_count": new_vocab_size - old_vocab_size,
        "classifier_changed": classifier_changed,
        "matched_keys": matched_keys,
        "skipped_keys": skipped_keys,
        "newly_initialized_keys": newly_initialized_keys,
        "total_parameters": sum(p.numel() for p in new_model.parameters()),
        "output_shape_for_1024": [1, 128, new_vocab_size],
    }

    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Adaptation report saved to  : {output_report_path}")
    print("=" * 70)
    return report


def main():
    parser = argparse.ArgumentParser(description="Adapt OCR checkpoint for unified vocabulary.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/best_cer.pth",
        help="Path to source checkpoint",
    )
    parser.add_argument(
        "--old_vocab",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/vocab.json",
        help="Path to old vocab.json",
    )
    parser.add_argument(
        "--new_vocab",
        type=str,
        default="configs/unified_vocab.json",
        help="Path to new unified vocab.json",
    )
    parser.add_argument(
        "--model_file",
        type=str,
        default="handoff/staging/ocr_engine_handoff_final/ocr_engine/model.py",
        help="Path to model.py",
    )
    parser.add_argument(
        "--output_checkpoint",
        type=str,
        default="artifacts/checkpoints/adapted_init.pth",
        help="Path to save adapted checkpoint",
    )
    parser.add_argument(
        "--output_report",
        type=str,
        default="artifacts/reports/adaptation_report.json",
        help="Path to save adaptation report",
    )

    args = parser.parse_args()
    adapt_checkpoint(
        checkpoint_path=Path(args.checkpoint).resolve(),
        old_vocab_path=Path(args.old_vocab).resolve(),
        new_vocab_path=Path(args.new_vocab).resolve(),
        model_source_path=Path(args.model_file).resolve(),
        output_checkpoint_path=Path(args.output_checkpoint).resolve(),
        output_report_path=Path(args.output_report).resolve(),
    )


if __name__ == "__main__":
    main()
