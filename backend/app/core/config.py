from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "ControlPoint-AI"
    ORGANIZATION: str = "IndustrySphere AI"
    TAGLINE: str = "Control What Your AI Agents Can Do."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security & DB
    SECRET_KEY: str = "controlpoint-insecure-secret-key-change-in-production-123456"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/controlpoint.db" if (os.getenv("VERCEL") == "1" or "VERCEL" in os.environ) else f"sqlite:///{BASE_DIR}/controlpoint.db"
    )
    
    # Rate Limiting Defaults
    RATE_LIMIT_REQUESTS: int = 15
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Frontend build location (for single-container production deployment)
    FRONTEND_DIST_DIR: Path = BASE_DIR.parent / "frontend" / "dist"
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
