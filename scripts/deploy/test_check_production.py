import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from check_production import MODEL_FILES, check_environment, check_models, public_origin, read_env


def valid_environment():
    return {
        "API_DOMAIN": "api.mathvisionkids.org", "CADDY_EMAIL": "owner@mathvisionkids.org",
        "CORS_ALLOWED_ORIGINS": "https://mathvisionkids.org,https://teacher.mathvisionkids.org",
        "DB_PASSWORD": "0123456789abcdef" * 4,
        "JWT_SECRET": "fedcba9876543210" * 4,
        "INTERNAL_API_KEY": "89abcdef01234567" * 4,
        "MINIO_SECRET_KEY": "abcdef0123456789" * 4,
        "REDIS_PASSWORD": "23456789abcdef01" * 4,
        "MINIO_ACCESS_KEY": "mathvision-storage", "MODEL_BUNDLE_DIR": "/srv/models",
        "GROQ_ENABLED": "false", "GEMINI_ENABLED": "false",
    }


class DeploymentInputTests(unittest.TestCase):
    def test_valid_configuration(self):
        self.assertEqual([], check_environment(valid_environment()))

    def test_private_and_placeholder_origins_rejected(self):
        for origin in ("http://mathvisionkids.org", "https://localhost", "https://127.0.0.1",
                       "https://192.168.1.2", "https://portal.example.com", "https://fake.test",
                       "https://user:password@mathvisionkids.org", "https://mathvisionkids.org/",
                       "https://mathvisionkids.org?x=1", "https://mathvisionkids.org:8000"):
            with self.subTest(origin=origin):
                self.assertFalse(public_origin(origin))

    def test_secrets_errors_do_not_include_values(self):
        values = valid_environment()
        secret = "secret-key-default-do-not-display-this"
        values["INTERNAL_API_KEY"] = secret
        errors = check_environment(values)
        self.assertTrue(errors)
        self.assertNotIn(secret, " ".join(errors))

    def test_duplicate_secrets_rejected(self):
        values = valid_environment()
        values["JWT_SECRET"] = values["DB_PASSWORD"]
        self.assertTrue(any("different" in error for error in check_environment(values)))

    def test_redis_password_requires_url_safe_hex(self):
        values = valid_environment()
        values["REDIS_PASSWORD"] = "unsafe-password-with@reserved:/symbols" * 2
        self.assertTrue(any("REDIS_PASSWORD" in error for error in check_environment(values)))

    def test_enabled_provider_requires_credentials(self):
        values = valid_environment()
        values["GROQ_ENABLED"] = "true"
        self.assertTrue(any("GROQ_API_KEYS" in error for error in check_environment(values)))

    def test_bootstrap_rejects_missing_and_oversized_password(self):
        values = valid_environment()
        values["BOOTSTRAP_ADMIN_ENABLED"] = "true"
        self.assertTrue(any("BOOTSTRAP_ADMIN_PASSWORD" in error for error in check_environment(values)))
        values["BOOTSTRAP_ADMIN_EMAIL"] = "owner@mathvisionkids.org"
        values["BOOTSTRAP_ADMIN_PASSWORD"] = "Abcdef1234567890" * 5
        self.assertTrue(any("BOOTSTRAP_ADMIN_PASSWORD" in error for error in check_environment(values)))

    def test_environment_quotes_bom_and_duplicate_handling(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = Path(temporary) / "environment"
            env.write_text('\ufeff# ignored\nSECRET="quoted#literal"\nNAME=owner # comment\n', encoding="utf-8")
            self.assertEqual({"SECRET": "quoted#literal", "NAME": "owner"}, read_env(env))
            env.write_text("SECRET=never-display\nSECRET=duplicate\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate") as raised:
                read_env(env)
            self.assertNotIn("never-display", str(raised.exception))

    def test_all_model_files_and_four_checksums(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in MODEL_FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"artifact")
            digest = hashlib.sha256(b"artifact").hexdigest()
            (root / "model_manifest.json").write_text(json.dumps({"sha256": digest}))
            (root / "ocr/text_detector_manifest.json").write_text(json.dumps({"sha256": digest}))
            (root / "ocr/crnn_vi_handwriting_v1/model_manifest.json").write_text(json.dumps({"artifact_sha256": digest, "vocab_sha256": digest}))
            self.assertEqual([], check_models(root))
            (root / "ocr/crnn_vi_handwriting_v1/vocab.json").write_bytes(b"changed")
            self.assertTrue(any("checksum mismatch" in error for error in check_models(root)))
            (root / "label_map_detection.json").unlink()
            self.assertTrue(any("missing" in error for error in check_models(root)))


if __name__ == "__main__":
    unittest.main()
