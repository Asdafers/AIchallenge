# Methodic

Autonomous research operations agent that turns B2B business decisions into governed, evidence-linked data.

**Track 1: Build — Net-New Agents** | Google for Startups AI Agent Challenge

## What Methodic Does

Static B2B surveys produce shallow answers like "price." Methodic replaces them with an autonomous multi-agent workflow:

1. **Plans the study** — organizer + methodology agents structure objectives and push back on sampling bias
2. **Conducts adaptive interviews** — probes vague answers into specific decision variables in real time
3. **Triangulates against CRM context** — MCP tools pull deal and telemetry data mid-interview
4. **Tracks coverage and autonomously re-plans** — identifies gaps across 8 canonical research variables
5. **Exports structured data** — evidence-linked rows with confidence scores directly to BigQuery

Result: **+0.692 composite quality improvement** over static surveys (same rubric, same participants; coverage from 16.7% to 100% across 8 research variables).

## Live Demo

**Cloud Run:** https://methodic-2030382823.us-central1.run.app

- Demo UI: `/static/demo.html` — watch the full pipeline run autonomously
- Interactive mode: `/static/interactive.html` — participate as the interview subject
- Agent card: `/.well-known/agent-card.json`

## Quick Start (Local)

```bash
pip install -r requirements.txt
uvicorn methodic.server:app --port 8080
# Open http://localhost:8080/static/demo.html
```

## Architecture

```
SequentialAgent (root)
├── plan_phase (SequentialAgent)
│   ├── session_init (BaseAgent)
│   ├── organizer (LlmAgent)
│   ├── methodology (LlmAgent)
│   └── question_design (LlmAgent)
├── fieldwork (LoopAgent, max_iterations=3)
│   └── fieldwork_body (SequentialAgent)
│       ├── interviewer (LlmAgent)
│       ├── participant_sim (LlmAgent, demo mode)
│       ├── extractor_step (BaseAgent)
│       ├── turn_checker (BaseAgent)
│       ├── coverage_assessment (BaseAgent)
│       └── replan_step (BaseAgent)
└── finalize (SequentialAgent)
    ├── quality_reviewer (LlmAgent)
    ├── bigquery_export (BaseAgent)
    └── completion (LlmAgent)
```

**Stack:** Google ADK · Gemini 3.1 Pro · MCP (stdio JSON-RPC 2.0) · FastAPI · Cloud Run · BigQuery · Vertex AI

## Project Structure

```
methodic/                  # ADK agent package
  __init__.py              # Model configuration (Gemini 3.1 Pro / Flash)
  agent.py                 # Agent graph (SequentialAgent + LoopAgent)
  server.py                # FastAPI server (SSE streaming, interactive API)
  schemas.py               # Pydantic models (ParticipantResponse, 8 canonical fields)
  agents/                  # Custom BaseAgent steps (extraction, coverage, re-plan, BQ export)
  tools/                   # MCP client, BigQuery export, quality scoring
  static/                  # Demo UI (demo.html) + Interactive UI (interactive.html)
scripts/                   # MCP server, validators, recording, legacy WP scripts
fixtures/                  # Deterministic test data (CRM, telemetry, participants)
tests/                     # 73 unit/integration + 60 Playwright E2E tests
docs/                      # Submission materials, evidence, reviews
```

## Tests

```bash
# All tests
python3 -m pytest tests/ -v

# Unit/integration only
python3 -m pytest tests/ --ignore=tests/e2e -v

# E2E (requires running server)
python3 -m pytest tests/e2e/ -v
```

## Evidence

| Evidence | Status | Source |
|----------|--------|--------|
| Cloud Run health | PASS | `curl /health` |
| 133 tests passing | PASS | `pytest --collect-only` |
| Live SSE stream (25 events) | PASS | [live-run-2026-05-14.md](docs/evidence/live-run-2026-05-14.md) |
| BigQuery live export (3 rows) | PASS | `bq query` on `methodic_demo.win_loss_responses` |
| Agent card | PASS | `/.well-known/agent-card.json` |
| Quality delta (+0.692) | PASS | [Fixture benchmark](fixtures/wp7_quality_report.json) |

## Honest Labels

See [docs/limitations.md](docs/limitations.md) for what the prototype proves and what it does not.

## Submission Materials

- [Devpost Copy](docs/devpost-copy.md)
- [Demo Script](docs/demo-script.md)
- [Limitations](docs/limitations.md)
- [Architecture Diagram](docs/architecture-diagram.md)
