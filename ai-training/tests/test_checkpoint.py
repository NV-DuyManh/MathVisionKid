"""Unit tests for OCR checkpoint loading, weights integrity, and parameter contracts."""
import pytest
import torch
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def test_base_checkpoint_exists():
    ckpt_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "best_cer.pth"
    assert ckpt_path.is_file(), f"Base checkpoint not found at {ckpt_path}"


def test_base_checkpoint_strict_load():
    import importlib.util
    model_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    ckpt_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "best_cer.pth"

    spec = importlib.util.spec_from_file_location("m_mod", str(model_path))
    m_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m_mod)

    model = m_mod.CRNN(num_classes=320)
    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)

    param_count = sum(p.numel() for p in model.parameters())
    assert param_count == 5962560, f"Expected 5,962,560 params, got {param_count}"


def test_forward_pass_shape():
    import importlib.util
    model_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    spec = importlib.util.spec_from_file_location("m_mod2", str(model_path))
    m_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m_mod)

    model = m_mod.CRNN(num_classes=320)
    dummy_input = torch.randn(2, 3, 64, 1024)
    model.eval()
    with torch.no_grad():
        out = model(dummy_input)

    assert out.shape == (2, 128, 320), f"Unexpected output shape: {out.shape}"


def test_adapted_checkpoint_forward():
    adapted_ckpt = _ROOT / "artifacts" / "checkpoints" / "adapted_init.pth"
    if not adapted_ckpt.is_file():
        pytest.skip("adapted_init.pth not yet created")

    import json
    import importlib.util
    vocab_path = _ROOT / "configs" / "unified_vocab.json"
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    model_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "model.py"
    spec = importlib.util.spec_from_file_location("m_mod3", str(model_path))
    m_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m_mod)

    model = m_mod.CRNN(num_classes=len(vocab))
    state = torch.load(adapted_ckpt, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)

    dummy_input = torch.randn(1, 3, 64, 1024)
    model.eval()
    with torch.no_grad():
        out = model(dummy_input)
    assert out.shape == (1, 128, len(vocab))
