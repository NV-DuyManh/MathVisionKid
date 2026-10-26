"""
Fine-tuning pipeline for MathVision Kids CRNN line-level handwriting OCR.

Key Features:
  - CUDA, Automatic Mixed Precision (AMP), AdamW, Gradient Clipping
  - Multi-stage transfer learning:
      * Stage 1: Freeze CNN backbone, tune BiLSTM and classifier head
      * Stage 2: Unfreeze with differential learning rates
  - Grace-period early stopping (min_steps_before_early_stop prevents premature stop)
  - CTC Blank Collapse Monitoring (logs CTC_BLANK_COLLAPSE_WARNING if empty rate spikes)
  - Full checkpoint resumption (model, optimizer, scheduler, scaler, step, best_cer)
  - Automatic backup to Google Drive in Colab environment (run_YYYYMMDD_HHMMSS/)
"""
import sys
import os
import json
import time
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca != cb)))
        prev = cur
    return prev[-1]


def cv2_imread_unicode(filepath: Path) -> Optional[np.ndarray]:
    try:
        data = np.fromfile(str(filepath), dtype=np.uint8)
        if data is None or len(data) == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


class LineOCRDataset(Dataset):
    def __init__(self, manifest_path: Path, vocab: Dict[str, int], is_train: bool = True, aug_cfg: Dict[str, Any] = None):
        self.vocab = vocab
        self.blank_idx = vocab.get("<blank>", 0)
        self.unk_idx = vocab.get("<unk>", self.blank_idx)
        self.is_train = is_train

        self.records = []
        if manifest_path.is_file():
            with open(manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line.strip())
                        # Verify image file exists
                        if Path(r.get("image_path", "")).is_file():
                            self.records.append(r)

        # Transforms
        base_transforms = [
            transforms.Resize((64, 1024)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]

        if is_train and aug_cfg and aug_cfg.get("enabled", True):
            aug_list = [
                transforms.RandomRotation(degrees=aug_cfg.get("random_rotation_degrees", 3.0)),
                transforms.ColorJitter(
                    brightness=aug_cfg.get("brightness_jitter", 0.1),
                    contrast=aug_cfg.get("contrast_jitter", 0.1),
                ),
            ]
            self.transform = transforms.Compose(aug_list + base_transforms)
        else:
            self.transform = transforms.Compose(base_transforms)

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        img_p = Path(rec["image_path"])
        text = rec["text"]

        img_bgr = cv2_imread_unicode(img_p)
        if img_bgr is None:
            # Fallback blank white canvas if read fails
            img_bgr = np.full((64, 1024, 3), 255, dtype=np.uint8)

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tensor = self.transform(pil_img)

        # Encode text to token IDs
        target_ids = [self.vocab.get(c, self.unk_idx) for c in text]
        return tensor, torch.tensor(target_ids, dtype=torch.long), text


def collate_ocr_batch(batch):
    images = torch.stack([item[0] for item in batch], dim=0)
    texts = [item[2] for item in batch]

    target_lengths = torch.tensor([len(item[1]) for item in batch], dtype=torch.long)
    targets = torch.cat([item[1] for item in batch], dim=0)

    return images, targets, target_lengths, texts


def get_crnn_class():
    import importlib.util
    model_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    spec = importlib.util.spec_from_file_location("crnn_module", str(model_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CRNN


def evaluate_val_set(
    model: nn.Module,
    val_loader: DataLoader,
    inv_vocab: Dict[int, str],
    blank_idx: int,
    device: torch.device,
) -> Dict[str, float]:
    model.eval()
    total_ed = 0
    total_tgt_len = 0
    exact_matches = 0
    empty_preds = 0
    total_samples = 0

    with torch.no_grad():
        for images, targets, target_lengths, texts in val_loader:
            images = images.to(device)
            logits = model(images)
            preds = logits.argmax(2).cpu().numpy()

            for b in range(preds.shape[0]):
                gt = texts[b]
                out, prev = [], -1
                for idx in preds[b]:
                    if idx != blank_idx and idx != prev:
                        out.append(inv_vocab.get(int(idx), "?"))
                    prev = idx
                pred_text = "".join(out).strip()

                ed = levenshtein(gt, pred_text)
                gt_len = max(1, len(gt))

                total_ed += ed
                total_tgt_len += gt_len
                if pred_text == gt:
                    exact_matches += 1
                if len(pred_text) == 0:
                    empty_preds += 1
                total_samples += 1

    cer = total_ed / max(1, total_tgt_len)
    em_rate = exact_matches / max(1, total_samples)
    empty_rate = empty_preds / max(1, total_samples)

    return {
        "val_cer": round(cer, 4),
        "val_exact_match": round(em_rate, 4),
        "val_empty_rate": round(empty_rate, 4),
        "val_samples": total_samples,
    }


def train_model(
    config_path: Path,
    train_manifest: Path,
    val_manifest: Path,
    resume_path: Optional[Path] = None,
    smoke_test: bool = False,
):
    print("=" * 70)
    print("           MATHVISION CRNN LINE OCR FINE-TUNING")
    print("=" * 70)

    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 1. Device and Environment
    dev_str = cfg.get("training", {}).get("device", "auto")
    device = torch.device(
        ("cuda" if torch.cuda.is_available() else "cpu") if dev_str == "auto" else dev_str
    )
    print(f"Device : {device}")

    # 2. Vocabulary
    vocab_file = Path(cfg.get("model", {}).get("vocab_path", "configs/unified_vocab.json"))
    with open(vocab_file, "r", encoding="utf-8") as f:
        vocab = json.load(f)
    inv_vocab = {int(v): k for k, v in vocab.items()}
    vocab_size = len(vocab)
    blank_idx = vocab.get("<blank>", 0)
    print(f"Vocab size: {vocab_size} (blank={blank_idx})")

    # 3. Model instantiation
    CRNN = get_crnn_class()
    model = CRNN(num_classes=vocab_size, dropout=cfg.get("model", {}).get("dropout", 0.2))

    # Load adapted base weights
    base_ckpt_path = Path(cfg.get("model", {}).get("base_checkpoint", "artifacts/checkpoints/adapted_init.pth"))
    if base_ckpt_path.is_file():
        print(f"Loading warm-start base checkpoint: {base_ckpt_path}")
        state = torch.load(base_ckpt_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state, strict=True)
        print("✓ Base checkpoint loaded successfully.")
    else:
        print(f"[WARN] Base checkpoint not found at {base_ckpt_path}, starting from scratch.")

    model.to(device)

    # 4. Datasets & Loaders
    aug_cfg = cfg.get("augmentation", {})
    train_dataset = LineOCRDataset(train_manifest, vocab, is_train=True, aug_cfg=aug_cfg)
    val_dataset = LineOCRDataset(val_manifest, vocab, is_train=False)

    print(f"Train samples : {len(train_dataset)}")
    print(f"Val samples   : {len(val_dataset)}")

    if len(train_dataset) == 0:
        raise ValueError(f"No valid train samples found in manifest: {train_manifest}")

    batch_size = cfg.get("training", {}).get("batch_size", 8)
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_ocr_batch,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_ocr_batch,
    )

    # 5. Optimizer & Stage 1 Freeze
    stage1_freeze = cfg.get("optimizer", {}).get("stage1_freeze_backbone", True)
    stage1_steps = cfg.get("optimizer", {}).get("stage1_steps", 200)
    backbone_lr = float(cfg.get("optimizer", {}).get("backbone_lr", 1e-5))
    head_lr = float(cfg.get("optimizer", {}).get("head_lr", 1e-4))
    weight_decay = float(cfg.get("optimizer", {}).get("weight_decay", 1e-4))

    # Parameters grouping
    cnn_params = [p for n, p in model.named_parameters() if n.startswith("cnn.")]
    head_params = [p for n, p in model.named_parameters() if not n.startswith("cnn.")]

    if stage1_freeze:
        print(f"[STAGE 1] Freezing CNN backbone for first {stage1_steps} steps.")
        for p in cnn_params:
            p.requires_grad = False
        optimizer = torch.optim.AdamW(head_params, lr=head_lr, weight_decay=weight_decay)
    else:
        optimizer = torch.optim.AdamW([
            {"params": cnn_params, "lr": backbone_lr},
            {"params": head_params, "lr": head_lr},
        ], weight_decay=weight_decay)

    ctc_loss_fn = nn.CTCLoss(blank=blank_idx, zero_infinity=True)

    use_amp = cfg.get("training", {}).get("use_amp", True) and device.type == "cuda"
    scaler = torch.amp.GradScaler('cuda', enabled=use_amp)

    # Resumption
    global_step = 0
    start_epoch = 0
    best_cer = float("inf")
    patience_counter = 0

    if resume_path and resume_path.is_file():
        print(f"Resuming checkpoint from: {resume_path}")
        ckpt_data = torch.load(resume_path, map_location=device)
        model.load_state_dict(ckpt_data["model_state"])
        optimizer.load_state_dict(ckpt_data["optimizer_state"])
        if "scaler_state" in ckpt_data and use_amp:
            scaler.load_state_dict(ckpt_data["scaler_state"])
        global_step = ckpt_data.get("global_step", 0)
        start_epoch = ckpt_data.get("epoch", 0)
        best_cer = ckpt_data.get("best_cer", float("inf"))
        print(f"Resumed at step={global_step}, epoch={start_epoch}, best_cer={best_cer:.4f}")

    # Output dirs
    ckpt_dir = Path(cfg.get("output", {}).get("checkpoints_dir", "artifacts/checkpoints"))
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_file = ckpt_dir / "best_cer.pth"
    latest_ckpt_file = ckpt_dir / "latest_checkpoint.pth"

    # Training loop constants
    max_steps = 15 if smoke_test else cfg.get("training", {}).get("max_steps", 2000)
    val_interval = 5 if smoke_test else cfg.get("training", {}).get("val_check_interval", 50)
    clip_norm = float(cfg.get("regularization", {}).get("gradient_clip_norm", 5.0))
    min_steps_early_stop = cfg.get("early_stopping", {}).get("min_steps_before_early_stop", 150)
    patience = cfg.get("early_stopping", {}).get("patience", 8)
    blank_collapse_thresh = float(cfg.get("monitoring", {}).get("blank_collapse_threshold", 0.15))
    grad_accum_steps = cfg.get("training", {}).get("gradient_accumulation_steps", 1)

    print(f"\nStarting training: max_steps={max_steps}, val_interval={val_interval}, grad_accum={grad_accum_steps}...")

    is_stage2 = not stage1_freeze
    model.train()
    optimizer.zero_grad()

    stop_training = False
    epoch = start_epoch

    while global_step < max_steps and not stop_training:
        epoch += 1
        for batch_idx, (images, targets, target_lengths, texts) in enumerate(train_loader):
            # Stage transition
            if stage1_freeze and not is_stage2 and global_step >= stage1_steps:
                print(f"\n>>> [STAGE 2] Transition: Unfreezing CNN backbone at step {global_step}...")
                for p in cnn_params:
                    p.requires_grad = True
                optimizer = torch.optim.AdamW([
                    {"params": cnn_params, "lr": backbone_lr},
                    {"params": head_params, "lr": head_lr},
                ], weight_decay=weight_decay)
                is_stage2 = True

            images = images.to(device)
            targets = targets.to(device)

            with torch.amp.autocast('cuda', enabled=use_amp):
                logits = model(images)  # [B, T=128, C=vocab_size]
                log_probs = logits.log_softmax(2).permute(1, 0, 2)  # [T, B, C] for CTCLoss
                input_lengths = torch.full(size=(images.size(0),), fill_value=128, dtype=torch.long, device=device)
                loss = ctc_loss_fn(log_probs, targets, input_lengths, target_lengths)
                loss = loss / grad_accum_steps

            scaler.scale(loss).backward()

            if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip_norm)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                global_step += 1

                # Step logging
                loss_val = loss.item() * grad_accum_steps
                if global_step % 10 == 0 or smoke_test:
                    print(f"Step {global_step:>5}/{max_steps} | Epoch {epoch:>2} | Loss: {loss_val:.4f}")

                # Validation check
                if global_step % val_interval == 0 or global_step == max_steps:
                    val_metrics = evaluate_val_set(model, val_loader, inv_vocab, blank_idx, device)
                    v_cer = val_metrics["val_cer"]
                    v_em = val_metrics["val_exact_match"]
                    v_empty = val_metrics["val_empty_rate"]

                    print(f"\n--- [Validation @ Step {global_step}] ---")
                    print(f"  Val CER        : {v_cer:.4f} ({v_cer*100:.2f}%)")
                    print(f"  Val ExactMatch : {v_em:.4f}")
                    print(f"  Val EmptyRate  : {v_empty:.4f}")

                    # Monitor blank collapse
                    if v_empty > blank_collapse_thresh:
                        print(f"  [CTC_BLANK_COLLAPSE_WARNING] Empty prediction rate is abnormally high ({v_empty:.2%})!")

                    # Save latest checkpoint
                    torch.save({
                        "epoch": epoch,
                        "global_step": global_step,
                        "model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "scaler_state": scaler.state_dict() if use_amp else {},
                        "best_cer": best_cer,
                        "config": cfg,
                    }, latest_ckpt_file)

                    # Best CER update
                    if v_cer < best_cer:
                        best_cer = v_cer
                        patience_counter = 0
                        torch.save(model.state_dict(), best_ckpt_file)
                        print(f"  ✓ NEW BEST CER: {best_cer:.4f}! Saved to {best_ckpt_file.name}")
                    else:
                        if global_step >= min_steps_early_stop:
                            patience_counter += 1
                            print(f"  Patience counter: {patience_counter}/{patience}")
                            if patience_counter >= patience:
                                print(f"\n[Early Stopping] No improvement for {patience} validations. Stopping.")
                                stop_training = True
                                break
                        else:
                            print(f"  [Grace Period] Step {global_step} < {min_steps_early_stop}, early stop inhibited.")

                    print("-" * 40 + "\n")
                    model.train()

                if global_step >= max_steps or stop_training:
                    break

    print("\n" + "=" * 70)
    print("                 TRAINING FINISHED")
    print("=" * 70)
    print(f"  Final Step : {global_step}")
    print(f"  Best CER   : {best_cer:.4f}")
    print(f"  Saved to   : {best_ckpt_file}")

    # Drive backup in Colab
    drive_root = Path(cfg.get("output", {}).get("drive_backup_root", "/content/drive/MyDrive/MathVisionKid_AI/checkpoints"))
    if Path("/content/drive/MyDrive").exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = drive_root / f"run_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nBacking up best checkpoint to Google Drive: {backup_dir}")
        shutil.copy2(best_ckpt_file, backup_dir / "best_cer.pth")
        shutil.copy2(config_path, backup_dir / "config.yaml")
        print("✓ Google Drive backup completed.")

    return {
        "status": "PASS",
        "final_step": global_step,
        "best_cer": best_cer,
        "best_checkpoint": str(best_ckpt_file),
    }


def main():
    parser = argparse.ArgumentParser(description="Fine-tune MathVision CRNN line OCR.")
    parser.add_argument("--config", type=str, default="configs/train_finetune.yaml", help="Config YAML")
    parser.add_argument("--train_manifest", type=str, default="data/manifests/train.jsonl", help="Train manifest")
    parser.add_argument("--val_manifest", type=str, default="data/manifests/val.jsonl", help="Val manifest")
    parser.add_argument("--resume", type=str, default="", help="Path to checkpoint to resume from")
    parser.add_argument("--smoke_test", action="store_true", help="Run 5-10 steps for smoke testing")

    args = parser.parse_args()
    train_model(
        config_path=Path(args.config).resolve(),
        train_manifest=Path(args.train_manifest).resolve(),
        val_manifest=Path(args.val_manifest).resolve(),
        resume_path=Path(args.resume).resolve() if args.resume else None,
        smoke_test=args.smoke_test,
    )


if __name__ == "__main__":
    main()
