import copy
import json
import unittest

import behavior_renderer as R


def source_row(mode="worked_solution", problem="Tính 2 + 3.", student_work=None):
    prompt = {"grade": 2, "problem": problem, "mode": mode}
    if student_work is not None:
        prompt["student_work"] = student_work
    if mode == "worked_solution":
        target = {
            "can_solve": True,
            "initial_guidance": ["Cộng theo phép tính đã cho."],
            "steps": [{"title": "Tính", "reason": "Thực hiện phép cộng.", "expression": "2+3", "result": "5", "explanation": "2 cộng 3 bằng 5."}],
            "answer": [{"quantity": "Tổng", "result": "5"}],
        }
    else:
        target = {"hint": "Xét hai số hạng.", "question": "Em sẽ cộng theo cách nào?"}
    return {
        "sample_id": "sample-1",
        "case_group_id": "case-1",
        "mode": mode,
        "split": "train",
        "messages": [
            {"role": "system", "content": "old system"},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            {"role": "assistant", "content": json.dumps(target, ensure_ascii=False)},
        ],
        "human_reviewed": True,
        "acceptance": "old-label",
    }


class BehaviorRendererTests(unittest.TestCase):
    def test_exact_duplicate_work_and_excerpt_are_not_repeated(self):
        row = source_row(
            problem="Bạn viết 2+3=6.",
            student_work={"text": "Bạn viết 2+3=6.", "observations": [{"excerpt": "Bạn viết 2+3=6."}]},
        )
        projected, _ = R.render(row)
        prompt = projected["messages"][1]["content"]
        self.assertEqual(prompt.count("Bạn viết 2+3=6."), 1)
        self.assertIn("Chế độ: Giải đầy đủ", prompt)
        self.assertLess(prompt.index("Chế độ: Giải đầy đủ"), prompt.index("Bạn viết 2+3=6."))
        self.assertEqual(prompt.count("Yêu cầu:"), 1)

    def test_distinct_work_and_excerpt_are_preserved(self):
        row = source_row(
            student_work={"text": "Em trả lời 6.", "observations": [{"excerpt": "Em quên nhớ một đơn vị."}]},
        )
        projected, _ = R.render(row)
        prompt = projected["messages"][1]["content"]
        self.assertIn("Em trả lời 6.", prompt)
        self.assertIn("Em quên nhớ một đơn vị.", prompt)

    def test_same_prompt_function_covers_all_four_modes(self):
        for mode in ("worked_solution", "hint_level_1", "hint_level_2", "hint_level_3"):
            with self.subTest(mode=mode):
                prompt = R.prompt({"grade": 2, "problem": "Bài toán.", "mode": mode})
                self.assertIn(R._MODE_HEADERS[mode], prompt)
                self.assertEqual(prompt.count("Yêu cầu:"), 1)
                self.assertTrue(prompt.endswith(R._MODE_INSTRUCTIONS[mode]))

    def test_target_is_exact_v3_target_and_row_is_immutable(self):
        row = source_row()
        before = copy.deepcopy(row)
        projected, proof = R.render(row)
        target, _ = R.V3.target(json.loads(row["messages"][2]["content"]), row["mode"])
        self.assertEqual(projected["messages"][2]["content"], target)
        self.assertEqual(row, before)
        self.assertEqual(proof["target_sha256"], R._sha(target.encode("utf-8")))
        self.assertFalse(proof["source_attestation_carried_forward"])
        self.assertNotIn("human_reviewed", projected)
        self.assertNotIn("acceptance", projected)

    def test_unknown_prompt_fields_fail_closed(self):
        with self.assertRaises(ValueError):
            R.prompt({"grade": 2, "problem": "Bài toán.", "mode": "worked_solution", "invented": True})

    def test_unknown_target_fields_fail_closed(self):
        row = source_row()
        target = json.loads(row["messages"][2]["content"])
        target["invented"] = "field"
        row["messages"][2]["content"] = json.dumps(target)
        with self.assertRaises(ValueError):
            R.render(row)


if __name__ == "__main__":
    unittest.main()

