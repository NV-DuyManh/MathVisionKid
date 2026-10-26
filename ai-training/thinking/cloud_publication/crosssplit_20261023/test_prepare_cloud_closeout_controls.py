"""Focused offline guard tests for the cloud closeout control preparer."""
import tempfile
import unittest
from pathlib import Path
import zipfile

import prepare_cloud_closeout_controls as prep


class CloseoutGuards(unittest.TestCase):
    def test_rejects_parent_checkpoint_as_dynamic_child(self):
        parent = {"id": "16Q9ft9xhcioconk-5zpxmdRv1ZDNxqFI",
                  "bytes": 9128976384,
                  "sha256": "586904f37ad439e6c5ab5e00c5ccf5e494cccf8d7def09f4d4db9e9dba697fee",
                  "fresh_raw_readback_verified": True}
        child = {"id": parent["id"], "bytes": 1, "sha256": "a" * 64,
                 "fresh_raw_readback_verified": True}
        with self.assertRaisesRegex(ValueError, "dynamic ID"):
            prep._validate_child_checkpoint(parent, child)

    def test_rejects_readiness_claim(self):
        with self.assertRaisesRegex(ValueError, "readiness"):
            prep._assert_conservative({"TRAINING_DATASET_READY": True}, {})

    def test_old_zip_members_must_remain_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            old, good, bad = (Path(td) / name for name in ("old.zip", "good.zip", "bad.zip"))
            with zipfile.ZipFile(old, "w") as zf:
                zf.writestr("historic.json", b"old bytes")
            with zipfile.ZipFile(good, "w") as zf:
                zf.writestr("historic.json", b"old bytes")
                zf.writestr(prep.PREFIX + "evidence.json", b"new evidence")
            prep._assert_old_zip_preserved(old, good)
            with zipfile.ZipFile(bad, "w") as zf:
                zf.writestr("historic.json", b"changed bytes")
            with self.assertRaisesRegex(ValueError, "changed"):
                prep._assert_old_zip_preserved(old, bad)


if __name__ == "__main__":
    unittest.main()
