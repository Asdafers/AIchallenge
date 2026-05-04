# Video Shot List

Recording plan for the 3:30 Methodic demo video. Each shot specifies what to capture and how.

## Equipment & Setup

- **Screen recording:** Full-screen terminal (dark theme, large font ~18pt)
- **Resolution:** 1920x1080 minimum
- **Voiceover:** Record separately, layer in post
- **Terminal:** Split-pane setup (iTerm2 or tmux) for side-by-side comparisons
- **Browser (optional):** For BigQuery console or dashboard mockup if available

## Pre-Recording

1. Run all verification commands from `docs/rehearsal-checklist.md`
2. Confirm Docker Desktop is running (for container shot)
3. Clear terminal history
4. Pre-stage fixture files in a viewer for quick `cat` or `jq` display

## Shot Sequence

| # | Time | Shot Type | Content | Command / File | Notes |
|---|------|-----------|---------|----------------|-------|
| 1 | 0:00-0:05 | Title card | "Methodic — Autonomous Research Operations Agent" | Static overlay | Add subtitle: "B2B SaaS Win-Loss Research" |
| 2 | 0:05-0:15 | Terminal | Show the problem: `cat fixtures/static_baseline/P-001.json \| jq .responses` | `jq` piped output | Highlight shallow "price" answer |
| 3 | 0:15-0:30 | Terminal | External request arrives | `python3 scripts/wp3_organizer_flow.py --output /tmp/demo_wp3.json` | Show stdout: 5 events. Then `jq .events[1] /tmp/demo_wp3.json` for the clarification |
| 4 | 0:30-0:50 | Terminal | Methodology pushback | `python3 scripts/wp4_methodology_review.py --mode fallback --output /tmp/demo_wp4.json` | Show stdout summary. Then `jq .methodology_review.pushbacks /tmp/demo_wp4.json` |
| 5 | 0:50-1:10 | Terminal | Revised sample + questions | `jq .sample_revision /tmp/demo_wp4.json` then `jq '.question_pool[:3]' /tmp/demo_wp4.json` | Show economic buyers added, question-variable mapping |
| 6 | 1:10-1:30 | Split terminal | Static vs Methodic conversation | Left: `cat fixtures/static_baseline/P-001.json \| jq .responses[0]` Right: `python3 scripts/wp5_conversation_engine.py ...` | Emphasize follow-up probing vs flat answers |
| 7 | 1:30-1:55 | Terminal | MCP triangulation | `python3 scripts/wp6_mcp_boundary.py --output /tmp/demo_wp6.json` | Show stdout: transport, tools, 3 calls. Then `jq '.calls[0].response' /tmp/demo_wp6.json` for CRM context |
| 8 | 1:55-2:00 | Terminal | Guardrail event | `jq '.processing_events["P-002"][] | select(.event_type=="guardrail_triggered")' fixtures/wp5_coverage_summary.json` | Quick flash of guardrail handling in trace |
| 9 | 2:00-2:25 | Terminal | Quality scoring | `python3 scripts/wp7_data_quality.py --output-report /tmp/demo_wp7.json ...` | Show stdout: methodic 0.761 vs static 0.069, delta +0.692 |
| 10 | 2:25-2:50 | Terminal | Re-plan trigger | `python3 scripts/wp8_replan_trigger.py --output /tmp/demo_wp8.json` | Show stdout: procurement_friction → P-005 → resolved |
| 11 | 2:50-3:10 | Terminal | BigQuery export | `python3 scripts/wp9a_bigquery_export.py --dry-run --output /tmp/demo_wp9a.json` | Show stdout: 17 schema fields, 6 rows validated |
| 12 | 3:10-3:25 | Terminal | Container demo proof | `jq '.demo_trace.pipeline' fixtures/wp9_deployment_trace.json` | Show 7/7 steps passed, total duration, local_container mode |
| 13 | 3:25-3:30 | Title card | "Methodic — Decision in, governed data out." | Static overlay | Add: "Gemini · MCP · Cloud Run · BigQuery" |

## Post-Production

- Layer voiceover from `docs/demo-script.md` onto screen recording
- Add subtle zoom/highlight on key terminal output (pushback text, MCP trace, quality delta)
- Add text annotations for Scene 3 split-screen comparison
- Keep transitions minimal (cuts, no fancy effects)
- Total runtime target: 3:25-3:35

## Backup Plan

If Docker is unavailable during recording, substitute shot #12 with:
```bash
cat fixtures/wp9_deployment_trace.json | jq '{verification, smoke_test: .smoke_test | {build: .build.success, health: .health_check.healthy, demo: .demo_call.success}}'
```
This shows the pre-recorded container proof without requiring Docker at recording time.
