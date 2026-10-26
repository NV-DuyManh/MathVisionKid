import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
import unicodedata

import exhaustive_colab_loader as loader


def rows(sid="a", group=None, split="train", topic="arithmetic"):
    for mode in loader.MODES:
        yield {"sample_id": sid + ":" + mode, "source_sample_id": sid,
               "case_group_id": group or sid, "split": split, "mode": mode,
               "topic": topic, "grade": 3,
               "messages": [{"role": "system", "content": "Gia sư toán."},
                            {"role": "user", "content": json.dumps({"problem": "Bài toán " + sid, "mode": mode})},
                            {"role": "assistant", "content": json.dumps({"answer": "bằng nhau"})}]}


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        result = {"shards": []}
        for number in range(2):
            path = self.root / f"{number}.jsonl.gz"
            with path.open("wb") as output:
                # Real concatenated GZIP members, not one synthetic member.
                for row in rows(str(number)):
                    output.write(gzip.compress((loader.canonical_json(row) + "\n").encode(), mtime=0))
            result["shards"].append({"file_id": str(number), "file_name": path.name,
                                      "sha256": loader.file_hash(path), "bytes": path.stat().st_size,
                                      "chat_rows": 4, "kind": "chat_gzip"})
        return result

    def test_multimember_and_two_shards(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        self.assertEqual(len(list(stream)), 8)

    def test_train_split_never_yields_validation_or_test_even_mixed_shard(self):
        path = self.root / "mixed.jsonl.gz"
        values = list(rows("a")) + list(rows("b", split="validation")) + list(rows("c", split="test"))
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            for value in values:
                stream.write(loader.canonical_json(value) + "\n")
        manifest = {"parts": [{"file_name": path.name, "sha256": loader.file_hash(path), "chat_rows": 12}]}
        train = loader.ManifestStream(manifest, self.root).for_split("train")
        actual = list(train)
        self.assertEqual(len(actual), 4)
        self.assertEqual({r["split"] for r in actual}, {"train"})

    def test_tokenized_consumer_requires_explicit_split(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        with self.assertRaisesRegex(ValueError, "explicit split"):
            next(loader.tokenized_stream(stream, None))

    def test_resume_cursor_is_bound_to_split(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        cursor = next(stream.for_split("train").iter_with_cursors())[1]
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            list(stream.for_split("validation").iter_with_cursors(cursor))

    def test_resume_after_interruption_exact_next_row(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        iterator = stream.iter_with_cursors()
        consumed = [next(iterator) for _ in range(5)]
        iterator.close()
        resumed = list(stream.iter_with_cursors(consumed[-1][1]))
        self.assertEqual(len(resumed), 3)
        self.assertEqual([r[0]["sample_id"] for r in consumed + resumed], [r["sample_id"] for r in stream])

    def test_manifest_change_rejects_resume(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        cursor = next(stream.iter_with_cursors())[1]
        with self.assertRaisesRegex(ValueError, "manifest changed"):
            list(loader.ManifestStream(self.manifest() | {"revision": 2}, self.root).iter_with_cursors(cursor))

    def test_hash_corruption_before_first_row(self):
        manifest = self.manifest()
        manifest["shards"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA256"):
            next(iter(loader.ManifestStream(manifest, self.root)))

    def test_wrong_row_count(self):
        manifest = self.manifest()
        manifest["shards"][0]["chat_rows"] = 5
        with self.assertRaisesRegex(ValueError, "row count"):
            list(loader.ManifestStream(manifest, self.root))

    def test_path_escape(self):
        manifest = self.manifest()
        manifest["shards"][0]["file_name"] = "../escape.gz"
        with self.assertRaisesRegex(ValueError, "escapes"):
            list(loader.ManifestStream(manifest, self.root))

    def test_id_path_mapping(self):
        manifest = self.manifest()
        manifest["shards"][0]["file_name"] = "unknown.gz"
        stream = loader.ManifestStream(manifest, self.root, {"0": "0.jsonl.gz"})
        self.assertEqual(len(list(stream)), 8)

    def test_cursor_beyond_eof(self):
        stream = loader.ManifestStream(self.manifest(), self.root)
        with self.assertRaisesRegex(ValueError, "beyond"):
            list(stream.iter_with_cursors(loader.Cursor(stream.manifest_sha256, 0, 99)))

    def test_schema_role_order(self):
        row = next(rows())
        row["messages"].reverse()
        with self.assertRaises(ValueError):
            loader.validate_chat(row)

    def test_balancing_preserves_mandatory_and_modes(self):
        source = list(rows("baseline", topic="pedagogy")) + [r for i in range(10) for r in rows(str(i))]
        selected, receipt = loader.selected_view(lambda: iter(source), mandatory_ids=["baseline"], optional_cases_per_category=2)
        self.assertEqual(len(list(selected())), 12)
        self.assertEqual(receipt["selected_cases"], 3)
        self.assertFalse(receipt["full_corpus_changed"])

    def test_balancing_deterministic_reverse_input(self):
        source = [r for i in range(30) for r in rows(str(i))]
        _, first = loader.selected_view(lambda: iter(source), optional_cases_per_category=3)
        _, second = loader.selected_view(lambda: iter(reversed(source)), optional_cases_per_category=3)
        self.assertEqual(first["selected_case_ids"], second["selected_case_ids"])

    def test_protected_kept_in_source_not_training(self):
        source = list(rows())
        selected, receipt = loader.selected_view(lambda: iter(source), {"a": {"canonical_signatures": ["p"]}}, ["p"], ["a"])
        self.assertEqual(len(source), 4)
        self.assertEqual(list(selected()), [])
        self.assertEqual(receipt["excluded_cases"]["a"]["reason"], "PROTECTED_CANONICAL_OVERLAP")

    def test_missing_mode_fails(self):
        source = list(rows())[:3]
        selected, _ = loader.selected_view(lambda: iter(source))
        with self.assertRaisesRegex(ValueError, "lacks modes"):
            list(selected())

    def test_holdout_precedes_training_for_every_input_order(self):
        source = list(rows("train")) + list(rows("held", split="test"))
        index = {sid: {"canonical_signatures": ["shared"]} for sid in ("train", "held")}
        for sequence in (source, list(reversed(source))):
            selected, receipt = loader.selected_view(lambda: iter(sequence), index, mandatory_ids=["train"])
            self.assertEqual({r["split"] for r in selected()}, {"test"})
            self.assertEqual(receipt["excluded_cases"]["train"]["reason"], "NEW_HOLDOUT_OVERLAP")

    def test_holdout_group_and_question_filter(self):
        source = list(rows("train", group="same")) + list(rows("held", group="same", split="validation"))
        selected, receipt = loader.selected_view(lambda: iter(source), mandatory_ids=["train"])
        self.assertEqual(len(list(selected())), 4)
        self.assertIn("group", receipt["excluded_cases"]["train"]["overlap_kinds"])

    def test_fraction_decimal_and_associative_signatures(self):
        def signature(expression):
            return loader.source_signatures({"worked_steps": [{"expression": expression}]})[0]
        self.assertEqual(signature("0.50 + 2"), signature("2 + 0.5"))
        self.assertEqual(signature("(1+2)+3"), signature("3+(2+1)"))
        self.assertNotEqual(signature("1/2"), signature("2/1"))
        self.assertEqual(len(signature("0.1 * (1/3)")), 64)

    def test_source_duplicate_rejected(self):
        path = self.root / "source.jsonl"
        path.write_text('{"sample_id":"a"}\n' * 2, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate source"):
            loader.load_source_index([path])

    def test_prior_step_reference_expands_and_checks_literal(self):
        signatures = set(loader.source_signatures({"worked_steps": [
            {"expression": "12+5", "result": "17"},
            {"expression": "{s0}-4", "result": "13"}]}))
        symbolic = loader.source_signatures({"worked_steps": [{"expression": "(12+5)-4"}]})[0]
        literal = loader.source_signatures({"worked_steps": [{"expression": "17-4"}]})[0]
        self.assertTrue({symbolic, literal} <= signatures)
        with self.assertRaisesRegex(ValueError, "unresolvable"):
            loader.source_signatures({"worked_steps": [{"expression": "{s0}+1"}]})

    def test_modulo_oracle_metadata_participates_in_protection(self):
        self.assertEqual(loader.source_signatures({"canonical_case": {"operations": ["1563%43"]}}),
                         loader.source_signatures({"worked_steps": [{"expression": "1563%43"}]}))

    def test_negative_cap_rejected(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            loader.selected_view(lambda: rows(), optional_cases_per_category=-1)

    def test_padding_attention_and_loss_mask(self):
        result = loader.pad_batch([{"input_ids": [1, 2], "attention_mask": [1, 1], "labels": [-100, 2]},
                                   {"input_ids": [3], "attention_mask": [1], "labels": [3]}])
        self.assertEqual(result["input_ids"][1], [3, 151643])
        self.assertEqual(result["attention_mask"][1], [1, 0])
        self.assertEqual(result["labels"][1], [3, -100])

    def test_question_unicode_normalization(self):
        first = next(rows())
        first["messages"][1]["content"] = json.dumps({"problem": "Bài toán:  Tổng"}, ensure_ascii=False)
        second = json.loads(json.dumps(first))
        second["messages"][1]["content"] = unicodedata.normalize("NFD", json.dumps({"problem": "bài toán: tổng"}, ensure_ascii=False))
        self.assertEqual(loader.question_key(first), loader.question_key(second))

    def test_derived_chat_hash_checked_without_relabeling_original(self):
        row = next(rows())
        row["selected_view_origin_chat_sha256"] = "1" * 64
        row["row_sha256"] = loader.digest_bytes(loader.canonical_json(row).encode())
        loader.validate_chat(row)
        row["grade"] = 5
        with self.assertRaisesRegex(ValueError, "derived row hash"):
            loader.validate_chat(row)

    def test_duplicate_sample(self):
        audit = loader.SplitAudit()
        row = next(rows())
        audit.add(row)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit.add(row)
        audit.close()

    def test_group_split_leak(self):
        audit = loader.SplitAudit()
        audit.add(next(rows("a", group="shared")))
        with self.assertRaisesRegex(ValueError, "group overlap"):
            audit.add(next(rows("b", group="shared", split="test")))
        audit.close()

    def test_numeric_split_leak(self):
        audit = loader.SplitAudit()
        audit.add(next(rows("a")), ["canonical"])
        with self.assertRaisesRegex(ValueError, "canonical overlap"):
            audit.add(next(rows("b", split="validation")), ["canonical"])
        audit.close()

    def test_categorical_answer_preserved(self):
        row = next(rows())
        loader.validate_chat(row)
        self.assertEqual(json.loads(row["messages"][2]["content"])["answer"], "bằng nhau")


class ActualQwenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots" / loader.REVISION
        if not cache.exists():
            raise unittest.SkipTest("official cached tokenizer not present")
        cls.tokenizer = loader.load_qwen_tokenizer(cache)

    def test_exact_eot_mask(self):
        encoded = loader.tokenize_assistant_only(next(rows()), self.tokenizer)
        labels = [value for value in encoded["labels"] if value != -100]
        self.assertEqual(labels[-1], 151645)
        self.assertEqual(labels.count(151645), 1)
        self.assertTrue(all(value == -100 for value in encoded["labels"][:encoded["prompt_tokens"]]))
        self.assertEqual(len(encoded["input_ids"]), len(encoded["labels"]))

    def test_no_truncation(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            loader.tokenize_assistant_only(next(rows()), self.tokenizer, max_sequence_tokens=1)

    def test_embedded_end_token_rejected(self):
        row = next(rows())
        row["messages"][-1]["content"] = "giả <|im_end|>"
        with self.assertRaises(ValueError):
            loader.tokenize_assistant_only(row, self.tokenizer)

    def test_full_audit_all_modes(self):
        receipt = loader.full_token_audit(rows(), self.tokenizer)
        self.assertEqual(receipt["unique_samples"], 4)
        self.assertEqual(set(receipt["by_mode"]), set(loader.MODES))


if __name__ == "__main__":
    unittest.main(verbosity=2)
