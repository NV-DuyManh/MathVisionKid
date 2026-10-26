"""Independent exact arithmetic checks for the freshly authored fixtures."""
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "locked_test_candidates.jsonl"
OUT = HERE / "authoring_exact_checks.json"

checks = {
    "fresh_01": Fraction(4 * 6),
    "fresh_02": Fraction(3 + 5),
    "fresh_05": Fraction(8 * 3),
    "fresh_06": Fraction(37 + 19),
    "fresh_09": {"quotient": 45 // 6, "remainder": 45 % 6},
    "fresh_10": Fraction(3, 4) * 4,
    "fresh_13": Fraction(180, 3),
    "fresh_14": Fraction(3, 5) * 40,
    "fresh_17": Fraction(2, 5) * 45,
    "fresh_18": Fraction(12 * 5 * 4),
    "fresh_20_conflict_area_from_dimensions": Decimal(5) * Decimal(4),
}


def render(value):
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


rows = [json.loads(line) for line in FIXTURES.read_text(encoding="utf-8").splitlines() if line.strip()]
by_id = {row["id"]: row for row in rows}
assert len(rows) == 20 and len(by_id) == 20
for grade in range(1, 6):
    subset = [r for r in rows if r["grade"] == grade]
    assert len(subset) == 4
    assert sum(r["mode"] == "answer" for r in subset) == 2
    assert sum(r["mode"] == "hint_no_answer" for r in subset) == 1
for row in rows:
    assert row["not_training_data"] is True
    if row["mode"] == "hint_no_answer":
        assert row["exact_reference_answer"] is None

computed = {key: render(value) for key, value in checks.items()}
expected_answers = {
    "fresh_01": "24", "fresh_02": "8", "fresh_05": "24", "fresh_06": "56",
    "fresh_09": {"quotient": 7, "remainder": 3}, "fresh_10": "3",
    "fresh_13": "60", "fresh_14": "24", "fresh_17": "18", "fresh_18": "240",
    "fresh_20_conflict_area_from_dimensions": "20",
}
assert computed == expected_answers, computed
for fid in ("fresh_01", "fresh_02", "fresh_05", "fresh_06", "fresh_10", "fresh_13", "fresh_14", "fresh_17", "fresh_18"):
    assert computed[fid] in by_id[fid]["exact_reference_answer"]
assert computed["fresh_09"]["quotient"] == 7 and computed["fresh_09"]["remainder"] == 3
receipt = {
    "schema": "MathVisionKid.fixture_authoring_exact_checks.v1",
    "status": "passed",
    "method": "Python Fraction and Decimal arithmetic, independently checked against fixture references",
    "fixture_count": len(rows),
    "computed_values": computed,
    "source_code": "authoring_exact_checks.py",
    "human_certification": False,
}
OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, ensure_ascii=False))
