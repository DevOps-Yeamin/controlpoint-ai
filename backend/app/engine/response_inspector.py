from typing import Any, List, Set, Tuple
from backend.app.engine.sensitive_data import SensitiveDataInspector

class ResponseInspector:
    @staticmethod
    def inspect_and_sanitize(
        raw_data: Any,
        permitted_fields: List[str],
        denied_fields: List[str]
    ) -> Tuple[Any, List[str]]:
        """
        Inspect outbound tool data.
        Guarantees that unauthorized fields or sensitive patterns never reach the agent.
        
        Returns:
            Tuple of (sanitized_data, list_of_redacted_field_names)
        """
        permitted_set = {f.lower().strip() for f in (permitted_fields or [])}
        denied_set = {f.lower().strip() for f in (denied_fields or [])}
        all_redacted: Set[str] = set()

        def _clean_item(item: Any) -> Any:
            if isinstance(item, dict):
                clean_dict = {}
                for k, v in item.items():
                    k_lower = str(k).lower().strip()
                    # If field is explicitly denied or unauthorized
                    if k_lower in denied_set:
                        clean_dict[k] = "[REDACTED: SENSITIVE_FIELD]"
                        all_redacted.add(k_lower)
                    elif permitted_set and k_lower not in permitted_set:
                        # Field leaked by tool without explicit permission
                        clean_dict[k] = "[REDACTED: SENSITIVE_FIELD]"
                        all_redacted.add(k_lower)
                    else:
                        clean_dict[k] = _clean_item(v)
                return clean_dict
            elif isinstance(item, list):
                return [_clean_item(elem) for elem in item]
            else:
                return item

        filtered = _clean_item(raw_data)

        # Run pattern-level redaction on filtered data
        final_data, pattern_redactions = SensitiveDataInspector.redact_data(
            filtered,
            denied_fields=denied_set,
            redact_patterns=True
        )
        for p in pattern_redactions:
            all_redacted.add(p)

        return final_data, sorted(list(all_redacted))
