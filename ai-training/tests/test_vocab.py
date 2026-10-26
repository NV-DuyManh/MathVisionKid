"""Unit tests for vocabulary contracts, special math symbols, and Vietnamese diacritics."""
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def test_base_vocab_contract():
    vocab_path = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine" / "vocab.json"
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    assert len(vocab) == 320, f"Expected 320 tokens in base vocab, got {len(vocab)}"
    assert vocab.get("<blank>") == 0, "Blank token must be at index 0"

    # Check digits
    for d in "0123456789":
        assert d in vocab, f"Digit {d} missing"

    # Check common operators
    for op in ["+", "-", "=", "*", "/", ":"]:
        assert op in vocab, f"Operator {op} missing"


def test_unified_vocab_extended_symbols():
    vocab_path = _ROOT / "configs" / "unified_vocab.json"
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    assert len(vocab) >= 320, "Unified vocab must be >= base vocab"
    assert vocab.get("<blank>") == 0

    # Ensure multiplication symbol × (U+00D7) and division symbol ÷ (U+00F7) are present
    assert "×" in vocab, "Multiplication sign '×' must be in unified vocab"
    assert "÷" in vocab, "Division sign '÷' must be in unified vocab"
    assert "±" in vocab, "Plus-minus sign '±' must be in unified vocab"

    # Check math specials
    for sp in ["%", "°", "²", "³"]:
        assert sp in vocab, f"Math symbol {sp} missing"

    # Check Vietnamese diacritics
    viet_samples = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
    for c in viet_samples:
        assert c in vocab, f"Vietnamese char '{c}' missing"


def test_indices_are_contiguous():
    vocab_path = _ROOT / "configs" / "unified_vocab.json"
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    indices = sorted(vocab.values())
    expected = list(range(len(vocab)))
    assert indices == expected, "Vocab indices must be strictly contiguous 0..N-1"
