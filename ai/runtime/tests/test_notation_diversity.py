"""
Tests for PB20: Notation Diversity and Equivalent Representation Handling.
Verifies that valid equivalent mathematical notations and layouts (e.g. Unicode minus,
en-dash, em-dash, fullwidth symbols, leading zeros) are recognized, parsed, and validated
correctly without being falsely rejected.
"""

import pytest
from app.schemas.core import ImageRecognitionResult, Token
from app.parsing.parser import StructuredParser, normalize_operator
from app.validation.addition import VerticalAdditionValidator
from app.validation.subtraction import VerticalSubtractionValidator


def make_tokens(op1: str, op: str, op2: str, res: str):
    tokens = []
    # Row 0: op1
    for i, ch in enumerate(reversed(op1)):
        tokens.append(Token(
            tokenId=f"r0_c{i}",
            tokenClass="digit",
            value=ch,
            row=0,
            column=i,
            boundingBox=[0.0, 0.0, 10.0, 10.0],
            confidence=0.99
        ))
    # Row 1: op2
    for i, ch in enumerate(reversed(op2)):
        tokens.append(Token(
            tokenId=f"r1_c{i}",
            tokenClass="digit",
            value=ch,
            row=1,
            column=i,
            boundingBox=[0.0, 0.0, 10.0, 10.0],
            confidence=0.99
        ))
    # Row 1: operator
    tokens.append(Token(
        tokenId="op",
        tokenClass="operator",
        value=op,
        row=1,
        column=max(len(op1), len(op2)),
        boundingBox=[0.0, 0.0, 10.0, 10.0],
        confidence=0.99
    ))
    # Row 2: res
    for i, ch in enumerate(reversed(res)):
        tokens.append(Token(
            tokenId=f"r2_c{i}",
            tokenClass="digit",
            value=ch,
            row=2,
            column=i,
            boundingBox=[0.0, 0.0, 10.0, 10.0],
            confidence=0.99
        ))
    return tokens


def test_normalize_operator():
    assert normalize_operator("+") == "+"
    assert normalize_operator("\uff0b") == "+"
    assert normalize_operator("-") == "-"
    assert normalize_operator("\u2212") == "-"  # Unicode minus
    assert normalize_operator("\u2013") == "-"  # en-dash
    assert normalize_operator("\u2014") == "-"  # em-dash
    assert normalize_operator("\uff0d") == "-"  # fullwidth hyphen-minus
    assert normalize_operator(" * ") == "*"
    assert normalize_operator(None) is None


@pytest.mark.parametrize("minus_glyph", ["-", "\u2212", "\u2013", "\u2014", "\uff0d"])
def test_equivalent_subtraction_glyphs(minus_glyph):
    parser = StructuredParser()
    validator = VerticalSubtractionValidator()

    tokens = make_tokens("50", minus_glyph, "17", "33")
    rec = ImageRecognitionResult(tokens=tokens, status="SUCCESS")

    parsed = parser.parse(rec)
    assert parsed.status == "VALID_STRUCTURE"
    assert parsed.operationType == "VERTICAL_SUBTRACTION"

    val_res = validator.validate(parsed)
    assert val_res["is_valid"] is True
    assert len(val_res["evidence"]) == 0


@pytest.mark.parametrize("plus_glyph", ["+", "\uff0b"])
def test_equivalent_addition_glyphs(plus_glyph):
    parser = StructuredParser()
    validator = VerticalAdditionValidator()

    tokens = make_tokens("128", plus_glyph, "72", "200")
    rec = ImageRecognitionResult(tokens=tokens, status="SUCCESS")

    parsed = parser.parse(rec)
    assert parsed.status == "VALID_STRUCTURE"
    assert parsed.operationType == "VERTICAL_ADDITION"

    val_res = validator.validate(parsed)
    assert val_res["is_valid"] is True
    assert len(val_res["evidence"]) == 0


def test_subtraction_with_borrow_and_unicode_minus():
    parser = StructuredParser()
    validator = VerticalSubtractionValidator()

    # 402 - 185 = 217
    tokens = make_tokens("402", "\u2212", "185", "217")
    rec = ImageRecognitionResult(tokens=tokens, status="SUCCESS")

    parsed = parser.parse(rec)
    assert parsed.status == "VALID_STRUCTURE"
    val_res = validator.validate(parsed)
    assert val_res["is_valid"] is True


def test_addition_with_carry_and_fullwidth_plus():
    parser = StructuredParser()
    validator = VerticalAdditionValidator()

    # 999 + 1 = 1000
    tokens = make_tokens("999", "\uff0b", "1", "1000")
    rec = ImageRecognitionResult(tokens=tokens, status="SUCCESS")

    parsed = parser.parse(rec)
    assert parsed.status == "VALID_STRUCTURE"
    val_res = validator.validate(parsed)
    assert val_res["is_valid"] is True


def test_incorrect_calculation_detected_regardless_of_glyph():
    parser = StructuredParser()
    validator = VerticalSubtractionValidator()

    # 50 - 17 = 43 (wrong: forgot to borrow in tens column)
    tokens = make_tokens("50", "\u2212", "17", "43")
    rec = ImageRecognitionResult(tokens=tokens, status="SUCCESS")

    parsed = parser.parse(rec)
    assert parsed.status == "VALID_STRUCTURE"
    val_res = validator.validate(parsed)
    assert val_res["is_valid"] is False
    assert len(val_res["evidence"]) == 1
    assert val_res["evidence"][0]["type"] == "CARRY_BORROW_ERROR"
