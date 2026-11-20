import json
from sqlalchemy.orm import Session
from backend.app.models.entities import Agent, Policy, SyntheticEmployee, AuditLog
from backend.app.engine.identity import hash_api_key

# Predefined API keys for demo agents (transparently documented for reproducible evaluation)
SEED_KEYS = {
    "hr-agent-01": "cp_live_hr_specialist_agent_key_2026",
    "finance-agent-01": "cp_live_finance_analyst_agent_key_2026",
    "guest-agent-01": "cp_live_guest_external_agent_key_2026"
}

def seed_database(db: Session):
    """Seed initial synthetic database, agents, and security policies."""
    
    # 1. Seed Synthetic Employees
    if db.query(SyntheticEmployee).count() == 0:
        employees = [
            SyntheticEmployee(
                employee_id="EMP-1001",
                name="Dr. Sarah Chen",
                email="sarah.chen@industrysphere.ai",
                department="Engineering",
                attendance="99.2%",
                salary=185000.00,
                national_id="SSN-982-12-8841"
            ),
            SyntheticEmployee(
                employee_id="EMP-1002",
                name="Marcus Vance",
                email="marcus.vance@industrysphere.ai",
                department="Engineering",
                attendance="97.8%",
                salary=162000.00,
                national_id="SSN-431-89-2201"
            ),
            SyntheticEmployee(
                employee_id="EMP-1003",
                name="Elena Rostova",
                email="elena.rostova@industrysphere.ai",
                department="Finance",
                attendance="98.5%",
                salary=145000.00,
                national_id="SSN-209-54-7712"
            ),
            SyntheticEmployee(
                employee_id="EMP-1004",
                name="David Kim",
                email="david.kim@industrysphere.ai",
                department="Human Resources",
                attendance="99.5%",
                salary=118000.00,
                national_id="SSN-773-19-4433"
            ),
            SyntheticEmployee(
                employee_id="EMP-1005",
                name="Amira Patel",
                email="amira.patel@industrysphere.ai",
                department="Marketing",
                attendance="96.4%",
                salary=132000.00,
                national_id="SSN-654-32-1190"
            ),
            SyntheticEmployee(
                employee_id="EMP-1006",
                name="James Wilson",
                email="james.wilson@industrysphere.ai",
                department="Legal",
                attendance="98.1%",
                salary=195000.00,
                national_id="SSN-881-45-9920"
            ),
        ]
        db.add_all(employees)
        db.commit()

    # 2. Seed Agents
    if db.query(Agent).count() == 0:
        agents = [
            Agent(
                id="hr-agent-01",
                name="HR Specialist Agent",
                role="HR Specialist",
                description="Autonomous HR Assistant authorized for employee profile & attendance queries.",
                api_key_hash=hash_api_key(SEED_KEYS["hr-agent-01"]),
                api_key_prefix="cp_live_hr...",
                rate_limit_per_minute=20,
                is_active=True
            ),
            Agent(
                id="finance-agent-01",
                name="Finance Operations Agent",
                role="Financial Analyst",
                description="Automated financial planning agent authorized for payroll and compensation records.",
                api_key_hash=hash_api_key(SEED_KEYS["finance-agent-01"]),
                api_key_prefix="cp_live_fin...",
                rate_limit_per_minute=20,
                is_active=True
            ),
            Agent(
                id="guest-agent-01",
                name="Guest Directory Agent",
                role="External Guest",
                description="Public-facing assistant with restricted access strictly limited to directory name & department.",
                api_key_hash=hash_api_key(SEED_KEYS["guest-agent-01"]),
                api_key_prefix="cp_live_gue...",
                rate_limit_per_minute=5,
                is_active=True
            ),
        ]
        db.add_all(agents)
        db.commit()

    # 3. Seed Policies
    if db.query(Policy).count() == 0:
        policies = [
            Policy(
                id="policy-hr-directory-v1",
                name="HR Employee Directory Access Policy",
                version="v1.0.0",
                description="Explicit permissions for HR agents. Allows reading directory attributes. Strictly denies salary and national ID.",
                target_role="HR Specialist",
                target_tool="employee_directory",
                allowed_operations=json.dumps(["read", "query"]),
                allowed_fields=json.dumps(["employee_id", "name", "email", "department", "attendance"]),
                denied_fields=json.dumps(["salary", "national_id"]),
                default_action="DENY",
                is_active=True
            ),
            Policy(
                id="policy-finance-payroll-v1",
                name="Finance Payroll & Compensation Access Policy",
                version="v1.0.0",
                description="Grants financial agents access to compensation fields. Denies national ID SSN by default.",
                target_role="Financial Analyst",
                target_tool="employee_directory",
                allowed_operations=json.dumps(["read", "query"]),
                allowed_fields=json.dumps(["employee_id", "name", "department", "salary"]),
                denied_fields=json.dumps(["national_id"]),
                default_action="DENY",
                is_active=True
            ),
            Policy(
                id="policy-guest-public-v1",
                name="Guest Public Directory Access Policy",
                version="v1.0.0",
                description="Least-privilege public access policy. Only public employee name and department permitted.",
                target_role="External Guest",
                target_tool="employee_directory",
                allowed_operations=json.dumps(["read"]),
                allowed_fields=json.dumps(["name", "department"]),
                denied_fields=json.dumps(["employee_id", "email", "attendance", "salary", "national_id"]),
                default_action="DENY",
                is_active=True
            ),
        ]
        db.add_all(policies)
        db.commit()
