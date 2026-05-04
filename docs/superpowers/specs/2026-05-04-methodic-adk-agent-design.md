# Methodic ADK Agent — Design Spec

**Date:** 2026-05-04
**Status:** Approved design, pending implementation
**Challenge:** Google for Startups AI Agent Challenge (Track 1: Build)
**Deadline:** 2026-06-05 17:00 PT

## Summary

Replace the current fixture-replay demo pipeline with a real multi-agent system built on Google ADK. The system uses Gemini for live conversations, MCP for tool access, A2A for agent interoperability, Cloud Run for deployment, and BigQuery for structured export. Existing fixtures become regression test cases.

## Key Decisions

| Decision | Choice |
|----------|--------|
| Framework | Google ADK (`pip install google-adk`) |
| Model | `gemini-3.1-pro-preview` everywhere |
| MCP | Reuse + extend `wp6_mcp_server.py` via `McpToolset` |
| A2A | `to_a2a()` — real A2A protocol |
| Deployment | Cloud Run via custom Dockerfile + `get_fast_api_app()` |
| BigQuery | Real writes, dataset-scoped IAM |
| Participant sim | Hybrid: Gemini simulation default, human input toggle |
| UI | ADK web chat + custom demo overlay HTML |
| Existing code | Keep as fixtures/validators/fallback |

---

## 1. Project Structure & Dependencies

### Directory Layout

```
methodic/                          # NEW — ADK agent package
  __init__.py
  agent.py                         # root_agent definition (ADK entry point)
  agents/
    __init__.py
    organizer.py                   # LlmAgent — request intake + clarification
    methodology.py                 # LlmAgent — pushback on bad methodology
    question_design.py             # LlmAgent — maps questions to variables
    participant.py                 # LlmAgent — conducts interviews
    participant_sim.py             # LlmAgent — simulates participant responses
    quality.py                     # LlmAgent (light) — contradiction/theme review
    replanner.py                   # LlmAgent — decides if more sessions needed
  tools/
    __init__.py
    deal_context.py                # McpToolset wrapping wp6_mcp_server.py
    quality_scorer.py              # FunctionTool — deterministic scoring logic
    bigquery_export.py             # FunctionTool — writes rows to BigQuery
    coverage_checker.py            # FunctionTool — computes variable coverage state
  schemas.py                       # Pydantic models mirroring JSON schemas
  prompts/
    interviewer_system.md          # System prompt for participant agent
    methodology_system.md          # System prompt for methodology agent
    sim_participant_system.md      # System prompt for simulated participant
  server.py                        # Custom FastAPI overlay
  static/
    demo.html                      # Split-screen + coverage dashboard page

scripts/                           # KEEP — legacy fixture pipeline + validators
fixtures/                          # KEEP — test data + regression expectations
docs/schema/                       # KEEP — canonical JSON schemas
```

### Dependencies

```
google-adk>=1.0.0
google-cloud-bigquery>=3.20.0
pydantic>=2.0
uvicorn>=0.30.0
fastapi>=0.110.0
jsonschema>=4.0
mcp>=1.23.3
```

### Design Note: Pydantic + JSON Schema

The JSON schemas in `docs/schema/` remain the canonical contract for fixtures, exports, and cross-agent validation. The Pydantic models in `schemas.py` mirror these for ADK runtime use: Gemini structured output typing, tool input/output validation, and session state serialization. One source of truth (JSON Schema), one runtime convenience layer (Pydantic).

---

## 2. Agent Architecture & Orchestration

### Agent Graph

```
root_agent (SequentialAgent)
  ├── study_planner (SequentialAgent)
  │     ├── organizer (LlmAgent)           — gemini-3.1-pro-preview
  │     ├── methodology (LlmAgent)         — gemini-3.1-pro-preview
  │     └── question_design (LlmAgent)     — gemini-3.1-pro-preview
  │
  ├── fieldwork_loop (LoopAgent, max_iterations=3)
  │     ├── session_runner (ParallelAgent)
  │     │     └── interview_loop (LoopAgent, max_iterations=12) ×N participants
  │     │           ├── interviewer (LlmAgent)      + McpToolset
  │     │           ├── participant_sim (LlmAgent)   [or human input]
  │     │           ├── extractor (FunctionTool)     structured field extraction
  │     │           └── turn_checker (FunctionTool)  escalates when done
  │     │
  │     ├── coverage_checker (FunctionTool) — deterministic, no LLM
  │     └── replanner (LlmAgent)           — escalates when coverage sufficient
  │
  └── finalize (SequentialAgent)
        ├── quality_reviewer (LlmAgent)
        ├── bigquery_export (FunctionTool)
        └── completion_responder (LlmAgent)
```

### Model Assignment

All agents use `gemini-3.1-pro-preview`. Model ID defined as a single constant for easy swapping:

```python
MODEL = "gemini-3.1-pro-preview"
```

If latency becomes an issue for high-volume conversation turns, swap interviewer/sim to `gemini-3.1-flash-lite-preview` in one line.

### State Flow Between Agents

ADK agents share state through the `InvocationContext` session state dict. Each agent writes output to a named key via `output_key`:

| Agent | Reads | Writes (`output_key`) |
|-------|-------|----------------------|
| `organizer` | user message | `study_brief` |
| `methodology` | `study_brief` | `methodology_review` |
| `question_design` | `study_brief`, `methodology_review` | `question_pool` |
| `interviewer` | `question_pool`, `study_brief`, persona metadata | `participant_responses` (appends) |
| `coverage_checker` | `participant_responses` | `coverage_state` |
| `replanner` | `coverage_state`, `participant_responses` | `replan_decision` (or escalates) |
| `quality_reviewer` | `participant_responses`, `coverage_state` | `quality_report` |
| `bigquery_export` | `participant_responses`, `quality_report` | `export_result` |
| `completion_responder` | all of the above | final user/A2A response |

### Interview Loop Pattern

Each participant session is a `LoopAgent` (max 12 turns) containing:

1. **`interviewer`** (LlmAgent) — asks the next question or calls an MCP tool
2. **`participant_sim`** (LlmAgent) — responds in character using persona fixture data as personality seed. In human mode, replaced by a passthrough that reads from the chat UI.
3. **`extractor`** (FunctionTool) — calls Gemini with `response_schema` to extract structured fields from the latest turn pair
4. **`turn_checker`** (FunctionTool) — evaluates coverage state for this participant; sets `tool_context.actions.escalate = True` when all target variables are `covered_high_confidence`, max turns reached, or participant disengaged

### LoopAgent Exit Mechanics

ADK's `LoopAgent` has no built-in exit condition. It runs sub-agents repeatedly until `max_iterations` or a sub-agent calls `tool_context.actions.escalate = True`. The `turn_checker` and `replanner` are the agents responsible for triggering escalation. Exit logic is deterministic and testable — not buried in LLM reasoning.

---

## 3. MCP Tools & FunctionTools

### MCP Tools (via McpToolset)

Reuse and extend the existing `wp6_mcp_server.py`:

**Tool 1: `lookup_deal_context`** (existing)
- Input: `participant_id`
- Output: `{ deal_stage, persona, trial_usage, crm_notes }`
- Source: fixture CRM + telemetry data
- Served via stdio MCP server (JSON-RPC 2.0)

**Tool 2: `lookup_trial_telemetry`** (new, same MCP server)
- Input: `participant_id`
- Output: `{ login_count, features_used, report_builder_reached, executive_logins }`
- Source: fixture telemetry data
- Enables the "I can see from approved trial telemetry..." triangulation moment

ADK integration:

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

deal_context_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[str(REPO_ROOT / "scripts" / "wp6_mcp_server.py")],
        ),
    ),
    tool_filter=["lookup_deal_context", "lookup_trial_telemetry"],
)
```

### FunctionTools (Python functions registered with ADK)

**Tool 3: `check_coverage`**
- Input: list of participant responses so far
- Output: per-variable coverage state + overall coverage fraction
- Logic: deterministic (reuses WP7 scoring rules), no LLM
- Used by: `turn_checker`, `replanner`

**Tool 4: `extract_structured_fields`** (referenced as `extractor` in the agent graph)
- Input: conversation transcript, question pool, variable definitions
- Output: `ParticipantResponse` (Pydantic model matching canonical schema)
- Logic: internally calls Gemini with `response_schema` for strict JSON extraction
- Returns confidence scores based on evidence strength
- Design note: this is a FunctionTool (not an LlmAgent) because Gemini's structured output mode is a single-shot generation call, not a multi-turn conversation. Wrapping it as a tool lets the interviewer call it after each turn and use the result to decide what to ask next.

**Tool 5: `export_to_bigquery`**
- Input: list of `ParticipantResponse` records, quality report
- Output: `{ rows_written, table_name, dataset }`
- Logic: uses `google-cloud-bigquery` client
- Has a `dry_run` parameter for local testing

### Tool Access Policy

| Agent | Tools Available |
|-------|---------------|
| Interviewer | `lookup_deal_context`, `lookup_trial_telemetry`, `extract_structured_fields` |
| Replanner | `check_coverage` |
| Quality Reviewer | `check_coverage` |
| Finalize | `export_to_bigquery` |
| All others | None (pure reasoning) |

---

## 4. A2A, Deployment & Serving

### A2A Endpoint

One function wraps the root agent as a compliant A2A server:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

a2a_app = to_a2a(root_agent, port=8080, agent_card=custom_card)
```

Custom Agent Card:

```json
{
  "name": "methodic",
  "description": "Autonomous B2B win-loss research agent. Accepts study requests, conducts governed participant interviews, returns evidence-linked structured data.",
  "version": "1.0.0",
  "capabilities": {},
  "skills": [
    {
      "name": "win_loss_study",
      "description": "Conduct a B2B win-loss research study with methodology review, adaptive interviews, and BigQuery export"
    }
  ],
  "default_input_modes": ["text/plain"],
  "default_output_modes": ["text/plain", "application/json"]
}
```

Served at `/.well-known/agent.json`. The mocked Sales Insights agent hits the A2A endpoint with a `request_study` message. Methodic responds through the standard A2A task lifecycle: clarification → acceptance → progress → completion with structured data.

### Serving Architecture

Two surfaces from one process (Cloud Run exposes one port):

```
Port 8080 ($PORT)
  ├── A2A protocol
  │     ├── /.well-known/agent.json    — Agent Card discovery
  │     └── A2A message handling        — via to_a2a()
  │
  └── ADK web + custom overlay
        ├── /                          — ADK chat interface
        ├── /api/*                     — ADK session API
        ├── /api/demo/run              — Custom: trigger full demo pipeline
        ├── /api/demo/{id}/coverage    — Custom: coverage state polling
        ├── /api/demo/{id}/events      — Custom: event timeline
        └── /static/demo.html          — Custom: split-screen overlay page
```

Implementation:

```python
from google.adk.cli.fast_api import get_fast_api_app
from fastapi.staticfiles import StaticFiles

app = get_fast_api_app(
    agents_dir="./methodic",
    session_service_uri="sqlite+aiosqlite:///./sessions.db",
    allow_origins=["*"],
    web=True,
)

app.mount("/static", StaticFiles(directory="methodic/static"), name="static")

@app.get("/api/demo/run")
async def run_demo(): ...

@app.get("/api/demo/{study_id}/coverage")
async def get_coverage(study_id: str): ...

@app.get("/api/demo/{study_id}/events")
async def get_events(study_id: str): ...
```

### Cloud Run Deployment

Custom Dockerfile (needed for overlay routes):

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "methodic.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

If `adk deploy cloud_run` supports mounting custom routes, use that instead. Try Option A first, fall back to custom Dockerfile.

### A2A + FastAPI Composition Note

`to_a2a()` returns an ASGI app and `get_fast_api_app()` returns a FastAPI app. These are separate ASGI apps. Two composition strategies, tried in order:

1. **Preferred:** Mount the A2A ASGI app as a sub-application on the FastAPI app via `app.mount("/a2a", a2a_app)`. The Agent Card route (`/.well-known/agent.json`) may need a manual FastAPI route to proxy to the A2A app.
2. **Fallback:** Run them on separate ports (8080 for FastAPI/ADK web, 8081 for A2A) behind a Cloud Run sidecar or reverse proxy. More complex but guaranteed to work.

Discovery during implementation will determine which works. Budget 1 day for this integration.

### Environment Variables

```
GOOGLE_API_KEY=<gemini-api-key>
GOOGLE_CLOUD_PROJECT=<project-id>
BIGQUERY_DATASET=methodic_demo
BIGQUERY_DRY_RUN=false
```

### BigQuery Setup

Reuse existing `docs/schema/bigquery-table.sql`. Service account gets:
- `roles/bigquery.dataEditor` scoped to the `methodic_demo` dataset
- `roles/bigquery.jobUser` on the project

Least-privilege: dataset scope, not project scope.

---

## 5. Demo UI & Testing

### Demo Overlay Page

A single `demo.html` page at `/static/demo.html`. Not a full SPA — a focused demo view that polls custom API endpoints.

Three-panel layout:

1. **Split-screen comparison** (top): Static survey (left) vs Methodic conversation (right). Static side shows fixture baseline data. Methodic side streams live conversation turns including MCP tool calls.

2. **Coverage dashboard** (middle): Eight horizontal progress bars, one per required variable. Each shows coverage state (missing/ambiguous/low/high) and confidence score. Highlights the `procurement_friction` ambiguity that triggers replan.

3. **Event timeline** (bottom): Horizontal flow showing agent handoffs: request → clarification → methodology_pushback → question_pool → P-001 → P-002 → P-003 → coverage_check → replan → P-005 → quality → export → completion.

Human mode toggle: button switches participant input from Gemini simulation to a text input field. Lets judges type real answers and see the agent adapt.

Implementation: vanilla HTML + CSS + JS. No build step, no framework. Polls `/api/demo/{study_id}/coverage` and `/api/demo/{study_id}/events`.

### Testing Strategy

**Layer 1: Schema validation (existing)**

```bash
python3 scripts/validate_schemas.py docs/schema/
```

Run after any schema change.

**Layer 2: Fixture regression (existing + new)**

```bash
python3 scripts/validate_fixtures.py
```

Existing validator checks fixture integrity. New addition: run the real ADK pipeline on fixture personas in simulated mode, validate output against canonical schema, check that structured field values are plausible (e.g., P-001 extracts `unclear_roi`, not `security_concern`).

**Layer 3: Integration smoke test (new)**

```bash
python3 -m pytest tests/test_integration.py
```

- Start MCP server, run one interview loop on P-001
- Validate ParticipantResponse against JSON schema
- Check at least one MCP tool call occurred
- Check coverage_state has no "missing" for P-001's known variables
- Runs in ~30 seconds

**Layer 4: Deployment smoke test (updated)**

```bash
python3 scripts/wp9_deployment_smoke.py --url https://methodic-HASH.run.app
```

Update existing smoke test to hit real Cloud Run URL.

---

## 6. Canonical Schemas

The following schemas are the source of truth. All agent outputs must validate against them.

### Participant Response Schema

Located at `docs/schema/participant-response.schema.json`. Key fields:

- `participant_id`, `study_id`, `segment`, `persona_summary`
- `conversation_status`: `complete | partial | excluded | static_form`
- `structured_fields`: 8 canonical variables with enum-constrained values
  - `primary_loss_reason`: `unclear_roi | budget_timing | procurement_friction | security_concern | competitor_pressure | missing_feature | economic_buyer_gap | other | unknown`
  - `secondary_loss_reason`: free string or null
  - `roi_clarity`: `clear | partially_clear | unclear | unknown`
  - `budget_timing`: `in_cycle | out_of_cycle | unknown`
  - `procurement_friction`: `none | low | medium | high | unknown`
  - `security_concern`: `none | low | medium | high | unknown`
  - `competitor_pressure`: `none | named_competitor | unknown`
  - `aha_moment_reached`: `yes | no | unknown`
- `field_confidence`: map of variable → float [0.0, 1.0]
- `coverage_state`: map of variable → `missing | ambiguous | covered_low_confidence | covered_high_confidence`
- `quality`: `{ variable_coverage, ambiguity_resolved, evidence_linked, requires_recontact }`
- `evidence`: array of `{ field, quote, transcript_turn_id, context_used[] }`
- `unresolved_ambiguities`: array of variable names

### Guardrail Event Schema

Located at `docs/schema/guardrail-event.schema.json`. Covers: vague answer recovery, contradiction detection, disengagement, scope violation.

### BigQuery Table Schema

Located at `docs/schema/bigquery-table.sql`. Maps ParticipantResponse to BigQuery columns.

---

## 7. Personas & Demo Flow

### Primary Personas (live in demo)

| ID | Segment | Role | Initial Answer | Underlying Reason | Methodic Outcome |
|----|---------|------|---------------|-------------------|-----------------|
| P-001 | lost_deal_economic_buyer | VP Finance | "Price was too high" | ROI unclear + budget closed | `unclear_roi` + `budget_timing` |
| P-002 | lost_deal_champion | RevOps Manager | "Security slowed us down" | Procurement/vendor consolidation unclear | `procurement_friction` = ambiguous |
| P-003 | slipping_deal_champion | Sales Ops Lead | "We are still interested" | No exec sponsor, can't prove ROI | `unclear_roi` + `economic_buyer_gap` |

### Reserve Persona (triggered by replan)

| ID | Segment | Role | Initial Answer | Underlying Reason | Methodic Outcome |
|----|---------|------|---------------|-------------------|-----------------|
| P-005 | slipping_deal_procurement | Procurement Lead | "Evaluation got stuck" | Vendor consolidation, weak ROI evidence | `procurement_friction` = high |

### Demo Narrative

1. Sales Insights agent sends `request_study` via A2A
2. Methodic asks clarification ("packaging, ROI messaging, or both?")
3. Organizer drafts research brief with 7 required variables
4. Methodology agent pushes back on champion-only sampling
5. Question design agent maps 8 questions to variables
6. P-001, P-002, P-003 interviewed (parallel or sequential)
7. Coverage check: `procurement_friction` remains ambiguous
8. Replanner adds P-005 (reserve procurement stakeholder)
9. P-005 resolves `procurement_friction` to `high`
10. Quality report: Methodic 7/8 high-confidence vs static 0/8
11. BigQuery export: 4 rows written
12. Completion response to Sales Insights agent via A2A

---

## 8. Explicitly Out of Scope

- User authentication (demo is unauthenticated)
- Multi-tenant study management
- Real participant recruitment
- Persistent study database beyond SQLite session store
- Statistical significance claims
- Vertex AI Search grounding
- Agent Engine Sessions or Memory Bank
- Marketing landing page
- Full production A2A compliance testing (we implement it, but don't formally certify)
- Support for models other than Gemini
- Mobile or responsive UI (desktop demo only)
