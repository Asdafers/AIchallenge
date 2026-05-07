# Methodic ADK Agent Implementation Plan (Rev 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real multi-agent B2B win-loss research system on Google ADK that replaces the current fixture-replay demo with live Gemini-powered conversations, MCP tool access, A2A interoperability, and BigQuery export.

**Architecture:** SequentialAgent root orchestrates study_planner -> fieldwork_loop (LoopAgent with custom step agents) -> finalize. Deterministic steps (extraction, coverage checking, turn checking, BigQuery export) are implemented as custom `BaseAgent` subclasses — not FunctionTools in the sub_agents list, because ADK workflow agents only accept agent instances as sub-agents. LlmAgents handle reasoning; custom agents handle deterministic logic and loop exit via `ctx.actions.escalate = True`.

**Tech Stack:** google-adk, google-genai (GA SDK), google-cloud-bigquery, pydantic 2, fastapi, uvicorn, mcp 1.23.3, gemini-3.1-pro-preview

**A2A Scope Decision:** A2A-compatible prototype. We serve an A2A 1.0-shaped Agent Card at `/.well-known/agent-card.json` and label the endpoint as "A2A-pattern". We do NOT use `to_a2a()` — integrating it with `get_fast_api_app()` is unproven and a schedule risk for a 32-day hackathon. If time permits, we upgrade to real `to_a2a()` in the final week.

**State Contract:** Agents communicate through `ctx.session.state` using these explicit keys:

| Key | Type | Written By | Read By |
|-----|------|-----------|---------|
| `study_brief` | dict | organizer | methodology, question_design |
| `methodology_review` | dict | methodology | question_design |
| `question_pool` | list[dict] | question_design | interviewer |
| `active_participant_id` | str | session_runner | interviewer, sim, extractor_step |
| `participants_to_run` | list[str] | organizer/replanner | session_runner |
| `transcripts_by_participant` | dict[str, list] | interviewer, sim | extractor_step |
| `latest_turn_pair` | dict | interviewer, sim | turn_checker_step |
| `participant_response_by_id` | dict[str, dict] | extractor_step | coverage_step, quality, export |
| `coverage_state` | dict | coverage_step | replanner |
| `replan_decision` | dict | replanner | fieldwork_loop (escalate) |
| `quality_report` | dict | quality_reviewer | completion_responder |
| `export_result` | dict | bigquery_export_step | completion_responder |
| `tool_events` | list[dict] | interviewer (MCP calls) | demo UI |

---

## Revision Log (from Gemini + Codex reviews)

| Finding | Source | Fix |
|---------|--------|-----|
| FunctionTools can't be workflow sub-agents | Codex BLOCKER | New Task 15: custom BaseAgent wrappers |
| Missing turn_checker | Both BLOCKER | Added to Task 15 as turn_checker_step |
| Orphaned tools not wired into graph | Both BLOCKER | Task 16 rewired with wrapper agents |
| /api/demo/run never invokes agent | Codex BLOCKER | New Task 17: demo_runner.py |
| Replanner lacks check_coverage tool | Both MAJOR | Task 14 revised |
| State flow under-specified | Codex MAJOR | State contract table above |
| Legacy google.generativeai SDK | Codex MAJOR | Task 1 + Task 6 use google-genai |
| A2A card wrong path/shape | Codex MAJOR | A2A scope decision above, Task 18 fixed |
| No error handling for extraction | Codex MAJOR | Task 6 revised with recovery matrix |
| MCP tests hand-roll framing | Codex MAJOR | Task 3 uses mcp.client.stdio |
| Interviewer/sim missing output_key | Codex MAJOR | Task 13 revised |
| BigQuery no table setup | Codex MAJOR | Task 7 revised with ensure_table |
| Dockerfile hardcodes port | Codex MINOR | Task 20 uses $PORT |

## Revision 3 Log (Post Agent Runtime Spike — 2026-05-06)

| Finding | Source | Fix |
|---------|--------|-----|
| Agent Runtime (agent_engine) deploy fails code 13 | Spike Gate 1 FAIL | Cloud Run is core deployment target |
| ADK `api_server` provides standard REST endpoints | Spike proof | Task 17 revised: use ADK api_server, add demo/A2A routes on top |
| Cloud Build fails with opaque errors | Spike evidence | Task 19 revised: local Docker build + push to Artifact Registry |
| MCP stdio needs Node.js in container | Architecture req | Task 19 revised: multi-stage build with node:20-slim |
| `adk api_server` already handles sessions/SSE | Spike proof | Task 17 simplified: no custom session management needed |
| Org policy blocks allUsers on Cloud Run | GCP org constraint | Task 21 revised: test with authenticated curl |

---

## File Map

| File | Responsibility |
|------|---------------|
| `methodic/__init__.py` | Package marker, exports `MODEL` constant |
| `methodic/agent.py` | `root_agent` definition (ADK entry point) |
| `methodic/schemas.py` | Pydantic models mirroring JSON schemas |
| `methodic/agents/__init__.py` | Agent subpackage marker |
| `methodic/agents/organizer.py` | LlmAgent - request intake + clarification |
| `methodic/agents/methodology.py` | LlmAgent - pushback on bad methodology |
| `methodic/agents/question_design.py` | LlmAgent - maps questions to variables |
| `methodic/agents/participant.py` | LlmAgent - conducts interviews |
| `methodic/agents/participant_sim.py` | LlmAgent - simulates participant responses |
| `methodic/agents/quality.py` | LlmAgent - contradiction/theme review |
| `methodic/agents/replanner.py` | LlmAgent - decides if more sessions needed |
| `methodic/agents/extractor_step.py` | **Custom BaseAgent** - Gemini structured extraction |
| `methodic/agents/turn_checker_step.py` | **Custom BaseAgent** - evaluates coverage, escalates loop exit |
| `methodic/agents/coverage_step.py` | **Custom BaseAgent** - computes study-wide coverage |
| `methodic/agents/bigquery_export_step.py` | **Custom BaseAgent** - writes rows to BigQuery |
| `methodic/tools/__init__.py` | Tools subpackage marker |
| `methodic/tools/deal_context.py` | McpToolset wrapping wp6_mcp_server.py |
| `methodic/tools/quality_scorer.py` | Pure function - deterministic coverage scoring |
| `methodic/tools/bigquery_export.py` | Pure function - flattens + writes rows to BigQuery |
| `methodic/tools/coverage_checker.py` | Pure function - computes variable coverage |
| `methodic/tools/extractor.py` | Pure function - calls Gemini for structured extraction |
| `methodic/prompts/interviewer_system.md` | System prompt for interviewer agent |
| `methodic/prompts/methodology_system.md` | System prompt for methodology agent |
| `methodic/prompts/sim_participant_system.md` | System prompt for simulated participant |
| `methodic/demo_runner.py` | **NEW** - async demo orchestrator that runs root_agent |
| `methodic/server.py` | Custom FastAPI overlay (demo API + A2A card) |
| `methodic/static/demo.html` | Split-screen demo overlay page |
| `scripts/wp6_mcp_server.py` | Extended with `lookup_trial_telemetry` tool |
| `tests/__init__.py` | Test package marker |
| `tests/test_schemas.py` | Pydantic model validation tests |
| `tests/test_tools.py` | Pure function unit tests |
| `tests/test_mcp_extended.py` | MCP server extension tests |
| `tests/test_agents.py` | Agent wiring + output_key tests |
| `tests/test_steps.py` | **NEW** - custom BaseAgent step tests |
| `tests/test_integration.py` | End-to-end integration smoke test |
| `requirements.txt` | Production dependencies |
| `requirements-dev.txt` | Dev/test dependencies |
| `Dockerfile` | Cloud Run deployment container |

---

### Task 1: Project Scaffold & Dependencies

**Files:**
- Create: `methodic/__init__.py`
- Create: `methodic/agents/__init__.py`
- Create: `methodic/tools/__init__.py`
- Create: `methodic/prompts/` (directory)
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p methodic/agents methodic/tools methodic/prompts methodic/static tests
```

- [ ] **Step 2: Write `requirements.txt`**

Create `requirements.txt`:

```
google-adk>=1.0.0
google-genai>=1.0.0
google-cloud-bigquery>=3.20.0
pydantic>=2.0
uvicorn>=0.30.0
fastapi>=0.110.0
jsonschema>=4.0
mcp>=1.23.3
```

- [ ] **Step 3: Write `requirements-dev.txt`**

Create `requirements-dev.txt`:

```
-r requirements.txt
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 4: Write `methodic/__init__.py`**

```python
"""Methodic ADK Agent - B2B win-loss research multi-agent system."""

MODEL = "gemini-3.1-pro-preview"
MODEL_FAST = "gemini-3.1-flash-lite-preview"
MODEL_STABLE_FALLBACK = "gemini-2.5-flash"
```

- [ ] **Step 5: Write package markers**

`methodic/agents/__init__.py`:
```python
"""Agent definitions for Methodic."""
```

`methodic/tools/__init__.py`:
```python
"""Pure functions and McpToolset integrations for Methodic."""
```

`tests/__init__.py`:
```python
"""Methodic test suite."""
```

- [ ] **Step 6: Install dependencies**

Run: `pip install -r requirements-dev.txt`
Expected: all packages install successfully

- [ ] **Step 7: Verify ADK and genai are importable**

Run:
```bash
python3 -c "from google.adk.agents import Agent; print('ADK OK')"
python3 -c "from google import genai; print('genai OK')"
```
Expected: `ADK OK` then `genai OK`

- [ ] **Step 8: Commit**

```bash
git add methodic/ requirements.txt requirements-dev.txt tests/__init__.py
git commit -m "feat(methodic): scaffold ADK agent package with dependencies"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `methodic/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemas.py`:

```python
"""Tests for Pydantic schema models."""

import pytest
from methodic.schemas import (
    ParticipantResponse,
    StructuredFields,
    QualityMetrics,
    EvidenceItem,
    GuardrailEvent,
    GuardrailTrigger,
    CoverageState,
)


def test_structured_fields_valid():
    sf = StructuredFields(
        primary_loss_reason="unclear_roi",
        secondary_loss_reason="budget_timing",
        roi_clarity="unclear",
        budget_timing="out_of_cycle",
        procurement_friction="none",
        security_concern="none",
        competitor_pressure="none",
        aha_moment_reached="no",
    )
    assert sf.primary_loss_reason == "unclear_roi"


def test_structured_fields_invalid_enum():
    with pytest.raises(Exception):
        StructuredFields(
            primary_loss_reason="invalid_value",
            secondary_loss_reason=None,
            roi_clarity="clear",
            budget_timing="in_cycle",
            procurement_friction="none",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="yes",
        )


def test_participant_response_minimal():
    resp = ParticipantResponse(
        participant_id="P-001",
        study_id="STUDY-001",
        segment="lost_deal_economic_buyer",
        persona_summary="VP Finance",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi",
            secondary_loss_reason=None,
            roi_clarity="unclear",
            budget_timing="out_of_cycle",
            procurement_friction="none",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.9, "roi_clarity": 0.85},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(
            variable_coverage=0.75,
            ambiguity_resolved=True,
            evidence_linked=True,
            requires_recontact=False,
        ),
        evidence=[
            EvidenceItem(
                field="primary_loss_reason",
                quote="We could never prove the ROI internally",
                transcript_turn_id="turn-003",
                context_used=["crm_notes"],
            )
        ],
        unresolved_ambiguities=[],
    )
    assert resp.participant_id == "P-001"
    assert resp.quality.variable_coverage == 0.75


def test_coverage_state_enum_validation():
    with pytest.raises(Exception):
        ParticipantResponse(
            participant_id="P-001",
            study_id="STUDY-001",
            segment="lost_deal",
            persona_summary="Test",
            conversation_status="complete",
            structured_fields=StructuredFields(
                primary_loss_reason="unclear_roi",
                secondary_loss_reason=None,
                roi_clarity="clear",
                budget_timing="in_cycle",
                procurement_friction="none",
                security_concern="none",
                competitor_pressure="none",
                aha_moment_reached="yes",
            ),
            field_confidence={},
            coverage_state={"primary_loss_reason": "invalid_state"},
            quality=QualityMetrics(
                variable_coverage=1.0,
                ambiguity_resolved=True,
                evidence_linked=True,
                requires_recontact=False,
            ),
            evidence=[],
            unresolved_ambiguities=[],
        )


def test_guardrail_event():
    event = GuardrailEvent(
        event_id="EVT-001",
        study_id="STUDY-001",
        participant_id="P-002",
        event_type="participant_vague_answer",
        trigger=GuardrailTrigger(
            transcript_turn_id="turn-005",
            trigger_text="It was complicated",
        ),
        action_taken="clarifying_followup",
        measurement_intent_preserved=True,
        variable_affected="procurement_friction",
        timestamp="2026-05-15T10:30:00Z",
    )
    assert event.event_type == "participant_vague_answer"
    assert event.action_taken == "clarifying_followup"


def test_field_confidence_bounds():
    with pytest.raises(Exception):
        ParticipantResponse(
            participant_id="P-001",
            study_id="STUDY-001",
            segment="lost_deal",
            persona_summary="Test",
            conversation_status="complete",
            structured_fields=StructuredFields(
                primary_loss_reason="unclear_roi",
                secondary_loss_reason=None,
                roi_clarity="clear",
                budget_timing="in_cycle",
                procurement_friction="none",
                security_concern="none",
                competitor_pressure="none",
                aha_moment_reached="yes",
            ),
            field_confidence={"primary_loss_reason": 1.5},
            coverage_state={},
            quality=QualityMetrics(
                variable_coverage=1.0,
                ambiguity_resolved=True,
                evidence_linked=True,
                requires_recontact=False,
            ),
            evidence=[],
            unresolved_ambiguities=[],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_schemas.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'methodic.schemas'`

- [ ] **Step 3: Write `methodic/schemas.py`**

```python
"""Pydantic models mirroring canonical JSON schemas.

Source of truth: docs/schema/participant-response.schema.json
                 docs/schema/guardrail-event.schema.json
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


PrimaryLossReason = Literal[
    "unclear_roi", "budget_timing", "procurement_friction",
    "security_concern", "competitor_pressure", "missing_feature",
    "economic_buyer_gap", "other", "unknown",
]

RoiClarity = Literal["clear", "partially_clear", "unclear", "unknown"]
BudgetTiming = Literal["in_cycle", "out_of_cycle", "unknown"]
FrictionLevel = Literal["none", "low", "medium", "high", "unknown"]
CompetitorPressure = Literal["none", "named_competitor", "unknown"]
AhaMoment = Literal["yes", "no", "unknown"]
ConversationStatus = Literal["complete", "partial", "excluded", "static_form"]

CoverageState = Literal[
    "missing", "ambiguous", "covered_low_confidence", "covered_high_confidence",
]

CANONICAL_FIELDS = [
    "primary_loss_reason", "secondary_loss_reason", "roi_clarity",
    "budget_timing", "procurement_friction", "security_concern",
    "competitor_pressure", "aha_moment_reached",
]

CanonicalField = Literal[
    "primary_loss_reason", "secondary_loss_reason", "roi_clarity",
    "budget_timing", "procurement_friction", "security_concern",
    "competitor_pressure", "aha_moment_reached",
]


class StructuredFields(BaseModel):
    primary_loss_reason: PrimaryLossReason
    secondary_loss_reason: str | None
    roi_clarity: RoiClarity
    budget_timing: BudgetTiming
    procurement_friction: FrictionLevel
    security_concern: FrictionLevel
    competitor_pressure: CompetitorPressure
    aha_moment_reached: AhaMoment


class QualityMetrics(BaseModel):
    variable_coverage: float = Field(ge=0.0, le=1.0)
    ambiguity_resolved: bool
    evidence_linked: bool
    requires_recontact: bool


class EvidenceItem(BaseModel):
    field: CanonicalField
    quote: str
    transcript_turn_id: str = Field(min_length=1)
    context_used: list[str]


class ParticipantResponse(BaseModel):
    participant_id: str = Field(min_length=1)
    study_id: str = Field(min_length=1)
    segment: str = Field(min_length=1)
    persona_summary: str
    conversation_status: ConversationStatus
    structured_fields: StructuredFields
    field_confidence: dict[CanonicalField, float] = Field(default_factory=dict)
    coverage_state: dict[CanonicalField, CoverageState] = Field(default_factory=dict)
    quality: QualityMetrics
    evidence: list[EvidenceItem]
    unresolved_ambiguities: list[CanonicalField]


GuardrailEventType = Literal[
    "participant_misunderstanding", "participant_contradiction",
    "participant_frustration", "participant_vague_answer",
]

GuardrailAction = Literal[
    "rephrase_once", "clarifying_followup", "mark_ambiguous", "graceful_end",
]


class GuardrailTrigger(BaseModel):
    transcript_turn_id: str = Field(min_length=1)
    trigger_text: str


class GuardrailEvent(BaseModel):
    event_id: str = Field(min_length=1)
    study_id: str = Field(min_length=1)
    participant_id: str = Field(min_length=1)
    event_type: GuardrailEventType
    trigger: GuardrailTrigger
    action_taken: GuardrailAction
    measurement_intent_preserved: bool
    variable_affected: CanonicalField | None
    timestamp: str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_schemas.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/schemas.py tests/test_schemas.py
git commit -m "feat(methodic): add Pydantic schema models with validation tests"
```

---

### Task 3: Extend MCP Server with `lookup_trial_telemetry`

**Files:**
- Modify: `scripts/wp6_mcp_server.py`
- Create: `tests/test_mcp_extended.py`
- Create: `fixtures/telemetry/P-002.json`
- Create: `fixtures/telemetry/P-005.json`

- [ ] **Step 1: Write the failing test (using mcp client, not hand-rolled framing)**

Create `tests/test_mcp_extended.py`:

```python
"""Tests for extended MCP server (lookup_trial_telemetry tool).

Uses the official mcp.client.stdio module for correct framing,
matching the pattern in scripts/wp6_mcp_boundary.py.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = str(REPO_ROOT / "scripts" / "wp6_mcp_server.py")


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _run_with_server(fn):
    """Start MCP server and run fn(session)."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


@pytest.mark.asyncio
async def test_list_tools_includes_telemetry():
    async def check(session):
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        assert "lookup_deal_context" in tool_names
        assert "lookup_trial_telemetry" in tool_names
        return True
    assert await _run_with_server(check)


@pytest.mark.asyncio
async def test_lookup_trial_telemetry_p001():
    async def check(session):
        result = await session.call_tool(
            "lookup_trial_telemetry",
            arguments={"participant_id": "P-001"},
        )
        content = json.loads(result.content[0].text)
        assert "login_count" in content
        assert "features_used" in content
        assert "report_builder_reached" in content
        return True
    assert await _run_with_server(check)


@pytest.mark.asyncio
async def test_lookup_trial_telemetry_missing_participant():
    async def check(session):
        result = await session.call_tool(
            "lookup_trial_telemetry",
            arguments={"participant_id": "P-999"},
        )
        content = result.content[0].text.lower()
        assert "error" in content or "not found" in content
        return True
    assert await _run_with_server(check)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_mcp_extended.py -v`
Expected: `test_list_tools_includes_telemetry` FAILS - `lookup_trial_telemetry` not in tool list

- [ ] **Step 3: Create telemetry fixtures for P-002 and P-005**

Update `fixtures/telemetry/P-001.json` to include required fields:
```json
{
  "login_count": 3,
  "features_used": ["dashboard"],
  "report_builder_reached": false,
  "executive_logins": 0,
  "last_active": "2026-02-20",
  "feature_touchpoints": ["basic_reports"]
}
```

Create `fixtures/telemetry/P-002.json`:
```json
{
  "login_count": 7,
  "features_used": ["dashboard", "reporting", "integrations"],
  "report_builder_reached": true,
  "executive_logins": 0,
  "last_active": "2026-03-15"
}
```

Create `fixtures/telemetry/P-005.json`:
```json
{
  "login_count": 1,
  "features_used": [],
  "report_builder_reached": false,
  "executive_logins": 0,
  "last_active": "2026-01-10"
}
```

- [ ] **Step 4: Extend `scripts/wp6_mcp_server.py`**

Add constant after `ALLOWED_FIELDS_ENUM`:

```python
TELEMETRY_FIELDS = ["login_count", "features_used", "report_builder_reached", "executive_logins"]
```

Add `lookup_trial_telemetry` to `list_tools()` return list:

```python
Tool(
    name="lookup_trial_telemetry",
    description=(
        "Look up trial usage telemetry for a participant. Returns login count, "
        "features used, report builder access, and executive login data."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "participant_id": {
                "type": "string",
                "description": "Participant identifier (e.g., P-001)",
            },
        },
        "required": ["participant_id"],
    },
),
```

Extend `call_tool()` to handle both tools:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    participant_id = arguments["participant_id"]

    if name == "lookup_deal_context":
        allowed_fields = arguments.get("allowed_fields", ALLOWED_FIELDS_ENUM)
        merged = _build_merged_context(participant_id)
        filtered = {k: merged[k] for k in allowed_fields if k in merged}
        if _DELAY_SECONDS > 0:
            await asyncio.sleep(_DELAY_SECONDS)
        return [TextContent(type="text", text=json.dumps(filtered, indent=2))]

    elif name == "lookup_trial_telemetry":
        telemetry_path = TELEMETRY_DIR / f"{participant_id}.json"
        if not telemetry_path.exists():
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"No telemetry data found for {participant_id}"}),
            )]
        telemetry = _load_json(telemetry_path)
        filtered = {k: telemetry[k] for k in TELEMETRY_FIELDS if k in telemetry}
        if _DELAY_SECONDS > 0:
            await asyncio.sleep(_DELAY_SECONDS)
        return [TextContent(type="text", text=json.dumps(filtered, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_mcp_extended.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/wp6_mcp_server.py tests/test_mcp_extended.py fixtures/telemetry/
git commit -m "feat(mcp): add lookup_trial_telemetry tool to MCP server"
```

---

### Task 4: Coverage Checker (Pure Function)

**Files:**
- Create: `methodic/tools/coverage_checker.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tools.py`:

```python
"""Tests for pure function tools."""

import pytest
from methodic.tools.coverage_checker import check_coverage
from methodic.schemas import (
    ParticipantResponse, StructuredFields, QualityMetrics,
    EvidenceItem, CANONICAL_FIELDS,
)


def _make_response(
    participant_id: str = "P-001",
    coverage: dict | None = None,
    confidence: dict | None = None,
) -> ParticipantResponse:
    return ParticipantResponse(
        participant_id=participant_id,
        study_id="STUDY-001",
        segment="lost_deal",
        persona_summary="Test persona",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi",
            secondary_loss_reason=None,
            roi_clarity="unclear",
            budget_timing="out_of_cycle",
            procurement_friction="unknown",
            security_concern="none",
            competitor_pressure="none",
            aha_moment_reached="no",
        ),
        field_confidence=confidence or {"primary_loss_reason": 0.9},
        coverage_state=coverage or {"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(
            variable_coverage=0.5, ambiguity_resolved=False,
            evidence_linked=True, requires_recontact=False,
        ),
        evidence=[
            EvidenceItem(
                field="primary_loss_reason", quote="Test quote",
                transcript_turn_id="turn-001", context_used=[],
            )
        ],
        unresolved_ambiguities=["procurement_friction"],
    )


def test_check_coverage_single_response():
    responses = [_make_response(coverage={
        "primary_loss_reason": "covered_high_confidence",
        "roi_clarity": "covered_high_confidence",
        "budget_timing": "covered_low_confidence",
        "procurement_friction": "ambiguous",
        "security_concern": "missing",
        "competitor_pressure": "missing",
        "aha_moment_reached": "missing",
    })]
    result = check_coverage(responses)
    assert result["overall_coverage"] == pytest.approx(2 / 8)
    assert result["per_variable"]["procurement_friction"] == "ambiguous"
    assert "procurement_friction" in result["ambiguous_variables"]


def test_check_coverage_aggregates_multiple():
    r1 = _make_response(participant_id="P-001",
        coverage={"primary_loss_reason": "covered_high_confidence"})
    r2 = _make_response(participant_id="P-002",
        coverage={"primary_loss_reason": "covered_high_confidence",
                   "procurement_friction": "covered_high_confidence"})
    result = check_coverage([r1, r2])
    assert result["per_variable"]["procurement_friction"] == "covered_high_confidence"


def test_check_coverage_empty():
    result = check_coverage([])
    assert result["overall_coverage"] == 0.0
    assert all(v == "missing" for v in result["per_variable"].values())


def test_check_coverage_all_covered():
    full = {f: "covered_high_confidence" for f in CANONICAL_FIELDS}
    result = check_coverage([_make_response(coverage=full)])
    assert result["overall_coverage"] == 1.0
    assert result["ambiguous_variables"] == []
    assert result["missing_variables"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tools.py -v`
Expected: FAIL - `ModuleNotFoundError`

- [ ] **Step 3: Write `methodic/tools/coverage_checker.py`**

```python
"""Coverage checker - deterministic variable coverage computation. No LLM calls."""

from __future__ import annotations
from methodic.schemas import ParticipantResponse, CoverageState, CANONICAL_FIELDS

COVERAGE_RANK = {
    "missing": 0, "ambiguous": 1,
    "covered_low_confidence": 2, "covered_high_confidence": 3,
}


def check_coverage(responses: list[ParticipantResponse]) -> dict:
    best: dict[str, CoverageState] = {f: "missing" for f in CANONICAL_FIELDS}
    for response in responses:
        for field, state in response.coverage_state.items():
            if field in best and COVERAGE_RANK.get(state, 0) > COVERAGE_RANK.get(best[field], 0):
                best[field] = state

    high_count = sum(1 for v in best.values() if v == "covered_high_confidence")
    return {
        "per_variable": best,
        "overall_coverage": high_count / len(CANONICAL_FIELDS) if CANONICAL_FIELDS else 0.0,
        "ambiguous_variables": [f for f, v in best.items() if v == "ambiguous"],
        "missing_variables": [f for f, v in best.items() if v == "missing"],
    }
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_tools.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/tools/coverage_checker.py tests/test_tools.py
git commit -m "feat(methodic): add deterministic coverage checker"
```

---

### Task 5: Quality Scorer (Pure Function)

**Files:**
- Create: `methodic/tools/quality_scorer.py`
- Modify: `tests/test_tools.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_tools.py`:

```python
from methodic.tools.quality_scorer import score_quality


def test_score_quality_complete():
    r = _make_response(
        coverage={f: "covered_high_confidence" for f in CANONICAL_FIELDS},
        confidence={f: 0.9 for f in CANONICAL_FIELDS},
    )
    r.evidence = [EvidenceItem(field=f, quote="Q", transcript_turn_id="t-1", context_used=[]) for f in CANONICAL_FIELDS]
    r.unresolved_ambiguities = []
    q = score_quality(r)
    assert q.variable_coverage == 1.0
    assert q.ambiguity_resolved is True
    assert q.requires_recontact is False


def test_score_quality_partial():
    r = _make_response(coverage={
        "primary_loss_reason": "covered_high_confidence",
        "procurement_friction": "ambiguous",
    })
    r.evidence = [EvidenceItem(field="primary_loss_reason", quote="Q", transcript_turn_id="t-1", context_used=[])]
    r.unresolved_ambiguities = ["procurement_friction"]
    q = score_quality(r)
    assert q.variable_coverage < 1.0
    assert q.ambiguity_resolved is False
    assert q.requires_recontact is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tools.py::test_score_quality_complete -v`
Expected: FAIL

- [ ] **Step 3: Write `methodic/tools/quality_scorer.py`**

```python
"""Quality scorer - deterministic quality metrics. No LLM calls."""

from __future__ import annotations
from methodic.schemas import ParticipantResponse, QualityMetrics, CANONICAL_FIELDS


def score_quality(response: ParticipantResponse) -> QualityMetrics:
    covered_high = sum(1 for f in CANONICAL_FIELDS
        if response.coverage_state.get(f) == "covered_high_confidence")
    variable_coverage = covered_high / len(CANONICAL_FIELDS)
    ambiguity_resolved = len(response.unresolved_ambiguities) == 0
    evidence_fields = {e.field for e in response.evidence}
    covered_fields = {f for f in CANONICAL_FIELDS
        if response.coverage_state.get(f) in ("covered_high_confidence", "covered_low_confidence")}
    evidence_linked = covered_fields.issubset(evidence_fields) if covered_fields else True
    requires_recontact = len(response.unresolved_ambiguities) > 0 or variable_coverage < 0.5
    return QualityMetrics(
        variable_coverage=variable_coverage, ambiguity_resolved=ambiguity_resolved,
        evidence_linked=evidence_linked, requires_recontact=requires_recontact,
    )
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_tools.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/tools/quality_scorer.py tests/test_tools.py
git commit -m "feat(methodic): add deterministic quality scorer"
```

---

### Task 6: Extractor (Gemini Structured Output via google-genai)

**Files:**
- Create: `methodic/tools/extractor.py`
- Modify: `tests/test_tools.py` (append)

- [ ] **Step 1: Write failing test**

Append to `tests/test_tools.py`:

```python
from unittest.mock import patch
from methodic.tools.extractor import extract_structured_fields


@pytest.mark.asyncio
async def test_extract_structured_fields_mock():
    mock_extraction = {
        "primary_loss_reason": "unclear_roi",
        "secondary_loss_reason": None,
        "roi_clarity": "unclear",
        "budget_timing": "out_of_cycle",
        "procurement_friction": "none",
        "security_concern": "none",
        "competitor_pressure": "none",
        "aha_moment_reached": "no",
        "field_confidence": {"primary_loss_reason": 0.92, "roi_clarity": 0.85},
        "evidence": [{
            "field": "primary_loss_reason",
            "quote": "We could never prove the ROI",
            "transcript_turn_id": "turn-003",
            "context_used": ["crm_notes"],
        }],
    }

    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.return_value = mock_extraction
        result = await extract_structured_fields(
            transcript=[
                {"role": "interviewer", "content": "What led to the decision?"},
                {"role": "participant", "content": "We could never prove the ROI internally."},
            ],
            participant_id="P-001",
            study_id="STUDY-001",
        )
    assert result.structured_fields.primary_loss_reason == "unclear_roi"
    assert result.field_confidence["primary_loss_reason"] == pytest.approx(0.92)
    assert len(result.evidence) == 1


@pytest.mark.asyncio
async def test_extract_handles_invalid_json():
    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.side_effect = [ValueError("Invalid JSON"), {
            "primary_loss_reason": "unknown", "secondary_loss_reason": None,
            "roi_clarity": "unknown", "budget_timing": "unknown",
            "procurement_friction": "unknown", "security_concern": "unknown",
            "competitor_pressure": "unknown", "aha_moment_reached": "unknown",
            "field_confidence": {}, "evidence": [],
        }]
        result = await extract_structured_fields(
            transcript=[{"role": "interviewer", "content": "Hello"}],
            participant_id="P-001", study_id="STUDY-001",
        )
    assert result.conversation_status == "partial"


@pytest.mark.asyncio
async def test_extract_marks_partial_on_total_failure():
    with patch("methodic.tools.extractor._call_gemini_extraction") as mock:
        mock.side_effect = Exception("API timeout")
        result = await extract_structured_fields(
            transcript=[{"role": "interviewer", "content": "Hello"}],
            participant_id="P-001", study_id="STUDY-001",
        )
    assert result.conversation_status == "partial"
    assert all(v == "missing" for v in result.coverage_state.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tools.py::test_extract_structured_fields_mock -v`
Expected: FAIL

- [ ] **Step 3: Write `methodic/tools/extractor.py`**

```python
"""Structured field extractor - calls Gemini with response_schema via google-genai SDK.

Recovery matrix:
- Invalid JSON: retry once with error context, then mark partial
- Missing evidence: downgrade affected coverage to ambiguous
- API timeout/rate limit: return partial response with all fields unknown
- Safety refusal: mark unresolved, do not fabricate
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai

from methodic import MODEL
from methodic.schemas import (
    ParticipantResponse, StructuredFields, QualityMetrics,
    EvidenceItem, CANONICAL_FIELDS,
)
from methodic.tools.quality_scorer import score_quality

log = logging.getLogger(__name__)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_loss_reason": {
            "type": "string",
            "enum": ["unclear_roi", "budget_timing", "procurement_friction",
                     "security_concern", "competitor_pressure", "missing_feature",
                     "economic_buyer_gap", "other", "unknown"],
        },
        "secondary_loss_reason": {"type": "string"},
        "roi_clarity": {"type": "string", "enum": ["clear", "partially_clear", "unclear", "unknown"]},
        "budget_timing": {"type": "string", "enum": ["in_cycle", "out_of_cycle", "unknown"]},
        "procurement_friction": {"type": "string", "enum": ["none", "low", "medium", "high", "unknown"]},
        "security_concern": {"type": "string", "enum": ["none", "low", "medium", "high", "unknown"]},
        "competitor_pressure": {"type": "string", "enum": ["none", "named_competitor", "unknown"]},
        "aha_moment_reached": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "field_confidence": {
            "type": "object",
            "properties": {f: {"type": "number"} for f in CANONICAL_FIELDS},
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"}, "quote": {"type": "string"},
                    "transcript_turn_id": {"type": "string"},
                    "context_used": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["field", "quote", "transcript_turn_id", "context_used"],
            },
        },
    },
    "required": ["primary_loss_reason", "roi_clarity", "budget_timing",
                  "procurement_friction", "security_concern", "competitor_pressure",
                  "aha_moment_reached", "field_confidence", "evidence"],
}

EXTRACTION_PROMPT = """You are a structured data extractor for B2B win-loss research.

Given a conversation transcript, extract:
1. The 8 canonical structured fields with their enum values
2. Confidence scores (0.0-1.0) for each field
3. Evidence items linking fields to specific quotes

Rules:
- Only extract what is explicitly stated or strongly implied
- Use "unknown" when the participant hasn't addressed a topic
- Confidence below 0.5 means weak or indirect evidence
- Every non-"unknown" field MUST have at least one evidence item

Transcript:
{transcript}
"""


async def _call_gemini_extraction(transcript_text: str) -> dict[str, Any]:
    client = genai.Client()
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=EXTRACTION_PROMPT.format(transcript=transcript_text),
        config={
            "response_mime_type": "application/json",
            "response_json_schema": EXTRACTION_SCHEMA,
        },
    )
    return json.loads(response.text)


def _format_transcript(transcript: list[dict[str, str]]) -> str:
    return "\n".join(
        f"[Turn {i+1}] {t.get('role', 'unknown').upper()}: {t.get('content', '')}"
        for i, t in enumerate(transcript)
    )


def _empty_response(participant_id: str, study_id: str, segment: str, persona_summary: str) -> ParticipantResponse:
    return ParticipantResponse(
        participant_id=participant_id, study_id=study_id,
        segment=segment, persona_summary=persona_summary,
        conversation_status="partial",
        structured_fields=StructuredFields(
            primary_loss_reason="unknown", secondary_loss_reason=None,
            roi_clarity="unknown", budget_timing="unknown",
            procurement_friction="unknown", security_concern="unknown",
            competitor_pressure="unknown", aha_moment_reached="unknown",
        ),
        field_confidence={},
        coverage_state={f: "missing" for f in CANONICAL_FIELDS},
        quality=QualityMetrics(variable_coverage=0.0, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=True),
        evidence=[], unresolved_ambiguities=[],
    )


async def extract_structured_fields(
    transcript: list[dict[str, str]],
    participant_id: str,
    study_id: str,
    segment: str = "unknown",
    persona_summary: str = "",
) -> ParticipantResponse:
    transcript_text = _format_transcript(transcript)

    # Retry once on failure
    raw = None
    for attempt in range(2):
        try:
            raw = await _call_gemini_extraction(transcript_text)
            break
        except Exception as e:
            log.warning("Extraction attempt %d failed: %s", attempt + 1, e)
            if attempt == 1:
                return _empty_response(participant_id, study_id, segment, persona_summary)

    if raw is None:
        return _empty_response(participant_id, study_id, segment, persona_summary)

    structured_fields = StructuredFields(
        primary_loss_reason=raw.get("primary_loss_reason", "unknown"),
        secondary_loss_reason=raw.get("secondary_loss_reason"),
        roi_clarity=raw.get("roi_clarity", "unknown"),
        budget_timing=raw.get("budget_timing", "unknown"),
        procurement_friction=raw.get("procurement_friction", "unknown"),
        security_concern=raw.get("security_concern", "unknown"),
        competitor_pressure=raw.get("competitor_pressure", "unknown"),
        aha_moment_reached=raw.get("aha_moment_reached", "unknown"),
    )

    field_confidence = {
        k: max(0.0, min(1.0, v))
        for k, v in raw.get("field_confidence", {}).items()
        if k in CANONICAL_FIELDS and isinstance(v, (int, float))
    }

    evidence = [
        EvidenceItem(field=e["field"], quote=e["quote"],
            transcript_turn_id=e.get("transcript_turn_id", f"turn-{i+1}"),
            context_used=e.get("context_used", []))
        for i, e in enumerate(raw.get("evidence", []))
        if e.get("field") in CANONICAL_FIELDS
    ]

    # Downgrade coverage for fields with no evidence
    evidence_fields = {e.field for e in evidence}
    coverage_state = {}
    for field in CANONICAL_FIELDS:
        value = getattr(structured_fields, field)
        conf = field_confidence.get(field, 0.0)
        if value == "unknown" or value is None:
            coverage_state[field] = "missing"
        elif field not in evidence_fields:
            coverage_state[field] = "ambiguous"
        elif conf >= 0.7:
            coverage_state[field] = "covered_high_confidence"
        elif conf >= 0.4:
            coverage_state[field] = "covered_low_confidence"
        else:
            coverage_state[field] = "ambiguous"

    response = ParticipantResponse(
        participant_id=participant_id, study_id=study_id,
        segment=segment, persona_summary=persona_summary,
        conversation_status="partial",
        structured_fields=structured_fields,
        field_confidence=field_confidence,
        coverage_state=coverage_state,
        quality=QualityMetrics(variable_coverage=0.0, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=evidence,
        unresolved_ambiguities=[f for f, s in coverage_state.items() if s == "ambiguous"],
    )
    response.quality = score_quality(response)
    return response
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_tools.py -v`
Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/tools/extractor.py tests/test_tools.py
git commit -m "feat(methodic): add Gemini structured extractor with retry and error handling"
```

---

### Task 7: BigQuery Export (with table setup)

**Files:**
- Create: `methodic/tools/bigquery_export.py`
- Modify: `tests/test_tools.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_tools.py`:

```python
from methodic.tools.bigquery_export import export_to_bigquery, _flatten_response


def test_export_dry_run():
    result = export_to_bigquery([_make_response()], dry_run=True)
    assert result["rows_written"] == 1
    assert result["dry_run"] is True


def test_export_flattens_fields():
    r = _make_response(
        coverage={f: "covered_high_confidence" for f in CANONICAL_FIELDS},
        confidence={"primary_loss_reason": 0.95, "roi_clarity": 0.8},
    )
    row = _flatten_response(r)
    assert row["primary_loss_reason"] == "unclear_roi"
    assert row["conf_primary_loss_reason"] == 0.95
    assert row["cov_primary_loss_reason"] == "covered_high_confidence"
    assert "exported_at" in row


def test_export_dry_run_fail_on_error():
    result = export_to_bigquery([_make_response()], dry_run=True, fail_on_error=True)
    assert result["rows_written"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tools.py::test_export_dry_run -v`
Expected: FAIL

- [ ] **Step 3: Write `methodic/tools/bigquery_export.py`**

```python
"""BigQuery export - flattens ParticipantResponse to BQ rows.

Supports dry_run mode for local testing. In live mode, ensures
dataset and table exist before inserting.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from methodic.schemas import ParticipantResponse, CANONICAL_FIELDS

DATASET = os.environ.get("BIGQUERY_DATASET", "methodic_demo")
TABLE_NAME = f"{DATASET}.win_loss_responses"


def _flatten_response(response: ParticipantResponse) -> dict[str, Any]:
    row: dict[str, Any] = {
        "participant_id": response.participant_id,
        "study_id": response.study_id,
        "segment": response.segment,
        "persona_summary": response.persona_summary,
        "conversation_status": response.conversation_status,
    }
    for field in CANONICAL_FIELDS:
        row[field] = getattr(response.structured_fields, field)
    for field in CANONICAL_FIELDS:
        if field == "secondary_loss_reason":
            continue
        row[f"conf_{field}"] = response.field_confidence.get(field)
    for field in CANONICAL_FIELDS:
        if field == "secondary_loss_reason":
            continue
        row[f"cov_{field}"] = response.coverage_state.get(field)
    row["quality_variable_coverage"] = response.quality.variable_coverage
    row["quality_ambiguity_resolved"] = response.quality.ambiguity_resolved
    row["quality_evidence_linked"] = response.quality.evidence_linked
    row["quality_requires_recontact"] = response.quality.requires_recontact
    row["evidence_json"] = json.dumps([e.model_dump() for e in response.evidence])
    row["unresolved_ambiguities_json"] = json.dumps(response.unresolved_ambiguities)
    row["exported_at"] = datetime.now(timezone.utc).isoformat()
    return row


def _ensure_bigquery_table(project: str, dataset: str) -> None:
    from google.cloud import bigquery
    from pathlib import Path

    client = bigquery.Client(project=project)
    dataset_ref = bigquery.DatasetReference(project, dataset)
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        ds = bigquery.Dataset(dataset_ref)
        ds.location = "US"
        client.create_dataset(ds)

    table_ref = dataset_ref.table("win_loss_responses")
    try:
        client.get_table(table_ref)
    except Exception:
        sql_path = Path(__file__).resolve().parent.parent.parent / "docs" / "schema" / "bigquery-table.sql"
        if sql_path.exists():
            client.query(sql_path.read_text()).result()


def export_to_bigquery(
    responses: list[ParticipantResponse],
    dry_run: bool | None = None,
    fail_on_error: bool = False,
) -> dict[str, Any]:
    if dry_run is None:
        dry_run = os.environ.get("BIGQUERY_DRY_RUN", "true").lower() == "true"

    rows = [_flatten_response(r) for r in responses]

    if dry_run:
        return {
            "rows_written": len(rows), "table_name": TABLE_NAME,
            "dataset": DATASET, "dry_run": True, "rows": rows,
        }

    from google.cloud import bigquery
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    _ensure_bigquery_table(project, DATASET)

    client = bigquery.Client(project=project)
    table_ref = client.dataset(DATASET).table("win_loss_responses")
    errors = client.insert_rows_json(table_ref, rows)

    if errors and fail_on_error:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    return {
        "rows_written": len(rows) if not errors else 0,
        "table_name": TABLE_NAME, "dataset": DATASET,
        "dry_run": False, "errors": errors if errors else None,
    }
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_tools.py -v`
Expected: 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/tools/bigquery_export.py tests/test_tools.py
git commit -m "feat(methodic): add BigQuery export with table setup and fail_on_error"
```

---

### Task 8: MCP Deal Context McpToolset Wrapper

**Files:**
- Create: `methodic/tools/deal_context.py`

- [ ] **Step 1: Write `methodic/tools/deal_context.py`**

```python
"""McpToolset wrapper for the wp6 MCP server."""

from __future__ import annotations
from pathlib import Path

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MCP_SERVER_PATH = REPO_ROOT / "scripts" / "wp6_mcp_server.py"


def get_deal_context_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python3", args=[str(MCP_SERVER_PATH)],
            ),
        ),
        tool_filter=["lookup_deal_context", "lookup_trial_telemetry"],
    )
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "from methodic.tools.deal_context import get_deal_context_toolset; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add methodic/tools/deal_context.py
git commit -m "feat(methodic): add McpToolset wrapper for deal context MCP"
```

---

### Task 9: Agent Prompts

**Files:**
- Create: `methodic/prompts/interviewer_system.md`
- Create: `methodic/prompts/methodology_system.md`
- Create: `methodic/prompts/sim_participant_system.md`

- [ ] **Step 1: Write `methodic/prompts/interviewer_system.md`**

```markdown
You are a B2B win-loss research interviewer for Methodic.

## Your Role
Conduct structured interviews with participants involved in recently lost or slipping B2B deals. Uncover real reasons behind deal outcomes through empathetic, probing conversation.

## Required Variables
Collect evidence for 8 structured fields:
1. primary_loss_reason 2. secondary_loss_reason 3. roi_clarity
4. budget_timing 5. procurement_friction 6. security_concern
7. competitor_pressure 8. aha_moment_reached

## Technique
- Start with open-ended questions about their experience
- When you hear surface-level answers (e.g., "price was too high"), probe deeper
- Use triangulation: compare claims with CRM context (via MCP tools)
- Ask one question at a time
- If a participant is vague, rephrase once. If still vague, move on.
- Never lead the witness
- Maximum 6 turns per participant. Prioritize uncovered variables.

## MCP Tool Usage
- `lookup_deal_context` - use early to understand participant's role and deal context
- `lookup_trial_telemetry` - use when participant mentions product usage to triangulate

Call tools BEFORE asking questions that reference the data.

## Output
Output your next question (1-3 sentences). End with a question unless wrapping up.
When sufficient coverage or turn limit reached: "Thank you for your time."
```

- [ ] **Step 2: Write `methodic/prompts/methodology_system.md`**

```markdown
You are a research methodology reviewer for Methodic.

## Your Role
Review study briefs and push back on methodological weaknesses.

## What to Review
1. Sampling bias - representative pool? Including economic buyers and procurement?
2. Question framing - neutral or leading?
3. Variable coverage - all 8 variables addressed?
4. Sample size - sufficient for claims?
5. Timing - memory decay risk?

## Output Format
{"verdict": "APPROVE" | "REVISE_REQUIRED", "issues": [...], "recommendations": [...]}

Always push back on champion-only sampling.
```

- [ ] **Step 3: Write `methodic/prompts/sim_participant_system.md`**

```markdown
You are simulating a B2B participant in a win-loss research interview.

## Your Character
Given a persona with role, deal stage, initial answer, and underlying reason.

## Behavior
1. First answer: give the surface answer. Brief and guarded.
2. When probed: gradually reveal more detail.
3. After 2-3 probes: reveal the underlying reason if asked correctly.
4. Vague on unknown topics: "I'm not sure" or "that wasn't my area."
5. Natural speech: contractions, filler words, incomplete thoughts.
6. Stay in character. Never break the fourth wall.

## Guardrails
- Unknown topics: say so naturally
- Pushy interviewer: express mild frustration
- Leading questions: push back
- Never fabricate data not in your persona

## Response Length
2-4 sentences. Occasionally one sentence to force probing.
```

- [ ] **Step 4: Commit**

```bash
git add methodic/prompts/
git commit -m "feat(methodic): add system prompts for interviewer, methodology, and sim"
```

---

### Task 10: Organizer Agent

**Files:**
- Create: `methodic/agents/organizer.py`
- Create: `tests/test_agents.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_agents.py`:

```python
"""Tests for agent definitions - verify wiring, not LLM behavior."""

import pytest
from google.adk.agents import Agent


def test_organizer_agent():
    from methodic.agents.organizer import organizer_agent
    assert isinstance(organizer_agent, Agent)
    assert organizer_agent.name == "organizer"
    assert organizer_agent.output_key == "study_brief"
    assert "gemini" in organizer_agent.model.lower()


def test_methodology_agent():
    from methodic.agents.methodology import methodology_agent
    assert isinstance(methodology_agent, Agent)
    assert methodology_agent.name == "methodology"
    assert methodology_agent.output_key == "methodology_review"


def test_question_design_agent():
    from methodic.agents.question_design import question_design_agent
    assert isinstance(question_design_agent, Agent)
    assert question_design_agent.name == "question_design"
    assert question_design_agent.output_key == "question_pool"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_agents.py::test_organizer_agent -v`
Expected: FAIL

- [ ] **Step 3: Write `methodic/agents/organizer.py`**

```python
"""Organizer agent - request intake and study brief generation."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

organizer_agent = Agent(
    name="organizer",
    model=MODEL,
    output_key="study_brief",
    instruction="""You are the study organizer for Methodic.

Accept a research request and produce a study brief.

If the request is clear, produce the brief immediately.
If ambiguous, ask ONE clarifying question.

Output JSON:
{
  "study_objective": "...",
  "target_segment": "...",
  "required_variables": ["primary_loss_reason", ...],
  "participant_pool": ["P-001", "P-002", "P-003"],
  "reserve_participants": ["P-005"],
  "hypotheses": ["..."]
}""",
)
```

- [ ] **Step 4: Run test**

Run: `python3 -m pytest tests/test_agents.py::test_organizer_agent -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/agents/organizer.py tests/test_agents.py
git commit -m "feat(methodic): add organizer LlmAgent"
```

---

### Task 11: Methodology + Question Design Agents

**Files:**
- Create: `methodic/agents/methodology.py`
- Create: `methodic/agents/question_design.py`

- [ ] **Step 1: Write `methodic/agents/methodology.py`**

```python
"""Methodology agent - reviews study brief, pushes back on weaknesses."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "methodology_system.md").read_text()

methodology_agent = Agent(
    name="methodology",
    model=MODEL,
    output_key="methodology_review",
    instruction=_PROMPT + "\n\nReview the study brief from the conversation history.",
)
```

- [ ] **Step 2: Write `methodic/agents/question_design.py`**

```python
"""Question design agent - maps questions to canonical variables."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

question_design_agent = Agent(
    name="question_design",
    model=MODEL,
    output_key="question_pool",
    instruction="""You are the question design agent for Methodic.

Design a pool of interview questions mapping to 8 canonical variables.

Rules:
- Each variable must have at least one question
- Questions must be open-ended and non-leading
- Include follow-up probes
- Maximum 12 questions

Output JSON array:
[{"question_id": "Q1", "text": "...", "target_variables": [...], "follow_up_probes": [...]}]""",
)
```

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest tests/test_agents.py -v`
Expected: 3 tests PASS

- [ ] **Step 4: Commit**

```bash
git add methodic/agents/methodology.py methodic/agents/question_design.py
git commit -m "feat(methodic): add methodology and question design LlmAgents"
```

---

### Task 12: Participant Interviewer + Sim Agents

**Files:**
- Create: `methodic/agents/participant.py`
- Create: `methodic/agents/participant_sim.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_agents.py`:

```python
def test_interviewer_agent():
    from methodic.agents.participant import interviewer_agent
    assert isinstance(interviewer_agent, Agent)
    assert interviewer_agent.name == "interviewer"
    assert interviewer_agent.output_key == "latest_interviewer_turn"
    assert "gemini" in interviewer_agent.model.lower()


def test_participant_sim_agent():
    from methodic.agents.participant_sim import participant_sim_agent
    assert isinstance(participant_sim_agent, Agent)
    assert participant_sim_agent.name == "participant_sim"
    assert participant_sim_agent.output_key == "latest_participant_turn"
    assert "gemini" in participant_sim_agent.model.lower()
```

- [ ] **Step 2: Write `methodic/agents/participant.py`**

```python
"""Interviewer agent - conducts live B2B win-loss interviews with MCP tools."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL
from methodic.tools.deal_context import get_deal_context_toolset

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "interviewer_system.md").read_text()

interviewer_agent = Agent(
    name="interviewer",
    model=MODEL,
    output_key="latest_interviewer_turn",
    instruction=_PROMPT,
    tools=[get_deal_context_toolset()],
)
```

- [ ] **Step 3: Write `methodic/agents/participant_sim.py`**

```python
"""Simulated participant agent - responds in character for testing/demo."""

from pathlib import Path
from google.adk.agents.llm_agent import Agent
from methodic import MODEL_FAST

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "sim_participant_system.md").read_text()

participant_sim_agent = Agent(
    name="participant_sim",
    model=MODEL_FAST,
    output_key="latest_participant_turn",
    instruction=_PROMPT + "\n\nPersona details are in the conversation context.",
)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_agents.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/agents/participant.py methodic/agents/participant_sim.py tests/test_agents.py
git commit -m "feat(methodic): add interviewer and participant_sim LlmAgents with output_keys"
```

---

### Task 13: Quality Reviewer + Replanner Agents

**Files:**
- Create: `methodic/agents/quality.py`
- Create: `methodic/agents/replanner.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_agents.py`:

```python
def test_quality_agent():
    from methodic.agents.quality import quality_agent
    assert isinstance(quality_agent, Agent)
    assert quality_agent.name == "quality_reviewer"
    assert quality_agent.output_key == "quality_report"


def test_replanner_agent():
    from methodic.agents.replanner import replanner_agent
    assert isinstance(replanner_agent, Agent)
    assert replanner_agent.name == "replanner"
    assert replanner_agent.output_key == "replan_decision"
    assert len(replanner_agent.tools) > 0, "replanner must have check_coverage tool"
```

- [ ] **Step 2: Write `methodic/agents/quality.py`**

```python
"""Quality reviewer - reviews participant responses for themes and contradictions."""

from google.adk.agents.llm_agent import Agent
from methodic import MODEL

quality_agent = Agent(
    name="quality_reviewer",
    model=MODEL,
    output_key="quality_report",
    instruction="""You are the quality reviewer for Methodic.

Review collected data for:
1. Cross-participant themes
2. Contradictions between participants
3. Evidence gaps
4. Data quality (specific quotes vs vague)

Output JSON:
{
  "themes": [{"theme": "...", "supporting_participants": [...], "confidence": 0.9}],
  "contradictions": [{"variable": "...", "participants": [...], "description": "..."}],
  "gaps": ["variable_name"],
  "overall_quality_score": 0.0-1.0,
  "recommendation": "SUFFICIENT" | "NEEDS_MORE_DATA"
}""",
)
```

- [ ] **Step 3: Write `methodic/agents/replanner.py` (with check_coverage tool)**

```python
"""Replanner - decides whether to add more sessions. Has check_coverage tool."""

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool
from methodic import MODEL
from methodic.tools.coverage_checker import check_coverage
from methodic.schemas import ParticipantResponse


def _check_coverage_tool(responses_json: str) -> str:
    """Check variable coverage across participant responses.

    Args:
        responses_json: JSON string of participant response dicts
    Returns:
        JSON string with coverage summary
    """
    import json
    data = json.loads(responses_json)
    responses = [ParticipantResponse.model_validate(d) for d in data]
    result = check_coverage(responses)
    return json.dumps(result)


replanner_agent = Agent(
    name="replanner",
    model=MODEL,
    output_key="replan_decision",
    tools=[FunctionTool(func=_check_coverage_tool)],
    instruction="""You are the replanner for Methodic's fieldwork loop.

You have the check_coverage tool. Use it to assess coverage.

Decision logic:
1. ALL 8 variables covered_high_confidence -> STOP
2. Variable is "ambiguous" and reserve participant can resolve -> ADD_PARTICIPANT
3. Max iterations reached -> STOP
4. Only "missing" with no available participants -> STOP

Output JSON:
{
  "decision": "STOP" | "ADD_PARTICIPANT",
  "reason": "...",
  "add_participant_id": null | "P-005",
  "target_variables": ["procurement_friction"]
}""",
)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_agents.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/agents/quality.py methodic/agents/replanner.py tests/test_agents.py
git commit -m "feat(methodic): add quality reviewer and replanner with check_coverage tool"
```

---

### Task 14: Custom BaseAgent Workflow Steps

**Files:**
- Create: `methodic/agents/extractor_step.py`
- Create: `methodic/agents/turn_checker_step.py`
- Create: `methodic/agents/coverage_step.py`
- Create: `methodic/agents/bigquery_export_step.py`
- Create: `tests/test_steps.py`

This is the critical task that fixes the BLOCKER: FunctionTools cannot be sub-agents in ADK workflow agents. Each deterministic step is a custom `BaseAgent` subclass that reads from `ctx.session.state`, runs logic, writes results back to state, and optionally escalates to exit a loop.

- [ ] **Step 1: Write failing tests**

Create `tests/test_steps.py`:

```python
"""Tests for custom BaseAgent workflow steps."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from methodic.schemas import CANONICAL_FIELDS


def _make_mock_ctx(state: dict):
    ctx = MagicMock()
    ctx.session.state = state
    ctx.actions = MagicMock()
    ctx.actions.escalate = False
    return ctx


def test_turn_checker_escalates_on_max_turns():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {"turn_count": 6}
    ctx = _make_mock_ctx(state)
    # Synchronous check
    assert step.should_escalate(state, max_turns=6) is True


def test_turn_checker_does_not_escalate_early():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {"turn_count": 3}
    assert step.should_escalate(state, max_turns=6) is False


def test_turn_checker_escalates_on_full_coverage():
    from methodic.agents.turn_checker_step import TurnCheckerStep

    step = TurnCheckerStep(name="turn_checker", max_turns=6)
    state = {
        "turn_count": 2,
        "participant_coverage": {f: "covered_high_confidence" for f in CANONICAL_FIELDS},
    }
    assert step.should_escalate(state, max_turns=6) is True


def test_coverage_step_computes_from_state():
    from methodic.agents.coverage_step import CoverageStep
    from methodic.schemas import ParticipantResponse, StructuredFields, QualityMetrics, EvidenceItem

    r = ParticipantResponse(
        participant_id="P-001", study_id="S-1", segment="lost",
        persona_summary="Test", conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason=None,
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="unknown", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.9},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(variable_coverage=0.5, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )

    step = CoverageStep(name="coverage")
    result = step.compute({"P-001": r.model_dump()})
    assert result["per_variable"]["primary_loss_reason"] == "covered_high_confidence"


def test_bigquery_export_step_dry_run():
    from methodic.agents.bigquery_export_step import BigQueryExportStep

    step = BigQueryExportStep(name="bq_export")
    # Just verify it can be instantiated
    assert step.name == "bq_export"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_steps.py -v`
Expected: FAIL - `ModuleNotFoundError`

- [ ] **Step 3: Write `methodic/agents/turn_checker_step.py`**

```python
"""Turn checker step - deterministic agent that exits the interview loop.

Checks turn count and per-participant coverage. Sets ctx.actions.escalate = True
when stop conditions are met. This is a custom BaseAgent, not a FunctionTool,
because ADK workflow sub_agents must be agent instances.
"""

from __future__ import annotations
from typing import Any

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.schemas import CANONICAL_FIELDS


class TurnCheckerStep(BaseAgent):
    max_turns: int = 6

    def should_escalate(self, state: dict, max_turns: int | None = None) -> bool:
        mt = max_turns or self.max_turns
        turn_count = state.get("turn_count", 0)
        if turn_count >= mt:
            return True
        coverage = state.get("participant_coverage", {})
        if coverage and all(
            coverage.get(f) == "covered_high_confidence"
            for f in CANONICAL_FIELDS
        ):
            return True
        return False

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        state["turn_count"] = state.get("turn_count", 0) + 1
        if self.should_escalate(state):
            ctx.actions.escalate = True
        return None
```

- [ ] **Step 4: Write `methodic/agents/extractor_step.py`**

```python
"""Extractor step - calls Gemini structured extraction after each turn pair.

Reads transcript from state, calls extractor, writes result back.
"""

from __future__ import annotations
from typing import Any

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.tools.extractor import extract_structured_fields


class ExtractorStep(BaseAgent):

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        participant_id = state.get("active_participant_id", "unknown")
        study_id = state.get("study_id", "unknown")
        transcripts = state.get("transcripts_by_participant", {})
        transcript = transcripts.get(participant_id, [])

        if not transcript:
            return None

        result = await extract_structured_fields(
            transcript=transcript,
            participant_id=participant_id,
            study_id=study_id,
            segment=state.get("segment", "unknown"),
            persona_summary=state.get("persona_summary", ""),
        )

        responses = state.get("participant_response_by_id", {})
        responses[participant_id] = result.model_dump()
        state["participant_response_by_id"] = responses
        state["participant_coverage"] = result.coverage_state

        return None
```

- [ ] **Step 5: Write `methodic/agents/coverage_step.py`**

```python
"""Coverage step - computes study-wide coverage from all participant responses."""

from __future__ import annotations

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.schemas import ParticipantResponse
from methodic.tools.coverage_checker import check_coverage


class CoverageStep(BaseAgent):

    def compute(self, responses_by_id: dict) -> dict:
        responses = [
            ParticipantResponse.model_validate(r) for r in responses_by_id.values()
        ]
        return check_coverage(responses)

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})
        result = self.compute(responses_by_id)
        state["coverage_state"] = result
        return None
```

- [ ] **Step 6: Write `methodic/agents/bigquery_export_step.py`**

```python
"""BigQuery export step - writes all participant responses to BigQuery."""

from __future__ import annotations

from google.adk.agents import BaseAgent
from google.genai import types

from methodic.schemas import ParticipantResponse
from methodic.tools.bigquery_export import export_to_bigquery


class BigQueryExportStep(BaseAgent):

    async def _run_async_impl(self, ctx) -> types.Content | None:
        state = ctx.session.state
        responses_by_id = state.get("participant_response_by_id", {})
        responses = [
            ParticipantResponse.model_validate(r) for r in responses_by_id.values()
        ]
        result = export_to_bigquery(responses)
        state["export_result"] = result
        return None
```

- [ ] **Step 7: Run tests**

Run: `python3 -m pytest tests/test_steps.py -v`
Expected: 5 tests PASS

- [ ] **Step 8: Commit**

```bash
git add methodic/agents/extractor_step.py methodic/agents/turn_checker_step.py \
       methodic/agents/coverage_step.py methodic/agents/bigquery_export_step.py \
       tests/test_steps.py
git commit -m "feat(methodic): add custom BaseAgent workflow steps for deterministic logic"
```

---

### Task 15: Root Agent Assembly

**Files:**
- Create: `methodic/agent.py`
- Modify: `tests/test_agents.py` (append)

- [ ] **Step 1: Write failing test**

Append to `tests/test_agents.py`:

```python
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents import LoopAgent


def test_root_agent():
    from methodic.agent import root_agent
    assert isinstance(root_agent, SequentialAgent)
    assert root_agent.name == "methodic"
    assert len(root_agent.sub_agents) == 3


def test_interview_loop_has_4_steps():
    from methodic.agent import interview_loop
    assert isinstance(interview_loop, LoopAgent)
    assert interview_loop.max_iterations == 6
    names = [a.name for a in interview_loop.sub_agents]
    assert "interviewer" in names
    assert "participant_sim" in names
    assert "extractor_step" in names
    assert "turn_checker" in names


def test_fieldwork_loop_has_replanner():
    from methodic.agent import fieldwork_loop
    assert isinstance(fieldwork_loop, LoopAgent)
    names = [a.name for a in fieldwork_loop.sub_agents]
    assert "replanner" in names


def test_finalize_has_export():
    from methodic.agent import finalize
    names = [a.name for a in finalize.sub_agents]
    assert "bigquery_export" in names
    assert "quality_reviewer" in names
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_agents.py::test_root_agent -v`
Expected: FAIL

- [ ] **Step 3: Write `methodic/agent.py`**

```python
"""Root agent definition - ADK entry point.

Agent graph (all sub_agents are agent instances, never raw FunctionTools):

root_agent (SequentialAgent)
  +-- study_planner (SequentialAgent)
  |     +-- organizer (LlmAgent)
  |     +-- methodology (LlmAgent)
  |     +-- question_design (LlmAgent)
  |
  +-- fieldwork_loop (LoopAgent, max_iterations=3)
  |     +-- session_runner (SequentialAgent)
  |     |     +-- interview_loop (LoopAgent, max_iterations=6)
  |     |           +-- interviewer (LlmAgent + MCP tools)
  |     |           +-- participant_sim (LlmAgent)
  |     |           +-- extractor_step (custom BaseAgent)
  |     |           +-- turn_checker (custom BaseAgent, escalates)
  |     +-- coverage_step (custom BaseAgent)
  |     +-- replanner (LlmAgent + check_coverage tool, escalates)
  |
  +-- finalize (SequentialAgent)
        +-- quality_reviewer (LlmAgent)
        +-- bigquery_export (custom BaseAgent)
        +-- completion_responder (LlmAgent)
"""

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from methodic import MODEL
from methodic.agents.organizer import organizer_agent
from methodic.agents.methodology import methodology_agent
from methodic.agents.question_design import question_design_agent
from methodic.agents.participant import interviewer_agent
from methodic.agents.participant_sim import participant_sim_agent
from methodic.agents.quality import quality_agent
from methodic.agents.replanner import replanner_agent
from methodic.agents.extractor_step import ExtractorStep
from methodic.agents.turn_checker_step import TurnCheckerStep
from methodic.agents.coverage_step import CoverageStep
from methodic.agents.bigquery_export_step import BigQueryExportStep

# Phase 1: Study Planning
study_planner = SequentialAgent(
    name="study_planner",
    sub_agents=[organizer_agent, methodology_agent, question_design_agent],
)

# Phase 2: Fieldwork Loop
interview_loop = LoopAgent(
    name="interview_loop",
    max_iterations=6,
    sub_agents=[
        interviewer_agent,
        participant_sim_agent,
        ExtractorStep(name="extractor_step"),
        TurnCheckerStep(name="turn_checker", max_turns=6),
    ],
)

session_runner = SequentialAgent(
    name="session_runner",
    sub_agents=[interview_loop],
)

fieldwork_loop = LoopAgent(
    name="fieldwork_loop",
    max_iterations=3,
    sub_agents=[
        session_runner,
        CoverageStep(name="coverage_step"),
        replanner_agent,
    ],
)

# Phase 3: Finalize
completion_responder = Agent(
    name="completion_responder",
    model=MODEL,
    instruction="""Summarize the study results. Include key findings,
coverage achieved, themes, and BigQuery export status.""",
)

finalize = SequentialAgent(
    name="finalize",
    sub_agents=[
        quality_agent,
        BigQueryExportStep(name="bigquery_export"),
        completion_responder,
    ],
)

# Root Agent
root_agent = SequentialAgent(
    name="methodic",
    sub_agents=[study_planner, fieldwork_loop, finalize],
)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_agents.py -v`
Expected: 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add methodic/agent.py tests/test_agents.py
git commit -m "feat(methodic): assemble root agent with custom BaseAgent workflow steps"
```

---

### Task 16: Demo Runner

**Files:**
- Create: `methodic/demo_runner.py`

- [ ] **Step 1: Write `methodic/demo_runner.py`**

```python
"""Demo runner - async orchestrator that invokes root_agent and streams state.

Bridges the gap between /api/demo/run and the ADK agent graph.
Updates the demo session dict with events and coverage snapshots.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)


async def run_demo_pipeline(
    demo_sessions: dict[str, dict],
    study_id: str,
) -> None:
    """Run the full Methodic pipeline as a background task.

    Updates demo_sessions[study_id] with events and coverage as the
    pipeline progresses. Sets status to 'complete' or 'failed'.
    """
    session = demo_sessions.get(study_id)
    if not session:
        return

    try:
        session["events"].append({"step": "request", "status": "done"})

        from methodic.agent import root_agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="methodic_demo",
            session_service=session_service,
        )

        adk_session = await session_service.create_session(
            app_name="methodic_demo",
            user_id="demo_user",
        )

        from google.genai import types

        user_message = types.Content(
            role="user",
            parts=[types.Part(text=(
                "Run a win-loss study on recent Q1 2026 lost deals. "
                "Focus on understanding why deals were lost, especially "
                "around ROI clarity and procurement friction. "
                "Available participants: P-001, P-002, P-003. "
                "Reserve: P-005."
            ))],
        )

        session["events"].append({"step": "pipeline_started", "status": "running"})

        async for event in runner.run_async(
            session_id=adk_session.id,
            user_id="demo_user",
            new_message=user_message,
        ):
            if hasattr(event, "actions") and event.actions:
                step_name = getattr(event, "agent_name", "unknown")
                session["events"].append({"step": step_name, "status": "done"})

            state = getattr(event, "state", None)
            if state and "coverage_state" in state:
                session["coverage"] = state["coverage_state"]

        session["status"] = "complete"
        session["events"].append({"step": "complete", "status": "done"})

    except Exception as e:
        log.exception("Demo pipeline failed: %s", e)
        session["status"] = "failed"
        session["events"].append({
            "step": "error", "status": "failed", "detail": str(e),
        })
```

- [ ] **Step 2: Verify import**

Run: `python3 -c "from methodic.demo_runner import run_demo_pipeline; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add methodic/demo_runner.py
git commit -m "feat(methodic): add demo runner that invokes root_agent pipeline"
```

---

### Task 17: Demo Runner + A2A Card (ADK api_server handles core serving)

**Context (Rev 3):** The Agent Runtime spike proved that ADK `api_server` on Cloud Run
provides `/list-apps`, session CRUD, and `/run_sse` out of the box. We do NOT need a
custom FastAPI server for the core agent loop. What we still need:
1. A `demo_runner.py` that creates a session, sends the study brief, collects SSE events, and
   exposes the before/after state for the demo UI.
2. An A2A-compatible Agent Card at `/.well-known/agent-card.json` (served as a static file).

**Files:**
- Create: `methodic/demo_runner.py`
- Create: `methodic/static/.well-known/agent-card.json`

- [ ] **Step 1: Write `methodic/demo_runner.py`**

```python
"""Demo pipeline runner — drives the ADK agent via InMemoryRunner and collects events for the UI."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from methodic.agent import root_agent

DEMO_STUDY_BRIEF = {
    "deal_id": "DEAL-2024-1847",
    "company_name": "TechCorp Solutions",
    "deal_outcome": "lost",
    "deal_stage": "Final Evaluation",
    "competitors_mentioned": ["CompetitorA"],
    "participants": [
        {"id": "P-001", "role": "VP Finance", "segment": "lost_deal_economic_buyer"},
        {"id": "P-002", "role": "Director of Engineering", "segment": "lost_deal_technical_evaluator"},
    ],
}


async def run_demo_pipeline(state_store: dict[str, dict], study_id: str) -> None:
    session_service = InMemorySessionService()
    runner = InMemoryRunner(agent=root_agent, app_name="methodic", session_service=session_service)
    session = await session_service.create_session(app_name="methodic", user_id="demo-user")

    user_msg = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps({"study_brief": DEMO_STUDY_BRIEF}))],
    )

    state_store[study_id]["status"] = "running"
    events: list[dict[str, Any]] = []

    async for event in runner.run_async(
        user_id="demo-user", session_id=session.id, new_message=user_msg
    ):
        evt = {
            "author": getattr(event, "author", "unknown"),
            "id": getattr(event, "id", None),
            "timestamp": getattr(event, "timestamp", None),
        }
        if hasattr(event, "content") and event.content and event.content.parts:
            evt["text"] = event.content.parts[0].text if event.content.parts[0].text else None
        if hasattr(event, "actions") and event.actions:
            sd = event.actions.state_delta
            if sd:
                evt["state_keys"] = list(sd.keys())
                if "coverage_state" in sd:
                    state_store[study_id]["coverage"] = sd["coverage_state"]
        events.append(evt)
        state_store[study_id]["events"] = events

    state_store[study_id]["status"] = "complete"
```

- [ ] **Step 2: Write A2A Agent Card**

Create `methodic/static/.well-known/agent-card.json`:
```json
{
  "name": "methodic",
  "description": "Autonomous B2B win-loss research agent. Accepts study requests, conducts governed participant interviews, returns evidence-linked structured data.",
  "version": "1.0.0",
  "url": "https://methodic-2030382823.us-central1.run.app",
  "capabilities": {},
  "supportedInterfaces": ["text"],
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain", "application/json"],
  "skills": [{
    "id": "win_loss_study",
    "name": "Win-Loss Study",
    "description": "Conduct a B2B win-loss research study with methodology review, adaptive interviews, and BigQuery export",
    "tags": ["research", "b2b", "win-loss"]
  }]
}
```

- [ ] **Step 3: Verify demo_runner imports**

Run: `python3 -c "from methodic.demo_runner import run_demo_pipeline, DEMO_STUDY_BRIEF; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add methodic/demo_runner.py methodic/static/.well-known/agent-card.json
git commit -m "feat(methodic): add demo runner and A2A agent card"
```

---

### Task 18: Demo UI Page

**Files:**
- Create: `methodic/static/demo.html`

- [ ] **Step 1: Write demo.html**

Create a single-page demo UI with three panels. Use vanilla HTML/CSS/JS with safe DOM methods (createElement, textContent - no innerHTML with dynamic data).

Layout:
- Header: "Methodic - Autonomous Win-Loss Research" + status badge
- Top split: static survey baseline (left) vs live conversation (right)
- Middle: 8 coverage bars showing variable states
- Bottom: step timeline
- Controls: Run Demo + Human Mode toggle

CSS: Dark theme, grid layout. JS: polls `/api/demo/{study_id}/coverage`, `/api/demo/{study_id}/events`, `/api/demo/{study_id}/status`.

All DOM updates via `document.createElement()` + `textContent`. Status badge updates via `textContent`.

- [ ] **Step 2: Verify file exists and is valid**

Run: `python3 -c "p = __import__('pathlib').Path('methodic/static/demo.html'); assert p.exists(); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add methodic/static/demo.html
git commit -m "feat(methodic): add split-screen demo UI overlay"
```

---

### Task 19: Dockerfile for Cloud Run (ADK api_server)

**Context (Rev 3):** Agent Runtime spike proved local Docker build + push to Artifact Registry
works. Cloud Build (both `adk deploy cloud_run` and `gcloud run deploy --source`) fails with
opaque errors. The Dockerfile uses ADK `api_server` as the entrypoint (not custom FastAPI).
Node.js is required for MCP stdio subprocess (`scripts/wp6_mcp_server.py` is Python but
McpToolset may spawn node-based MCP servers in future; include node for safety).

**Files:**
- Create: `Dockerfile.cloudrun`

- [ ] **Step 1: Write `Dockerfile.cloudrun`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm && rm -rf /var/lib/apt/lists/*

USER appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

ENV GOOGLE_GENAI_USE_VERTEXAI=1
ENV GOOGLE_CLOUD_PROJECT=methodic-ai-challenge
ENV GOOGLE_CLOUD_LOCATION=us-central1

COPY --chown=appuser:appuser methodic/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir google-adk==1.32.0 -r /tmp/requirements.txt

COPY --chown=appuser:appuser agents/methodic/ /app/agents/methodic/
COPY --chown=appuser:appuser scripts/wp6_mcp_server.py /app/scripts/wp6_mcp_server.py
COPY --chown=appuser:appuser fixtures/ /app/fixtures/
COPY --chown=appuser:appuser docs/schema/ /app/docs/schema/

EXPOSE 8000

CMD ["sh", "-c", "adk api_server --port=${PORT:-8000} --host=0.0.0.0 /app/agents"]
```

- [ ] **Step 2: Verify Dockerfile parses**

Run: `python3 -c "d = __import__('pathlib').Path('Dockerfile.cloudrun').read_text(); assert 'adk api_server' in d; assert 'GOOGLE_GENAI_USE_VERTEXAI' in d; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Build locally**

```bash
docker build --platform linux/amd64 -f Dockerfile.cloudrun \
  -t us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1 .
```

- [ ] **Step 4: Push to Artifact Registry**

```bash
docker push us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1
```

- [ ] **Step 5: Deploy to Cloud Run**

```bash
gcloud run deploy methodic \
  --image=us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1 \
  --project=methodic-ai-challenge --region=us-central1 \
  --port=8000 --max-instances=1 --memory=1Gi \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=methodic-ai-challenge,GOOGLE_CLOUD_LOCATION=us-central1
```

- [ ] **Step 6: Commit**

```bash
git add Dockerfile.cloudrun
git commit -m "feat(methodic): add Cloud Run Dockerfile with ADK api_server entrypoint"
```

---

### Task 20: Integration Smoke Tests

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write `tests/test_integration.py`**

```python
"""Integration smoke tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_root_agent_graph():
    from methodic.agent import root_agent, study_planner, fieldwork_loop, finalize, interview_loop
    assert root_agent.name == "methodic"
    assert len(root_agent.sub_agents) == 3
    assert study_planner.name == "study_planner"
    assert len(study_planner.sub_agents) == 3
    assert fieldwork_loop.max_iterations == 3
    assert interview_loop.max_iterations == 6
    assert len(interview_loop.sub_agents) == 4
    assert len(finalize.sub_agents) == 3


@pytest.mark.asyncio
async def test_mcp_server_lists_both_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(REPO_ROOT / "scripts" / "wp6_mcp_server.py")],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            assert "lookup_deal_context" in names
            assert "lookup_trial_telemetry" in names


def test_coverage_checker_with_fixture_data():
    from methodic.tools.coverage_checker import check_coverage
    from methodic.schemas import (
        ParticipantResponse, StructuredFields, QualityMetrics, EvidenceItem,
    )

    p001 = ParticipantResponse(
        participant_id="P-001", study_id="STUDY-DEMO",
        segment="lost_deal_economic_buyer", persona_summary="VP Finance",
        conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason="budget_timing",
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="unknown", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.92},
        coverage_state={
            "primary_loss_reason": "covered_high_confidence",
            "procurement_friction": "missing",
        },
        quality=QualityMetrics(variable_coverage=0.75, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )
    result = check_coverage([p001])
    assert result["per_variable"]["primary_loss_reason"] == "covered_high_confidence"
    assert "procurement_friction" in result["missing_variables"]


def test_bigquery_export_dry_run():
    from methodic.tools.bigquery_export import export_to_bigquery
    from methodic.schemas import (
        ParticipantResponse, StructuredFields, QualityMetrics,
    )
    r = ParticipantResponse(
        participant_id="P-001", study_id="STUDY-DEMO", segment="lost",
        persona_summary="VP", conversation_status="complete",
        structured_fields=StructuredFields(
            primary_loss_reason="unclear_roi", secondary_loss_reason=None,
            roi_clarity="unclear", budget_timing="out_of_cycle",
            procurement_friction="none", security_concern="none",
            competitor_pressure="none", aha_moment_reached="no",
        ),
        field_confidence={"primary_loss_reason": 0.92},
        coverage_state={"primary_loss_reason": "covered_high_confidence"},
        quality=QualityMetrics(variable_coverage=0.75, ambiguity_resolved=True,
                                evidence_linked=True, requires_recontact=False),
        evidence=[], unresolved_ambiguities=[],
    )
    result = export_to_bigquery([r], dry_run=True)
    assert result["dry_run"] is True
    assert result["rows_written"] == 1
    assert result["rows"][0]["primary_loss_reason"] == "unclear_roi"


def test_server_has_a2a_card():
    from methodic.server import app
    paths = [r.path for r in app.routes if hasattr(r, 'path')]
    assert "/.well-known/agent-card.json" in paths
    assert "/api/demo/run" in paths
    assert "/api/demo/{study_id}/status" in paths


def test_turn_checker_exits_loop():
    from methodic.agents.turn_checker_step import TurnCheckerStep
    from methodic.schemas import CANONICAL_FIELDS
    step = TurnCheckerStep(name="tc", max_turns=6)
    assert step.should_escalate({"turn_count": 6}) is True
    assert step.should_escalate({"turn_count": 2}) is False
    assert step.should_escalate({
        "turn_count": 1,
        "participant_coverage": {f: "covered_high_confidence" for f in CANONICAL_FIELDS},
    }) is True
```

- [ ] **Step 2: Run integration tests**

Run: `python3 -m pytest tests/test_integration.py -v`
Expected: 7 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test(methodic): add integration smoke tests with loop exit verification"
```

---

### Task 21: End-to-End Verification (Cloud Run)

**Context (Rev 3):** Verification targets the deployed Cloud Run service, not a local server.
Auth is required (org policy blocks allUsers). ADK api_server provides the core endpoints.

**Files:** None new (verification only)

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest tests/ -v --tb=short`
Expected: All tests PASS (~45 total)

- [ ] **Step 2: Validate schemas**

Run:
```bash
python3 scripts/validate_schemas.py docs/schema/
python3 scripts/validate_fixtures.py
```
Expected: Both pass

- [ ] **Step 3: Test Cloud Run — list agents**

```bash
TOKEN=$(gcloud auth print-identity-token)
curl -s -H "Authorization: Bearer $TOKEN" https://methodic-2030382823.us-central1.run.app/list-apps
```
Expected: `["methodic"]`

- [ ] **Step 4: Test Cloud Run — create session**

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  https://methodic-2030382823.us-central1.run.app/apps/methodic/users/test/sessions -d '{}'
```
Expected: JSON with `id`, `appName`, `userId`

- [ ] **Step 5: Test Cloud Run — agent query via SSE**

```bash
SESSION_ID=<from step 4>
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  https://methodic-2030382823.us-central1.run.app/run_sse \
  -d '{"app_name":"methodic","user_id":"test","session_id":"'$SESSION_ID'","new_message":{"role":"user","parts":[{"text":"{\"study_brief\":{\"deal_id\":\"DEMO-001\"}}"}]}}'
```
Expected: SSE events with `author` fields showing agent handoffs (study_planner, interviewer, etc.)

- [ ] **Step 6: Test A2A Agent Card (static file)**

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://methodic-2030382823.us-central1.run.app/static/.well-known/agent-card.json
```
Expected: A2A 1.0-shaped card with `supportedInterfaces`, `defaultInputModes`

- [ ] **Step 7: Final commit if needed**

```bash
git add -A
git commit -m "fix(methodic): address issues found in end-to-end verification"
```

---

## Post-Plan: Next Steps (not tasks)

1. **Cloud Trace instrumentation**: Add minimal OpenTelemetry for one observability screenshot
2. **ADK Evaluation artifact**: One trajectory file (expected vs actual agent steps)
3. **Prompt engineering iteration**: Refine interviewer_system.md through live Gemini testing on Cloud Run
4. **Demo recording**: 3-4 minute video per challenge spec, using Cloud Run SSE for live agent
5. **Devpost submission**: Write submission text, fill links, submit

**Deployment workflow (proven):**
```bash
docker build --platform linux/amd64 -f Dockerfile.cloudrun -t us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:vN .
docker push us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:vN
gcloud run deploy methodic --image=...methodic:vN --project=methodic-ai-challenge --region=us-central1 --port=8000
```
