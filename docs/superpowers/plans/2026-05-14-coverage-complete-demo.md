# Coverage-Complete Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure the recorded Methodic demo never ends with uncovered in-scope survey objectives presented as a successful completed study.

**Architecture:** Add an explicit coverage readiness gate between fieldwork and finalization, make the replanner deterministic-first for missing/ambiguous required variables, and update the demo fixtures/UI/script so the story shows the agent redirecting toward complete objective coverage. The final state is either `ready_for_decision_use` with all in-scope fields covered, or `needs_targeted_followup` with a visible caveat and no success framing.

**Tech Stack:** Python 3, Pydantic 2, google-adk custom `BaseAgent` steps, FastAPI SSE, vanilla JS demo UI, Playwright E2E tests, pytest.

---

## Strategy Linkage

This plan supports the Methodic thesis: no reliable insights without good data capture. It directly protects the demo proof beats in `docs/spec.md`: required variable coverage, stop condition/coverage loop, and autonomous re-plan. A static survey can end with unanswered fields; Methodic must either pursue them or refuse to overclaim.

## File Structure

| File | Responsibility |
| --- | --- |
| `methodic/tools/coverage_checker.py` | Compute study-level variable state and finalization readiness. |
| `methodic/agents/coverage_gate_step.py` | New deterministic ADK step that blocks “complete” framing when required objectives are not covered. |
| `methodic/agents/replanner.py` | Choose `ADD_PARTICIPANT`, `REDIRECT_INTERVIEW`, or `STOP` from coverage readiness before falling back to LLM wording. |
| `methodic/agent.py` | Insert `coverage_gate_step` before `quality_reviewer` and keep fieldwork loop behavior consistent. |
| `methodic/prompts/interviewer_system.md` | Instruct interviewer to pursue the current coverage directive before broad questions. |
| `methodic/static/interactive.html` | Show “Ready for decision use” only when coverage gate passes; otherwise show targeted follow-up state. |
| `tests/test_coverage_checker.py` | Unit tests for readiness states and incomplete objectives. |
| `tests/test_agents.py` | Wiring test for the new coverage gate step. |
| `tests/e2e/fixtures/sse_coverage_replan_success.txt` | Deterministic video-path fixture: starts incomplete, replans, ends complete. |
| `tests/e2e/fixtures/sse_coverage_needs_followup.txt` | Deterministic fallback fixture: no reserve participant, ends with visible caveat. |
| `tests/e2e/test_interactive_scenarios.py` | E2E tests for successful coverage completion and non-overclaim fallback. |
| `docs/demo-script.md` | Update video narration so the ending proves coverage completion or honest refusal. |

## Coverage Policy

Required in-scope objectives are the 8 canonical fields unless the organizer explicitly disables a field before fieldwork starts. The demo should use all 8 fields.

Study finalization rules:

| State | Meaning | Final video label |
| --- | --- | --- |
| All required fields `covered_high_confidence` | Decision-ready data capture complete | `Ready for decision use` |
| Required fields include `covered_low_confidence` but no `missing`/`ambiguous` | Usable with caveats | `Covered with caveats` |
| Any required field is `missing` or `ambiguous` and a reserve participant exists | Must re-plan | `Targeted follow-up in progress` |
| Any required field is `missing` or `ambiguous` and no reserve participant exists | Do not overclaim | `Needs targeted follow-up` |

For the submission video, use the first state. Keep the fourth state implemented because it is the safety net that prevents dishonest completion.

---

### Task 1: Add Coverage Readiness Computation

**Files:**
- Modify: `methodic/tools/coverage_checker.py`
- Create/modify: `tests/test_coverage_checker.py`

- [ ] **Step 1: Write failing tests for readiness states**

Add these tests to `tests/test_coverage_checker.py`:

```python
from methodic.schemas import CANONICAL_FIELDS
from methodic.tools.coverage_checker import summarize_coverage_readiness


def test_readiness_blocks_missing_required_field():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}
    coverage["procurement_friction"] = "missing"

    result = summarize_coverage_readiness(
        coverage,
        required_fields=CANONICAL_FIELDS,
        reserve_participants=["P-005"],
    )

    assert result["ready_for_decision_use"] is False
    assert result["next_action"] == "ADD_PARTICIPANT"
    assert result["incomplete_fields"] == ["procurement_friction"]
    assert result["final_label"] == "Targeted follow-up in progress"


def test_readiness_all_high_confidence_is_decision_ready():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}

    result = summarize_coverage_readiness(
        coverage,
        required_fields=CANONICAL_FIELDS,
        reserve_participants=["P-005"],
    )

    assert result["ready_for_decision_use"] is True
    assert result["next_action"] == "STOP"
    assert result["incomplete_fields"] == []
    assert result["final_label"] == "Ready for decision use"


def test_readiness_low_confidence_is_covered_with_caveats():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}
    coverage["security_concern"] = "covered_low_confidence"

    result = summarize_coverage_readiness(
        coverage,
        required_fields=CANONICAL_FIELDS,
        reserve_participants=[],
    )

    assert result["ready_for_decision_use"] is False
    assert result["ready_with_caveats"] is True
    assert result["next_action"] == "STOP_WITH_CAVEATS"
    assert result["caveat_fields"] == ["security_concern"]
    assert result["final_label"] == "Covered with caveats"


def test_readiness_without_reserve_refuses_overclaim():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}
    coverage["competitor_pressure"] = "ambiguous"

    result = summarize_coverage_readiness(
        coverage,
        required_fields=CANONICAL_FIELDS,
        reserve_participants=[],
    )

    assert result["ready_for_decision_use"] is False
    assert result["next_action"] == "NEEDS_FOLLOWUP"
    assert result["incomplete_fields"] == ["competitor_pressure"]
    assert result["final_label"] == "Needs targeted follow-up"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_coverage_checker.py -v
```

Expected: FAIL with `ImportError` or `AttributeError` because `summarize_coverage_readiness` does not exist.

- [ ] **Step 3: Implement `summarize_coverage_readiness`**

Add this function to `methodic/tools/coverage_checker.py` below `check_coverage`:

```python
def summarize_coverage_readiness(
    coverage: dict[str, CoverageState],
    required_fields: list[str] | tuple[str, ...] | None = None,
    reserve_participants: list[str] | tuple[str, ...] | None = None,
) -> dict:
    """Return the finalization policy for study-level coverage."""
    required = list(required_fields or CANONICAL_FIELDS)
    reserves = list(reserve_participants or [])

    incomplete = [
        field for field in required
        if coverage.get(field, "missing") in ("missing", "ambiguous")
    ]
    caveats = [
        field for field in required
        if coverage.get(field) == "covered_low_confidence"
    ]

    if incomplete and reserves:
        return {
            "ready_for_decision_use": False,
            "ready_with_caveats": False,
            "next_action": "ADD_PARTICIPANT",
            "incomplete_fields": incomplete,
            "caveat_fields": caveats,
            "target_participant_id": reserves[0],
            "final_label": "Targeted follow-up in progress",
        }

    if incomplete:
        return {
            "ready_for_decision_use": False,
            "ready_with_caveats": False,
            "next_action": "NEEDS_FOLLOWUP",
            "incomplete_fields": incomplete,
            "caveat_fields": caveats,
            "target_participant_id": None,
            "final_label": "Needs targeted follow-up",
        }

    if caveats:
        return {
            "ready_for_decision_use": False,
            "ready_with_caveats": True,
            "next_action": "STOP_WITH_CAVEATS",
            "incomplete_fields": [],
            "caveat_fields": caveats,
            "target_participant_id": None,
            "final_label": "Covered with caveats",
        }

    return {
        "ready_for_decision_use": True,
        "ready_with_caveats": False,
        "next_action": "STOP",
        "incomplete_fields": [],
        "caveat_fields": [],
        "target_participant_id": None,
        "final_label": "Ready for decision use",
    }
```

- [ ] **Step 4: Update `check_coverage` to include readiness**

In `methodic/tools/coverage_checker.py`, replace the final `return` block with:

```python
    result = {
        "per_variable": best,
        "overall_coverage": high_count / len(CANONICAL_FIELDS) if CANONICAL_FIELDS else 0.0,
        "ambiguous_variables": [f for f, v in best.items() if v == "ambiguous"],
        "missing_variables": [f for f, v in best.items() if v == "missing"],
    }
    result["readiness"] = summarize_coverage_readiness(best)
    return result
```

- [ ] **Step 5: Run tests to verify pass**

Run:

```bash
python -m pytest tests/test_coverage_checker.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add methodic/tools/coverage_checker.py tests/test_coverage_checker.py
git commit -m "feat: add coverage readiness policy"
```

---

### Task 2: Add Finalization Coverage Gate

**Files:**
- Create: `methodic/agents/coverage_gate_step.py`
- Modify: `methodic/agent.py`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Write failing wiring test**

Add this test to `tests/test_agents.py`:

```python
def test_finalize_has_coverage_gate_before_quality():
    from methodic.agent import finalize

    names = [a.name for a in finalize.sub_agents]
    assert "coverage_gate" in names
    assert names.index("coverage_gate") < names.index("quality_reviewer")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_agents.py::test_finalize_has_coverage_gate_before_quality -v
```

Expected: FAIL because `coverage_gate` is not in `finalize.sub_agents`.

- [ ] **Step 3: Create the coverage gate step**

Create `methodic/agents/coverage_gate_step.py`:

```python
"""Coverage gate step - prevents successful finalization with missing objectives."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from methodic.schemas import CANONICAL_FIELDS
from methodic.tools.coverage_checker import summarize_coverage_readiness


class CoverageGateStep(BaseAgent):
    """Writes finalization readiness into session state."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        coverage_state = state.get("coverage_state", {})
        per_variable = coverage_state.get("per_variable", coverage_state)
        reserve_participants = state.get("reserve_participants", [])
        required_fields = state.get("required_fields", CANONICAL_FIELDS)

        readiness = summarize_coverage_readiness(
            per_variable,
            required_fields=required_fields,
            reserve_participants=reserve_participants,
        )

        state["coverage_readiness"] = readiness
        yield Event(
            author=self.name,
            content=None,
            actions=EventActions(state_delta={"coverage_readiness": readiness}),
        )


coverage_gate_step = CoverageGateStep(name="coverage_gate")
```

- [ ] **Step 4: Insert gate in finalize sequence**

In `methodic/agent.py`, import and insert the gate before `quality_reviewer`:

```python
from methodic.agents.coverage_gate_step import coverage_gate_step
```

Then define `finalize` with this order:

```python
finalize = SequentialAgent(
    name="finalize",
    sub_agents=[coverage_gate_step, quality_agent, bigquery_export_step, completion_responder_agent],
)
```

Keep the exact existing variable names for `quality_agent`, `bigquery_export_step`, and `completion_responder_agent` from the file.

- [ ] **Step 5: Run wiring tests**

Run:

```bash
python -m pytest tests/test_agents.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add methodic/agents/coverage_gate_step.py methodic/agent.py tests/test_agents.py
git commit -m "feat: gate finalization on objective coverage"
```

---

### Task 3: Make Replanner Deterministic-First

**Files:**
- Modify: `methodic/agents/replanner.py`
- Create/modify: `tests/test_replanner.py`

- [ ] **Step 1: Write tests for ADD_PARTICIPANT and STOP**

Create or extend `tests/test_replanner.py`:

```python
from methodic.agents.replanner import decide_next_fieldwork_action
from methodic.schemas import CANONICAL_FIELDS


def test_replanner_adds_reserve_when_required_field_missing():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}
    coverage["procurement_friction"] = "missing"

    decision = decide_next_fieldwork_action(
        per_variable_coverage=coverage,
        reserve_participants=["P-005"],
    )

    assert decision == {
        "decision": "ADD_PARTICIPANT",
        "reason": "Required objectives remain incomplete: procurement_friction",
        "add_participant_id": "P-005",
        "target_variables": ["procurement_friction"],
    }


def test_replanner_stops_when_all_required_fields_high_confidence():
    coverage = {field: "covered_high_confidence" for field in CANONICAL_FIELDS}

    decision = decide_next_fieldwork_action(
        per_variable_coverage=coverage,
        reserve_participants=["P-005"],
    )

    assert decision["decision"] == "STOP"
    assert decision["target_variables"] == []
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_replanner.py -v
```

Expected: FAIL because `decide_next_fieldwork_action` does not exist.

- [ ] **Step 3: Implement deterministic decision helper**

Add this helper above `class ReplannerStep` in `methodic/agents/replanner.py`:

```python
def decide_next_fieldwork_action(
    per_variable_coverage: dict,
    reserve_participants: list[str] | tuple[str, ...] | None = None,
) -> dict:
    readiness = summarize_coverage_readiness(
        per_variable_coverage,
        reserve_participants=reserve_participants or [],
    )
    incomplete = readiness["incomplete_fields"]

    if readiness["next_action"] == "ADD_PARTICIPANT":
        return {
            "decision": "ADD_PARTICIPANT",
            "reason": "Required objectives remain incomplete: " + ", ".join(incomplete),
            "add_participant_id": readiness["target_participant_id"],
            "target_variables": incomplete,
        }

    if readiness["next_action"] == "NEEDS_FOLLOWUP":
        return {
            "decision": "NEEDS_FOLLOWUP",
            "reason": "Required objectives remain incomplete and no reserve participant is available: " + ", ".join(incomplete),
            "add_participant_id": None,
            "target_variables": incomplete,
        }

    if readiness["next_action"] == "STOP_WITH_CAVEATS":
        return {
            "decision": "STOP_WITH_CAVEATS",
            "reason": "All required objectives are covered, but some remain low confidence: " + ", ".join(readiness["caveat_fields"]),
            "add_participant_id": None,
            "target_variables": readiness["caveat_fields"],
        }

    return {
        "decision": "STOP",
        "reason": "All required objectives are covered at high confidence.",
        "add_participant_id": None,
        "target_variables": [],
    }
```

Also add this import:

```python
from methodic.tools.coverage_checker import check_coverage, summarize_coverage_readiness
```

- [ ] **Step 4: Use helper before LLM fallback**

Inside `ReplannerStep._run_async_impl`, after `coverage = check_coverage(responses)`, add:

```python
        per_variable = coverage.get("per_variable", coverage)
        reserve_participants = state.get("reserve_participants", ["P-005"])
        decision = decide_next_fieldwork_action(
            per_variable_coverage=per_variable,
            reserve_participants=reserve_participants,
        )

        if decision["decision"] in {"ADD_PARTICIPANT", "NEEDS_FOLLOWUP", "STOP_WITH_CAVEATS", "STOP"}:
            state["replan_decision"] = decision
            if decision["decision"] in {"STOP", "STOP_WITH_CAVEATS", "NEEDS_FOLLOWUP"}:
                yield Event(author=self.name, content=None, actions=EventActions(state_delta={"replan_decision": decision}, escalate=True))
                return

            new_pid = decision["add_participant_id"]
            state["active_participant_id"] = new_pid
            state["turn_count"] = 0
            state["coverage_directive"] = {
                "target_variables": decision["target_variables"],
                "reason": decision["reason"],
            }
            yield Event(author=self.name, content=None, actions=EventActions(state_delta={"replan_decision": decision, "coverage_directive": state["coverage_directive"]}))
            return
```

Remove the old path that lets the LLM decide `STOP` when required fields are still incomplete. Keep the existing LLM prompt only if it is used to generate explanatory wording after deterministic policy has already selected the action.

- [ ] **Step 5: Run replanner tests**

Run:

```bash
python -m pytest tests/test_replanner.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add methodic/agents/replanner.py tests/test_replanner.py
git commit -m "feat: make replanner pursue incomplete objectives"
```

---

### Task 4: Teach Interviewer to Follow Coverage Directive

**Files:**
- Modify: `methodic/prompts/interviewer_system.md`
- Modify: `tests/test_agents.py`

- [ ] **Step 1: Add prompt regression test**

Add to `tests/test_agents.py`:

```python
def test_interviewer_prompt_mentions_coverage_directive():
    from pathlib import Path

    prompt = (Path("methodic/prompts/interviewer_system.md")).read_text()
    assert "coverage_directive" in prompt
    assert "target_variables" in prompt
    assert "Do not wrap up while required target variables remain missing or ambiguous" in prompt
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_agents.py::test_interviewer_prompt_mentions_coverage_directive -v
```

Expected: FAIL because the prompt does not mention `coverage_directive`.

- [ ] **Step 3: Update interviewer prompt**

In `methodic/prompts/interviewer_system.md`, add this section before `## Technique`:

```markdown
## Coverage Directive

The session state may include `coverage_directive` with:
- `target_variables`: required fields that are still missing or ambiguous
- `reason`: why the study cannot finalize yet

When `coverage_directive.target_variables` is present, prioritize those variables before asking broad exploratory questions. Ask one targeted, neutral follow-up tied to the first target variable. Do not wrap up while required target variables remain missing or ambiguous unless the participant cannot answer after one clear rephrase.
```

- [ ] **Step 4: Run prompt test**

Run:

```bash
python -m pytest tests/test_agents.py::test_interviewer_prompt_mentions_coverage_directive -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add methodic/prompts/interviewer_system.md tests/test_agents.py
git commit -m "feat: direct interviewer toward uncovered objectives"
```

---

### Task 5: Update Demo SSE Fixtures and UI Final Labels

**Files:**
- Create: `tests/e2e/fixtures/sse_coverage_replan_success.txt`
- Create: `tests/e2e/fixtures/sse_coverage_needs_followup.txt`
- Modify: `tests/e2e/test_interactive_scenarios.py`
- Modify: `methodic/static/interactive.html`

- [ ] **Step 1: Create replan-success fixture**

Create `tests/e2e/fixtures/sse_coverage_replan_success.txt`:

```text
data: {"author": "organizer", "text": "Study brief parsed. Required variables: 8 canonical win-loss objectives.", "state_delta": {}}

data: {"author": "methodology", "text": "Methodology review complete. Verdict: APPROVE. Use reserve participant if required objectives remain incomplete.", "state_delta": {}}

data: {"author": "question_design", "text": "Question pool generated for all 8 required objectives.", "state_delta": {}}

data: {"author": "interviewer", "text": "Could you walk me through why the evaluation did not move forward?", "state_delta": {}}

data: {"author": "participant_sim", "text": "It looked too expensive and the ROI case was not clear.", "state_delta": {"participant_coverage": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "missing", "budget_timing": "missing", "procurement_friction": "missing", "security_concern": "missing", "competitor_pressure": "missing", "aha_moment_reached": "missing"}}}

data: {"author": "interviewer", "text": "What happened after finance reviewed the business case?", "state_delta": {}}

data: {"author": "participant_sim", "text": "Finance paused it because the budget window had closed, and procurement had not finished the vendor review.", "state_delta": {"participant_coverage": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "ambiguous", "security_concern": "missing", "competitor_pressure": "missing", "aha_moment_reached": "missing"}}}

data: {"author": "coverage_step", "text": "", "state_delta": {"coverage_state": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "ambiguous", "security_concern": "missing", "competitor_pressure": "missing", "aha_moment_reached": "missing"}}}

data: {"author": "replanner", "text": "Required objectives remain incomplete: procurement_friction, security_concern, competitor_pressure, aha_moment_reached. Adding reserve participant P-005 for a targeted follow-up.", "state_delta": {"replan_decision": {"decision": "ADD_PARTICIPANT", "add_participant_id": "P-005", "target_variables": ["procurement_friction", "security_concern", "competitor_pressure", "aha_moment_reached"]}, "coverage_directive": {"target_variables": ["procurement_friction", "security_concern", "competitor_pressure", "aha_moment_reached"], "reason": "Required objectives remain incomplete."}}}

data: {"author": "interviewer", "text": "For the follow-up, what specifically blocked procurement, and did security or competitor evaluation affect the decision?", "state_delta": {}}

data: {"author": "participant_sim", "text": "Procurement required a current SOC 2 package and security questionnaire. We compared CompetitorX, but they did not win; the bigger issue was that our team never reached the reporting workflow that would have shown the value.", "state_delta": {"participant_coverage": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "covered_high_confidence", "security_concern": "covered_high_confidence", "competitor_pressure": "covered_high_confidence", "aha_moment_reached": "covered_high_confidence"}}}

data: {"author": "coverage_step", "text": "", "state_delta": {"coverage_state": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "covered_high_confidence", "security_concern": "covered_high_confidence", "competitor_pressure": "covered_high_confidence", "aha_moment_reached": "covered_high_confidence"}}}

data: {"author": "coverage_gate", "text": "", "state_delta": {"coverage_readiness": {"ready_for_decision_use": true, "ready_with_caveats": false, "next_action": "STOP", "incomplete_fields": [], "caveat_fields": [], "target_participant_id": null, "final_label": "Ready for decision use"}}}

data: {"author": "quality_reviewer", "text": "Quality review complete. All 8 in-scope objectives are covered at high confidence with evidence links.", "state_delta": {}}

data: {"author": "completion_responder", "text": "Study complete. All 8 in-scope objectives are covered at high confidence. Ready for decision use.", "state_delta": {}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 2: Create needs-followup fixture**

Create `tests/e2e/fixtures/sse_coverage_needs_followup.txt`:

```text
data: {"author": "coverage_step", "text": "", "state_delta": {"coverage_state": {"primary_loss_reason": "covered_high_confidence", "roi_clarity": "covered_high_confidence", "secondary_loss_reason": "covered_high_confidence", "budget_timing": "covered_high_confidence", "procurement_friction": "ambiguous", "security_concern": "missing", "competitor_pressure": "covered_high_confidence", "aha_moment_reached": "covered_high_confidence"}}}

data: {"author": "coverage_gate", "text": "", "state_delta": {"coverage_readiness": {"ready_for_decision_use": false, "ready_with_caveats": false, "next_action": "NEEDS_FOLLOWUP", "incomplete_fields": ["procurement_friction", "security_concern"], "caveat_fields": [], "target_participant_id": null, "final_label": "Needs targeted follow-up"}}}

data: {"author": "completion_responder", "text": "Study not finalized. Procurement friction and security concern remain unresolved; Methodic recommends one targeted economic-buyer follow-up before decision use.", "state_delta": {}}

data: {"author": "system", "text": "Stream complete.", "state_delta": {}}
```

- [ ] **Step 3: Add E2E tests**

Add to `tests/e2e/test_interactive_scenarios.py`:

```python
def test_replan_success_finishes_with_all_fields_high(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_coverage_replan_success.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    results = page.locator("#results-overlay")
    expect(results).to_contain_text("Ready for decision use")
    high_badges = page.locator("#results-overlay .coverage-badge.high")
    assert high_badges.count() == 8
    expect(page.locator(".agentic-card.replanner, .agentic-card.autonomy").first).to_contain_text("Adding reserve participant")


def test_needs_followup_does_not_claim_ready_for_decision_use(page: Page, demo_server: str):
    _route_and_start(page, demo_server, "sse_coverage_needs_followup.txt")
    expect(page.locator("#status-badge")).to_have_text("complete", timeout=15_000)

    results = page.locator("#results-overlay")
    expect(results).to_contain_text("Needs targeted follow-up")
    expect(results).not_to_contain_text("Ready for decision use")
```

- [ ] **Step 4: Run tests to verify UI failure**

Run:

```bash
python -m pytest tests/e2e/test_interactive_scenarios.py::test_replan_success_finishes_with_all_fields_high tests/e2e/test_interactive_scenarios.py::test_needs_followup_does_not_claim_ready_for_decision_use -v
```

Expected: FAIL if the UI does not surface `coverage_readiness.final_label` yet.

- [ ] **Step 5: Surface readiness label in results UI**

In `methodic/static/interactive.html`, update the SSE handler so when `state_delta.coverage_readiness` exists, it stores it in UI state:

```javascript
if (delta.coverage_readiness) {
  state.coverageReadiness = delta.coverage_readiness;
}
```

In the results rendering function, compute:

```javascript
var readinessLabel = state.coverageReadiness && state.coverageReadiness.final_label
  ? state.coverageReadiness.final_label
  : 'Coverage review complete';
```

Render `readinessLabel` in the results heading or summary line. If `state.coverageReadiness.ready_for_decision_use === false`, do not render “Ready for decision use” anywhere else.

- [ ] **Step 6: Run E2E tests**

Run:

```bash
python -m pytest tests/e2e/test_interactive_scenarios.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add methodic/static/interactive.html tests/e2e/fixtures/sse_coverage_replan_success.txt tests/e2e/fixtures/sse_coverage_needs_followup.txt tests/e2e/test_interactive_scenarios.py
git commit -m "feat: show coverage-complete demo ending"
```

---

### Task 6: Update Demo Script and Recording Gate

**Files:**
- Modify: `docs/demo-script.md`
- Modify: `docs/evidence/live-run-2026-05-14.md` or create a new evidence file for the next run.

- [ ] **Step 1: Update demo script ending**

In `docs/demo-script.md`, replace the ending coverage language with:

```markdown
**On screen:** The coverage dashboard briefly shows remaining gaps after the first pass. Methodic does not finalize. The replanner adds a targeted reserve participant and sends the interviewer back with a narrow coverage directive.

**Voiceover:** "This is the core difference from a survey. Methodic can see that the data is not ready yet. It does not pretend the study is complete; it redirects fieldwork toward the missing objectives."

**On screen:** The final coverage gate flips to `Ready for decision use`: 8 of 8 in-scope objectives covered at high confidence, evidence linked, and BigQuery export complete.

**Voiceover:** "The final dataset is decision-ready because every in-scope objective was either resolved or explicitly blocked. In this demo, all eight are resolved."
```

- [ ] **Step 2: Add recording acceptance checklist**

Append this checklist to `docs/demo-script.md`:

```markdown
## Recording Acceptance Gate

Before recording the final video:

- [ ] The UI shows at least one mid-run missing/ambiguous coverage state.
- [ ] The replanner visibly reacts to the gap.
- [ ] The final screen says `Ready for decision use`.
- [ ] The final screen shows 8/8 in-scope objectives covered.
- [ ] The final narration does not say "complete" while any in-scope objective is missing or ambiguous.
- [ ] If a live run cannot reach 8/8, record the honest fallback path: `Needs targeted follow-up`, not a completed-study ending.
```

- [ ] **Step 3: Run documentation grep check**

Run:

```bash
rg -n "Coverage sufficient|6/8|No recontact required|No ambiguity resolution needed" docs methodic tests
```

Expected: any remaining matches are in historical evidence or tests only. No active demo script should claim success at `6/8`.

- [ ] **Step 4: Commit**

```bash
git add docs/demo-script.md docs/evidence
git commit -m "docs: require coverage-complete demo ending"
```

---

### Task 7: Verify Live Path Before Recording

**Files:**
- Create: `docs/evidence/coverage-complete-live-run-YYYY-MM-DD.md`

- [ ] **Step 1: Run local unit and E2E suite**

Run:

```bash
python -m pytest tests/test_coverage_checker.py tests/test_replanner.py tests/test_agents.py -v
python -m pytest tests/e2e/test_interactive_scenarios.py -v
```

Expected: PASS.

- [ ] **Step 2: Run live or deployed SSE smoke**

Run the existing smoke path used for the current Cloud Run evidence. Capture the SSE output and confirm it includes:

```text
"author": "coverage_gate"
"final_label": "Ready for decision use"
"ready_for_decision_use": true
```

If the live model run ends with `NEEDS_FOLLOWUP`, do not record it as a successful final video. Either tune the prompt/fixture path until the live run reaches 8/8, or record the fallback honestly as a data-quality refusal.

- [ ] **Step 3: Write evidence file**

Create `docs/evidence/coverage-complete-live-run-YYYY-MM-DD.md` with:

```markdown
# Coverage-Complete Live Run — YYYY-MM-DD

## Endpoint

`<local or Cloud Run URL>`

## Verification

- Coverage gate emitted: yes
- Final label: `Ready for decision use`
- In-scope objectives covered: 8/8
- Missing objectives at final screen: 0
- Ambiguous objectives at final screen: 0
- BigQuery export: `<dry_run true/false, rows_written>`

## Evidence Snippet

```json
{
  "coverage_readiness": {
    "ready_for_decision_use": true,
    "final_label": "Ready for decision use",
    "incomplete_fields": []
  }
}
```
```

- [ ] **Step 4: Commit**

```bash
git add docs/evidence/coverage-complete-live-run-*.md
git commit -m "docs: capture coverage-complete live run evidence"
```

---

## Self-Review

- Spec coverage: the plan covers the finalization gate, deterministic re-plan, interviewer redirection, UI proof, demo script, and live verification.
- Placeholder scan: no `TBD`, `TODO`, or “implement later” placeholders remain.
- Type consistency: `coverage_readiness`, `ready_for_decision_use`, `next_action`, `incomplete_fields`, `caveat_fields`, and `final_label` are used consistently across backend, SSE, UI, and tests.
- Scope check: this is a focused demo-confidence fix, not a broad survey-platform expansion.
