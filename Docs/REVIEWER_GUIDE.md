# Reviewer Reproduction Guide
**Project**: ControlPoint-AI  
**Submission**: NDSS SafeOSE '27 (Area 03)  
**Organization**: IndustrySphere AI  
**Repository**: [https://github.com/DevOps-Yeamin/controlpoint-ai](https://github.com/DevOps-Yeamin/controlpoint-ai)  

---

## 1. Quickstart (One-Command Setup)

ControlPoint-AI runs completely locally on Windows, macOS, or Linux using standard Python 3.12+ or Docker Desktop. **No cloud accounts, API keys, or paid services are required.**

### Option A: Local Python & Node Setup
```powershell
# 1. Clone repository
git clone https://github.com/DevOps-Yeamin/controlpoint-ai.git
cd controlpoint-ai

# 2. Install backend dependencies
python -m pip install -r requirements.txt

# 3. Seed synthetic HR database & run tests
python -m pytest backend/tests -v

# 4. Start backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option B: Docker Compose Setup
```bash
docker compose up --build
```
The application will be accessible at:
- Web Dashboard: `http://localhost:5173` (or `http://localhost:8000`)
- OpenAPI Interactive API Documentation: `http://localhost:8000/docs`

---

## 2. Reproducing the 15 Security Evaluation Scenarios

Run the automated test suite directly to evaluate all 15 attack and authorization scenarios:

```powershell
python -m pytest backend/tests/test_synthetic_scenarios.py -v
```

Expected output:
```text
backend/tests/test_synthetic_scenarios.py::test_scenario_1_hr_requests_name_and_attendance PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_2_hr_requests_salary PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_3_hr_requests_name_and_salary PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_4_guest_requests_national_id PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_5_finance_requests_salary PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_6_invalid_identity PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_7_rate_limit_exceeded PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_8_tool_leak_response_inspection PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_9_malformed_arguments_denied PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_10_unknown_tool_denied PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_11_policy_conflict_resolution PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_12_unauthorized_privilege_escalation PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_13_repeated_unauthorized_requests PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_14_audit_chain_tamper_verification PASSED
backend/tests/test_synthetic_scenarios.py::test_scenario_15_nlip_adapter_roundtrip PASSED
================================ 15 passed in 1.12s ================================
```

---

## 3. Running the Tri-Baseline Benchmark Suite

To measure real latency, throughput, and attack prevention metrics across Baseline A (Unprotected), Baseline B (Basic Auth), and Baseline C (ControlPoint-AI):

```powershell
python backend/scripts/run_benchmarks.py
```

Generated raw telemetry files:
- `benchmarks/benchmark_results.json`: Full machine-readable benchmark report with P50/P95 latencies and scenario logs.
- `benchmarks/benchmark_results.csv`: Spreadsheet export for offline analysis.
- `benchmarks/environment_info.json`: Hardware, OS, and Python runtime telemetry.

---

## 4. Interactive Reviewer Verification via Web UI

1. Open your browser to `http://localhost:5173`.
2. **Security Dashboard**: View real-time decision telemetry and verify SHA-256 hash-chain status (`VERIFIED`).
3. **Security Playground**:
   - Select **HR Specialist Agent**.
   - Request `name` and `attendance` -> Click **Execute Protected Tool Call** -> Observe decision **`ALLOW`** with full attendance records.
   - Request `name` and `salary` -> Observe decision **`REDACT`** where name is returned but salary is sanitized to `[REDACTED: SENSITIVE_FIELD]`.
   - Enable **Simulate Tool Leak** -> Observe outbound response inspector intercepting unrequested confidential fields.
4. **Evaluation & Benchmarks**: Click **Run Benchmark Suite** to trigger a live run of all 15 scenarios and inspect the comparative tri-baseline table.
5. **NLIP Protocol**: Submit an official `NLIP_Message` payload to verify roundtrip parsing and submessage token creation.
