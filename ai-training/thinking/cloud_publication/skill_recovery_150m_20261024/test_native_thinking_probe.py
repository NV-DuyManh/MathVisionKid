import unittest
import hashlib
import json
import pathlib
import sys
import tempfile
import time
from unittest.mock import patch

import behavior_renderer as B
import inference_contract as I
import native_thinking_probe as N


def fixtures():
    selected_grade = {index: offset % 5 + 1 for offset, index in enumerate(N.DEV_INDICES)}
    selected_mode = {}
    grade_seen = {grade: 0 for grade in range(1, 6)}
    for offset, index in enumerate(N.DEV_INDICES):
        grade = selected_grade[index]
        seen = grade_seen[grade]
        selected_mode[index] = "answer" if seen < 2 else ("student_error" if grade % 2 else "missing_or_contradictory_info")
        grade_seen[grade] += 1
    return [{"id": f"dev-{i}", "grade": selected_grade.get(i, i % 5 + 1),
             "mode": selected_mode.get(i, "hint_no_answer"),
             "userproblem": f"Whole request {i} intact."} for i in range(30)]


class FakeTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        import json
        return list(json.dumps([messages, kwargs.get("enable_thinking")], ensure_ascii=False).encode())


class FakeIds(list):
    @property
    def shape(self):
        return (1, len(self[0]))

    def to(self, _device):
        return self


class FakeTokenRow(list):
    def tolist(self):
        return list(self)


class FakeInputIds:
    def __init__(self):
        self.row = FakeTokenRow([11, 22, 33])
        self.shape = (1, 3)

    def __getitem__(self, index):
        if index == 0:
            return self.row
        raise IndexError(index)


class FakeBatch(dict):
    def __init__(self):
        super().__init__(input_ids=FakeInputIds())

    def to(self, _device):
        return self


class FakeResult:
    def __getitem__(self, key):
        return [151645]


class FakeTorch:
    @staticmethod
    def manual_seed(_seed):
        return None

    class cuda:
        @staticmethod
        def manual_seed_all(_seed):
            return None

    class inference_mode:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False


class FakeGenerationConfig(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class NativeThinkingProbeTests(unittest.TestCase):
    def test_dev_subset_is_exact_fixed_order_and_grade_stratified(self):
        selected = N.select_dev(fixtures())
        self.assertEqual([int(x["id"].split("-")[1]) for x in selected], N.DEV_INDICES)
        self.assertEqual(len(selected), 15)
        self.assertEqual({g: sum(x["grade"] == g for x in selected) for g in range(1, 6)}, {1: 3, 2: 3, 3: 3, 4: 3, 5: 3})
        self.assertEqual(sum(x["mode"] == "answer" for x in selected), 10)
        self.assertEqual(sum(x["mode"] in ("student_error", "missing_or_contradictory_info") for x in selected), 5)

    def test_build_messages_is_original_i_prompt_and_contains_no_fixture_metadata(self):
        f = fixtures()[6]
        actual = N.build_messages(f)
        self.assertEqual(actual, I.messages(f))
        self.assertEqual(actual[-1]["content"], B.prompt({
            "grade": f["grade"], "problem": f["userproblem"],
            "mode": I.MODE_MAP[f["mode"]],
        }))
        self.assertNotIn(f["id"], actual[-1]["content"])

    def test_prompt_hashes_bind_native_and_nonthinking_templates(self):
        selected = N.select_dev(fixtures())[:2]
        think = N.prompt_hashes(FakeTokenizer(), selected, True)
        plain = N.prompt_hashes(FakeTokenizer(), selected, False)
        self.assertEqual(set(think), {f["id"] for f in selected})
        self.assertTrue(all(len(x) == 64 for x in think.values()))
        self.assertNotEqual(think, plain)

    def test_extraction_requires_eos_closed_think_and_nonempty_answer(self):
        self.assertEqual(N.extract_final("reason</think>final answer<|im_end|>", True, True, False), "final answer")
        self.assertEqual(N.extract_final("complete answer<|im_end|>", False, True, False), "complete answer")
        for args, error in [
            (("reason", True, True, False), "closed final-answer"),
            (("</think>", True, True, False), "no final answer"),
            (("answer", False, False, False), "truncated"),
            (("answer", False, True, False, True), "reached max_new_tokens"),
            (("answer", False, True, True), "timed out"),
        ]:
            with self.subTest(error=error), self.assertRaisesRegex((ValueError, TimeoutError), error):
                N.extract_final(*args)

    def test_scope_is_phase_specific_and_hash_pinned(self):
        scope = {"schema": "MathVisionKid.native_probe_scope.v1", "dev_fixture_sha256": "a" * 64,
                 "selection_policy_sha256": "b" * 64}
        N.validate_scope(scope, "dev")
        with self.assertRaisesRegex(ValueError, "missing"):
            N.validate_scope(scope, "final")
        N.validate_scope({**scope, "native_locked15_sha256": "c" * 64}, "final")
        with self.assertRaisesRegex(ValueError, "Invalid scope SHA"):
            N.validate_scope({**scope, "dev_fixture_sha256": "x" * 64}, "dev")

    def test_final_gate_binds_candidate_dev_output_and_policy(self):
        scope = {"selection_policy_sha256": "b" * 64}
        good = {"schema": "MathVisionKid.native_probe_gate.v1", "candidate_eligible": True,
                "dev_output_sha256": "a" * 64, "policy_sha256": "b" * 64}
        N.validate_final_gate(good, scope, "a" * 64)
        for changed in (
            {**good, "candidate_eligible": False},
            {**good, "dev_output_sha256": "c" * 64},
            {**good, "policy_sha256": "d" * 64},
            {**good, "schema": "wrong"},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                N.validate_final_gate(changed, scope, "a" * 64)

    def test_mocked_generation_runs_contract_hash_and_prompt_hash_validation(self):
        fixture = fixtures()[N.DEV_INDICES[0]]
        prompt_sha = I.digest(I.canonical([11, 22, 33]).encode())
        contract = {"prompt_token_sha256": {"native_thinking": {fixture["id"]: prompt_sha}}}
        contract_sha = I.digest(I.canonical(contract).encode())

        class Tok:
            pad_token_id = 0
            def apply_chat_template(self, *_args, **_kwargs):
                return FakeBatch()
            def decode(self, _tokens, skip_special_tokens=False):
                return "reasoning</think>Final answer<|im_end|>"

        class Model:
            def eval(self):
                return None
            def generate(self, **_kwargs):
                return FakeResult()

        class Fast:
            @staticmethod
            def for_inference(_model):
                return None

        fake_transformers = type("FakeTransformers", (), {"GenerationConfig": FakeGenerationConfig})
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, {"torch": FakeTorch, "transformers": fake_transformers}):
            out = pathlib.Path(tmp)
            records, output_sha = N.run_generation(
                Model(), Tok(), [fixture], out, "native_thinking", True,
                {"max_new_tokens": 1536}, contract, contract_sha,
                time.time() + 30, {"phase": "dev"},
            )
            self.assertEqual(records[0]["final_output"], "Final answer")
            self.assertEqual(records[0]["prompt_token_sha256"], prompt_sha)
            self.assertEqual(len(output_sha), 64)
            raw = json.loads((out / "native_thinking_raw.jsonl").read_text(encoding="utf-8"))
            self.assertIn("reasoning</think>", raw["raw_output"])
            self.assertFalse((out / "native_thinking_raw.jsonl").read_text(encoding="utf-8").find("final_output") >= 0)

    def test_contract_pins_protocol_fixture_bytes_and_mode(self):
        selected = N.select_dev(fixtures())
        c = N.make_contract(selected, "a" * 64, "dev")
        self.assertEqual(c["fixture_sha256"], "a" * 64)
        self.assertEqual(c["fixture_ids"], [x["id"] for x in selected])
        self.assertTrue(c["enable_thinking"])
        self.assertEqual(c["thinking_decoding"]["temperature"], .6)
        self.assertEqual(c["thinking_decoding"]["max_new_tokens"], 1536)
        final = N.make_contract(fixtures()[:15], "c" * 64, "final")
        self.assertEqual(final["base_decoding"]["temperature"], .7)
        self.assertEqual(final["base_decoding"]["max_new_tokens"], 1024)

    def test_dev_requires_exactly_thirty_unique_fixtures(self):
        with self.assertRaisesRegex(ValueError, "exactly 30"):
            N.select_dev(fixtures()[:-1])
        duplicate = fixtures()
        duplicate[-1]["id"] = duplicate[0]["id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            N.select_dev(duplicate)
        wrong_mode = fixtures()
        wrong_mode[N.DEV_INDICES[0]]["mode"] = "hint_no_answer"
        with self.assertRaisesRegex(ValueError, "two answer tasks"):
            N.select_dev(wrong_mode)


if __name__ == "__main__":
    unittest.main()
