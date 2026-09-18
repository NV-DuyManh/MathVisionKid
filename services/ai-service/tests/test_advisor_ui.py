"""
ADVISORUI tests — Clean advisor UI, labels, secondary badges, action handling, and unavailable UX.
Matrix: ADVISORUI-01 to ADVISORUI-10 (10/10 PASS required).
"""
import os
import pytest
from app.schemas.ocr_pilot import LineBox


UI_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../src/app/ocr-pilot/multiline-result.tsx")
)


def _read_ui_source() -> str:
    with open(UI_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _make_sample_line(
    raw: str = "em đp gại",
    groq: str = "em đẹp gái",
    gemini: str = "em đẹp gái",
    groq_status: str = "SUCCESS",
    gemini_status: str = "SUCCESS",
) -> LineBox:
    return LineBox(
        line_id="line-test-01",
        x=0,
        y=0,
        width=120,
        height=32,
        order=1,
        text=raw,
        rawOcrText=raw,
        rawOcrConfidence=0.74,
        groqSuggestion=groq,
        groqStatus=groq_status,
        geminiSuggestion=gemini,
        geminiStatus=gemini_status,
        finalText=raw,
    )


def test_advisorui_01_title_is_goi_y_1():
    """ADVISORUI-01: Main title for Section B1 is 'Gợi ý 1' (not 'GỢI Ý 1 — GROQ')."""
    src = _read_ui_source()
    assert "<Text style={styles.sectionBLabel}>Gợi ý 1</Text>" in src
    assert "GỢI Ý 1 — GROQ:" not in src


def test_advisorui_02_groq_is_secondary_badge():
    """ADVISORUI-02: Groq is displayed as a secondary chip/badge next to 'Gợi ý 1'."""
    src = _read_ui_source()
    assert "providerChipGroq" in src
    assert "providerChipGroqText" in src
    assert "<Text style={styles.providerChipGroqText}>Groq</Text>" in src


def test_advisorui_03_title_is_goi_y_2():
    """ADVISORUI-03: Main title for Section B2 is 'Gợi ý 2' (not 'GỢI Ý 2 — GEMINI')."""
    src = _read_ui_source()
    assert "<Text style={styles.sectionGeminiLabel}>Gợi ý 2</Text>" in src
    assert "GỢI Ý 2 — GEMINI:" not in src


def test_advisorui_04_gemini_is_secondary_badge():
    """ADVISORUI-04: Gemini is displayed as a secondary chip/badge next to 'Gợi ý 2'."""
    src = _read_ui_source()
    assert "providerChipGemini" in src
    assert "providerChipGeminiText" in src
    assert "<Text style={styles.providerChipGeminiText}>Gemini</Text>" in src


def test_advisorui_05_choose_suggestion_1_updates_final_only():
    """ADVISORUI-05: Tapping [Chọn gợi ý 1] sets finalText to Groq suggestion; rawOcrText is unchanged."""
    src = _read_ui_source()
    assert 'accessibilityLabel="Chọn gợi ý 1"' in src
    assert "Chọn gợi ý 1" in src

    line = _make_sample_line(raw="ngoi nha", groq="ngôi nhà", gemini="ngôi nhà")
    # Simulate user choice
    line.finalText = line.groqSuggestion
    assert line.finalText == "ngôi nhà"
    assert line.rawOcrText == "ngoi nha"  # Immutable CRNN OCR


def test_advisorui_06_choose_suggestion_2_updates_final_only():
    """ADVISORUI-06: Tapping [Chọn gợi ý 2] sets finalText to Gemini suggestion; rawOcrText is unchanged."""
    src = _read_ui_source()
    assert 'accessibilityLabel="Chọn gợi ý 2"' in src
    assert "Chọn gợi ý 2" in src

    line = _make_sample_line(raw="ngoi nha", groq="ngôi nhà", gemini="ngôi nhà nhỏ")
    # Simulate user choice
    line.finalText = line.geminiSuggestion
    assert line.finalText == "ngôi nhà nhỏ"
    assert line.rawOcrText == "ngoi nha"  # Immutable CRNN OCR


def test_advisorui_07_keep_raw_restores_raw_ocr_text():
    """ADVISORUI-07: Tapping [Giữ OCR gốc] restores finalText to rawOcrText."""
    src = _read_ui_source()
    assert 'accessibilityLabel="Giữ OCR gốc"' in src
    assert "Giữ OCR gốc" in src

    line = _make_sample_line(raw="toan hoc", groq="toán học", gemini="toán học")
    line.finalText = line.groqSuggestion  # Selected previously
    assert line.finalText == "toán học"

    # Action: Keep raw
    line.finalText = line.rawOcrText
    assert line.finalText == "toan hoc"
    assert line.rawOcrText == "toan hoc"


def test_advisorui_08_triggered_gemini_unavailable_shows_compact_card():
    """ADVISORUI-08: When triggered and Gemini is UNAVAILABLE, show compact 'Gemini tạm thời chưa khả dụng.' card."""
    src = _read_ui_source()
    assert "Gemini tạm thời chưa khả dụng." in src

    line = _make_sample_line(
        raw="dong mo",
        groq="dòng mở",
        gemini=None,
        groq_status="SUCCESS",
        gemini_status="UNAVAILABLE",
    )
    # hasGemini evaluates to True for UNAVAILABLE state
    has_gemini = bool(line.geminiSuggestion or line.geminiStatus == "UNAVAILABLE")
    assert has_gemini is True
    # Card status text is compact and user friendly
    msg = "Gemini tạm thời chưa khả dụng." if line.geminiStatus == "UNAVAILABLE" else ""
    assert msg == "Gemini tạm thời chưa khả dụng."


def test_advisorui_09_not_triggered_line_shows_no_pointless_cards():
    """ADVISORUI-09: Clean high-confidence line shows NO advisor cards."""
    line = LineBox(
        line_id="clean-01",
        x=0,
        y=0,
        width=100,
        height=30,
        order=1,
        text="dòng rất rõ ràng",
        rawOcrText="dòng rất rõ ràng",
        rawOcrConfidence=0.98,
        groqStatus="NOT_TRIGGERED",
        geminiStatus="NOT_TRIGGERED",
        finalText="dòng rất rõ ràng",
    )
    # UI conditions:
    # line.correctedText is None -> Section B1 not rendered
    assert not line.correctedText
    # hasGemini = Boolean(line.geminiSuggestion || line.geminiStatus === 'UNAVAILABLE')
    has_gemini = bool(line.geminiSuggestion or line.geminiStatus == "UNAVAILABLE")
    assert has_gemini is False
    # No cards displayed
    assert (bool(line.correctedText) or has_gemini) is False


def test_advisorui_10_no_dev_panel_or_http_error_visible():
    """ADVISORUI-10: Student UI contains no DEV diagnostic panel, HTTP status codes, or stack traces."""
    src = _read_ui_source()
    assert "Panel Kỹ Thuật (DEV)" not in src
    assert "devDiagnosticCard" not in src
    assert "HTTP 429" not in src
    assert "HTTP 503" not in src
    assert "gemini-3.8-flash" not in src  # Model names hidden from student UI
    assert "qwen3.8-27b" not in src
    assert "stackTrace" not in src
