# api/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # These will be loaded from .env automatically
    app_name: str = "Research Retrieval"  # Default if not in .env
    
    # MinIO settings - will be read from .env
    minio_endpoint: str  # Required, no default
    minio_access_key: str  # Required
    minio_secret_key: str  # Required
    minio_bucket: str = "research-papers"  # Default value
    
    # Optional settings
    vllm_url: str = "http://localhost:8000"
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # MINIO_ENDPOINT or minio_endpoint both work