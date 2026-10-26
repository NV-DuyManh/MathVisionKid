import hashlib
import json
import unittest
from pathlib import Path

import build_source_example_bank as B


class SourceExampleBankTests(unittest.TestCase):
    def setUp(self):
        self.bank = B.build_bank()

    def test_exact_required_counts_and_fixed_order(self):
        expected = {
            "worked_solution": [
                "exhaustive_v1_sub_565_103:worked_solution",
                "primary_20261018_finish_g5_decimal_read_compare_more_digits_not_larger:worked_solution",
                "sgk_gap_20261019_g4_data_reconstruction_guard:worked_solution",
            ],
            "hint_level_1": ["exhaustive_v1_sub_565_103:hint_level_1", "exhaustive_v1_div_788_1:hint_level_1"],
            "hint_level_2": ["exhaustive_v1_sub_565_103:hint_level_2", "exhaustive_v1_div_788_1:hint_level_2"],
            "hint_level_3": ["exhaustive_v1_sub_565_103:hint_level_3", "exhaustive_v1_div_788_1:hint_level_3"],
        }
        self.assertEqual(self.bank["mode_counts"], {k: len(v) for k, v in expected.items()})
        for mode, ids in expected.items():
            self.assertEqual([e["sample_id"] for e in B.select_examples(self.bank, mode)], ids)

    def test_prompt_and_target_are_exact_source_strings_and_hashes(self):
        projection, _ = B.read_json(B.PROJECTION)
        behavior, _ = B.read_json(B.BEHAVIOR)
        sources = {x["sample_id"]: x for x in projection["samples"] + behavior["samples"]}
        for entry in self.bank["entries"]:
            source = sources[entry["sample_id"]]
            self.assertEqual(entry["actual_prompt"], source["actual_prompt"])
            self.assertEqual(entry["actual_target"], source["actual_target"])
            self.assertEqual(entry["source_raw_row_sha256"], source["source_original_raw_row_sha256"])
            self.assertEqual(entry["prompt_sha256"], hashlib.sha256(entry["actual_prompt"].encode()).hexdigest())
            self.assertEqual(entry["target_sha256"], hashlib.sha256(entry["actual_target"].encode()).hexdigest())

    def test_mode_selector_and_message_order_are_stable(self):
        mode = "hint_level_2"
        selected = B.select_examples(self.bank, mode)
        messages = B.messages_for_mode(self.bank, mode, "system")
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user", "assistant"])
        self.assertEqual([messages[i]["content"] for i in (1, 3)], [e["actual_prompt"] for e in selected])
        self.assertEqual([messages[i]["content"] for i in (2, 4)], [e["actual_target"] for e in selected])
        self.assertEqual(messages[0], {"role": "system", "content": "system"})
        with self.assertRaises(ValueError):
            B.select_examples(self.bank, "hint_oracle")

    def test_bank_contains_no_behavior_or_attestation_fields(self):
        self.assertIsNone(self.bank["human_or_teacher_attestation"])
        forbidden = {"behavior", "student_work_present", "human_reviewed", "acceptance", "teacher_label"}
        for entry in self.bank["entries"]:
            self.assertTrue(forbidden.isdisjoint(entry))

    def test_character_counts_are_not_reported_as_tokens(self):
        self.assertIsNone(self.bank["token_count"])
        self.assertIn("not token estimates", self.bank["token_count_note"])
        for entry in self.bank["entries"]:
            self.assertEqual(entry["prompt_chars"], len(entry["actual_prompt"]))
            self.assertEqual(entry["target_chars"], len(entry["actual_target"]))


if __name__ == "__main__":
    unittest.main()
