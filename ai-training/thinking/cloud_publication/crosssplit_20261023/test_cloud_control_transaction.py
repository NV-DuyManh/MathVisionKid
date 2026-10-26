"""Offline fake-API tests for cloud_control_transaction."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("cloud_control_transaction.py")
spec = importlib.util.spec_from_file_location("cloud_control_transaction", MODULE_PATH)
transaction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transaction)


def pin(path, file_id):
    data = path.read_bytes()
    return {"id": file_id, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "path": str(path)}


class FakeFiles:
    def __init__(self, store):
        self.store = store
        self.writes = []

    def update(self, fileId, media_body, **kwargs):
        def execute():
            self.store[fileId] = Path(media_body.filename).read_bytes()
            self.writes.append(fileId)
            return {"id": fileId}
        return types.SimpleNamespace(execute=execute)

    def get(self, **kwargs):
        raise AssertionError("tests replace the streaming download helper")


class FakeAPI:
    def __init__(self, store):
        self.resource = FakeFiles(store)

    def files(self):
        return self.resource


class CloudControlTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.old_dir = self.root / "old"
        self.new_dir = self.root / "new"
        self.old_dir.mkdir()
        self.new_dir.mkdir()
        (self.old_dir / "context").write_bytes(b"history\n")
        (self.new_dir / "context").write_bytes(b"history\nnew\n")
        (self.old_dir / "chat").write_text(json.dumps({"accepted_cases": 1629922, "training_chat_rows": 6502344}), encoding="utf-8")
        (self.new_dir / "chat").write_text(json.dumps({"chat_rows": 6502344, "count_reconciliation": {"declared_candidate_chat_rows": 6502344, "historical_accepted_case_counter_preserved": 1629922}, "TRAINING_DATASET_READY": False, "training_started": False}), encoding="utf-8")
        (self.old_dir / "state").write_text(json.dumps({"old": True}), encoding="utf-8")
        (self.new_dir / "state").write_text(json.dumps({"accepted_cases": 1629922, "training_chat_rows": 6502344, "TRAINING_DATASET_READY": False, "training_started": False}), encoding="utf-8")
        for folder in (self.old_dir, self.new_dir):
            with zipfile.ZipFile(folder / "progress", "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("old/member.json", b"preserved")
                if folder == self.new_dir:
                    archive.writestr("run/receipt.json", b"added")
        self.ids = {kind: f"existing-{kind}" for kind in transaction.KINDS}
        self.parents = {kind: pin(self.old_dir / kind, self.ids[kind]) for kind in transaction.KINDS}
        self.prepared = {kind: pin(self.new_dir / kind, self.ids[kind]) for kind in transaction.KINDS}
        self.store = {self.ids[kind]: (self.old_dir / kind).read_bytes() for kind in transaction.KINDS}

    def tearDown(self):
        self.temp.cleanup()

    def fake_download(self, api, file_id, dest, expected_size):
        data = self.store[file_id]
        dest.write_bytes(data)
        return len(data), hashlib.sha256(data).hexdigest()

    def patch_google_upload(self):
        http = types.ModuleType("googleapiclient.http")
        http.MediaFileUpload = lambda filename, **kwargs: types.SimpleNamespace(filename=filename)
        package = types.ModuleType("googleapiclient")
        package.http = http
        self.modules = {key: sys.modules.get(key) for key in ("googleapiclient", "googleapiclient.http")}
        sys.modules["googleapiclient"] = package
        sys.modules["googleapiclient.http"] = http

    def restore_google_upload(self):
        for key, value in self.modules.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value

    def test_changed_parent_rejects_before_any_write(self):
        self.store[self.ids["chat"]] = b"unexpected"
        transaction._download = self.fake_download
        api = FakeAPI(self.store)
        with self.assertRaisesRegex(RuntimeError, "changed from both expected parent and prepared"):
            transaction.publish_controls(api, self.parents, self.prepared, self.runtime)
        self.assertEqual(api.resource.writes, [])

    def test_state_is_written_last_and_every_write_is_read_back(self):
        transaction._download = self.fake_download
        self.patch_google_upload()
        try:
            api = FakeAPI(self.store)
            result = transaction.publish_controls(api, self.parents, self.prepared, self.runtime)
        finally:
            self.restore_google_upload()
        self.assertEqual(api.resource.writes, [self.ids[k] for k in ("progress", "chat", "context", "state")])
        self.assertEqual([item["kind"] for item in result["verified_writes"]], ["progress", "chat", "context", "state"])
        self.assertTrue(all(item["fresh_raw_readback_verified"] for item in result["verified_writes"]))


if __name__ == "__main__":
    unittest.main()

