# Methodic ADK Agent Implementation Review

**Branch:** `feat/methodic-adk-agent`  
**Reviewer:** claude-code-reviewer (blind, fresh context)  
**Date:** 2026-05-04  
**Verdict:** REVISE_REQUIRED

---

## Critical Issues (Pipeline Blockers)

### 1. BaseAgent `_run_async_impl` returns None instead of yielding Events

All four custom BaseAgent subclasses implement `_run_async_impl` as a plain coroutine returning `None`. The ADK contract requires an async generator yielding `Event` objects. The ADK runner iterates with `async for event in agent._run_async_impl(ctx)` — a None return causes `TypeError: 'NoneType' object is not an async iterable`.

**Files:** turn_checker_step.py, extractor_step.py, coverage_step.py, bigquery_export_step.py  
**Fix:** Convert to async generators that yield after completing work.

### 2. `transcripts_by_participant` and `active_participant_id` never written

ExtractorStep reads these state keys but no agent writes them. Interviewer/sim agents use `output_key` which writes single turns, not assembled transcripts. Result: extraction always gets empty transcript, returns None, downstream pipeline operates on empty data.

**Files:** extractor_step.py (reads), agent.py (no writer exists)  
**Fix:** Add transcript assembly step that collects turn outputs into per-participant transcript dict.

### 3. Outer `fieldwork_loop` has no escalate path

TurnCheckerStep exits the inner `interview_loop`, but the outer `fieldwork_loop` always runs all `max_iterations=3`. Replanner outputs JSON with `decision: "STOP"` but nothing reads it to set `ctx.actions.escalate`.

**Files:** replanner.py, agent.py  
**Fix:** Convert replanner to custom BaseAgent that parses decision and escalates when STOP.

### 4. `response_json_schema` is wrong SDK key

google-genai Python SDK uses `response_schema`, not `response_json_schema` (Go SDK key). The schema constraint is silently ignored — model returns unconstrained JSON.

**File:** methodic/tools/extractor.py line 91  
**Fix:** Change to `"response_schema"`.

### 5. Demo coverage panel never updates

`demo_runner.py` reads `event.state` which doesn't exist on ADK Event objects. Coverage always shows empty.

**File:** methodic/demo_runner.py lines 72-74  
**Fix:** Read state from session service after runner completes.

---

## Important Issues

### 6. `turn_count` never resets between participants

TurnCheckerStep accumulates turn_count across participants. After participant 1 reaches 6 turns, participants 2+ immediately trigger escalation on their first turn.

**Fix:** Reset turn_count at start of each session_runner iteration.

### 7. A2A card missing `authentication` field

A2A 1.0 requires `authentication` object. Strict clients will reject the card.

**Fix:** Add `"authentication": {"schemes": ["none"]}`.

### 8. BigQuery blocking I/O on async event loop

`export_to_bigquery()` performs synchronous BQ HTTP calls inside an async context.

**Fix:** Wrap in `asyncio.to_thread()`.

---

## Passing Criteria

- **Criterion 1 (Agent graph):** PASS — topology matches spec exactly
- **Criterion 6 (MCP integration):** PASS — McpToolset wrapper correct
- **Criterion 10 (Dockerfile):** PASS — Cloud Run ready with dynamic PORT
- **State contract (wired keys):** PASS for 11/13 keys

---

## Recommendation

Fix criticals 1-5 before demo. Issues 6-8 are important but won't crash the pipeline.
