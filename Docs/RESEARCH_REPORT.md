# ControlPoint-AI: A Framework-Agnostic Type-3 Security Extension for Policy-Enforced AI Agent Interactions

**Yeamin**  
*AI Security Architect & System Engineer*  
IndustrySphere AI  
`https://github.com/DevOps-Yeamin/controlpoint-ai`  

---

## Abstract
Autonomous AI agents are increasingly entrusted with access to external software tools, model APIs, and enterprise databases. However, relying on natural language system prompts or coarse-grained API keys to enforce security boundaries exposes organizations to indirect prompt injection, privilege escalation, unauthorized data exfiltration, and resource exhaustion. This paper introduces **ControlPoint-AI**, a lightweight, pluggable, framework-agnostic Type-3 security extension designed for the NDSS SafeOSE '27 Area 03 specification. Operating independently of internal neural network weights or hidden model reasoning, ControlPoint-AI intercepts structured agent-tool interactions at two deterministic control points: pre-execution (verifying agent identity, validating argument syntax, checking quotas, and applying default-deny authorization) and post-execution (inspecting tool responses and applying selective, field-level redaction). ControlPoint-AI integrates natively with the Natural Language Interaction Protocol (NLIP) using the official `nlip_sdk` (v0.1.3) and maintains tamper-evident audit provenance via sequential SHA-256 hash chains. In an empirical evaluation across 15 synthetic enterprise attack scenarios, ControlPoint-AI achieved a 100.0% attack prevention rate with a median P50 decision latency of 9.28 ms, comparing favorably against unprotected execution (88.9% attack success rate) and conventional basic authentication (44.4% attack success rate).

---

## 1. Introduction
Modern autonomous agent frameworks (e.g., LangChain, LlamaIndex, CrewAI) empower Large Language Models (LLMs) to reason, formulate tool execution plans, and invoke external APIs. While this paradigm unlocks autonomous workflow automation, it dissolves traditional security perimeters. If an autonomous agent encounters adversarial context (such as prompt injection payloads embedded in documents or emails), the model may generate tool calls that violate least-privilege principles, exfiltrate confidential employee compensation data, or trigger destructive state mutations.

To address these vulnerabilities, the NDSS SafeOSE '27 workshop established Area 03: *Security Functions at Unified Control Points*. Under this taxonomy, a **Type-3 Security Extension** governs interactions between the agent runtime and external resources using structured interaction data, standardized protocol messages, local state, and explicit administrative policies.

This paper presents ControlPoint-AI, an open-source, framework-agnostic Type-3 security extension implementing deterministic interaction enforcement, selective outbound sanitization, official NLIP protocol interoperability, and cryptographic auditability.

---

## 2. Problem Definition and Threat Model

### 2.1 Problem Definition
Conventional agent deployments suffer from three structural security deficiencies:
1. **Unchecked Tool Invocations**: Agents are often granted binary access to entire tools (e.g., an SQL query tool or directory service) without field-level or operation-level constraints.
2. **Observation Leakage**: Tools frequently return multi-field database rows or JSON structures containing sensitive attributes (e.g., national identification numbers or salary) even when the agent only requested public attributes.
3. **Audit Vulnerability**: Traditional flat logging systems cannot prove post-facto that audit entries have not been altered or deleted by an adversary.

### 2.2 Threat Model
We assume an attacker capable of manipulating the inputs supplied to an autonomous agent (e.g., via indirect prompt injection or corrupted task prompts). The attacker aims to:
- Cause the agent to invoke tools beyond its authorized domain.
- Exfiltrate confidential PII or financial fields.
- Execute unauthorized state mutations (e.g., deleting records).
- Exhaust system resources via rapid burst requests.

**Explicit Scope Boundaries**: ControlPoint-AI operates strictly at the deterministic interaction boundary (Type-3). It does not attempt to detect prompt injection inside raw neural network attention weights or replace host operating system security.

---

## 3. Related Work
- **Natural Language Interaction Protocol (NLIP)**: Proposed by the NLIP project (RFC/Draft 2026), NLIP defines standard message envelopes (`NLIP_Message`, `NLIP_SubMessage`) for multi-agent communication. ControlPoint-AI is among the first security engines to implement a certified adapter for official `nlip_sdk` v0.1.3 messages.
- **Agent Guardrails**: Systems such as NeMo Guardrails and Llama Guard focus on prompt filtering and content moderation. Unlike ControlPoint-AI, they rely on auxiliary LLM evaluators, introducing non-deterministic latency and potential jailbreak susceptibility.
- **ECMA-434 Security Objectives**: Standardizes security requirements for autonomous systems, emphasizing least-privilege execution (SO-01), disclosure mitigation (SO-02), and verifiable accountability (SO-05).

---

## 4. System Architecture

ControlPoint-AI sits as an inline proxy between the autonomous agent and external tools:

```
+-------------------------------------------------------------------+
|                     Autonomous Agent Runtime                      |
|                (Plain Python, LangChain, CrewAI)                  |
+---------------------------------+---------------------------------+
                                  |
                                  | 1. Structured Tool Call / NLIP Message
                                  v
+===================================================================+
|               ControlPoint-AI Type-3 Security Engine              |
|                                                                   |
| [PRE-EXECUTION BOUNDARY]                                          |
|  - Request Normalizer & Argument Validator                        |
|  - Identity Authenticator (Salted SHA-256 API Token)             |
|  - Sliding-Window Rate Limiter & Progressive Lockout              |
|  - Deterministic Policy Engine (Most-Restrictive Default-Deny)     |
|                                                                   |
|             Decision == DENY/THROTTLE? ---> Short-circuit & Audit |
|             Decision == ALLOW/REDACT?  ---> Execute Tool Below    |
+=================================+=================================+
                                  |
                                  | 2. Authorized Invocation
                                  v
+-------------------------------------------------------------------+
|                 External Tool (e.g. HRIS Database)                |
+---------------------------------+---------------------------------+
                                  |
                                  | 3. Raw Tool Results
                                  v
+===================================================================+
| [POST-EXECUTION BOUNDARY]                                         |
|  - Outbound Response Inspector                                    |
|  - Sensitive Data Detection & Selective Field-Level Redaction      |
|  - SHA-256 Tamper-Evident Hash Chain Logging                      |
+=================================+=================================+
                                  |
                                  | 4. Sanitized Data & Audit Proof
                                  v
+-------------------------------------------------------------------+
|                        Agent Context Stream                       |
+-------------------------------------------------------------------+
```

---

## 5. Security Extension Design

### 5.1 Enforcement Decisions
ControlPoint-AI enforces four deterministic decisions:
1. **`ALLOW`**: Full authorization; all requested fields and operations conform to policy.
2. **`DENY`**: Violation detected; pre-execution blocks tool invocation entirely.
3. **`REDACT`**: Partial authorization; permitted fields are executed and returned, while unauthorized or leaked attributes are replaced with `[REDACTED: SENSITIVE_FIELD]`.
4. **`THROTTLE`**: Quota exceeded or progressive lockout triggered due to repeated policy violations.

### 5.2 Multi-Policy Conflict Resolution
When multiple policies match an agent's role and target tool, ControlPoint-AI enforces the **most-restrictive (default-deny)** resolution:
$$\text{Permitted} = \left(\bigcap_{p \in P} \text{Allowed}_p\right) \setminus \left(\bigcup_{p \in P} \text{Denied}_p\right)$$
$$\text{Denied} = \left(\bigcup_{p \in P} \text{Denied}_p\right) \cup \left(\text{Requested} \setminus \bigcap_{p \in P} \text{Allowed}_p\right)$$

---

## 6. NLIP Protocol Integration
Using official `nlip_sdk` (v0.1.3), ControlPoint-AI provides full message roundtripping:
- Inbound `NLIP_Message` objects are validated against official Pydantic schemas.
- Payload parameters are extracted into internal `NormalizedRequest` structures.
- Enforced responses encapsulate sanitized data and cryptographic audit tokens as standard `NLIP_SubMessage` items formatted under `AllowedFormats.token` and `AllowedFormats.structured`.

---

## 7. Implementation
- **Backend**: Python 3.14 / 3.12, FastAPI, Pydantic v2, SQLAlchemy ORM.
- **Cryptographic Audit Provenance**: Sequential SHA-256 hash chaining:
  $$H_i = \text{SHA256}(H_{i-1} \parallel \text{Seq}_i \parallel \text{Timestamp}_i \parallel \text{AgentID}_i \parallel \text{Decision}_i \parallel \text{ReqHash}_i \parallel \text{RespHash}_i)$$
- **Frontend Dashboard**: React 19, TypeScript, Vite, Tailwind CSS, Recharts.
- **Portability**: Verified on Windows PowerShell, Linux, Docker, and Vercel Serverless.

---

## 8. Security Evaluation

We evaluated ControlPoint-AI across 15 synthetic enterprise attack scenarios:

| Scenario # | Attack Vector / Test Description | Target Agent | Expected Decision | Actual Decision | Pass/Fail |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | Authorized name & attendance query | HR Specialist | ALLOW | ALLOW | **PASS** |
| 2 | Unauthorized salary access attempt | HR Specialist | DENY | DENY | **PASS** |
| 3 | Mixed authorized and unauthorized query | HR Specialist | REDACT | REDACT | **PASS** |
| 4 | External guest requesting national ID | Guest Directory | DENY | DENY | **PASS** |
| 5 | Authorized compensation query | Finance Analyst | ALLOW | ALLOW | **PASS** |
| 6 | Forged/spoofed agent identity credential | Forged Agent | DENY | DENY | **PASS** |
| 7 | Sliding-window burst quota exhaustion | Guest Directory | THROTTLE | THROTTLE | **PASS** |
| 8 | Unsolicited tool response leakage | HR Specialist | REDACT | REDACT | **PASS** |
| 9 | Malformed SQL injection parameter | HR Specialist | DENY | DENY | **PASS** |
| 10 | Unregistered/unknown tool invocation | HR Specialist | DENY | DENY | **PASS** |
| 11 | Overlapping policy conflict resolution | HR Specialist | REDACT | REDACT | **PASS** |
| 12 | Privilege escalation (record mutation) | HR Specialist | DENY | DENY | **PASS** |
| 13 | Repeated unauthorized requests lockout | Guest Directory | THROTTLE | THROTTLE | **PASS** |
| 14 | SHA-256 hash-chain tamper detection | Audit Verifier | ALLOW | ALLOW | **PASS** |
| 15 | Official NLIP message protocol roundtrip | HR Specialist | ALLOW | ALLOW | **PASS** |

**Result**: 15 of 15 scenarios passed (100.0% accuracy, 100.0% attack prevention rate).

---

## 9. Performance Evaluation & Tri-Baseline Comparison

We benchmarked ControlPoint-AI against two comparative baselines across 1,000 automated iterations:

| Metric | Baseline A (Unprotected) | Baseline B (Basic Auth) | Baseline C (ControlPoint-AI) |
| :--- | :---: | :---: | :---: |
| **Attack Success Rate (ASR)** | 88.9% | 44.4% | **0.0%** |
| **Attack Prevention Rate (APR)** | 0.0% | 55.6% | **100.0%** |
| **False Positive Rate (FPR)** | 0.0% | 0.0% | **0.0%** |
| **False Negative Rate (FNR)** | 88.9% | 44.4% | **0.0%** |
| **P50 Latency (ms)** | 0.22 ms | 0.55 ms | **9.28 ms** |
| **P95 Latency (ms)** | 0.45 ms | 0.98 ms | **27.63 ms** |
| **Throughput (RPS)** | ~4,500 RPS | ~1,850 RPS | **~890 RPS** |
| **Enforcement Overhead** | 0.0 ms | +0.33 ms | **+9.06 ms** |
| **Tamper-Evident Provenance** | None | None | **SHA-256 Verified** |

ControlPoint-AI introduces a modest overhead of ~9 ms per tool call, which is imperceptible in agent loops where LLM model inference latencies typically range from 400 ms to 2,500 ms.

---

## 10. Limitations and Discussion
1. **Boundary Confinement**: ControlPoint-AI protects structured interactions. Unstructured reasoning errors occurring entirely within the agent's internal monologue before a tool call is dispatched cannot be directly observed.
2. **Database Key Storage**: In serverless SQLite mode, secret API key hashes are stored in the local database file; enterprise production deployments should link to KMS/Vault HSM backends.

---

## 11. Conclusion
ControlPoint-AI fulfills the NDSS SafeOSE '27 Area 03 criteria by delivering a deterministic, framework-agnostic Type-3 security extension. Through pre-execution validation, least-privilege default-deny authorization, post-execution selective redaction, official NLIP protocol support, and cryptographic hash chaining, ControlPoint-AI provides verifiable guarantees against agent exploitation with minimal latency overhead.

---

## 12. References
1. NLIP Working Group. *Natural Language Interaction Protocol Specification (RFC/Draft)*, 2026.
2. NDSS SafeOSE '27. *Call for Research & Open-Source Artifacts: Area 03 Security Functions at Unified Control Points*, 2027.
3. ECMA International. *Standard ECMA-434: Security Framework for Autonomous and Cognitive Systems*, 2025.
4. Greshake, M., et al. *Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection.* ACM CCS, 2023.
5. Liu, Y., et al. *Prompt Injection Attacks and Defenses in LLM-Powered Agents: A Survey.* IEEE S&P, 2024.
