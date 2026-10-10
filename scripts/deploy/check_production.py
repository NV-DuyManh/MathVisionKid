"""Validate deployment inputs without displaying credentials or contacting providers."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


MODEL_FILES = (
    "model_manifest.json", "yolov8n_mathvision_det_v1.pt", "label_map_detection.json",
    "ocr/text_detection_cn_ppocrv3_2023may.onnx", "ocr/text_detector_manifest.json",
    "ocr/crnn_vi_handwriting_v1/best_cer.pth", "ocr/crnn_vi_handwriting_v1/vocab.json",
    "ocr/crnn_vi_handwriting_v1/model_manifest.json",
)


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid environment assignment at line {number}.")
        key, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"Invalid environment name at line {number}.")
        if key in values:
            raise ValueError(f"Duplicate environment name at line {number}.")
        value = value.strip()
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed environment quote at line {number}.")
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if "$" in value or "\x00" in value:
            raise ValueError(f"Unsupported environment expansion at line {number}.")
        values[key] = value
    return values


def public_host(host: str | None) -> bool:
    if not host:
        return False
    host = host.lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".example", ".test", ".invalid")):
        return False
    if host in {"example.com", "example.org", "example.net"} or any(host.endswith("." + name) for name in ("example.com", "example.org", "example.net")):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return "." in host and bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host))


def public_origin(value: str) -> bool:
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and public_host(url.hostname) and not url.username
                and not url.password and url.path == "" and not url.query and not url.fragment
                and url.port in (None, 443))
    except ValueError:
        return False


def strong_secret(value: str, minimum: int = 32) -> bool:
    lowered = value.lower()
    placeholders = ("password123", "secret-key-default", "minioadmin", "development", "change-me", "changeme", "replace", "example")
    return (len(value.encode("utf-8")) >= minimum and len(set(value)) >= 8
            and not any(placeholder in lowered for placeholder in placeholders))


def check_environment(values: dict[str, str]) -> list[str]:
    errors = []
    domain = values.get("API_DOMAIN", "")
    if not public_origin("https://" + domain) or ":" in domain:
        errors.append("API_DOMAIN must be a public DNS hostname without a protocol or path.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values.get("CADDY_EMAIL", "")):
        errors.append("CADDY_EMAIL must be a certificate contact email.")
    origins = values.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if not origins or any(not public_origin(origin.strip()) for origin in origins):
        errors.append("CORS_ALLOWED_ORIGINS must list exact public HTTPS origins; no wildcards or placeholders.")
    for name in ("DB_PASSWORD", "JWT_SECRET", "INTERNAL_API_KEY", "MINIO_SECRET_KEY"):
        if not strong_secret(values.get(name, "")):
            errors.append(f"{name} must be an independent random secret of at least 32 bytes.")
    secrets = [values.get(name, "") for name in ("DB_PASSWORD", "JWT_SECRET", "INTERNAL_API_KEY", "MINIO_SECRET_KEY", "REDIS_PASSWORD")]
    if len(set(secrets)) != len(secrets):
        errors.append("Service secrets must be different from one another.")
    redis_password = values.get("REDIS_PASSWORD", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64,}", redis_password) or len(set(redis_password.lower())) < 8:
        errors.append("REDIS_PASSWORD must be at least 64 random hexadecimal characters for safe URL encoding.")
    access_key = values.get("MINIO_ACCESS_KEY", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", access_key) or access_key == "minioadmin":
        errors.append("MINIO_ACCESS_KEY must be a dedicated nondefault storage identity.")
    if not values.get("MODEL_BUNDLE_DIR"):
        errors.append("MODEL_BUNDLE_DIR must identify the private runtime model directory.")
    for provider in ("GROQ", "GEMINI"):
        flag = values.get(provider + "_ENABLED", "true").lower()
        if flag not in {"true", "false"}:
            errors.append(f"{provider}_ENABLED must be true or false.")
        elif flag == "true" and not any(key.strip() for key in values.get(provider + "_API_KEYS", "").split(",")):
            errors.append(f"{provider}_API_KEYS is required when that provider is enabled.")
    if values.get("BOOTSTRAP_ADMIN_ENABLED", "false").lower() == "true":
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values.get("BOOTSTRAP_ADMIN_EMAIL", "")):
            errors.append("BOOTSTRAP_ADMIN_EMAIL is required for first-time provisioning.")
        password = values.get("BOOTSTRAP_ADMIN_PASSWORD", "")
        if not strong_secret(password, 16) or len(password.encode("utf-8")) > 72:
            errors.append("BOOTSTRAP_ADMIN_PASSWORD must be a strong password within BCrypt's 72-byte limit.")
    return errors


def check_models(root: Path) -> list[str]:
    errors = [f"Model bundle is missing {name}." for name in MODEL_FILES if not (root / name).is_file()]
    if errors:
        return errors
    checks = (
        ("model_manifest.json", "yolov8n_mathvision_det_v1.pt", "sha256"),
        ("ocr/text_detector_manifest.json", "ocr/text_detection_cn_ppocrv3_2023may.onnx", "sha256"),
        ("ocr/crnn_vi_handwriting_v1/model_manifest.json", "ocr/crnn_vi_handwriting_v1/best_cer.pth", "artifact_sha256"),
        ("ocr/crnn_vi_handwriting_v1/model_manifest.json", "ocr/crnn_vi_handwriting_v1/vocab.json", "vocab_sha256"),
    )
    for manifest, artifact, key in checks:
        try:
            expected = json.loads((root / manifest).read_text(encoding="utf-8"))[key]
            with (root / artifact).open("rb") as handle:
                actual = hashlib.file_digest(handle, "sha256").hexdigest()
            if not isinstance(expected, str) or actual != expected:
                errors.append(f"Model checksum mismatch for {artifact}.")
        except (ValueError, KeyError, OSError):
            errors.append(f"Model manifest cannot verify {artifact}.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument("--models", type=Path, help="Override MODEL_BUNDLE_DIR for pre-upload verification.")
    args = parser.parse_args()
    try:
        values = read_env(args.env_file)
        errors = check_environment(values)
        model_root = args.models or Path(values.get("MODEL_BUNDLE_DIR", ""))
        errors.extend(check_models(model_root))
    except (OSError, ValueError):
        print("FAIL: Environment file could not be read or parsed. No credentials were displayed.")
        return 1
    for error in errors:
        print("FAIL: " + error)
    if errors:
        return 1
    print("PASS: Production inputs and four model checksums verified. Cloud deployment is not yet verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
