import hashlib
import json
import unittest

import fewshot_contract as F


class FakeTokenizer:
    pad_token_id = 0

    def __init__(self, force_length=None):
        self.force_length = force_length

    def apply_chat_template(self, messages, **kwargs):
        if self.force_length is not None:
            return {"input_ids": [list(range(self.force_length))]}
        wire = json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ids = list(wire)
        return {"input_ids": ids}


def fixture(mode="answer"):
    return {
        "id": "fixture-secret-unique-7e2d",
        "grade": 4,
        "mode": mode,
        "userproblem": "Solve 9 + 8. REQUEST_WHOLE_INTACT",
        "expected_answer": "ORACLE_ANSWER_7319",
        "student_error_class": "ORACLE_STUDENT_ERROR_9271",
        "guard_label": "ORACLE_GUARD_1365",
    }


class FewshotContractTests(unittest.TestCase):
    def setUp(self):
        self.bank, self.bank_sha = F.load_and_validate_bank()

    def test_bank_integrity_source_ids_and_hashes(self):
        self.assertEqual(len(self.bank["entries"]), 9)
        self.assertEqual(self.bank_sha, hashlib.sha256(F.BANK_PATH.read_bytes()).hexdigest())
        for entry in self.bank["entries"]:
            self.assertEqual(entry["prompt_sha256"], F.digest(entry["actual_prompt"].encode()))
            self.assertEqual(entry["target_sha256"], F.digest(entry["actual_target"].encode()))
            self.assertEqual(len(entry["source_raw_row_sha256"]), 64)

    def test_selection_uses_requested_mode_only_and_final_request_is_intact(self):
        f = fixture("hint_no_answer")
        messages, ids = F.messages_with_examples(f, self.bank)
        expected = [e["sample_id"] for e in self.bank["entries"] if e["mode"] == "hint_level_1"]
        self.assertEqual(ids, expected)
        self.assertEqual(messages[-1], F.I.messages(f)[-1])
        rendered = "\n".join(m["content"] for m in messages)
        self.assertIn("REQUEST_WHOLE_INTACT", rendered)
        self.assertNotIn(f["id"], rendered)
        self.assertNotIn(f["expected_answer"], rendered)
        self.assertNotIn(f["student_error_class"], rendered)
        self.assertNotIn(f["guard_label"], rendered)
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user", "assistant", "user"])

    def test_every_requested_mode_selects_only_matching_examples(self):
        for mode in F.I.MODE_MAP:
            with self.subTest(mode=mode):
                _, ids = F.messages_with_examples(fixture(mode), self.bank)
                selected_modes = {entry["mode"] for entry in self.bank["entries"] if entry["sample_id"] in ids}
                self.assertEqual(selected_modes, {F.I.MODE_MAP[mode]})

    def test_prompt_token_hash_and_limit_are_explicit_no_truncation(self):
        f = fixture()
        tok = FakeTokenizer()
        encoded, _, _, token_sha = F.tokenize(tok, f, self.bank, max_prompt_tokens=10000)
        self.assertEqual(len(token_sha), 64)
        self.assertGreater(len(encoded["input_ids"]), 0)
        with self.assertRaisesRegex(ValueError, "refusing truncation"):
            F.tokenize(FakeTokenizer(force_length=33), f, self.bank, max_prompt_tokens=32)

    def test_contract_binds_bank_and_fixture_prompts(self):
        f = fixture("student_error")
        raw_dev_sha = "a" * 64
        contract, contract_sha = F.eval_contract(
            [f], FakeTokenizer(), fixture_sha256=raw_dev_sha,
            max_prompt_tokens=10000, frozen_fixture_ids=[f["id"], "other-frozen-id"],
        )
        self.assertEqual(contract["example_bank_sha256"], self.bank_sha)
        self.assertEqual(contract["fixture_ids"], [f["id"]])
        self.assertEqual(contract["frozen_fixture_ids"], [f["id"], "other-frozen-id"])
        self.assertEqual(contract["fixture_sha256"], raw_dev_sha)
        self.assertEqual(contract["example_selections_by_fixture"][f["id"]], [e["sample_id"] for e in self.bank["entries"] if e["mode"] == "worked_solution"])
        self.assertEqual(contract["decoding"]["max_new_tokens"], 1024)
        self.assertFalse(contract["enable_thinking"])
        self.assertEqual(len(contract_sha), 64)

    def test_generation_helper_rejects_unlabeled_adapter_stage_without_loading_runtime(self):
        with self.assertRaisesRegex(ValueError, "untrained-base stages"):
            F.generate_fixtures(None, None, [], ".", "adapter_after_training", {}, "", 1, None)

    def test_bank_tampering_fails_hash_validation(self):
        from pathlib import Path
        import tempfile
        raw = json.loads(F.BANK_PATH.read_bytes())
        raw["entries"][0]["actual_target"] += " changed"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bank.json"
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from source|hash mismatch"):
                F.load_and_validate_bank(path)


if __name__ == "__main__":
    unittest.main()

