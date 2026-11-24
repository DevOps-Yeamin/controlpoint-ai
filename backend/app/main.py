import sys
import os
from pathlib import Path

# Ensure project root is in sys.path for Vercel and serverless execution
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

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
        "- Official NLIP Protocol Adapter\n"
        "- Administrative RBAC & Secret Governance"
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# Explicit CORS Origins (No wildcard when credentials are enabled)
cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key", "X-Agent-Key"],
)

# Security Headers & Request Limit Middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Enforce request size limit (5MB max)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 5 * 1024 * 1024:
        return JSONResponse(
            status_code=413,
            content={"detail": "Payload too large. Maximum allowable request size is 5MB."}
        )

    try:
        response = await call_next(request)
    except Exception as exc:
        # In production, avoid leaking raw stack tracebacks
        if settings.ENVIRONMENT == "production":
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Incident logged for security review."}
            )
        raise exc

    # Attach baseline security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

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
            "docs": "/docs",
            "environment": settings.ENVIRONMENT
        }
