# Gemini Review: Methodic Winning Strategy & 72-Hour Execution Focus

**Date:** 2026-05-05
**Reviewer:** gemini-2026-05-05T1029-1ae2
**Verdict:** REVISE_REQUIRED

---

## Executive Summary

The transition to a "Live Vertical Slice" is the correct strategic pivot for this stage of the competition. The thesis—*No useful insights without good data*—is a compelling "wedge" that differentiates Methodic from generic survey bots. However, the execution plan contains structural flaws in its understanding of the Google ADK and A2A protocols that will cause the implementation to fail unless corrected in the next 72 hours.

This review aligns with the **Methodic Thesis** (Data capture as the weakest link) and **Stack Alignment** (Gemini, ADK, MCP, BigQuery).

---

## 1. Winning Chance Assessment

**Verdict:** HIGH (if technical blockers are resolved).

The strategy of "Declarative Data Capture" (pursuing variables, not just finishing forms) is a 10x improvement over legacy surveys. Judges in the Google AI Agent Challenge will look for:
- **Agentic Depth:** Shown through methodology pushback and autonomous re-planning.
- **Ecosystem Integration:** Shown through MCP triangulation and BigQuery export.
- **Business Value:** Quantifiable data quality improvements.

The strategy maximizes winning chances by focusing on *Measurement Quality* rather than just *Chat Interface*.

---

## 2. 72-Hour Execution Focus & Sequencing

The proposed sequence is logical but relies on a successful "Patch" (Step 1) of the ADK design.

### [BLOCKER] ADK Graph Semantics Failure
**Finding:** The current plan treats `FunctionTool` objects as workflow sub-agents.
**Impact:** `SequentialAgent` and `LoopAgent` in ADK require `Agent` instances. Passing raw functions will cause the graph to fail at assembly.
**Mitigation:** The "Patch" must explicitly create wrapper agents (e.g., `ExtractorStepAgent`, `CoverageStepAgent`) for all deterministic functions.

### [MAJOR] SDK Inconsistency
**Finding:** The implementation plan references legacy `google-generativeai` imports, while `requirements.txt` correctly identifies `google-genai`.
**Impact:** Implementation will fail due to missing dependencies or mismatched API calls.
**Mitigation:** Standardize on the `google-genai` SDK and use `response_json_schema` for all extraction tasks as specified in current Google documentation.

---

## 3. Winning Bar: Breadth vs. Narrowness

**Verdict:** CORRECTLY NARROW.

Focusing on B2B SaaS win-loss research is a smart move. It provides a concrete domain where "Product Telemetry" (MCP) and "Economic Buyer" (Methodology) have clear, high-value meanings.

**Missing Proof Points:**
- **[MAJOR] Data Quality Delta:** The "measurable improvement" claim requires a clear baseline comparison. The 72-hour plan should include the creation of the `static_baseline` fixture/logic to prove the delta in the final demo.

---

## 4. Google Stack Claims & Technical Credibility

### [MAJOR] A2A Protocol Compliance
**Finding:** The design specifies `/.well-known/agent.json` and snake_case fields for the Agent Card.
**Impact:** Non-compliance with A2A 1.0 (`/.well-known/agent-card.json` + camelCase). This undermines the "A2A Interoperability" claim.
**Mitigation:** Use ADK's `to_a2a()` to generate the card or manually align with the A2A 1.0 specification.

### [MAJOR] BigQuery Lifecycle
**Finding:** The export logic lacks dataset/table initialization and error surfacing.
**Impact:** A "successful" demo might fail to actually persist data without user feedback.
**Mitigation:** Add an `ensure_dataset_and_table` step and ensure export errors are captured in the session events.

---

## 5. Strategy Refinements (Add/Cut)

### Add
- **Deterministic Loop Exit:** Explicitly define the `escalate = True` tool calls in the 72-hour patch to ensure loops don't hang.
- **Traceability UI:** Prioritize the "Developer Trace View." For a technical challenge, showing *how* the agents hand off is as important as the final output.

### Cut
- **Multi-port A2A:** If A2A + FastAPI composition proves difficult in the first 24 hours of the spike, cut the multi-port complexity and stick to a single ADK-managed endpoint.

---

## Findings Summary

| ID | Title | Severity | Mitigation |
| :--- | :--- | :--- | :--- |
| V-001 | ADK Graph Modeling | BLOCKER | Wrap tools in deterministic agents. |
| V-002 | A2A Discovery Path | MAJOR | Align with A2A 1.0 (agent-card.json). |
| V-003 | SDK Alignment | MAJOR | Use `google-genai` consistently. |
| V-004 | Loop Exit Semantics | MAJOR | Use explicit escalation tools. |
| V-005 | Baseline Comparison | MINOR | Implement static survey baseline for delta proof. |

---

## Final Verdict: APPROVE (with Mandatory Revision of the ADK Design Patch)

The strategy is winning, but the implementation blueprints are currently broken. The 72-hour focus must prioritize the "Patch" of the ADK Design Spec to fix the graph and state contract before a single line of `methodic/` runtime code is written.
