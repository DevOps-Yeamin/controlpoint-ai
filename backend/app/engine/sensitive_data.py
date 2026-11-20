import re
from typing import Any, Dict, List, Set, Tuple

# Sensitive patterns
SSN_REGEX = re.compile(r"\b(?:\d{3}-\d{2}-\d{4}|SSN-[A-Za-z0-9-]+)\b", re.IGNORECASE)
CREDIT_CARD_REGEX = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")
API_KEY_REGEX = re.compile(r"\b(?:cp_live_|sk_live_|key_)[a-zA-Z0-9_-]{12,}\b")

DEFAULT_SENSITIVE_FIELD_NAMES = {
    "salary", "compensation", "wage",
    "national_id", "ssn", "social_security_number",
    "password", "api_key", "secret", "credit_card",
    "bank_account", "tax_id"
}

class SensitiveDataInspector:
    @staticmethod
    def inspect_text_for_patterns(text: str) -> List[str]:
        """Detect sensitive patterns in a string."""
        findings = []
        if not isinstance(text, str):
            return findings
        if SSN_REGEX.search(text):
            findings.append("national_id_pattern")
        if CREDIT_CARD_REGEX.search(text):
            findings.append("credit_card_pattern")
        if API_KEY_REGEX.search(text):
            findings.append("api_key_pattern")
        return findings

    @staticmethod
    def redact_data(
        data: Any,
        denied_fields: Set[str] = None,
        redact_patterns: bool = True
    ) -> Tuple[Any, List[str]]:
        """
        Recursively redact denied fields and sensitive patterns from data structures.
        Returns:
            Tuple of (redacted_data, list_of_redacted_field_or_pattern_names)
        """
        denied_fields = {f.lower().strip() for f in (denied_fields or set())}
        redacted_occurrences: List[str] = []

        def _traverse(node: Any) -> Any:
            if isinstance(node, dict):
                redacted_dict = {}
                for k, v in node.items():
                    k_str = str(k).lower().strip()
                    if k_str in denied_fields:
                        redacted_dict[k] = "[REDACTED: SENSITIVE_FIELD]"
                        if k_str not in redacted_occurrences:
                            redacted_occurrences.append(k_str)
                    else:
                        redacted_dict[k] = _traverse(v)
                return redacted_dict

            elif isinstance(node, list):
                return [_traverse(item) for item in node]

            elif isinstance(node, str) and redact_patterns:
                # Inspect for sensitive regex patterns
                cleaned = node
                if SSN_REGEX.search(cleaned):
                    cleaned = SSN_REGEX.sub("[REDACTED: NATIONAL_ID]", cleaned)
                    if "national_id" not in redacted_occurrences:
                        redacted_occurrences.append("national_id")
                if CREDIT_CARD_REGEX.search(cleaned):
                    cleaned = CREDIT_CARD_REGEX.sub("[REDACTED: CREDIT_CARD]", cleaned)
                    if "credit_card" not in redacted_occurrences:
                        redacted_occurrences.append("credit_card")
                if API_KEY_REGEX.search(cleaned):
                    cleaned = API_KEY_REGEX.sub("[REDACTED: API_KEY]", cleaned)
                    if "api_key" not in redacted_occurrences:
                        redacted_occurrences.append("api_key")
                return cleaned

            return node

        result = _traverse(data)
        return result, redacted_occurrences
