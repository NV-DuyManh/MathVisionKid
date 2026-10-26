"""Adversarial handoff/lease, immutable payload and resumable audit tests."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import math_data_portable_resume as P
import math_data_archive_audit as A
import exhaustive_colab_loader as L


def checkpoint():
    return P.new_checkpoint({"state": {"file_id": "same-existing-id", "sha256": "a" * 64, "bytes": 5}},
                            [{"profile_id": "historical-data-owner"}])


def work(c):
    return P.add_task(c, P.task_spec("audit", [{"sha256": "b" * 64}], {"revision": L.REVISION}))


def rows(split="train", prefix="a", group="group"):
    for mode in L.MODES:
        yield {"sample_id": prefix + ":" + mode, "source_sample_id": prefix, "case_group_id": group,
               "mode": mode, "split": split, "canonical_signatures": [],
               "messages": [{"role": "system", "content": "Tutor"},
                            {"role": "user", "content": json.dumps({"problem": "one question"})},
                            {"role": "assistant", "content": "answer"}]}


class PortableTests(unittest.TestCase):
    def test_rebind_read_does_not_imply_update(self):
        c = checkpoint()
        observations = {"state": {**c["artifacts"]["state"], "fresh_raw_verified": True}}
        original = deepcopy(c)
        self.assertEqual(P.rebind(c, "chosen", "chosen", observations)["access"], "read")
        self.assertEqual(c, original)
        with self.assertRaisesRegex(ValueError, "update rights"):
            P.rebind(c, "chosen", "chosen", observations, "update")
        observations["state"]["can_update"] = True
        self.assertEqual(P.rebind(c, "chosen", "chosen", observations, "update")["access"], "update")

    def test_wrong_profile_id_hash_rejected(self):
        c = checkpoint()
        observations = {"state": {**c["artifacts"]["state"], "fresh_raw_verified": True}}
        with self.assertRaises(ValueError):
            P.rebind(c, "chosen", "other", observations)
        for field, value in [("file_id", "duplicate"), ("sha256", "c" * 64), ("bytes", 6)]:
            wrong = deepcopy(observations); wrong["state"][field] = value
            with self.assertRaises(ValueError):
                P.rebind(c, "chosen", "chosen", wrong)

    def test_same_content_task_dedup_and_frozen_guard(self):
        c = checkpoint(); key = work(c)
        self.assertEqual(key, work(c)); self.assertEqual(len(c["tasks"]), 1)
        with self.assertRaisesRegex(ValueError, "frozen"):
            P.task_spec("audit", [{"sha256": "b" * 64, "role": "frozen_evaluation"}])
        with self.assertRaises(ValueError):
            P.task_spec("audit", [{"sha256": "b" * 64}], {"link_id": "runtime-only"})
        self.assertEqual(P.task_spec('audit',[{'sha256':'b'*64,'file_id':'same-data-A'}]),
                         P.task_spec('audit',[{'sha256':'b'*64,'file_id':'same-data-B'}]))
        with self.assertRaisesRegex(ValueError, 'runtime identity'):
            P.task_spec('audit',[{'sha256':'b'*64}], {'selected_profile':'account-A'})

    def test_expired_worker_cannot_finish_after_reclaim(self):
        c = checkpoint(); key = work(c)
        first = P.claim(c, key, "worker-account-A", now=100, ttl=10)
        with self.assertRaisesRegex(ValueError, "already leased"):
            P.claim(c, key, "worker-account-B", now=105)
        second = P.claim(c, key, "worker-account-B", now=111)
        with self.assertRaisesRegex(ValueError, "stale"):
            P.acknowledge(c, key, first, result={"rows": 4}, now=112)
        P.acknowledge(c, key, second, result={"rows": 4}, now=112)
        self.assertIsNone(P.claim(c, key, "worker-account-A", now=113))

    def test_progress_and_result_survive_account_session(self):
        c = checkpoint(); key = work(c)
        with tempfile.TemporaryDirectory() as root:
            path = str(Path(root) / "ledger.sqlite")
            ledger = P.Ledger(path); ledger.initialize(c)
            token = ledger.mutate(P.claim, key, "portable-worker", now=1)
            ledger.mutate(P.acknowledge, key, token, {"next_unconsumed_line": 129}, now=2)
            ledger.close()
            resumed = P.Ledger(path)
            self.assertEqual(resumed.export()["tasks"][key]["progress"]["next_unconsumed_line"], 129)
            resumed.mutate(P.acknowledge, key, token, result={"rows": 440}, now=3)
            self.assertEqual(resumed.export()["completed"][key]["rows"], 440)
            resumed.close()

    def test_merge_idempotence_conflict_and_revision(self):
        c = checkpoint(); key = work(c); exported = deepcopy(c)
        token = P.claim(exported, key, "worker", now=1)
        P.acknowledge(exported, key, token, result={"rows": 4}, now=2)
        self.assertTrue(P.merge_results(c, exported, 0))
        self.assertFalse(P.merge_results(c, exported, 1))
        with self.assertRaisesRegex(ValueError, "revision"):
            P.merge_results(c, exported, 0)
        conflicting = deepcopy(exported); conflicting["completed"][key] = {"rows": 8}
        conflicting["tasks"][key]["result_sha256"] = P.digest({"rows": 8})
        with self.assertRaisesRegex(ValueError, "conflicting"):
            P.merge_results(c, conflicting, 1)

    def test_two_local_connections_cannot_claim_same_live_task(self):
        c = checkpoint(); key = work(c)
        with tempfile.TemporaryDirectory() as root:
            path = str(Path(root)/'shared.sqlite')
            a,b = P.Ledger(path),P.Ledger(path)
            try:
                a.initialize(c)
                a.mutate(P.claim,key,'A',now=1)
                with self.assertRaisesRegex(ValueError,'already leased'):
                    b.mutate(P.claim,key,'B',now=2)
                self.assertEqual(a.export(),b.export())
            finally:
                a.close(); b.close()


class ArchiveAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make(self, content=None):
        content = list(rows()) if content is None else content
        path = self.root / "chat.jsonl.gz"
        path.write_bytes(gzip.compress("".join(P.canonical(r) + "\n" for r in content).encode(), mtime=0))
        return path, {"sha256": P.file_hash(path), "bytes": path.stat().st_size,
                      "rows": len(content), "role": "candidate_chat"}

    def test_restart_cursor_exactly_once_and_partial_case_status(self):
        path, entry = self.make(); catalog = {"members": [entry]}; db = self.root / "audit.sqlite"
        first = A.AuditStore(db, catalog)
        self.assertTrue(first.consume(entry, path, max_rows=2)["bounded_pause"])
        self.assertEqual(first.report()["incomplete_four_mode_cases"], 1); first.close()
        second = A.AuditStore(db, catalog)
        self.assertTrue(second.consume(entry, path)["complete"])
        self.assertEqual(second.report()["rows_processed"], 4)
        self.assertEqual(second.report()["incomplete_four_mode_cases"], 0)
        self.assertEqual(second.report()["issues"], {})
        self.assertTrue(second.consume(entry, path)["already_complete"])
        self.assertFalse(second.report()["full_archive_token_split_audit_complete"]); second.close()

    def test_hash_tamper_refused_before_rows(self):
        path, entry = self.make(); path.write_bytes(path.read_bytes() + b"tamper")
        store = A.AuditStore(self.root / "a.sqlite", {"members": [entry]})
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            store.consume(entry, path)
        self.assertEqual(store.report()["rows_processed"], 0); store.close()

    def test_catalog_change_cannot_resume(self):
        path, entry = self.make(); db = self.root / "a.sqlite"
        A.AuditStore(db, {"members": [entry]}).close()
        with self.assertRaisesRegex(ValueError, "changed"):
            A.AuditStore(db, {"members": []})

    def test_zip_member_hash_required_and_guard(self):
        plain = "".join(P.canonical(r) + "\n" for r in rows()).encode()
        path = self.root / "a.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("data/chat.jsonl", plain)
        import hashlib
        entry = {"bytes": path.stat().st_size, "sha256": P.file_hash(path), "member": "data/chat.jsonl",
                 "member_sha256": hashlib.sha256(plain).hexdigest(), "role": "candidate_chat", "rows": 4}
        store = A.AuditStore(self.root / "a.sqlite", {"members": [entry]})
        self.assertEqual(store.consume(entry, path)["rows"], 4); store.close()
        for overrides in [{"member_sha256": "b" * 64}, {"role": "frozen_evaluation"}, {"member": "sealed/chat.jsonl"}]:
            with self.assertRaises(ValueError):
                with A.payload({**entry, **overrides}, path) as stream:
                    list(stream)

    def test_duplicate_and_cross_split_are_evidence_not_silent_pass(self):
        path, entry = self.make(list(rows()) + list(rows("validation", "b")) + list(rows()))
        store = A.AuditStore(self.root / "a.sqlite", {"members": [entry]})
        store.consume(entry, path)
        issues = store.report()["issues"]
        self.assertEqual(issues["DUPLICATE_SAMPLE_OR_MODE"], 4)
        self.assertEqual(issues["CROSS_SPLIT_GROUP"], 4)
        self.assertEqual(issues["CROSS_SPLIT_QUESTION"], 4); store.close()

    def test_chat_tamper_and_source_hash_mismatch(self):
        source = {"sample_id":"a", "case_group_id":"group", "grade":1, "problem":"one question", "givens":[],
                  "requested_quantity":"answer", "student_work":None, "can_solve":True,
                  "initial_guidance":["think"], "worked_steps":[], "expected_answer":[],
                  "hints":[{"level":i,"hint":"think","question":"why?"} for i in (1,2,3)]}
        sourcepath = self.root / "source.jsonl"
        # Deliberately noncanonical whitespace: verify exact raw row hash rather
        # than substituting a semantic/canonical hash for evidence.
        raw = json.dumps(source, indent=None, separators=(", ", ": "))
        sourcepath.write_text(raw + "\n", encoding="utf8")
        import hashlib
        sourcehash = hashlib.sha256(raw.encode()).hexdigest()
        chats = list(rows())
        for row in chats:
            row["source_row_sha256"] = sourcehash
            row["messages"][1]["content"] = P.canonical({"problem":source['problem'], "grade":1, "mode":row['mode']})
            target = {"can_solve":True,"initial_guidance":["think"],"steps":[],"answer":[]} if row['mode']=='worked_solution' else {"hint":"think","question":"why?"}
            row["messages"][2]["content"] = P.canonical(target)
        chats[1]["messages"][2]["content"] = '{"hint":"wrong","question":"why?"}'
        chats[2]["messages"][1]["content"] = P.canonical({"problem":"tampered question", "grade":1, "mode":chats[2]['mode']})
        chats[3]["source_row_sha256"] = "f"*64
        path, entry = self.make(chats)
        se = {"bytes":sourcepath.stat().st_size,"sha256":P.file_hash(sourcepath),"role":"candidate_source","rows":1}
        catalog = {"members":[se,entry]}
        store = A.AuditStore(self.root/'a.sqlite',catalog)
        store.consume(se,sourcepath); store.consume(entry,path)
        report = store.report()
        self.assertEqual(report['issues']['SOURCE_CHAT_LINKAGE_MISMATCH'],2)
        self.assertEqual(report['issues']['SOURCE_HASH_MISMATCH'],1)
        self.assertEqual(report['source_raw_row_hash_unverified_rows'],1)
        self.assertEqual(report['source_linkage_unverified_rows'],2)
        store.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
