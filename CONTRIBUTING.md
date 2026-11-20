# Contributing to ControlPoint-AI

Thank you for your interest in contributing to ControlPoint-AI, an open-source project by IndustrySphere AI.

## Development Workflow

1. Fork and clone the repository.
2. Set up the Python environment:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set up the Frontend environment:
   ```powershell
   cd frontend
   npm install
   ```

## Running Tests

All pull requests must pass the complete test harness:
```powershell
# Run backend tests and synthetic scenarios
python -m pytest backend/tests -v

# Run frontend build check
cd frontend
npm run build
```

## Contribution Principles
- **No Fabricated Benchmarks**: Never commit hardcoded or synthetic benchmark claims unless verified by the automated benchmark runner.
- **Synthetic Data Only**: Never commit real PII, credentials, or production tokens.
- **Type-3 Determinism**: All policy decisions must be deterministic (`ALLOW`, `DENY`, `REDACT`, `THROTTLE`).
- **Cryptographic Audit**: Any modifications to the audit schema must maintain hash-chain integrity.
