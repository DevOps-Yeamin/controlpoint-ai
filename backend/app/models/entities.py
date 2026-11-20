import datetime
import json
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from backend.app.database import Base

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    api_key_hash = Column(String(128), nullable=False)
    api_key_prefix = Column(String(16), nullable=False) # e.g. "cp_live_..."
    is_active = Column(Boolean, default=True)
    rate_limit_per_minute = Column(Integer, default=15)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    version = Column(String(32), default="v1.0.0")
    description = Column(Text, nullable=True)
    target_role = Column(String(64), nullable=False, index=True)
    target_tool = Column(String(128), nullable=False, default="*") # tool name or *
    allowed_operations = Column(Text, default="[]") # JSON list
    allowed_fields = Column(Text, default="[]") # JSON list
    denied_fields = Column(Text, default="[]") # JSON list
    default_action = Column(String(16), default="DENY") # Default-deny
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    def get_allowed_operations(self):
        try:
            return json.loads(self.allowed_operations or "[]")
        except:
            return []

    def get_allowed_fields(self):
        try:
            return json.loads(self.allowed_fields or "[]")
        except:
            return []

    def get_denied_fields(self):
        try:
            return json.loads(self.denied_fields or "[]")
        except:
            return []

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    sequence_number = Column(Integer, nullable=False, unique=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    agent_role = Column(String(64), nullable=False)
    tool_name = Column(String(128), nullable=False)
    operation = Column(String(64), nullable=False)
    requested_fields = Column(Text, default="[]") # JSON list
    decision = Column(String(16), nullable=False, index=True) # ALLOW, DENY, REDACT, THROTTLE
    reason = Column(Text, nullable=False)
    redacted_fields = Column(Text, default="[]") # JSON list
    request_payload_hash = Column(String(64), nullable=False)
    response_payload_hash = Column(String(64), nullable=False)
    prev_entry_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)

    def get_requested_fields(self):
        try:
            return json.loads(self.requested_fields or "[]")
        except:
            return []

    def get_redacted_fields(self):
        try:
            return json.loads(self.redacted_fields or "[]")
        except:
            return []

class SyntheticEmployee(Base):
    __tablename__ = "synthetic_employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    department = Column(String(64), nullable=False)
    attendance = Column(String(32), nullable=False)
    salary = Column(Float, nullable=False)
    national_id = Column(String(64), nullable=False)
