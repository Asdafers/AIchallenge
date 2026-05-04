# Methodic Demo Script (3:30)

Target runtime: 3 minutes 30 seconds. Each scene has voiceover text and on-screen actions.

---

## Scene 1: The Hook (0:00 - 0:30)

**On screen:** Terminal showing a revenue dashboard concept — slipping mid-market deals.

**Voiceover:**
> "Dashboards tell you what happened. But to know *why* deals slip, B2B teams rely on static surveys that return vague answers like 'price.' Methodic fixes the upstream data-capture layer."

**Action:** Run the external request flow.

```bash
python3 scripts/wp3_organizer_flow.py --output /tmp/demo_wp3.json
```

**On screen:** Show the `request_study` payload arriving, then the clarification question: "Is the concern about per-seat packaging or total ROI justification?" Show the 5-event log: request → clarification → response → brief → approval.

**Proof beats:** B1 (external agent request)

---

## Scene 2: Agentic Planning & Pushback (0:30 - 1:10)

**Voiceover:**
> "Methodic isn't a form generator. When a human suggests interviewing only product champions, the Methodology Agent pushes back."

**Action:** Run the methodology review.

```bash
python3 scripts/wp4_methodology_review.py --mode fallback --output /tmp/demo_wp4.json
```

**On screen:** Show the biased sample plan (`fixtures/sample_plan_biased.json` — all champions), then the pushback output: "Champions alone cannot answer pricing questions. Adding economic buyers to avoid sample bias." Show the revised 7-participant sample with economic buyers added.

**Voiceover:**
> "It corrects a biased sample, adds the right participant segments, and generates measurement-mapped questions — all before a single conversation starts."

**On screen:** Show the question pool (8 questions) with variable mappings.

**Proof beats:** B2 (methodology pushback), B5 (variable-to-question mapping)

---

## Scene 3: Conversations & MCP Triangulation (1:10 - 2:00)

**Voiceover:**
> "Now watch what happens when a participant says 'price was too high.'"

**Action:** Run the conversation engine.

```bash
python3 scripts/wp5_conversation_engine.py --output-responses /tmp/demo_wp5r.json --output-coverage /tmp/demo_wp5c.json
```

**On screen (split):**
- **Left:** Static survey accepts "Price" and moves on.
- **Right:** Methodic opens a Developer Trace Overlay.

**Action:** Run the MCP boundary to show the real tool call.

```bash
python3 scripts/wp6_mcp_boundary.py --output /tmp/demo_wp6.json
```

**On screen:** The MCP trace overlay shows `lookup_deal_context` called via stdio JSON-RPC 2.0. CRM data reveals the trial account never reached the report builder. Methodic asks: "Was the cost an issue, or could your team not prove the ROI internally?"

**Voiceover:**
> "Methodic uses the Model Context Protocol to securely pull CRM telemetry, turning vague answers into precise, evidence-linked data. The MCP server filters fields to only what the study approves — no data leakage."

**On screen:** Show `filtering_verified: true` in the trace, the `allowed_fields` list, and the guardrail event log (B9: contradiction handled for P-001 without forcing category).

**Proof beats:** B3 (interactive capture), B4 (MCP triangulation), B9 (guardrail recovery)

---

## Scene 4: Quality Dashboard & Autonomous Re-Plan (2:00 - 2:50)

**Action:** Run data quality scoring.

```bash
python3 scripts/wp7_data_quality.py --output-report /tmp/demo_wp7.json --output-csv /tmp/demo_wp7.csv --output-bigquery /tmp/demo_wp7bq.json
```

**On screen:** Quality dashboard showing variable coverage states. Most variables are `covered_high_confidence`, but `procurement_friction` is stuck at `ambiguous`.

**Voiceover:**
> "Methodic tracks variable coverage in real time. When procurement friction remains ambiguous after all planned sessions, it autonomously triggers a re-plan."

**Action:** Run the re-plan trigger.

```bash
python3 scripts/wp8_replan_trigger.py --output /tmp/demo_wp8.json
```

**On screen:** Re-plan decision: `procurement_friction` unresolved → P-005 (Procurement Lead) added → one targeted session → variable resolved. Dashboard updates to show all variables covered.

**Voiceover:**
> "One targeted economic-buyer session closes the gap. No human intervention required."

**Proof beats:** B5 (coverage loop), B6 (autonomous re-plan), B7 (quality scoring visible)

---

## Scene 5: Export & Google Stack Close (2:50 - 3:30)

**Action:** Run BigQuery export validation and show the container demo.

```bash
python3 scripts/wp9a_bigquery_export.py --dry-run --output /tmp/demo_wp9a.json
```

**On screen:** Structured JSON export with evidence quotes linked to variables. CSV export. BigQuery schema with 17 fields, 6 validated rows.

**Voiceover:**
> "The final dataset is BigQuery-ready with full evidence linking — every data point traces back to the conversation turn that produced it. Schema validation and dry-run export confirm the rows are clean."

**On screen:** Show the deployment trace (`fixtures/wp9_deployment_trace.json`): 7/7 steps pass in Docker container. Show the `honest_label` and `operator_steps` for Cloud Run deployment.

**Voiceover:**
> "Powered by Gemini, connected through MCP, and containerized for Cloud Run, Methodic exports clean, decision-ready data. Static surveys give you 'price.' Methodic gives you the procurement friction that actually killed the deal."

**On screen:** Side-by-side quality comparison: static composite 0.069 vs Methodic composite 0.761. Delta: +0.692.

**Proof beats:** B7 (measurable quality delta), B8 (Google-aligned deployability)

---

## Closing (3:25 - 3:30)

**On screen:** "Methodic — Decision in, governed data out."

**Voiceover:**
> "Methodic. Decision in, governed data out."
