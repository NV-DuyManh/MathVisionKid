import json
import unittest

import behavior_renderer as B
import fewshot_contract as F
import inference_contract as I
import selected_inference_runtime as R


def selection(**updates):
    value = json.loads(R.SELECTION_PATH.read_text(encoding="utf-8"))
    for key, item in updates.items():
        if key in R.LEGAL_MODES:
            value["mode_selection"][key] = item
        else:
            value[key] = item
    return value


class FakeTokenizer:
    pad_token_id = 0

    def __init__(self, force_length=None):
        self.force_length = force_length

    def apply_chat_template(self, messages, **kwargs):
        if self.force_length is not None:
            return list(range(self.force_length))
        return list(json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def fixture(mode, problem="Solve 2 + 3. KEEP_THIS_REQUEST_WHOLE", grade=2):
    return {"id": "fixture-id-SECRET", "grade": grade, "mode": mode, "userproblem": problem}


class SelectedInferenceRuntimeTests(unittest.TestCase):
    def test_actual_standard_work_and_hint2_3_messages_match_contract_prompt(self):
        problem = "Problem intact 12 + 5. KEEP_THIS_REQUEST_WHOLE"
        for mode, request_mode in (("worked_solution", "answer"), ("hint_level_2", "hint_no_answer"),
                                   ("hint_level_3", "hint_no_answer")):
            with self.subTest(mode=mode):
                actual = R.messages_for_request(problem, 2, mode, selection())
                if mode == "worked_solution":
                    self.assertEqual(actual, I.messages(fixture(request_mode, problem)))
                else:
                    self.assertEqual(actual, [
                        {"role": "system", "content": B.SYSTEM},
                        {"role": "user", "content": B.prompt({"grade": 2, "problem": problem, "mode": mode})},
                    ])

    def test_selected_hint1_fewshot_matches_f_and_keeps_raw_request_last(self):
        problem = "A whole hint request 1.3 - 0.4."
        actual = R.messages_for_request(problem, 5, "hint_level_1", selection())
        expected, source_ids = F.messages_with_examples(fixture("hint_no_answer", problem, 5))
        self.assertEqual(actual, expected)
        self.assertEqual(len(source_ids), 2)
        self.assertEqual(actual[-1], {"role": "user", "content": B.prompt({"grade": 5, "problem": problem, "mode": "hint_level_1"})})

    def test_actual_selection_rejects_ineligible_worked_and_hint2_3_fewshot(self):
        for mode in ("worked_solution", "hint_level_2", "hint_level_3"):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "not marked eligible|not validated"):
                R.messages_for_request("Bài toán.", 3, mode, selection(**{mode: "fewshot_contract"}))

    def test_unknown_mode_grade_and_selection_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "Unsupported tutor mode"):
            R.messages_for_request("Bài", 2, "oracle_mode", selection())
        with self.assertRaisesRegex(ValueError, "Grade"):
            R.messages_for_request("Bài", True, "worked_solution", selection())
        with self.assertRaisesRegex(ValueError, "schema"):
            R.messages_for_request("Bài", 2, "worked_solution", {"mode_selection": {}})
        bad = selection()
        bad["mode_selection"]["worked_solution"] = "oracle_route"
        with self.assertRaisesRegex(ValueError, "Unknown mode selection"):
            R.messages_for_request("Bài", 2, "worked_solution", bad)

    def test_selection_metadata_and_fixture_oracle_are_not_prompt_messages(self):
        msgs = R.messages_for_request("Problem intact.", 1, "hint_level_1", selection())
        rendered = "\n".join(item["content"] for item in msgs)
        for secret in ("baseline_output_sha256", "root_semantic_review_sha256", "eligible_by_model_mode", "fixture-id-SECRET", "expected_answer"):
            self.assertNotIn(secret, rendered)

    def test_real_frozen_selection_bank_and_module_hashes_validate(self):
        current = selection()
        modes, selection_sha = R.validate_selection(current)
        self.assertEqual(modes["hint_level_1"], "fewshot_contract")
        self.assertEqual(modes["worked_solution"], "inference_contract")
        self.assertEqual(selection_sha, R._sha(R.SELECTION_PATH.read_bytes()))
        self.assertEqual(current["bank_sha256"], R._sha(F.BANK_PATH.read_bytes()))

    def test_bad_freeze_eligibility_hashes_and_missing_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, "before final-test"):
            R.validate_selection(selection(selected_before_final_test=False))
        partial = selection()
        del partial["mode_selection"]["hint_level_3"]
        with self.assertRaisesRegex(ValueError, "exactly the four"):
            R.validate_selection(partial)
        with self.assertRaisesRegex(ValueError, "example-bank SHA256"):
            R.validate_selection(selection(bank_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "inference-module SHA256"):
            R.validate_selection(selection(inference_module_sha256={"fewshot_contract": "0" * 64, "inference_contract": "0" * 64}))

    def test_prompt_over_limit_fails_without_truncation(self):
        with self.assertRaisesRegex(ValueError, "truncation is forbidden"):
            R.tokenize_request(FakeTokenizer(force_length=101), "Bài", 2, "worked_solution", selection(), max_prompt_tokens=100)

    def test_prompt_hash_protocol_and_source_example_ids_are_returned(self):
        encoded, msgs, ids, prompt_sha, selection_sha = R.tokenize_request(
            FakeTokenizer(), "Bài intact.", 4, "hint_level_1", selection(), max_prompt_tokens=10000,
        )
        self.assertEqual(len(prompt_sha), 64)
        self.assertEqual(selection_sha, R._sha(R.SELECTION_PATH.read_bytes()))
        self.assertEqual(ids, [e["sample_id"] for e in F.load_and_validate_bank()[0]["entries"] if e["mode"] == "hint_level_1"])
        self.assertEqual(msgs[-1]["content"], B.prompt({"grade": 4, "problem": "Bài intact.", "mode": "hint_level_1"}))
        self.assertGreater(len(encoded), 0)


if __name__ == "__main__":
    unittest.main()
