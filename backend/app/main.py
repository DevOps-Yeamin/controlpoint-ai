import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.engine.seed import seed_database
from backend.app.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "ControlPoint-AI: A Framework-Agnostic Type-3 Security Extension for Policy-Enforced AI Agent Interactions.\n\n"
        "Features:\n"
        "- Deterministic Least-Privilege Authorization (ALLOW, DENY, REDACT, THROTTLE)\n"
        "- Request Normalization & Agent Identity Verification\n"
        "- Sensitive Data Pattern Inspection & Response Redaction\n"
        "- Tamper-Evident Hash-Chain Audit Logging\n"
        "- Official NLIP Protocol Adapter"
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve compiled React frontend if present
frontend_dist = settings.FRONTEND_DIST_DIR
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root_info():
        return {
            "service": settings.PROJECT_NAME,
            "organization": settings.ORGANIZATION,
            "tagline": settings.TAGLINE,
            "version": settings.VERSION,
            "status": "online",
            "api_docs": "/docs",
            "frontend_status": "building or standalone mode"
        }
