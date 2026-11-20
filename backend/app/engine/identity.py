import hashlib
import secrets
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import Agent

SALT = "controlpoint_agent_salt_2026"

def hash_api_key(api_key: str) -> str:
    """Generate deterministic salted hash for agent API key."""
    return hashlib.sha256(f"{SALT}:{api_key}".encode("utf-8")).hexdigest()

def generate_agent_key(agent_id: str) -> Tuple[str, str, str]:
    """
    Generate a new API key pair for an agent.
    Returns: (raw_key, key_hash, prefix)
    """
    rand_token = secrets.token_hex(16)
    raw_key = f"cp_live_{agent_id}_{rand_token}"
    key_hash = hash_api_key(raw_key)
    prefix = f"cp_live_{agent_id[:6]}..."
    return raw_key, key_hash, prefix

class IdentityValidator:
    @staticmethod
    def validate(
        db: Session,
        agent_id: str,
        api_key: Optional[str]
    ) -> Tuple[Optional[Agent], Optional[str]]:
        """
        Validates agent identity using cryptographic credential verification.
        Never trusts user-supplied agent ID alone.
        
        Returns:
            Tuple of (Agent, None) on success, or (None, error_reason) on failure.
        """
        if not agent_id or not agent_id.strip():
            return None, "Missing agent identifier"

        agent = db.query(Agent).filter(Agent.id == agent_id.strip()).first()
        if not agent:
            return None, f"Agent '{agent_id}' is not registered in security directory"

        if not agent.is_active:
            return None, f"Agent '{agent_id}' account is disabled"

        if not api_key or not api_key.strip():
            return None, "Unauthenticated: Missing agent API key credentials"

        # Verify hashed secret
        computed_hash = hash_api_key(api_key.strip())
        if computed_hash != agent.api_key_hash:
            return None, "Authentication failed: Invalid credentials for agent identity"

        return agent, None
