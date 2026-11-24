# 3–5 Minute Video Demo Script & Storyboard
**Title**: ControlPoint-AI: Type-3 Policy-Enforced Security Extension for Autonomous AI Agents  
**Target Submission**: NDSS SafeOSE '27 Demonstration Video  
**Duration**: 4 minutes 30 seconds  
**Presenter**: Yeamin (IndustrySphere AI)  

---

## Storyboard & Timing Breakdown

```
[0:00 - 0:45] Problem Definition: Over-Privileged AI Agents & Tool Exploitation
[0:45 - 1:15] Solution Architecture: Type-3 Unified Control Point
[1:15 - 1:45] Official NLIP Protocol Integration (nlip_sdk v0.1.3)
[1:45 - 3:15] Live Security Demonstrations (ALLOW, DENY, REDACT, THROTTLE)
[3:15 - 3:55] Tri-Baseline Benchmark Suite & Real Performance Metrics
[3:55 - 4:30] Limitations, Scope Boundaries, and Open-Source Availability
```

---

## Detailed Script & Visual Cues

### Scene 1: The Problem (0:00 – 0:45)
- **Visual**: Title slide with `IndustrySphere AI • Control What Your AI Agents Can Do.` transitioning to an architectural diagram showing an autonomous agent directly querying enterprise tools and database endpoints without boundaries.
- **Presenter**:
  > *"Autonomous AI agents are increasingly entrusted with direct access to enterprise databases, internal APIs, and critical tools. However, conventional defenses rely on model prompt instructions or coarse API keys. When an agent experiences indirect prompt injection or hallucinated tool parameters, conventional systems fail—allowing sensitive compensation data, employee PII, or mutation commands to leak directly to the LLM context. We need deterministic, external boundary control."*

### Scene 2: ControlPoint-AI Overview & Type-3 Boundary (0:45 – 1:15)
- **Visual**: Animated diagram highlighting the Type-3 security boundary intercepting structured tool calls pre-execution and tool observations post-execution.
- **Presenter**:
  > *"ControlPoint-AI is a framework-agnostic, Type-3 security extension designed for the NDSS SafeOSE Area 03 specification. Operating independently of internal neural weights or hidden reasoning chains, ControlPoint-AI intercepts structured interactions at two deterministic boundaries: pre-execution, where agent identity, tool names, parameters, and quotas are authorized under default-deny policies; and post-execution, where returned payloads are inspected and selectively sanitized before reaching the agent."*

### Scene 3: Official NLIP Integration (1:15 – 1:45)
- **Visual**: Screen capture of `NLIP Protocol` tab in the ControlPoint-AI dashboard displaying an official `NLIP_Message` schema with `nlip_sdk` v0.1.3 verification badge.
- **Presenter**:
  > *"ControlPoint-AI natively supports the Natural Language Interaction Protocol using the official nlip-sdk. Inbound NLIP messages are normalized into our internal security model, evaluated deterministically, and formatted back into valid NLIP response messages with cryptographic audit tokens embedded as standard NLIP submessages."*

### Scene 4: Live Interactive Demonstrations (1:45 – 3:15)
- **Visual**: Live interaction in the **Security Playground** on `http://localhost:5173`:
  1. **Demo 1 (ALLOW)**: HR Specialist requests `name` and `attendance`. Click *Execute*. Result is instantly returned with green `ALLOW` badge.
  2. **Demo 2 (DENY)**: HR Specialist requests confidential `salary`. Click *Execute*. Red `DENY` badge displayed; backend logs confirm tool execution was completely prevented.
  3. **Demo 3 (REDACT)**: HR Specialist requests `name` and `salary`. Click *Execute*. Yellow `REDACT` badge; `name` is preserved while `salary` is replaced with `[REDACTED: SENSITIVE_FIELD]`.
  4. **Demo 4 (THROTTLE)**: Rapid consecutive calls trigger sliding-window quota exhaustion; purple `THROTTLE` badge appears with retry countdown.
  5. **Demo 5 (Audit Chain)**: Click into **Audit Logs**, trigger *Verify Hash-Chain Integrity*, showing sequential SHA-256 integrity across all actions.
- **Presenter**:
  > *"Here in the Security Playground, watch our four core decisions in action. An authorized query is allowed. An unauthorized request for compensation is strictly blocked before the tool can execute. A mixed query receives selective field-level redaction, returning non-sensitive operational fields while protecting confidential attributes. Burst requests are throttled, and every single evaluation is linked in a tamper-evident SHA-256 audit chain."*

### Scene 5: Benchmark & Performance Evaluation (3:15 – 3:55)
- **Visual**: **Evaluation & Benchmarks** tab showing live execution of the 15 security scenarios and the tri-baseline comparison table.
- **Presenter**:
  > *"In our empirical evaluation across 15 attack scenarios, Baseline A (unprotected execution) suffered an 88.9% attack success rate. Baseline B (basic authentication) reduced this to 44.4% but failed against tool leakage and mixed-field queries. ControlPoint-AI achieved a 100% attack prevention rate with a median P50 decision latency of just 9.28 milliseconds, adding negligible overhead to agent workflows."*

### Scene 6: Limitations & Conclusion (3:55 – 4:30)
- **Visual**: Summary slide displaying Apache-2.0 open-source repository link, reproducibility guide, and NDSS SafeOSE '27 submission artifacts.
- **Presenter**:
  > *"ControlPoint-AI enforces explicit interaction security at structured control points. While physical host tampering and direct manipulation of raw neural weights remain outside our boundary scope, ControlPoint-AI establishes robust, verifiable governance over agent-tool interactions. The complete codebase, benchmark suite, and reviewer guide are open-source and available on GitHub. Thank you."*
