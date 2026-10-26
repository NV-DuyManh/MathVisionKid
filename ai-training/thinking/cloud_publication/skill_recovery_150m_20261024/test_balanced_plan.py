import copy
import unittest

from balanced_plan import prepare_plan


def row(sid, grade=1, topic="", mode="worked_solution", target=None,
        work=None, split="train", case="case", source=None):
    if target is None:
        target = {"can_solve": True, "answer": ["5"]}
    prompt = {"grade": grade, "problem": "2 + 3", "mode": mode}
    if work is not None:
        prompt["student_work"] = work
    return {
        "sample_id": sid, "split": split, "grade": grade, "topic": topic,
        "case_group_id": case, "source_sample_id": source,
        "mode": mode,
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": __import__("json").dumps(prompt)},
            {"role": "assistant", "content": __import__("json").dumps(target)},
        ],
    }


class BalancedPlanTests(unittest.TestCase):
    def test_deterministic_round_robin_and_target_dedup_with_provenance(self):
        rows = [
            row("a1", topic="addition", target={"answer": 5}),
            row("a2", topic="addition", target={"answer": 5}),
            row("a3", topic="addition", target={"answer": 6}),
            row("b1", topic="geometry", grade=2, target={"answer": 4}),
            row("c1", topic="measure", mode="hint_level_1", target={"hint": "count"}),
        ]
        original = copy.deepcopy(rows)
        first = prepare_plan(rows, "0" * 64, seed=7)
        second = prepare_plan(rows, "0" * 64, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(rows, original)
        self.assertEqual(first["view_rows"], 4)
        self.assertEqual({"b1", "c1"}, set(first["schedule"][:3]) & {"b1", "c1"})
        self.assertEqual(3, len({
            (next(r["grade"] for r in rows if r["sample_id"] == sid),
             next(r["topic"] for r in rows if r["sample_id"] == sid),
             next(r["mode"] for r in rows if r["sample_id"] == sid))
            for sid in first["schedule"][:3]
        }))
        rep = next(k for k, v in first["representative_provenance"].items() if set(v) == {"a1", "a2"})
        self.assertIn(rep, first["schedule"])
        self.assertEqual(first["source_rows_modified_or_deleted"], 0)
        self.assertNotEqual(first["source_raw_sha256"], first["selected_rows"][0]["canonical_embedded_row_sha256"])

    def test_blank_topics_partition_by_case_and_behavior_uses_actual_fields(self):
        rows = [
            row("guard", target={"can_solve": False, "answer": []}, case="same"),
            row("feedback", target={"can_solve": True, "answer": ["5"]}, work="4", case="same"),
            row("standard", target={"can_solve": True, "answer": ["5"]}, case="same"),
            row("other_case", target={"can_solve": True, "answer": ["5"]}, case="other"),
        ]
        plan = prepare_plan(rows, "1" * 64)
        self.assertEqual(plan["behavior_counts"], {"guard": 1, "student_feedback": 1, "standard": 2})
        self.assertEqual(plan["view_rows"], 4)
        self.assertTrue(all("unlabeled_case" in str(k) for k in plan["group_counts"]))

    def test_fails_closed_for_invalid_mode_duplicate_ids_and_nontrain(self):
        base = row("x")
        for rows in ([{**base, "mode": "guess"}], [base, copy.deepcopy(base)],
                     [{**base, "split": "dev"}]):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    prepare_plan(rows, "2" * 64)


if __name__ == "__main__":
    unittest.main()
