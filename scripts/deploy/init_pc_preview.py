"""Provision isolated PC preview secrets and a verified runtime bundle; never print credentials."""
from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
from pathlib import Path

from check_production import MODEL_FILES, check_environment, check_models, read_env

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "infra/local-runtime/pc-preview"
PROVIDER_KEYS = (
    "GROQ_ENABLED", "GROQ_API_KEYS", "GROQ_PRIMARY_VISION_MODEL", "GROQ_FALLBACK_VISION_MODEL",
    "GROQ_LINE_ASSIST_MODE", "GROQ_CONSENSUS_MODE", "GROQ_TIMEOUT_SECONDS",
    "GROQ_POST_CORRECTION_ENABLED", "GEMINI_ENABLED", "GEMINI_API_KEYS", "GEMINI_MODEL",
    "GEMINI_FALLBACK_ENABLED", "GEMINI_POST_CORRECTION_ENABLED", "CLOUD_ADVISOR_MAX_CONCURRENCY",
)


def write_env(path: Path, values: dict[str, str]) -> None:
    for key, value in values.items():
        if any(character in value for character in ('\n', '\r', '"', '$', '\x00')):
            raise ValueError(f"Unsupported characters in {key}; no credentials were displayed.")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("".join(f'{key}="{value}"\n' for key, value in values.items()), encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def initialize(state: Path, owner_email: str, source_models: Path, provider_files: tuple[Path, ...]) -> None:
    env_file = state / ".env.preview"
    credentials_file = state / "owner-credentials.json"
    if env_file.exists():
        values = read_env(env_file)
        errors = check_environment(values) + check_models(Path(values.get("MODEL_BUNDLE_DIR", "")))
        if errors:
            raise ValueError("Existing preview configuration failed validation: " + " ".join(errors))
        if not credentials_file.is_file():
            raise ValueError("Existing preview is missing its private owner credential file; no secret was changed.")
        return
    if credentials_file.exists():
        raise ValueError("Incomplete preview initialization; preserve owner-credentials.json and repair the missing environment file.")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", owner_email):
        raise ValueError("First initialization requires --owner-email with the owner's email address.")
    model_errors = check_models(source_models)
    if model_errors:
        raise ValueError("Runtime source validation failed: " + " ".join(model_errors))
    providers: dict[str, str] = {}
    for path in provider_files:
        if path.is_file():
            providers.update(read_env(path))
    values = read_env(REPO / "infra/production/.env.production.example")
    values.update({name: providers[name] for name in PROVIDER_KEYS if name in providers})
    values.update({name: secrets.token_hex(32) for name in
                   ("DB_PASSWORD", "REDIS_PASSWORD", "JWT_SECRET", "INTERNAL_API_KEY", "MINIO_SECRET_KEY")})
    password = secrets.token_urlsafe(32)
    values.update({
        # The quick tunnel supplies the actual hostname after startup; the HTTP gateway ignores API_DOMAIN.
        "API_DOMAIN": "pc-preview.trycloudflare.com", "CADDY_EMAIL": owner_email,
        "CORS_ALLOWED_ORIGINS": ",".join(f"https://mathvisionkid-{app}.vercel.app" for app in ("portal", "teacher", "admin")),
        "MINIO_ACCESS_KEY": "mathvision-preview-storage", "MODEL_BUNDLE_DIR": (state / "models").resolve().as_posix(),
        "BOOTSTRAP_ADMIN_ENABLED": "true", "BOOTSTRAP_ADMIN_EMAIL": owner_email,
        "BOOTSTRAP_ADMIN_PASSWORD": password, "BOOTSTRAP_ADMIN_NAME": "Project Owner",
    })
    errors = check_environment(values)
    if errors:
        raise ValueError("Preview configuration failed validation: " + " ".join(errors))
    state.mkdir(parents=True, exist_ok=True)
    model_root = state / "models"
    if model_root.exists():
        if check_models(model_root):
            raise ValueError("Existing private model bundle is incomplete; no model file was overwritten.")
    else:
        for name in MODEL_FILES:
            target = model_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_models / name, target)
        if check_models(model_root):
            raise ValueError("Copied runtime bundle failed checksum verification.")
    # A pending environment file permits recovery if writing the credential file is interrupted.
    pending = state / ".env.preview.pending"
    write_env(pending, values)
    credentials_file.write_text(json.dumps({"email": owner_email, "password": password}, indent=2) + "\n", encoding="utf-8")
    credentials_file.chmod(0o600)
    pending.replace(env_file)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-email", default="")
    parser.add_argument("--models", type=Path, default=REPO / "ai/runtime/.container-smoke-models")
    parser.add_argument("--finish-bootstrap", action="store_true", help="Disable bootstrap only after the owner login was verified.")
    args = parser.parse_args()
    try:
        if args.finish_bootstrap:
            values = read_env(STATE / ".env.preview")
            values.update({"BOOTSTRAP_ADMIN_ENABLED": "false", "BOOTSTRAP_ADMIN_EMAIL": "", "BOOTSTRAP_ADMIN_PASSWORD": ""})
            write_env(STATE / ".env.preview", values)
            print("Owner bootstrap disabled. Private login credentials were retained.")
        else:
            initialize(STATE, args.owner_email, args.models, (REPO / "ai/runtime/.env", REPO / "ai/runtime/.env.local"))
            print("PC preview initialized and verified; existing secrets are preserved on subsequent runs.")
    except (OSError, ValueError):
        print("FAIL: Preview configuration or runtime bundle could not be verified. No credentials were displayed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
