import hmac
from typing import Optional
from fastapi import Request, Header, HTTPException, status
from backend.app.core.config import settings

# Predefined demo agent key prefixes to detect and prevent agent privilege escalation attempts
AGENT_KEY_PREFIXES = ("cp_live_hr_", "cp_live_finance_", "cp_live_guest_")

def verify_admin_access(
    request: Request,
    x_admin_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Enforce administrative authentication and role separation.
    Protects administrative operations (agent creation, policy modification, audit logs).
    Separates ordinary AI agent identities from administrative privileges.
    """
    token: Optional[str] = None
    if x_admin_key:
        token = x_admin_key.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

    # If missing credential:
    if not token:
        # In demo mode, allow read-only GET requests for dashboard telemetry
        if settings.ENABLE_DEMO_MODE and request.method in ("GET", "HEAD"):
            return "demo_viewer"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Provide valid 'X-Admin-Key' or 'Authorization: Bearer <token>' header."
        )

    # Detect privilege escalation: An ordinary agent attempting to act as admin
    if any(token.startswith(prefix) for prefix in AGENT_KEY_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Agent identities are strictly separated from administrative privileges. Privilege escalation denied."
        )

    # Constant-time comparison against configured ADMIN_API_KEY
    if not hmac.compare_digest(token, settings.ADMIN_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Invalid administrative credentials."
        )

    return "superadmin"
