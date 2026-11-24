import os
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "ControlPoint-AI"
    ORGANIZATION: str = "IndustrySphere AI"
    TAGLINE: str = "Control What Your AI Agents Can Do."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    
    # Administrative & Security Keys
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "cp_live_admin_secret_key_2026")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cp_dev_secret_key_for_local_testing_only_64chars_min_length_abcdef")
    ENABLE_DEMO_MODE: bool = os.getenv("ENABLE_DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/controlpoint.db" if (os.getenv("VERCEL") == "1" or "VERCEL" in os.environ) else f"sqlite:///{BASE_DIR}/controlpoint.db"
    )
    
    # Rate Limiting Defaults
    RATE_LIMIT_REQUESTS: int = 15
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Explicit CORS Origins (No wildcard with credentials)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    
    # Frontend build location (for single-container production deployment)
    FRONTEND_DIST_DIR: Path = BASE_DIR.parent / "frontend" / "dist"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    def validate_production_secrets(self):
        """Ensure secure secrets when running in production mode."""
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY.startswith("cp_dev_secret"):
                raise ValueError("Production environment requires a secure, non-default SECRET_KEY.")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production.")
            if not self.ADMIN_API_KEY or self.ADMIN_API_KEY == "cp_live_admin_secret_key_2026":
                raise ValueError("Production environment requires a unique, secure ADMIN_API_KEY.")

settings = Settings()
# Validate if started in production mode
if os.getenv("ENVIRONMENT", "").lower() == "production":
    settings.validate_production_secrets()
