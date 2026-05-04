# Limitations and Honest Labels

Methodic is a vertical-slice prototype built for the Google AI Agent Challenge. This document lists what it does and does not prove, so judges and future developers have an accurate picture.

## What the Prototype Proves

1. **Agentic research workflow** — External request → planning → methodology pushback → interactive conversations → quality scoring → autonomous re-plan → structured export. All steps execute end-to-end.
2. **Real MCP boundary** — `lookup_deal_context` runs through a real MCP server via stdio JSON-RPC 2.0, not a simulated function call. Field filtering is enforced server-side.
3. **Measurable quality delta** — Static surveys and Methodic output are scored by the same 4-dimension rubric. The prototype consistently shows a +0.692 composite improvement.
4. **Container-ready architecture** — Docker image builds and runs, orchestrating all 7 work packages in `local_container` mode. Cloud Run deployment instructions are embedded in the trace.
5. **Autonomous re-plan** — Unresolved `procurement_friction` triggers exactly one targeted follow-up session without human intervention.

## What the Prototype Does Not Prove

### Local Container, Not Live Cloud Run

The demo runs in `local_container` mode (Docker on the developer's machine). It has never been deployed to a live Cloud Run instance. The `honest_label` in every trace artifact says this explicitly. The `operator_steps` section provides exact `gcloud` commands for a real deployment, but execution requires GCP credentials and billing.

### Deterministic Fallback for Methodology (WP4)

When `GEMINI_API_KEY` is absent (e.g., inside the container), WP4 falls back to a deterministic pushback engine. The live Gemini path works when the key is set, but the container demo always uses the fallback. The trace labels this as `methodology_review_source: "deterministic_fallback"`.

### BigQuery Dry-Run Only (WP9a)

The BigQuery export validates schema and rows locally but does not write to an actual BigQuery table. The trace labels this as `mode: "dry_run_forced"`. A real export requires `GOOGLE_CLOUD_PROJECT` and authenticated `google-cloud-bigquery` credentials.

### Fixture-Driven Conversations (WP5)

Participant conversations use deterministic fixture data, not live Gemini-generated dialogue. The conversation engine demonstrates the probing logic, follow-up selection, and structured extraction, but the "turns" are pre-authored. A live version would use Gemini to generate adaptive responses.

### Small Sample Size (n=3+1)

The prototype uses 3 primary participants and 1 reserve (P-005 for re-plan). This is sufficient to demonstrate the workflow but does not prove statistical representativeness. The quality delta (+0.692) is a demonstration of the rubric mechanics, not a peer-reviewed finding.

### No Live ADK Integration

The architecture references ADK (Agent Development Kit) as the orchestration layer. The current prototype uses direct subprocess orchestration via `wp9_demo_server.py`. ADK would replace this in a production build, but the current code does not import or depend on ADK.

### No Frontend / UI

All demo interactions happen in the terminal. There is no web frontend, dashboard, or visual interface. The "quality dashboard" and "developer overlay" referenced in the demo script are terminal output visualized via `jq` formatting.

## Honest Label Policy

Every generated trace artifact includes an `honest_label` field that describes exactly what the artifact proves and what it does not. This is a deliberate design choice: over-claiming deployment status or statistical rigor would undermine trust in the submission. The labels are not disclaimers — they are part of the product's integrity story.
