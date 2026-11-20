from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.entities import SyntheticEmployee

ALL_EMPLOYEE_FIELDS = [
    "employee_id",
    "name",
    "email",
    "department",
    "attendance",
    "salary",
    "national_id"
]

class EmployeeDirectoryTool:
    """
    Synthetic HR Employee Directory Tool.
    Simulates enterprise HRIS tool calls made by autonomous agents.
    """
    @staticmethod
    def execute(
        db: Session,
        operation: str = "read",
        parameters: Dict[str, Any] = None,
        requested_fields: Optional[List[str]] = None,
        force_leak_unauthorized_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute tool query against synthetic employee database.
        If requested_fields is provided and force_leak_unauthorized_data is False,
        projects only the requested fields (standard DB query behavior).
        If force_leak_unauthorized_data is True, simulates an insecure tool returning
        all internal attributes (salary, SSN) regardless of request.
        """
        parameters = parameters or {}
        query = db.query(SyntheticEmployee)

        if "department" in parameters and parameters["department"]:
            query = query.filter(SyntheticEmployee.department.ilike(f"%{parameters['department']}%"))
        
        if "employee_id" in parameters and parameters["employee_id"]:
            query = query.filter(SyntheticEmployee.employee_id == parameters["employee_id"])

        limit = int(parameters.get("limit", 10))
        records = query.limit(limit).all()

        fields_to_return = ALL_EMPLOYEE_FIELDS if (force_leak_unauthorized_data or not requested_fields) else requested_fields

        results = []
        for emp in records:
            item = {}
            for field in fields_to_return:
                f_clean = str(field).lower().strip()
                if hasattr(emp, f_clean):
                    item[f_clean] = getattr(emp, f_clean)
            results.append(item)

        return results
