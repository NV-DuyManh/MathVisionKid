import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from check_production import MODEL_FILES, read_env
from init_pc_preview import initialize


class PCPreviewTests(unittest.TestCase):
    def test_initialization_preserves_secrets_and_provider_file_precedence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            for name in MODEL_FILES:
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"model-test")
            digest = hashlib.sha256(b"model-test").hexdigest()
            (source / "model_manifest.json").write_text(json.dumps({"sha256": digest}))
            (source / "ocr/text_detector_manifest.json").write_text(json.dumps({"sha256": digest}))
            (source / "ocr/crnn_vi_handwriting_v1/model_manifest.json").write_text(json.dumps({"artifact_sha256": digest, "vocab_sha256": digest}))
            base = root / "base.env"
            local = root / "local.env"
            base.write_text('GROQ_ENABLED=true\nGROQ_API_KEYS=base-private-key\nGEMINI_ENABLED=false\n')
            local.write_text('GROQ_API_KEYS=local-private-key\n')
            state = root / "state"
            initialize(state, "owner@mathvisionkids.org", source, (base, local))
            original = (state / ".env.preview").read_bytes()
            values = read_env(state / ".env.preview")
            self.assertEqual("local-private-key", values["GROQ_API_KEYS"])
            self.assertEqual(5, len({values[name] for name in ("DB_PASSWORD", "REDIS_PASSWORD", "JWT_SECRET", "INTERNAL_API_KEY", "MINIO_SECRET_KEY")}))
            self.assertLessEqual(len(values["BOOTSTRAP_ADMIN_PASSWORD"].encode()), 72)
            self.assertEqual(set(MODEL_FILES), {path.relative_to(state / "models").as_posix() for path in (state / "models").rglob("*") if path.is_file()})
            # Existing configuration does not depend on a deleted source, owner argument or updated local keys.
            initialize(state, "", root / "missing", ())
            self.assertEqual(original, (state / ".env.preview").read_bytes())
            (state / "owner-credentials.json").unlink()
            with self.assertRaisesRegex(ValueError, "missing its private owner"):
                initialize(state, "different@mathvisionkids.org", source, ())
            self.assertEqual(original, (state / ".env.preview").read_bytes())


if __name__ == "__main__":
    unittest.main()
