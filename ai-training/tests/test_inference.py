"""Unit tests for inference module, batching, and error handling."""
import pytest
from pathlib import Path
from PIL import Image

_ROOT = Path(__file__).resolve().parent.parent


def test_predict_text_on_sample():
    eng_dir = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine"
    sample_img = eng_dir / "samples" / "sample_01.jpg"
    if not sample_img.is_file():
        pytest.skip("sample_01.jpg not found")

    import sys
    if str(eng_dir) not in sys.path:
        sys.path.insert(0, str(eng_dir))

    from predict import predict_text
    text = predict_text(str(sample_img))
    assert isinstance(text, str)
    assert len(text) > 5, f"Prediction text too short: '{text}'"


def test_predict_batch():
    eng_dir = _ROOT / "handoff" / "staging" / "ocr_engine_handoff_final" / "ocr_engine"
    samples = list((eng_dir / "samples").glob("*.jpg"))[:3]
    if not samples:
        pytest.skip("No sample images found")

    import sys
    if str(eng_dir) not in sys.path:
        sys.path.insert(0, str(eng_dir))

    from predict import predict_batch
    batch_res = predict_batch([str(s) for s in samples], batch_size=2)
    assert len(batch_res) == len(samples)
    for t in batch_res:
        assert isinstance(t, str)
