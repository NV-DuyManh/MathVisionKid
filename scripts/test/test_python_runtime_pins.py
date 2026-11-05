"""A checkout update cannot silently keep stale local security packages."""
import importlib.util
from importlib import metadata
from pathlib import Path
import tempfile
import unittest


path = Path(__file__).resolve().parents[1] / "dev" / "check_python_runtime.py"
spec = importlib.util.spec_from_file_location("python_runtime_pins", path)
pins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pins)


class PythonRuntimePinsTest(unittest.TestCase):
    def test_current_stale_and_missing_packages_are_distinguished(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements.txt").write_text("edge-tts==7.3.1\npillow==12.3.0\n", encoding="utf-8")
            (root / "requirements-lock.txt").write_text(
                "\n".join(f"{name}==13.0.0" for name in pins.CHECKED_PACKAGES if name != "edge-tts"), encoding="utf-8")
            def installed(name):
                if name == "certifi":
                    raise metadata.PackageNotFoundError(name)
                return "12.3.0" if name == "pillow" else "7.3.1" if name == "edge-tts" else "13.0.0"
            self.assertEqual(pins.check_dependencies(root, installed), [
                "pillow: installed=12.3.0, required=13.0.0", "certifi: installed=missing, required=13.0.0"])
            self.assertEqual(pins.check_dependencies(root, lambda name: "7.3.1" if name == "edge-tts" else "13.0.0"), [])


if __name__ == "__main__":
    unittest.main()
