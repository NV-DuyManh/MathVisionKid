"""Exercise the real batch launcher with isolated service stubs; never deploy."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.name == "nt", "The launcher requires Windows cmd.exe")
class RunLauncherTest(unittest.TestCase):
    def run_launcher(self, configured=True, public_exit=0, core_exit=0, launcher_name="RUN_MATHVISION.bat", setup_exit=0, launcher_args=(),
                     diagnostic_exit=0, internal_key="synthetic-backend-local", parent_key=None):
        source = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="mathvision launcher ") as directory:
            root = Path(directory)

            def write(name, content=""):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return target

            # Execute real launchers, replacing only their interactive pauses.
            for name in ("RUN_MATHVISION.bat", "DEPLOY_WEB.bat", "SETUP_MATHVISION.bat"):
                write(name, (source / name).read_text(encoding="utf-8")
                      .replace("pause >nul", "rem pause suppressed in test"))
            launcher = root / launcher_name
            for name in ("scripts/dev/check-runtime.ps1", "scripts/dev/local-env.ps1"):
                write(name, (source / name).read_text(encoding="utf-8"))
            if internal_key is not None:
                for name, key in ((".env", "synthetic-root"), (".env.local", "synthetic-root-local"),
                                  ("backend/business-api/.env", "synthetic-backend"),
                                  ("backend/business-api/.env.local", internal_key)):
                    write(name, f"INTERNAL_API_KEY='{key}'\nLAUNCHER_UNRELATED=must-not-load\n")
            for name in ("infra/docker/docker-compose.yml", "backend/business-api/gradlew.bat",
                         "apps/student-mobile/package.json", "apps/portal-web/package.json"):
                write(name)
            log = root / "events.txt"
            write("scripts/start-all.bat",
                  f'@echo off\necho core>>"%LAUNCHER_TEST_LOG%"\nexit /b {core_exit}\n')
            write("scripts/start-student-metro.ps1",
                  "Add-Content -LiteralPath $env:LAUNCHER_TEST_LOG -Value 'metro'\nexit 0\n")
            write("scripts/dev/setup-local.ps1",
                  "param([switch]$CheckOnly)\n"
                  "Add-Content -LiteralPath $env:LAUNCHER_TEST_LOG -Value ('setup:' + $CheckOnly.IsPresent)\n"
                  f"exit {setup_exit}\n")
            write("tools/diagnostics/check_runtime.py",
                  "import os\nfrom pathlib import Path\n"
                  "with Path(os.environ['LAUNCHER_TEST_LOG']).open('a') as log: log.write('diagnostics\\n')\n"
                  "if not os.environ.get('INTERNAL_API_KEY'): raise SystemExit(23)\n"
                  "if os.environ['INTERNAL_API_KEY'] != os.environ['LAUNCHER_EXPECTED_KEY']: raise SystemExit(24)\n"
                  "if os.environ.get('PORT') != '8000': raise SystemExit(25)\n"
                  "if os.environ.get('LAUNCHER_UNRELATED'): raise SystemExit(26)\n"
                  f"raise SystemExit({diagnostic_exit})\n")
            write("scripts/dev/show-student-qr.cjs",
                  "require('node:fs').appendFileSync(process.env.LAUNCHER_TEST_LOG, 'qr\\n');\n")
            write("scripts/deploy/Start-PC-Preview.ps1",
                  "param([switch]$Build,[switch]$PublishWeb)\n$ErrorActionPreference = 'Stop'\n"
                  "Import-Module Microsoft.PowerShell.Security -ErrorAction Stop\n"
                  "if (-not (Get-Command Get-AuthenticodeSignature)) { exit 98 }\n"
                  "if (-not $PublishWeb -or -not $Build) { exit 99 }\n"
                  "Add-Content -LiteralPath $env:LAUNCHER_TEST_LOG -Value 'public-publish'\n"
                  f"exit {public_exit}\n")
            preview = write("infra/local-runtime/pc-preview/.env.preview", "private-config-retained") if configured else None
            env = dict(os.environ, LAUNCHER_TEST_LOG=str(log))
            # Never let real credentials mask a missing diagnostic configuration.
            env.pop("INTERNAL_API_KEY", None)
            env.pop("LAUNCHER_UNRELATED", None)
            if parent_key is not None:
                env["INTERNAL_API_KEY"] = parent_key
            env["LAUNCHER_EXPECTED_KEY"] = parent_key or internal_key or ""
            env["PORT"] = "9371"
            env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env["PATH"]
            result = subprocess.run(["cmd.exe", "/d", "/c", str(launcher), *launcher_args], cwd=root.parent, env=env,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            events = log.read_text(encoding="utf-8-sig").splitlines() if log.exists() else []
            if preview:
                self.assertEqual("private-config-retained", preview.read_text(encoding="utf-8"))
            return result, events

    def test_local_entry_point_never_publishes_even_if_preview_is_configured(self):
        result, events = self.run_launcher(public_exit=7)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "qr"], events)

    def test_fresh_clone_still_runs_expo_without_public_configuration(self):
        result, events = self.run_launcher(configured=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "qr"], events)

    def test_final_diagnostic_loads_literal_key_from_shared_configuration(self):
        key = "synthetic-$(!);literal-key"
        result, events = self.run_launcher(internal_key=key)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "qr"], events)
        self.assertNotIn(key, result.stdout + result.stderr)

    def test_explicit_parent_credential_wins_over_dotenv(self):
        key = "synthetic-parent-only"
        result, events = self.run_launcher(parent_key=key)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics", "qr"], events)
        self.assertNotIn(key, result.stdout + result.stderr)

    def test_missing_credential_cannot_report_ecosystem_ready(self):
        result, events = self.run_launcher(internal_key=None)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics"], events)
        self.assertIn("Complete ecosystem diagnostics did not pass", result.stdout)
        self.assertNotIn("Local Ecosystem Ready!", result.stdout)

    def test_final_diagnostic_failure_stops_before_qr(self):
        result, events = self.run_launcher(diagnostic_exit=7)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core", "metro", "diagnostics"], events)
        self.assertIn("STARTUP FAILED", result.stdout)
        self.assertNotIn("Local Ecosystem Ready!", result.stdout)

    def test_deploy_builds_and_publishes_without_starting_local_or_expo(self):
        result, events = self.run_launcher(launcher_name="DEPLOY_WEB.bat", core_exit=3)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["public-publish"], events)
        self.assertIn("WEB DEPLOYMENT COMPLETE", result.stdout)

    def test_deploy_failure_returns_error_without_starting_expo(self):
        result, events = self.run_launcher(launcher_name="DEPLOY_WEB.bat", public_exit=7)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["public-publish"], events)
        self.assertIn("WEB DEPLOYMENT FAILED", result.stdout)
        self.assertNotIn("WEB DEPLOYMENT COMPLETE", result.stdout)

    def test_deploy_from_a_fresh_clone_refuses_to_provision_or_publish(self):
        result, events = self.run_launcher(launcher_name="DEPLOY_WEB.bat", configured=False)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], events)

    def test_local_failure_does_not_start_publication(self):
        result, events = self.run_launcher(core_exit=3)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual(["core"], events)
        self.assertIn("STARTUP FAILED", result.stdout)

    def test_setup_entry_preserves_failure_and_forwards_read_only_option(self):
        for exit_code in (0, 7):
            with self.subTest(exit_code=exit_code):
                result, events = self.run_launcher(
                    launcher_name="SETUP_MATHVISION.bat", setup_exit=exit_code, launcher_args=("-CheckOnly",))
                self.assertEqual(exit_code, result.returncode, result.stdout + result.stderr)
                self.assertEqual(["setup:True"], events)


if __name__ == "__main__":
    unittest.main()
