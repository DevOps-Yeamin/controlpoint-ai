# Deployment Guide — ControlPoint-AI

This document outlines the deployment configurations for ControlPoint-AI, specifically addressing the **Vercel** serverless platform and **Docker** containerized environments.

---

## 1. Vercel Deployment

### Root Cause of `[FASTAPI_ENTRYPOINT_NOT_FOUND]`

When Vercel builds Python / FastAPI applications without an explicit entrypoint, its framework detector scans the repository for top-level variables named `app = FastAPI(...)` or `from ... import app`.

In the original configuration:
- `backend/app/main.py` defines `app = FastAPI(...)` (Production entrypoint).
- `backend/tests/conftest.py` imported `from backend.app.main import app` for test fixtures.

This ambiguity caused Vercel's automated scanner to discover multiple competing entrypoints and throw:
```text
[FASTAPI_ENTRYPOINT_NOT_FOUND]
Potential entrypoints:
- backend/app/main.py (variable: app)
- backend/tests/conftest.py (variable: app)
```

### Remediation Applied

1. **Scoped Test Fixtures**: `backend/tests/conftest.py` was refactored to alias the import as `_main_app` (`from backend.app.main import app as _main_app`), ensuring `backend/app/main.py` is the **only** Python file exporting `app`.
2. **Explicit FastAPI & Vercel Entrypoint**: Configured `pyproject.toml`:
   ```toml
   [tool.fastapi]
   entrypoint = "backend.app.main:app"

   [tool.vercel]
   entrypoint = "backend/app/main.py:app"
   ```
3. **Multi-Runtime `vercel.json`**: Created [vercel.json](file:///C:/Users/Yeamin/Documents/controlpoint-ai/vercel.json) instructing Vercel to:
   - Build `backend/app/main.py` using `@vercel/python`.
   - Build `frontend/package.json` using `@vercel/static-build`.
   - Route `/api/(.*)`, `/docs`, and `/openapi.json` to `backend/app/main.py`.
   - Route all single-page application routes to `frontend/dist`.
4. **Serverless Filesystem Adaptation**: Updated `backend/app/core/config.py` so that under the Vercel serverless environment (`VERCEL=1`), SQLite defaults to `/tmp/controlpoint.db` (the only writable directory in AWS Lambda / Vercel functions).
5. **Dynamic `sys.path` Resolution**: Injected the project root into `sys.path` in `backend/app/main.py` to ensure `from backend.app...` imports resolve seamlessly across all serverless invocations.

---

### Exact Vercel Project Settings

When importing the repository (`https://github.com/DevOps-Yeamin/controlpoint-ai`) in the Vercel Dashboard:

| Setting | Recommended Value | Notes |
| :--- | :--- | :--- |
| **Framework Preset** | **Other** (or **FastAPI**) | With `vercel.json` present, **Other** allows `vercel.json` to orchestrate both Python and Vite. |
| **Root Directory** | `./` | Leave blank or set to repository root (`.`). |
| **Build Command** | *Default* (handled by `vercel.json`) | `vercel.json` builds both `backend/app/main.py` and `frontend/package.json`. |
| **Output Directory** | *Default* | Handled automatically by `vercel.json`. |
| **Install Command** | *Default* | Automatically installs `requirements.txt` and `frontend/package.json`. |

#### Recommended Environment Variables in Vercel:

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `ControlPoint-AI` | Project name displayed across API responses |
| `ORGANIZATION` | `IndustrySphere AI` | Organization banner |
| `TAGLINE` | `Control What Your AI Agents Can Do.` | Tagline banner |
| `SECRET_KEY` | *(generate a random 32-character string)* | Session & cryptographic HMAC signing |
| `RATE_LIMIT_REQUESTS` | `20` | Requests allowed per minute per agent |
| `RATE_LIMIT_WINDOW_SECONDS`| `60` | Sliding window duration in seconds |

---

## 2. Docker & Containerized Deployment

For production deployments on VPS, AWS EC2, DigitalOcean, or Render:

```powershell
# Build and run with Docker Compose
docker compose up --build -d

# Check logs and health
docker compose ps
docker compose logs -f
```

The production container uses a multi-stage Docker build:
1. `node:22-alpine` compiles the React 19 frontend into static assets.
2. `python:3.12-slim` serves both the FastAPI API and the compiled frontend from a single port (`8000`).

---

## 3. Local Verification

To test the application locally prior to redeployment:

```powershell
# 1. Verify 23/23 tests pass
python -m pytest backend/tests -v

# 2. Verify frontend compilation
cd frontend
npm run build
cd ..

# 3. Test FastAPI discovery
python -c "from fastapi_cli.config import FastAPIConfig; print(FastAPIConfig.resolve())"

# 4. Start local development server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
