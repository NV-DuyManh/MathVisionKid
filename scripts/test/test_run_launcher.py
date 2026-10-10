"""Exercise the real batch launcher with isolated service stubs; never deploy."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.name == "nt", "The launcher requires Windows cmd.exe")
class RunLauncherTest(unittest.TestCase):
    def run_launcher(self, configured=True, public_exit=0, core_exit=0):
        source = Path(__file__).resolve().parents[2] / "RUN_MATHVISION.bat"
        with tempfile.TemporaryDirectory(prefix="mathvision launcher ") as directory:
            root = Path(directory)

            def write(name, content=""):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return target

            # Only suppress the browser and pause; execute all production branches.
            launcher = write("RUN_MATHVISION.bat", source.read_text(encoding="utf-8")
                             .replace("start http://localhost:5172", "rem browser suppressed in test")
                             .replace("pause >nul", "rem pause suppressed in test"))
            for name in ("infra/docker/docker-compose.yml", "backend/business-api/gradlew.bat",
                         "apps/student-mobile/package.json", "apps/portal-web/package.json"):
                write(name)
            log = root / "events.txt"
            write("scripts/start-all.bat",
                  f'@echo off\necho core>>"%LAUNCHER_TEST_LOG%"\nexit /b {core_exit}\n')
            write("scripts/start-student-metro.ps1",
                  "Add-Content -LiteralPath $env:LAUNCHER_TEST_LOG -Value 'metro'\nexit 0\n")
            write("tools/diagnostics/check_runtime.py",
                  "import os\nfrom pathlib import Path\n"
                  "with Path(os.environ['LAUNCHER_TEST_LOG']).open('a') as log: log.write('diagnostics\\n')\n")
            write("scripts/dev/show-student-qr.cjs",
                  "require('node:fs').appendFileSync(process.env.LAUNCHER_TEST_LOG, 'qr\\n');\n")
            write("scripts/deploy/Start-PC-Preview.ps1",
                  "param([switch]$PublishWeb)\n$ErrorActionPreference = 'Stop'\n"
                  "Import-Module Microsoft.PowerShell.Security -ErrorAction Stop\n"
                  "if (-not (Get-Command Get-AuthenticodeSignature)) { exit 98 }\n"
                  "if (-not $PublishWeb) { exit 99 }\n"
                  "Add-Content -LiteralPath $env:LAUNCHER_TEST_LOG -Value 'public-publish'\n"
                  f"exit {public_exit}\n")
            preview = write("infra/local-runtime/pc-preview/.env.preview", "private-config-retained") if configured else None
            env = dict(os.environ, LAUNCHER_TEST_LOG=str(log))
            env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
            result = subprocess.run(["cmd.exe", "/d", "/c", str(launcher)], cwd=root, env=env,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            events = log.read_text(encoding="utf-8-sig").splitlines() if log.exists() else []
            if preview:
                self.assertEqual("private-config-retained", preview.read_text(encoding="utf-8"))
            return result, events

    def test_configured_pc_starts_public_web_after_local_readiness(self):
        result, events = self.run_launcher()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "public-publish", "qr"], events)
        self.assertIn("Public Website: READY", result.stdout)
        self.assertIn("https://mathvisionkid-portal.vercel.app", result.stdout)

    def test_public_failure_keeps_local_qr_and_returns_failure(self):
        result, events = self.run_launcher(public_exit=7)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "public-publish", "qr"], events)
        self.assertIn("Public Website: FAILED", result.stdout)
        self.assertNotIn("Vercel Portal:", result.stdout)

    def test_fresh_clone_skips_private_preview_without_provisioning(self):
        result, events = self.run_launcher(configured=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "qr"], events)
        self.assertIn("Public Website: NOT_CONFIGURED", result.stdout)

    def test_local_failure_does_not_start_publication(self):
        result, events = self.run_launcher(core_exit=3)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core"], events)
        self.assertIn("STARTUP FAILED", result.stdout)


if __name__ == "__main__":
    unittest.main()
