"""
ControlPoint-AI Benchmark & Evaluation Runner
Executes reproducible tri-baseline benchmarks on the active host environment.
Measures real latencies, throughput, attack prevention rate, and exports raw data.
"""
import time
import json
import csv
import sys
import platform
import os
from pathlib import Path

# Ensure root is in sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.database import SessionLocal, Base, engine
from backend.app.api.endpoints import run_scenarios
from backend.app.engine.seed import seed_database

def run_evaluation_suite():
    print("=" * 70)
    print("CONTROLPOINT-AI: NDSS SafeOSE '27 Evaluation & Benchmark Suite")
    print("=" * 70)

    # 1. Initialize & Seed Clean Test DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    try:
        print("[*] Running 15 Deterministic Security Evaluation Scenarios...")
        t0 = time.perf_counter()
        report = run_scenarios(db)
        total_time_ms = (time.perf_counter() - t0) * 1000

        print(f"[✓] Scenarios Completed: {report.passed_scenarios}/{report.total_scenarios} Passed")
        print(f"[✓] Attack Prevention Rate: {report.prevention_rate_pct}%")
        print(f"[✓] Accuracy Rate: {report.accuracy_rate_pct}%")
        print(f"[✓] P50 Latency: {report.p50_latency_ms} ms")
        print(f"[✓] P95 Latency: {report.p95_latency_ms} ms")
        print(f"[✓] Total Suite Execution Time: {round(total_time_ms, 2)} ms")

        # 2. Collect Environment Info
        env_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sqlite_version": "3",
            "framework": "FastAPI + Pydantic v2 + SQLAlchemy"
        }

        # 3. Export Raw Results
        out_dir = repo_root / "benchmarks"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "benchmark_results.json"
        csv_path = out_dir / "benchmark_results.csv"
        env_path = out_dir / "environment_info.json"

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        print(f"[+] Raw JSON results exported to: {json_path}")

        # Write CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Scenario ID", "Name", "Agent ID", "Requested Fields",
                "Expected Decision", "Actual Decision", "Passed",
                "Latency (ms)", "Details"
            ])
            for s in report.scenarios:
                writer.writerow([
                    s.scenario_id, s.name, s.agent_id,
                    ";".join(s.requested_fields), s.expected_decision,
                    s.actual_decision, s.passed, s.latency_ms, s.details
                ])
        print(f"[+] Raw CSV results exported to: {csv_path}")

        # Write Environment Info
        with open(env_path, "w", encoding="utf-8") as f:
            json.dump(env_info, f, indent=2)
        print(f"[+] Environment telemetry exported to: {env_path}")

        print("\n" + "=" * 70)
        print("TRI-BASELINE COMPARISON SUMMARY")
        print("=" * 70)
        for b in report.baselines or []:
            print(f"- {b.name}:")
            print(f"    Attack Success Rate: {b.attack_success_rate_pct}% | Prevention: {b.attack_prevention_rate_pct}%")
            print(f"    P50 Latency: {b.p50_latency_ms} ms | Overhead: {b.enforcement_overhead_ms} ms")
            print(f"    Throughput: {b.throughput_rps} RPS | Audit Verified: {b.audit_chain_verified}")

    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation_suite()
