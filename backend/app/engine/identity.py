import hashlib
import secrets
import hmac
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import Agent

# Iterations for PBKDF2 key derivation
PBKDF2_ITERATIONS = 50000
LEGACY_SALT = "controlpoint_agent_salt_2026"

def hash_api_key(api_key: str, salt: Optional[str] = None) -> str:
    """
    Generate a cryptographic hash for an agent API key using per-key salt and PBKDF2-HMAC-SHA256.
    Format: salt$derived_hash
    """
    if not salt:
        salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        api_key.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    ).hex()
    return f"{salt}${derived}"

def verify_api_key_hash(api_key: str, stored_hash: str) -> bool:
    """
    Constant-time API key verification with support for both per-key salted PBKDF2 and legacy hashes.
    """
    if not api_key or not stored_hash:
        return False

    if "$" in stored_hash:
        salt, expected_digest = stored_hash.split("$", 1)
        computed_digest = hashlib.pbkdf2_hmac(
            "sha256",
            api_key.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS
        ).hex()
        return hmac.compare_digest(computed_digest, expected_digest)
    else:
        # Backward compatibility for legacy seed entries
        legacy_digest = hashlib.sha256(f"{LEGACY_SALT}:{api_key}".encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_digest, stored_hash)

def generate_agent_key(agent_id: str) -> Tuple[str, str, str]:
    """
    Generate a new API key pair for an agent with unique cryptographic salt.
    Returns: (raw_key, key_hash, prefix)
    """
    rand_token = secrets.token_hex(20)
    raw_key = f"cp_live_{agent_id}_{rand_token}"
    key_hash = hash_api_key(raw_key)
    prefix = f"{raw_key[:12]}..."
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
            return None, f"Agent '{agent_id}' credential is revoked or disabled"

        if not api_key or not api_key.strip():
            return None, "Unauthenticated: Missing agent API key credentials"

        # Constant-time comparison against per-key salted cryptographic hash
        if not verify_api_key_hash(api_key.strip(), agent.api_key_hash):
            return None, "Authentication failed: Invalid credentials for agent identity"

        return agent, None

    @staticmethod
    def revoke_agent(db: Session, agent_id: str) -> Tuple[bool, str]:
        """Revoke an agent's active credentials."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False, f"Agent '{agent_id}' not found"
        agent.is_active = False
        db.commit()
        return True, f"Agent '{agent_id}' credentials successfully revoked"

    @staticmethod
    def rotate_agent_key(db: Session, agent_id: str) -> Tuple[Optional[str], str]:
        """Rotate an agent's API key, generating a fresh salt and invalidating previous key."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None, f"Agent '{agent_id}' not found"
        
        raw_key, new_hash, prefix = generate_agent_key(agent_id)
        agent.api_key_hash = new_hash
        agent.api_key_prefix = prefix
        agent.is_active = True
        db.commit()
        return raw_key, f"API key rotated for agent '{agent_id}'"
