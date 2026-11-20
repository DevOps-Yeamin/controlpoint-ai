# Security Policy — ControlPoint-AI

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting Security Vulnerabilities

The ControlPoint-AI engineering team at IndustrySphere AI takes software and AI security seriously. If you discover a security vulnerability in our policy enforcement engine, request normalizer, or hash-chain logging system, please report it responsibly.

### How to Report
1. Email: `security@industrysphere.ai` with the subject `[VULNERABILITY] ControlPoint-AI`.
2. Include:
   - Component affected (e.g., Policy Engine, Response Inspector, Hash-Chain Audit).
   - Step-by-step reproduction instructions or test case.
   - Potential impact and severity assessment.
   - Proof of concept payload (using synthetic test data only).

Please do **not** file public GitHub issues for undisclosed security vulnerabilities.

### Response Timeline
- Initial acknowledgment: within 24 hours.
- Vulnerability triage and validation: within 72 hours.
- Coordinated remediation and patch release: within 14 calendar days.

## Security Design Assumptions

- **Untrusted Agents**: Agent IDs supplied in network payloads are never trusted without cryptographic credential verification.
- **Default Deny**: Any tool call, operation, or attribute not explicitly authorized by active policy is blocked.
- **Response Inspection**: Data returned from external tools is inspected and sanitized prior to return to prevent accidental leaks.
- **Limitations**: ControlPoint-AI enforces deterministic interaction security; it does not claim to prevent all prompt injection attacks at the foundational model level.
