# Methodic

Autonomous research operations agent that turns B2B business decisions into governed, evidence-linked data.

**Track 1: Build — Net-New Agents** | Google for Startups AI Agent Challenge

## What Methodic Does

Static B2B surveys produce shallow answers like "price." Methodic replaces them with an autonomous workflow that:

1. **Accepts external agent requests** and asks clarifying questions before proceeding
2. **Pushes back on bad methodology** — corrects biased sampling before any data is collected
3. **Conducts adaptive conversations** that probe vague answers into decision-relevant variables
4. **Uses MCP to triangulate** CRM and telemetry context through a real server boundary
5. **Tracks coverage and autonomously re-plans** when measurement gaps remain
6. **Exports structured data** to BigQuery with full evidence traceability

Result: **+69% quality improvement** over static surveys (same rubric, same participants).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python3 scripts/wp3_organizer_flow.py --output /tmp/wp3.json
python3 scripts/wp4_methodology_review.py --mode fallback --output /tmp/wp4.json
python3 scripts/wp5_conversation_engine.py --output-responses /tmp/wp5r.json --output-coverage /tmp/wp5c.json
python3 scripts/wp6_mcp_boundary.py --output /tmp/wp6.json
python3 scripts/wp7_data_quality.py --output-report /tmp/wp7.json --output-csv /tmp/wp7.csv --output-bigquery /tmp/wp7bq.json
python3 scripts/wp8_replan_trigger.py --output /tmp/wp8.json
python3 scripts/wp9a_bigquery_export.py --dry-run --output /tmp/wp9a.json
```

## Container Demo

```bash
# Build and run the Docker container
docker build -t methodic-demo .
docker run -p 8080:8080 methodic-demo

# Hit the demo endpoint (runs all 7 work packages)
curl http://localhost:8080/demo | jq .

# Or run the automated smoke test
python3 scripts/wp9_deployment_smoke.py
```

## Architecture

```
External Agent ──► Organizer (WP3) ──► Methodology (WP4) ──► Conversations (WP5)
                                                                    │
                                                              MCP Server (WP6)
                                                            lookup_deal_context
                                                                    │
                                                              Quality (WP7) ──► Re-Plan (WP8)
                                                                    │
                                                              BigQuery (WP9a)
```

**Stack:** Gemini API · MCP (stdio JSON-RPC 2.0) · Docker · Cloud Run (deployment-ready) · BigQuery (dry-run validated)

See [docs/architecture-diagram.md](docs/architecture-diagram.md) for full Mermaid diagrams.

## Project Structure

```
scripts/
  wp3_organizer_flow.py        # External request → clarification → brief → approval
  wp4_methodology_review.py    # Methodology pushback + question design (live Gemini or fallback)
  wp5_conversation_engine.py   # Interactive participant conversations + coverage tracking
  wp6_mcp_server.py            # MCP server: lookup_deal_context (CRM + telemetry)
  wp6_mcp_boundary.py          # MCP client harness + trace writer
  wp7_data_quality.py          # 4-dimension quality rubric + static vs Methodic comparison
  wp8_replan_trigger.py        # Autonomous re-plan for unresolved coverage gaps
  wp9_demo_server.py           # Cloud Run HTTP server orchestrating all steps
  wp9_deployment_smoke.py      # Docker build + container smoke test
  wp9a_bigquery_export.py      # BigQuery schema validation + dry-run export
  validate_schemas.py          # JSON Schema validator
  validate_fixtures.py         # Fixture integrity checker

fixtures/                      # Deterministic test data (CRM, telemetry, participants, traces)
docs/schema/                   # Canonical JSON Schemas (participant-response, etc.)
docs/                          # Design docs, delivery plan, storyboard, submission materials
Dockerfile                     # Container config (node:20-alpine + Python 3)
```

## Key Artifacts

| File | What It Proves |
|------|---------------|
| `fixtures/wp4_methodology_package.json` | Methodology pushback: 4 corrections, biased sample revised |
| `fixtures/wp6_mcp_trace.json` | Real MCP boundary: 3 calls, stdio JSON-RPC 2.0, field filtering verified |
| `fixtures/wp7_quality_report.json` | Quality delta: Methodic 0.761 vs static 0.069 (+0.692) |
| `fixtures/wp8_replan_trace.json` | Autonomous re-plan: procurement_friction → P-005 → resolved |
| `fixtures/wp9_deployment_trace.json` | Container proof: 7/7 steps pass in local_container mode |
| `fixtures/wp9a_bigquery_export_trace.json` | BigQuery schema: 17 fields, 6 rows validated |

## Honest Labels

Every trace artifact includes an `honest_label` field stating exactly what it proves and what it doesn't. The container runs locally (not on live Cloud Run), WP4 uses deterministic fallback without API keys, and BigQuery exports are dry-run validated. See [docs/limitations.md](docs/limitations.md) for the full list.

## Submission Materials

- [Demo Script](docs/demo-script.md) — 3:30 voiceover + on-screen actions
- [Video Shot List](docs/video-shot-list.md) — Recording plan
- [Rehearsal Checklist](docs/rehearsal-checklist.md) — B1-B9 proof beats → evidence mapping
- [Architecture Diagram](docs/architecture-diagram.md) — Mermaid source
- [Limitations](docs/limitations.md) — What the prototype does and doesn't prove
- [Devpost Copy](docs/devpost-copy.md) — Submission form text
- [Judge Storyboard](docs/judge-storyboard.md) — Narrative design for the demo video
- [Delivery Plan](docs/delivery-plan.md) — Full task graph with proof beats and gates
