import json
import unittest

from balanced_plan_v2 import prepare_plan


def make_row(sid, grade, topic, mode, behavior="standard", answer="a", split="train"):
    prompt = {"grade": grade, "problem": "fixture", "mode": mode}
    target = {"answer": answer}
    if behavior == "student_feedback":
        prompt["student_work"] = "student text"
    elif behavior == "guard":
        target["can_solve"] = False
    return {
        "sample_id": sid, "split": split, "grade": grade, "topic": topic,
        "case_group_id": sid, "mode": mode,
        "messages": [
            {"role": "system", "content": "s"},
            {"role": "user", "content": json.dumps(prompt)},
            {"role": "assistant", "content": json.dumps(target)},
        ],
    }


class BalancedPlanV2Tests(unittest.TestCase):
    def test_grade_and_mode_behavior_prefix_coverage_under_grade1_skew(self):
        rows = [make_row(f"g1-{i}", 1, f"topic-{i:03}", "worked_solution", answer=str(i)) for i in range(120)]
        for grade in range(2, 6):
            rows.append(make_row(f"g{grade}-worked", grade, f"topic-g{grade}", "worked_solution", answer=f"w{grade}"))
            rows.append(make_row(f"g{grade}-hint", grade, f"topic-g{grade}", "hint_level_1", answer=f"h{grade}"))
        rows.extend([
            make_row("g5-guard", 5, "guard-topic", "worked_solution", "guard"),
            make_row("g5-feedback", 5, "feedback-topic", "worked_solution", "student_feedback"),
        ])
        plan = prepare_plan(rows, "a" * 64, seed=33)
        by_id = {r["sample_id"]: r for r in rows}
        prefix5 = [by_id[sid] for sid in plan["schedule"][:5]]
        self.assertEqual({1, 2, 3, 4, 5}, {r["grade"] for r in prefix5})
        first_few = [by_id[sid] for sid in plan["schedule"][:32]]
        self.assertTrue({"worked_solution", "hint_level_1"}.issubset({r["mode"] for r in first_few}))
        self.assertIn("guard", {x["behavior"] for x in plan["selected_rows"][:32]})
        self.assertIn("student_feedback", {x["behavior"] for x in plan["selected_rows"][:32]})
        self.assertEqual(len(plan["schedule"]), len(set(plan["schedule"])))
        self.assertEqual(len(rows), plan["source_rows"])

    def test_dedup_ids_provenance_and_sha_fail_closed(self):
        rows = [
            make_row("one", 1, "add", "worked_solution", answer="same"),
            make_row("two", 1, "add", "worked_solution", answer="same"),
        ]
        plan = prepare_plan(rows, "b" * 64)
        self.assertEqual(plan["view_rows"], 1)
        self.assertEqual(set(next(iter(plan["representative_provenance"].values()))), {"one", "two"})
        for bad in ("z" * 64, "a" * 63, "a" * 65):
            with self.assertRaises(ValueError):
                prepare_plan(rows, bad)

    def test_invalid_modes_duplicates_and_nontrain_fail_closed(self):
        row = make_row("id", 1, "x", "worked_solution")
        invalid_mode = dict(row, mode=[])
        for fixture in ([invalid_mode], [row, dict(row)], [dict(row, split="dev")]):
            with self.subTest():
                with self.assertRaises(ValueError):
                    prepare_plan(fixture, "c" * 64)


if __name__ == "__main__":
    unittest.main()
