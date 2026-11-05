"""Reject stale security/speech packages before starting the local runtime."""
from importlib import metadata
from pathlib import Path
import sys


CHECKED_PACKAGES = ("pillow", "certifi", "urllib3", "filelock", "setuptools", "edge-tts")


def check_dependencies(runtime_dir, get_version=metadata.version):
    pins = {}
    for name in ("requirements.txt", "requirements-lock.txt"):
        for line in (runtime_dir / name).read_text(encoding="utf-8-sig").splitlines():
            package, separator, version = line.strip().partition("==")
            if separator:
                pins[package.lower()] = version
    mismatches = []
    for package in CHECKED_PACKAGES:
        if package not in pins:
            raise ValueError(f"Missing runtime pin: {package}")
        try:
            installed = get_version(package)
        except metadata.PackageNotFoundError:
            installed = "missing"
        if installed != pins[package]:
            mismatches.append(f"{package}: installed={installed}, required={pins[package]}")
    return mismatches


def main():
    runtime_dir = Path(__file__).resolve().parents[2] / "ai" / "runtime"
    mismatches = check_dependencies(runtime_dir)
    if mismatches:
        print("Runtime dependencies do not match this checkout:")
        print("\n".join(mismatches))
        print("Install ai/runtime/requirements.txt with ai/runtime/requirements-lock.txt constraints, then restart.")
        return 1
    print("Security and speech runtime pins verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
