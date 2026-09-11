from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_env: str = "development"
    runtime_mode: str = "FIXTURE"
    
    port: int = 8000
    host: str = "0.0.0.0"
    
    redis_url: str = "redis://localhost:6379/0"
    
    spring_callback_base_url: str = "http://localhost:8080/internal/v1/ai/jobs"
    # Internal API callback authentication (overridden via INTERNAL_API_KEY)
    internal_api_key: str = "secret-key-default"  # Local non-secret development default
    
    model_manifest_path: Optional[str] = None
    model_artifact_path: Optional[str] = None

    # MinIO storage configuration (private internal access only)
    # Production values must be provided via environment variables (MINIO_ACCESS_KEY, MINIO_SECRET_KEY)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"      # Local non-secret development default
    minio_secret_key: str = "minioadmin123"   # Local non-secret development default
    minio_secure: bool = False
    minio_bucket: str = "mathvision"

    # OCR configuration
    # Default is "noop" (disabled/test provider) to protect established grading runtime.
    # Set OCR_PROVIDER="crnn_vi_handwriting_v1" for explicit staging/dev testing.
    ocr_provider: str = "noop"
    ocr_model_dir: Optional[str] = None
    ocr_bridge_mode: str = "off"  # "off" | "shadow"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
