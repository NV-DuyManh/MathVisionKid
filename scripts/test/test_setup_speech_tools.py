"""Exercise the portable speech installer without downloading or touching user tools."""

import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile


class SpeechSetupTest(unittest.TestCase):
    def test_all_speech_dependencies_have_the_same_pins_as_the_uv_lock(self):
        runtime = Path(__file__).resolve().parents[2] / "ai/runtime"
        packages = {p["name"]: p for p in tomllib.loads((runtime / "uv.lock").read_text())["package"]}
        pins = dict(line.split("==", 1) for line in (runtime / "requirements-lock.txt").read_text().splitlines() if "==" in line)
        seen = set()
        pending = ["edge-tts"]
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            self.assertEqual(packages[name]["version"], pins.get(name), name)
            pending.extend(d["name"] for d in packages[name].get("dependencies", []))

    def run_installer(self, checksum_matches=True):
        source = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="mathvision speech setup ") as directory:
            root = Path(directory)
            script = root / "scripts/dev/install-local-quiz-speech.py"
            script.parent.mkdir(parents=True)
            shutil.copyfile(source / "scripts/dev/install-local-quiz-speech.py", script)
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("ffmpeg-test/bin/ffmpeg.exe", b"fixture-decoder")
                package.writestr("ffmpeg-test/LICENSE.txt", "fixture-license")
            payload = archive.getvalue()
            checksum = hashlib.sha256(payload).hexdigest() if checksum_matches else "0" * 64

            def fetch(url, **kwargs):
                return io.BytesIO(checksum.encode() if url.endswith(".sha256") else payload)

            decoder = root / "infra/local-runtime/tools/ffmpeg/bin/ffmpeg.exe"
            with patch("urllib.request.urlopen", side_effect=fetch), patch.object(Path, "home", return_value=root / "home"):
                if not checksum_matches:
                    with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                        runpy.run_path(str(script))
                    self.assertFalse(decoder.exists())
                    return
                runpy.run_path(str(script))
            self.assertEqual(b"fixture-decoder", decoder.read_bytes())
            receipt = json.loads((root / ".local-artifacts/setup/ffmpeg-install.json").read_text())
            self.assertTrue(receipt["checksumVerified"])
            self.assertEqual(checksum, receipt["archiveSha256"])
            self.assertFalse((root / "report").exists())

    def test_fresh_clone_creates_local_receipt_and_verified_decoder(self):
        self.run_installer()

    def test_bad_download_does_not_install_decoder(self):
        self.run_installer(checksum_matches=False)


if __name__ == "__main__":
    unittest.main()
