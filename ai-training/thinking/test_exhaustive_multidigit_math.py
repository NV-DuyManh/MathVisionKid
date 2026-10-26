"""Adversarial tests, no payload materialization/network/model calls."""
from __future__ import annotations
import copy
import hashlib
import json
import random
import unittest
from pathlib import Path

import exhaustive_multidigit_math as m


class MultidigitTests(unittest.TestCase):
    def row(self, op, a, b):
        row = m.make_row(op, a, b)
        self.assertTrue(m.validate_row(row)["validated"])
        return row

    def test_one_two_three_digit_factors_and_carries(self):
        for a, b in ((89, 7), (567, 89), (999, 999), (208, 304),
                     (1001, 101), (99, 99), (999999, 999)):
            with self.subTest(a=a, b=b):
                row = self.row("*", a, b)
                self.assertEqual(row["expected_answer"][0]["result"], str(a * b))

    def test_zero_one_powers_of_ten(self):
        for pair in ((0, 999), (999, 0), (1, 809), (809, 1), (709, 10),
                     (709, 100), (709, 1000), (1000, 1000), (0, 0)):
            with self.subTest(pair=pair):
                self.row("*", *pair)

    def test_ordered_pairs_share_commutative_group_not_id(self):
        a, b = self.row("*", 12, 47), self.row("*", 47, 12)
        self.assertNotEqual(a["sample_id"], b["sample_id"])
        self.assertEqual(a["case_group_id"], b["case_group_id"])
        self.assertEqual(a["sample_id"], "exhaustive_v1_mul_12_47")

    def test_regression1563_43(self):
        row = self.row("/", 1563, 43)
        self.assertEqual([x["result"] for x in row["expected_answer"]], ["36", "15"])
        self.assertFalse(row["training_eligible"])
        self.assertFalse(row["evaluation_eligible"])
        self.assertEqual(list(m.chat_records(row)), [])
        mutated = copy.deepcopy(row)
        mutated["training_eligible"] = True
        with self.assertRaises(ValueError):
            m.validate_row(mutated)

    def test_adjacent_division_variants_and_exact_identity(self):
        for a, b in ((1562, 43), (1564, 43), (1548, 43), (1577, 43),
                     (9999, 99), (123456, 123), (997002, 999)):
            row = self.row("/", a, b)
            self.assertEqual(list(map(int, [x["result"] for x in row["expected_answer"]])), list(divmod(a, b)))

    def test_quotient_internal_and_trailing_zero_digits(self):
        for a, b, q in ((12012, 12, 1001), (1005, 5, 201),
                        (10101, 101, 100), (5005, 55, 91),
                        (1001, 10, 100), (100000, 100, 1000)):
            row = self.row("/", a, b)
            self.assertEqual(row["expected_answer"][0]["result"], str(q))
            written = [d["quotient_digit"] for d in row["operation_metadata"]["long_division_digits"]
                       if d["quotient_digit_written"]]
            self.assertEqual("".join(map(str, written)), str(q))

    def test_less_than_divisor_and_zero_dividend(self):
        for a, b in ((0, 10), (0, 999), (9, 10), (100, 999), (17, 43)):
            row = self.row("/", a, b)
            self.assertEqual([x["result"] for x in row["expected_answer"]], ["0", str(a)])

    def test_invalid_division_guard(self):
        for a in (0, 1, 1563):
            row = self.row("/", a, 0)
            self.assertEqual(row["coverage"]["operation"], "invalid_division")
            self.assertTrue(all(s["expression"] is None for s in row["worked_steps"]))
            self.assertIn("không xác định", row["expected_answer"][0]["result"])

    def test_addition_and_zero_borrow_chain(self):
        for op, a, b in (("+", 999, 1), ("+", 90909, 10101),
                         ("+", 123, 456), ("-", 10000, 1),
                         ("-", 100000, 99999), ("-", 843, 421)):
            self.row(op, a, b)

    def test_actual_mutated_answer_trace_and_hint_rejected(self):
        examples = [("*", 208, 304), ("/", 12012, 12)]
        for args in examples:
            row = self.row(*args)
            bad = copy.deepcopy(row)
            bad["expected_answer"][0]["result"] = "666"
            with self.assertRaises(ValueError):
                m.validate_row(bad)
            bad = copy.deepcopy(row)
            bad["hints"][0]["hint"] += " Đáp số 666."
            with self.assertRaises(ValueError):
                m.validate_row(bad)
            bad = copy.deepcopy(row)
            if args[0] == "*":
                bad["operation_metadata"]["multiplication_partial_products"][0]["columns"][0]["outgoing_carry"] += 1
            else:
                cell = bad["operation_metadata"]["long_division_digits"][1]
                cell["quotient_digit_written"] = not cell["quotient_digit_written"]
            with self.assertRaises(ValueError):
                m.validate_row(bad)

    def test_modulo_metadata_only(self):
        row = self.row("/", 1587, 43)
        self.assertEqual(row["operation_metadata"]["modulo_oracle_metadata_only"], "1587%43")
        bad = copy.deepcopy(row)
        bad["worked_steps"][0]["expression"] = "1587%43"
        with self.assertRaises(ValueError):
            m.validate_row(bad)

    def test_all_four_modes_same_group_and_truthful_provenance(self):
        row = self.row("*", 99, 101)
        chat = list(m.chat_records(row))
        self.assertEqual(len(chat), 4)
        self.assertEqual(len({c["case_group_id"] for c in chat}), 1)
        for c in chat:
            self.assertEqual([x["role"] for x in c["messages"]], ["system", "user", "assistant"])
            self.assertEqual(c["acceptance_status"], m.ACCEPTANCE)
            self.assertFalse(c["human_verified"])
            self.assertFalse(c["teacher_certified"])
        # Hints are input-independent and contain no decimal digits; this
        # supplementary check is not the semantic-meaning review.
        for op in ("*", "/"):
            self.assertFalse(any(c.isdecimal() for h in m.hints(op) for c in h["hint"] + h["question"]))

    def test_finite_domains_complete_disjoint_previous_excluded(self):
        seen = set()
        for spec in m.finite_domain_specs():
            count = 0
            for a, b in m.iter_domain_pairs(spec):
                key = (spec["operation"], a, b)
                self.assertNotIn(key, seen)
                seen.add(key)
                if spec["operation"] == "*":
                    self.assertFalse(a <= 10 and b <= 10)
                count += 1
            self.assertEqual(count, spec["expected_pairs"])
        self.assertEqual(sum(x["expected_pairs"] for x in m.finite_domain_specs() if x["operation"] == "*"), 10080)
        self.assertEqual(sum(x["expected_pairs"] for x in m.finite_domain_specs() if x["operation"] == "/"), 99990)

    def test_stable_content_hash(self):
        for args in (("*", 208, 304), ("/", 12012, 12), ("+", 999, 1)):
            a = m.validate_row(m.make_row(*args))["row_sha256"]
            b = m.validate_row(m.make_row(*args))["row_sha256"]
            self.assertEqual(a, b)

    def test_seeded_independent_numeric_and_trace_oracles(self):
        rng = random.Random(20261018)
        for _ in range(300):
            self.row("*", rng.randint(0, 999999), rng.randint(0, 999))
            self.row("/", rng.randint(0, 99999999), rng.randint(1, 999))

    def test_bad_inputs_fail_explicitly(self):
        for args in (("-", 1, 2), ("*", True, 2), ("*", 1001, 1001),
                     ("+", -1, 2), ("+", 9999999, 1), ("invalid_division", 4, 2)):
            with self.assertRaises(ValueError):
                m.make_row(*args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
