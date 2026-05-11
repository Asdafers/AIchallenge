# Submission Hardening Plan — Methodic AI Agent Challenge

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden every judge-facing surface — claims, README, landing page, UI, screenshots — so nothing breaks trust in the first 3 minutes. No new features. Deadline: June 5, 2026.

**Architecture:** Audit-first (find what's stale), then fix (README, root route, UI), then capture (screenshots, evidence doc), then rehearsal and freeze.

**Tech Stack:** Python, FastAPI, Playwright, curl, bq CLI

**Calendar:**
- Phase 1 (May 11-13): Evidence audit
- Phase 2 (May 14-22): Fix judge-facing surfaces
- Phase 3 (May 23-29): Screenshots and fallback
- Phase 4 (May 30-Jun 1): Submission rehearsal
- Phase 5 (Jun 2-5): Freeze — blockers only

**Scope rule:** Every code change in this plan is polish, not new scope. A root-route redirect, README rewrite, and UI readability fixes are judge-facing credibility — not new features.

---

## Phase 1: Evidence Audit

### Task 1: Create submission evidence audit

**Files:**
- Create: `docs/submission-evidence-audit.md`

- [ ] **Step 1: Run all verification commands and record results**

Run each command and record pass/fail:

```bash
# 1. Check main vs origin/main
git log --oneline origin/main..main | wc -l

# 2. Test count
python3 -m pytest --collect-only -q 2>&1 | tail -3

# 3. All tests pass
python3 -m pytest tests/ -x -q 2>&1 | tail -5

# 4. Schema validators
python3 scripts/validate_schemas.py docs/schema
python3 scripts/validate_fixtures.py

# 5. Cloud Run health
curl -s https://methodic-2030382823.us-central1.run.app/health

# 6. Agent card
curl -s https://methodic-2030382823.us-central1.run.app/.well-known/agent-card.json | python3 -m json.tool

# 7. Root URL destination
curl -s -L -o /dev/null -w "%{url_effective}" https://methodic-2030382823.us-central1.run.app/

# 8. Demo UI loads
curl -s -o /dev/null -w "%{http_code}" https://methodic-2030382823.us-central1.run.app/static/demo.html

# 9. Interactive UI loads
curl -s -o /dev/null -w "%{http_code}" https://methodic-2030382823.us-central1.run.app/static/interactive.html

# 10. BigQuery rows exist
bq query --project_id=methodic-ai-challenge "SELECT participant_id, quality_variable_coverage, exported_at FROM methodic_demo.win_loss_responses ORDER BY exported_at DESC LIMIT 5"

# 11. Demo video exists locally
ls -lh demo_output/demo.webm

# 12. Linked docs all exist
ls docs/video-shot-list.md docs/rehearsal-checklist.md docs/judge-storyboard.md docs/delivery-plan.md docs/architecture-diagram.md docs/limitations.md docs/devpost-copy.md docs/demo-script.md
```

- [ ] **Step 2: Cross-reference Devpost claims against evidence**

Read `docs/devpost-copy.md` line by line. For each factual claim, verify it matches reality:

| Claim | Devpost Line | Verified? | Source |
|-------|-------------|-----------|--------|
| 133 automated tests | line 59 | ? | `pytest --collect-only` |
| 69 unit + 64 E2E | line 59 | ? | count files in `tests/` vs `tests/e2e/` |
| 34 events per run | line 42 | ? | `docs/evidence/live-run-2026-05-09.md` |
| 7 LlmAgent nodes | line 40 | ? | `methodic/agent.py` |
| 6 custom BaseAgent steps | line 40 | ? | grep `BaseAgent` in `methodic/agents/` |
| BigQuery live writes | line 45 | ? | BQ query result |
| 2 rows exported | line 45 | ? | BQ query result |
| 14 blind reviews | line 47 | ? | count files in `docs/reviews/` |
| +0.692 composite score | line 60 | ? | `fixtures/wp7_quality_report.json` |
| ~12.5% to ~87.5% | line 60 | ? | quality report fixture |
| Gemini 2.5 Pro | line 79 | ? | `methodic/__init__.py` |
| Cloud Run URL | line 96 | ? | curl health check |

- [ ] **Step 3: Cross-reference README against current system**

Check these README claims:
1. Quick Start commands (lines 27-34) — do they match the ADK server, or are they stale WP scripts?
2. Architecture diagram (line 53-61) — does it match the ADK graph in `methodic/agent.py`?
3. Project Structure (lines 69-88) — does it mention `methodic/` package at all?
4. Key Artifacts table (lines 92-99) — are fixture paths correct?
5. Linked docs (lines 107-114) — do all files exist? (Already checked, but verify)
6. "BigQuery exports are dry-run validated" (line 103) — stale, BQ is live now

- [ ] **Step 4: Cross-reference limitations.md**

Read `docs/limitations.md` and check each claim:
1. "7 LlmAgents and 6 custom BaseAgent steps" — verify count in `methodic/agent.py` and `methodic/agents/`
2. "BigQuery export defaults to dry-run" — check `Dockerfile.cloudrun` for `BIGQUERY_DRY_RUN` env
3. "Gemini 2.5 Pro" — verify in `methodic/__init__.py`

- [ ] **Step 5: Write the audit document**

Create `docs/submission-evidence-audit.md` with this structure:

```markdown
# Submission Evidence Audit — 2026-05-11

## Verification Results

| # | Check | Command | Result | Status |
|---|-------|---------|--------|--------|
| 1 | main vs origin | `git log ...` | 0 commits ahead | PASS/FAIL |
| 2 | Test count | `pytest --collect-only` | 133 | PASS/FAIL |
| ... | ... | ... | ... | ... |

## Devpost Claim Audit

| Claim | Line | Verified | Source | Action Needed |
|-------|------|----------|--------|---------------|
| ... | ... | ... | ... | ... |

## README Audit

| Section | Current State | Matches Reality? | Fix Needed |
|---------|--------------|-----------------|------------|
| Quick Start | wp3-wp9 scripts | NO — stale | Rewrite for ADK server |
| ... | ... | ... | ... |

## Limitations Audit

| Claim | Matches Code? | Fix Needed |
|-------|--------------|------------|
| ... | ... | ... |
```

- [ ] **Step 6: Commit**

```bash
git add docs/submission-evidence-audit.md
git commit -m "docs: add submission evidence audit"
```

---

## Phase 2: Fix Judge-Facing Surfaces

### Task 2: Rewrite README for ADK reality

**Files:**
- Modify: `README.md`

The current README tells judges to run `wp3_organizer_flow.py` through `wp9a_bigquery_export.py` — those are pre-ADK standalone scripts. The actual system is a FastAPI server with an ADK agent graph. This is the single biggest credibility gap: the first thing judges see on GitHub contradicts the Devpost.

- [ ] **Step 1: Read the current README**

```bash
cat README.md
```

- [ ] **Step 2: Read the ADK entry points to understand current architecture**

```bash
head -40 methodic/agent.py
head -20 methodic/server.py
```

- [ ] **Step 3: Rewrite README**

Replace the entire README with content matching the ADK reality. Key sections:

```markdown
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

Result: **+69% quality improvement** over static surveys (same rubric, same participants).

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

**Stack:** Google ADK · Gemini 2.5 Pro · MCP (stdio JSON-RPC 2.0) · FastAPI · Cloud Run · BigQuery · Vertex AI

## Project Structure

```
methodic/                  # ADK agent package
  __init__.py              # Model configuration (Gemini 2.5 Pro / Flash)
  agent.py                 # Agent graph (SequentialAgent + LoopAgent)
  server.py                # FastAPI server (SSE streaming, interactive API)
  schemas.py               # Pydantic models (ParticipantResponse, 8 canonical fields)
  agents/                  # Custom BaseAgent steps (extraction, coverage, re-plan, BQ export)
  tools/                   # MCP client, BigQuery export, quality scoring
  static/                  # Demo UI (demo.html) + Interactive UI (interactive.html)
scripts/                   # MCP server, validators, recording, legacy WP scripts
fixtures/                  # Deterministic test data (CRM, telemetry, participants)
tests/                     # 69 unit/integration + 64 Playwright E2E tests
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
| Live SSE stream (34 events) | PASS | [live-run-2026-05-09.md](docs/evidence/live-run-2026-05-09.md) |
| BigQuery live export (2 rows) | PASS | `bq query` on `methodic_demo.win_loss_responses` |
| Agent card | PASS | `/.well-known/agent-card.json` |
| Quality delta (+0.692) | PASS | [Fixture benchmark](fixtures/wp7_quality_report.json) |

## Honest Labels

See [docs/limitations.md](docs/limitations.md) for what the prototype proves and what it does not.

## Submission Materials

- [Devpost Copy](docs/devpost-copy.md)
- [Demo Script](docs/demo-script.md)
- [Limitations](docs/limitations.md)
- [Architecture Diagram](docs/architecture-diagram.md)
```

- [ ] **Step 4: Verify all links in the new README resolve**

```bash
# Check every linked file exists
ls docs/limitations.md docs/devpost-copy.md docs/demo-script.md docs/architecture-diagram.md docs/evidence/live-run-2026-05-09.md fixtures/wp7_quality_report.json
```

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for ADK reality — Quick Start, architecture, evidence"
```

---

### Task 3: Add root route redirect to demo UI

**Files:**
- Modify: `methodic/server.py:100-106`
- Test: `tests/test_tools.py` (or inline verification)

Right now `GET /` returns 307 → `/dev-ui/` (ADK's generic dev interface). A judge visiting the Cloud Run URL should land on our demo UI, not ADK scaffolding.

- [ ] **Step 1: Read the current route setup area**

```bash
sed -n '87,110p' methodic/server.py
```

- [ ] **Step 2: Add root redirect before the static mount**

After `app.mount("/static", ...)` (line 101), add a root route that redirects to `/static/demo.html`:

```python
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        from starlette.responses import RedirectResponse
        return RedirectResponse(url="/static/demo.html")
```

This must be added AFTER `app.mount("/static", ...)` so the static files are available, and BEFORE returning `app`.

- [ ] **Step 3: Run existing tests to verify nothing breaks**

```bash
python3 -m pytest tests/ -x -q
```

Expected: all 133 tests pass.

- [ ] **Step 4: Verify locally**

```bash
uvicorn methodic.server:app --port 8080 &
sleep 2
curl -s -o /dev/null -w "%{http_code} %{redirect_url}" http://localhost:8080/
# Expected: 307 http://localhost:8080/static/demo.html
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add methodic/server.py
git commit -m "feat: redirect root URL to demo UI for judge first-impression"
```

---

### Task 4: Update limitations.md with BQ live status

**Files:**
- Modify: `docs/limitations.md:22-23`

The BigQuery section says "defaults to dry-run" — but `Dockerfile.cloudrun` now sets `BIGQUERY_DRY_RUN=false` and live writes are confirmed. This is a stale claim.

- [ ] **Step 1: Read current limitations.md**

```bash
cat docs/limitations.md
```

- [ ] **Step 2: Verify Dockerfile.cloudrun has the env var**

```bash
grep BIGQUERY_DRY_RUN Dockerfile.cloudrun
```

Expected: `ENV BIGQUERY_DRY_RUN=false` (or absent, meaning the code defaults to dry-run but Cloud Run overrides).

- [ ] **Step 3: Update the BigQuery section**

Replace the BigQuery section in `docs/limitations.md`:

Old:
```markdown
### BigQuery Export Mode
BigQuery export defaults to dry-run (`BIGQUERY_DRY_RUN=true`) unless explicitly configured with GCP credentials. The schema, flattening logic, and table creation path are production-ready; live writes require IAM setup.
```

New:
```markdown
### BigQuery Export Mode
BigQuery export runs live on Cloud Run (`BIGQUERY_DRY_RUN=false`) and has confirmed writes to `methodic_demo.win_loss_responses` (2 rows, 2026-05-09). Local development defaults to dry-run unless GCP credentials are configured.
```

- [ ] **Step 4: Commit**

```bash
git add docs/limitations.md
git commit -m "docs: update limitations.md — BQ is live on Cloud Run"
```

---

### Task 5: Improve demo UI readability for video/judging

**Files:**
- Modify: `methodic/static/demo.html`

These are CSS-only changes that improve readability during screen recording and judge evaluation. No new features.

- [ ] **Step 1: Read the current CSS section for font sizes and colors**

Read lines 1-100 of `methodic/static/demo.html` to understand the current typography.

- [ ] **Step 2: Increase base font size for video legibility**

Find the `body` CSS rule and change `font-family` line area. Add or update:

```css
body {
  background: #1e1e2f;
  color: #e0e0e0;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 15px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
```

(Ensure `font-size: 15px` is present — current may be browser default 16px or unset.)

- [ ] **Step 3: Make coverage bar labels larger**

Find the `.var-name` and `.var-pct` CSS rules. Ensure:

```css
.var-name {
  font-size: 0.78rem;
}
.var-pct {
  font-size: 0.75rem;
}
```

If they are smaller (e.g., 0.65rem), increase to these values.

- [ ] **Step 4: Increase agentic moment card contrast**

Find the `.agentic-card` or equivalent CSS. Ensure the background has enough contrast against the dark theme. Target:

```css
.agentic-card {
  background: #1a2a3a;
  border-left: 3px solid #f39c12;
}
```

- [ ] **Step 5: Run Playwright E2E tests to verify nothing breaks**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py -x -q
```

Expected: all E2E tests pass.

- [ ] **Step 6: Commit**

```bash
git add methodic/static/demo.html
git commit -m "style: improve demo UI readability for video recording and judging"
```

---

## Phase 3: Screenshots and Fallback

### Task 6: Capture fresh screenshots for Devpost

**Files:**
- Create: `demo_output/screenshots/` (gitignored — local only for Devpost upload)

Screenshots are uploaded directly to Devpost, not committed to git. These are the images judges see in the gallery.

- [ ] **Step 1: Start local server**

```bash
uvicorn methodic.server:app --port 8080 &
```

- [ ] **Step 2: Capture screenshots via Playwright**

```python
# Run as a script or in Python REPL
from playwright.sync_api import sync_playwright
import os

os.makedirs("demo_output/screenshots", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    # Screenshot 1: Intro overlay (before starting)
    page.goto("http://localhost:8080/static/demo.html")
    page.wait_for_selector("#intro-overlay", timeout=5000)
    page.screenshot(path="demo_output/screenshots/01_intro.png")

    # Screenshot 2: Pipeline running (mid-interview)
    page.click("#start-btn")
    page.wait_for_timeout(15000)  # Wait for some events
    page.screenshot(path="demo_output/screenshots/02_pipeline.png")

    # Screenshot 3: Wait for completion
    page.wait_for_timeout(60000)  # Wait longer for events
    page.screenshot(path="demo_output/screenshots/03_events.png")

    browser.close()
```

- [ ] **Step 3: Also capture interactive mode intro**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:8080/static/interactive.html")
    page.wait_for_timeout(3000)
    page.screenshot(path="demo_output/screenshots/04_interactive.png")
    browser.close()
```

- [ ] **Step 4: Verify screenshots look good**

```bash
ls -lh demo_output/screenshots/
# Should have 4 PNG files, each > 50KB
```

- [ ] **Step 5: Kill the local server**

```bash
kill %1
```

No commit needed — `demo_output/` is gitignored.

---

### Task 7: Add Gemini latency fallback for live judging

**Files:**
- Modify: `methodic/static/demo.html`

If Cloud Run / Gemini is slow during judging, the demo UI should handle it gracefully instead of appearing broken. This is a timeout message, not a new feature.

- [ ] **Step 1: Read the current SSE connection handler**

Find the `EventSource` or `fetch` call in `demo.html` that connects to `/api/stream`.

- [ ] **Step 2: Add a timeout indicator**

After the SSE connection is opened, add a 30-second timeout check. If no events arrive within 30 seconds, show a message in the event log:

```javascript
var latencyTimer = setTimeout(function() {
    addEventToLog('system', 'Gemini is warming up — first response may take 15-30 seconds on Cloud Run cold start...');
}, 15000);
```

Clear the timer when the first event arrives:

```javascript
// Inside the event handler, at the top:
if (latencyTimer) {
    clearTimeout(latencyTimer);
    latencyTimer = null;
}
```

- [ ] **Step 3: Add a 5-minute overall timeout**

```javascript
var overallTimer = setTimeout(function() {
    addEventToLog('system', 'Pipeline is taking longer than expected. Gemini responses are non-deterministic — some runs complete faster than others.');
}, 300000);
```

- [ ] **Step 4: Run E2E tests**

```bash
python3 -m pytest tests/e2e/test_demo_ui.py -x -q
```

- [ ] **Step 5: Commit**

```bash
git add methodic/static/demo.html
git commit -m "feat: add latency timeout messages for Cloud Run cold starts"
```

---

## Phase 4: Submission Rehearsal

### Task 8: Full submission dry run

**Files:**
- Create: `docs/submission-rehearsal-2026-05-30.md`

This is a manual checklist executed as if submitting. Every step must pass.

- [ ] **Step 1: Verify git state**

```bash
git status
# Expected: clean working tree, 0 commits ahead of origin
git log --oneline -5
```

- [ ] **Step 2: Verify Cloud Run is live**

```bash
curl -s https://methodic-2030382823.us-central1.run.app/health
# Expected: {"status":"ok"}

curl -s -o /dev/null -w "%{http_code}" https://methodic-2030382823.us-central1.run.app/static/demo.html
# Expected: 200

curl -s -o /dev/null -w "%{http_code}" https://methodic-2030382823.us-central1.run.app/static/interactive.html
# Expected: 200
```

- [ ] **Step 3: Verify root redirect works**

```bash
curl -s -L -o /dev/null -w "%{url_effective}" https://methodic-2030382823.us-central1.run.app/
# Expected: ends with /static/demo.html
```

- [ ] **Step 4: Run a live pipeline**

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"study_brief":"Why are we losing mid-market enterprise deals?"}' \
  https://methodic-2030382823.us-central1.run.app/api/stream --max-time 600
# Expected: SSE events streaming, 20+ events
```

- [ ] **Step 5: Verify BigQuery has recent data**

```bash
bq query --project_id=methodic-ai-challenge \
  "SELECT participant_id, exported_at FROM methodic_demo.win_loss_responses ORDER BY exported_at DESC LIMIT 3"
# Expected: at least 2 rows
```

- [ ] **Step 6: Verify tests pass**

```bash
python3 -m pytest tests/ -x -q
# Expected: 133 passed
```

- [ ] **Step 7: Verify demo video exists and plays**

```bash
ls -lh demo_output/demo.webm
# Expected: file exists, > 1MB
# Manually: open demo_output/demo.webm, verify it plays end-to-end, shows 5 scenes
```

- [ ] **Step 8: Read Devpost copy end-to-end**

```bash
cat docs/devpost-copy.md
```

Read every claim. Flag anything that feels wrong or stale.

- [ ] **Step 9: Verify agent card**

```bash
curl -s https://methodic-2030382823.us-central1.run.app/.well-known/agent-card.json | python3 -m json.tool
# Expected: correct URL, streaming: true, version 1.0.0
```

- [ ] **Step 10: Write rehearsal report**

Create `docs/submission-rehearsal-2026-05-30.md`:

```markdown
# Submission Rehearsal — 2026-05-30

| Check | Result | Notes |
|-------|--------|-------|
| Git clean | PASS/FAIL | |
| Cloud Run health | PASS/FAIL | |
| Root redirect | PASS/FAIL | |
| Demo UI loads | PASS/FAIL | |
| Interactive UI loads | PASS/FAIL | |
| Live pipeline runs | PASS/FAIL | Event count: |
| BigQuery rows | PASS/FAIL | Row count: |
| 133 tests pass | PASS/FAIL | |
| Demo video plays | PASS/FAIL | Duration: |
| Agent card correct | PASS/FAIL | |
| Devpost copy reviewed | PASS/FAIL | |
```

- [ ] **Step 11: Commit**

```bash
git add docs/submission-rehearsal-2026-05-30.md
git commit -m "docs: add submission rehearsal report"
```

---

## Phase 5: Freeze (Jun 2-5)

### Task 9: Final push and freeze

**Files:**
- No new files

- [ ] **Step 1: Push all commits**

```bash
git push origin main
```

- [ ] **Step 2: Verify GitHub repo is public (or shared with judges)**

```bash
gh repo view --json visibility -q '.visibility'
# Expected: "PUBLIC" or confirm judges have access
```

- [ ] **Step 3: Final Cloud Run smoke**

```bash
curl -s https://methodic-2030382823.us-central1.run.app/health
curl -s -o /dev/null -w "%{http_code}" https://methodic-2030382823.us-central1.run.app/static/demo.html
```

- [ ] **Step 4: Submit on Devpost**

Human action: copy from `docs/devpost-copy.md`, upload demo video from `demo_output/demo.webm`, upload screenshots from `demo_output/screenshots/`.

---

## Verification

After all phases:
1. `git status` — clean tree, 0 ahead of origin
2. `pytest tests/ -v` — 133 tests pass
3. `curl /health` on Cloud Run — `{"status":"ok"}`
4. Root URL → redirects to demo UI
5. Demo video plays end-to-end
6. Every claim in `devpost-copy.md` traces to evidence
7. `limitations.md` matches current code reality
8. README Quick Start works: `pip install && uvicorn → demo loads`
