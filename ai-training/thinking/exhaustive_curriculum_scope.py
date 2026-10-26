"""Source-bound numeric classification; every ordered input remains in the corpus.

``grade`` is a placement recommendation on enrichment rows, never evidence that
the operation is a required outcome in that grade. Positions are zero-based from
the units column. Borrow chains count every exchanged column, not only the first
column that requested an exchange. No assessment/evaluation data are read.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

VERSION = "numeric_curriculum_scope.v1"
CURRENT = "CURRENT_2018_NUMERIC_REFERENCE"
ENRICHMENT = "ENRICHMENT_BEYOND_SPECIFIC_OPERATION_BOUND"
EVIDENCE_PATH = "thinking/evidence/exhaustive_math_20261018/curriculum_2026_27_research.json"
EVIDENCE_SHA256 = "c40eb54a8a46f4e788ebaa19a30b44f27aeccc801ae0c6d9b8a9729c3698e076"
ANNEX_PATH = "thinking/evidence/exhaustive_math_20261018/curriculum_math2018_annex.pdf"
ANNEX_SHA256 = "f35d34ff84da2ca3f9ab72d5d67482ada414684b611deea98c4b329801b661ab"
ANNEX_URL = "https://storage-vnportal.vnpt.vn/edu-vtu/4803/2023/Thongtu32/3.-chuong-trinh-mon-toan.pdf"
BLUEPRINT_PATH = "thinking/data/primary_math_teacher_20261016/curriculum_blueprint.json"
BLUEPRINT_SHA256 = "c0fa09d55b29b86cdaae01d25fad1952f64df7b48c721c382043c6391ca2f8f7"


@lru_cache(maxsize=1)
def verify_source_evidence():
    """Fail closed on changed evidence; cached once per generator process."""
    root = Path(__file__).resolve().parent.parent
    for relative, expected in ((EVIDENCE_PATH, EVIDENCE_SHA256),
                               (ANNEX_PATH, ANNEX_SHA256),
                               (BLUEPRINT_PATH, BLUEPRINT_SHA256)):
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Curriculum evidence hash mismatch: {relative}")
    return True


def exchange_positions(op, a, b):
    """Compute column exchanges independently of a worked-trace renderer."""
    if op not in ("+", "-"):
        return []
    if a < 0 or b < 0 or (op == "-" and a < b):
        return []
    positions, incoming, place, index = [], 0, 1, 0
    while place <= max(a, b) or (op == "+" and incoming):
        x, y = a // place % 10, b // place % 10
        outgoing = int(x + y + incoming >= 10) if op == "+" else int(x - incoming < y)
        if outgoing:
            positions.append(index)
        incoming = outgoing
        index += 1
        place *= 10
    return positions


def _nonadjacent(positions):
    return all(y - x > 1 for x, y in zip(positions, positions[1:]))


def _given_positions(positions, op):
    if positions is None:
        return None
    if isinstance(positions, dict):
        positions = positions.get("carry_positions" if op == "+" else "borrow_positions")
    if positions is None:
        return None
    if not isinstance(positions, (list, tuple)) or any(type(x) is not int or x < 0 for x in positions):
        raise ValueError("positions must be a list of nonnegative zero-based column indices")
    return list(positions)


def classify(op, a, b, positions=None):
    """Classify an integer ordered pair without filtering or changing its values.

    This API classifies the generator's column-arithmetic / quotient-remainder
    representation, not every alternative mental strategy for the same numbers.
    Input trace positions are checked against canonical independent exchanges;
    canonical positions control the decision even when a renderer undercounts.
    """
    verify_source_evidence()
    aliases = {"×": "*", "÷": "/", ":": "/", "−": "-"}
    op = aliases.get(op, op)
    if op not in ("+", "-", "*", "/", "invalid_division"):
        raise ValueError(f"Unsupported operation: {op}")
    if type(a) is not int or type(b) is not int:
        raise TypeError("This numeric-reference classifier accepts exact integers only")
    actual = exchange_positions(op, a, b)
    supplied = _given_positions(positions, op) if op in ("+", "-") else None
    base = {
        "classifier_version": VERSION,
        "source_evidence": EVIDENCE_PATH + "#sha256=" + EVIDENCE_SHA256,
        "ordered_pair_retained": True,
        "exchange_positions": actual,
        "exchange_position_convention": "zero_based_units_first_every_column_exchange",
        "supplied_positions_match": None if supplied is None else supplied == actual,
        "has_consecutive_exchanges": not _nonadjacent(actual),
    }

    def answer(grade, scope, node, pages, reason, **extra):
        return {**base, "grade": grade, "curriculum_scope": scope,
                "current_node_id": node, "annex_pdf_pages_1based": pages,
                "grade_is_recommendation_only": scope == ENRICHMENT,
                "reason": reason, **extra}

    def enrich(reason, pages=(25, 29, 30, 35)):
        return answer(4, ENRICHMENT, None, list(pages),
                      reason + " Giữ nguyên cặp số làm bài mở rộng; lớp 4 chỉ là gợi ý bố trí, không phải khẳng định yêu cầu bắt buộc.")

    if a < 0 or b < 0:
        return enrich("Có toán hạng âm, vượt miền số tự nhiên của tham chiếu này.")
    if op in ("/", "invalid_division") and b == 0:
        return answer(3, CURRENT, "current_g3_multiply_divide_one_digit", [30],
                      "Nhận biết điều kiện số chia khác 0 qua quan hệ nhân ngược; đây là bài nhận biết phép chia không xác định, không có thương số học.",
                      numeric_answer_allowed=False, representation="division_by_zero_concept")
    if op == "invalid_division":
        raise ValueError("invalid_division requires a zero divisor")
    if op == "-" and a < b:
        return enrich("Hiệu âm không thuộc phép trừ số tự nhiên trong các giới hạn đã dẫn.")
    if op in ("+", "-"):
        result = a + b if op == "+" else a - b
        largest = max(a, b, result)
        count, nonadj = len(actual), _nonadjacent(actual)
        detail = f"{count} lượt đổi nhóm tại các cột {actual}; "
        if largest <= 100 and count == 0:
            return answer(1, CURRENT, "current_g1_addition_subtraction_no_carry", [22],
                          detail + "các số và kết quả trong phạm vi 100, không nhớ.")
        if largest <= 1000 and count <= 1:
            return answer(2, CURRENT, "current_g2_addition_subtraction_carry_once", [25],
                          detail + "các số và kết quả trong phạm vi 1000, không quá một lượt nhớ/mượn.")
        if largest <= 99999 and count <= 2 and nonadj:
            return answer(3, CURRENT, "current_g3_addition_subtraction_5digits", [29],
                          detail + "không quá hai lượt và không liên tiếp; các số và kết quả không quá 5 chữ số.")
        if largest <= 999999999 and count <= 3 and nonadj:
            return answer(4, CURRENT, "current_g4_addition_subtraction_many_digits", [34, 35],
                          detail + "không quá ba lượt và không liên tiếp; đặt trong miền số đến lớp triệu đã học. Đây là tham chiếu phép tính cụ thể, không bao phủ mọi bài nhiều chữ số.")
        return enrich(detail + "không đáp ứng giới hạn số chữ số hoặc số lượt/không liên tiếp của phép cộng, trừ được viện dẫn.")
    if op == "*":
        small, large = sorted((a, b))
        if a <= 10 and b <= 10 and (a in (2, 5) or b in (2, 5)):
            return answer(2, CURRENT, "current_g2_multiplication_division_tables_2_5", [25],
                          "Thuộc bảng nhân 2 hoặc 5 (thừa số còn lại từ 0 đến 10); hai thứ tự được xét cùng mức và vẫn giữ riêng từng cặp đầu vào.")
        # One-digit-factor algorithm, including zero/one conceptual cases.
        # The other factor's 5-digit ceiling is a conservative reference domain.
        carry, mulpositions, i, remaining = 0, [], 0, large
        while remaining or carry:
            total = remaining % 10 * small + carry
            carry = total // 10
            if remaining and carry:
                mulpositions.append(i)
            remaining //= 10
            i += 1
        if small <= 9 and large <= 99999 and len(mulpositions) <= 2 and _nonadjacent(mulpositions):
            return answer(3, CURRENT, "current_g3_multiply_divide_one_digit", [29, 30],
                          "Phép nhân có thừa số một chữ số, không quá hai lượt nhớ và không liên tiếp; các bảng ngoài 2/5 không gắn lớp 2. Không thay đổi thứ tự cặp gốc.",
                          multiplication_carry_positions=mulpositions)
        if small <= 99 and max(a, b, a * b) <= 999999999:
            return answer(4, CURRENT, "current_g4_multiply_divide_two_digits", [35],
                          "Phép nhân với thừa số không quá hai chữ số, trong miền đến lớp triệu; không dùng nhãn bảng nhân lớp 2 cho bảng khác.",
                          multiplication_carry_positions=mulpositions)
        return enrich("Phép nhân vượt miền tham chiếu có thừa số một/hai chữ số hoặc miền số đã giới hạn.")
    if b <= 9 and a <= 99999:
        return answer(3, CURRENT, "current_g3_multiply_divide_one_digit", [29, 30],
                      "Chia số tự nhiên không quá 5 chữ số cho số chia một chữ số khác 0; biểu diễn thương và số dư theo yêu cầu lớp 3, kể cả trường hợp chia hết.",
                      numeric_answer_allowed=True, representation="integer_quotient_remainder")
    if b <= 99 and a <= 999999999:
        return answer(4, CURRENT, "current_g4_multiply_divide_two_digits", [35],
                      "Số chia không quá hai chữ số và số bị chia trong miền đến lớp triệu.",
                      numeric_answer_allowed=True, representation="integer_quotient_remainder")
    return enrich("Số chia hoặc số bị chia vượt giới hạn cụ thể của tham chiếu phép chia này.")


def _self_test():
    cases = [
        ("+", 0, 0, [], 1, CURRENT),
        ("+", 9, 1, [0], 2, CURRENT),
        ("+", 99, 1, [0, 1], 4, ENRICHMENT),
        ("+", 999, 1, [0, 1, 2], 4, ENRICHMENT),
        ("-", 1000, 1, [0, 1, 2], 4, ENRICHMENT),
        ("-", 95, 88, [0], 2, CURRENT),
        ("+", 909, 101, [0, 2], 3, CURRENT),
        ("-", 909, 101, [], 2, CURRENT),
        ("+", 90909, 10101, [0, 2, 4], 4, CURRENT),
        ("+", 100000, 0, [], 4, CURRENT),
        ("*", 2, 9, [], 2, CURRENT),
        ("*", 9, 2, [], 2, CURRENT),
        ("*", 3, 9, [], 3, CURRENT),
        ("*", 9, 3, [], 3, CURRENT),
        ("*", 10, 10, [], 4, CURRENT),
        ("/", 1000, 9, [], 3, CURRENT),
        ("/", 0, 9, [], 3, CURRENT),
        ("/", 9, 0, [], 3, CURRENT),
        ("/", 0, 0, [], 3, CURRENT),
    ]
    reviewed = []
    for op, a, b, positions, grade, scope in cases:
        row = classify(op, a, b, positions)
        assert (row["grade"], row["curriculum_scope"]) == (grade, scope), (op, a, b, row)
        if op in ("+", "-"):
            assert row["supplied_positions_match"] is True
        reviewed.append({"operation": op, "a": a, "b": b, "classification": row})
    chain = classify("-", 1000, 1, [0])
    assert chain["supplied_positions_match"] is False and chain["curriculum_scope"] == ENRICHMENT
    for a in range(11):
        for b in range(11):
            left, right = classify("*", a, b), classify("*", b, a)
            assert (left["grade"], left["curriculum_scope"]) == (right["grade"], right["curriculum_scope"])
    assert classify("/", 0, 0)["numeric_answer_allowed"] is False
    return {"status": "PASS", "boundary_cases": len(cases), "multiplication_symmetry_pairs": 121,
            "borrow_chain_undercount_detected": True, "cases": reviewed}


if __name__ == "__main__":
    print(json.dumps(_self_test(), ensure_ascii=False, indent=2))
