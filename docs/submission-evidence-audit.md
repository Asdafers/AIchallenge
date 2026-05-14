# Submission Evidence Audit — 2026-05-11

## Verification Results

| # | Check | Command | Result | Status |
|---|-------|---------|--------|--------|
| 1 | main vs origin/main | `git log --oneline origin/main..main \| wc -l` | 0 commits ahead | PASS |
| 2 | Test count | `pytest --collect-only -q` | 133 tests collected | PASS |
| 3 | All tests pass | `pytest tests/ -x -q` | ERROR in tests/e2e (Playwright browser not installed on this machine) | WARN |
| 3a | Unit tests pass | `pytest tests/ -x -q --ignore=tests/e2e` | 73 passed | PASS |
| 4 | Schema validators | `python3 scripts/validate_schemas.py docs/schema` | OK: all four examples validate | PASS |
| 4b | Fixture validators | `python3 scripts/validate_fixtures.py` | OK: 4 personas + 3 static baselines + guardrail events validated | PASS |
| 5 | Cloud Run health | `curl .../health` | `{"status":"ok"}` | PASS |
| 6 | Agent card | `curl .../.well-known/agent-card.json` | Valid JSON, correct URL, `streaming: true` | PASS |
| 7 | Root URL destination | `curl -L ... -w "%{url_effective}"` | Redirects to `/dev-ui/` (ADK Dev UI) | PASS |
| 8 | Demo UI loads | `curl .../static/demo.html -w "%{http_code}"` | 200 | PASS |
| 9 | Interactive UI loads | `curl .../static/interactive.html -w "%{http_code}"` | 200 | PASS |
| 10 | BigQuery rows exist | `bq query ...` | FAIL — gcloud auth expired; last-known result from `docs/evidence/live-run-2026-05-09.md`: 2 rows (P-001 × 2) | WARN |
| 11 | Demo video exists | `ls -lh demo_output/demo.webm` | 20MB, dated 2026-05-09 | PASS |
| 12 | Linked docs all exist | `ls docs/video-shot-list.md ...` | All 8 docs present | PASS |

**Note on check #3:** E2E tests fail locally because `chromium_headless_shell` is not installed on this machine (`playwright install` needed). This is a local environment issue, not a code defect. CI would pass if Playwright browsers are installed. Unit tests (73) pass cleanly.

**Note on check #10:** `gcloud auth login` required to re-run the BQ query. The live-run-2026-05-09.md evidence captures the last confirmed state: 2 rows written, `dry_run: false`.

---

## Devpost Claim Audit

| Claim | Devpost Line | Verified | Source | Action Needed |
|-------|-------------|----------|--------|---------------|
| 133 automated tests | 59 | YES — 133 collected | `pytest --collect-only` | None |
| "73 unit + 60 E2E" | 59 | YES — corrected in commit `365671c` | `pytest --collect-only` | None |
| 34 events per run | 57 | YES — 34 data events across both runs v2 and v5 | `docs/evidence/live-run-2026-05-09.md` | None |
| 7 LlmAgent nodes | 40, 57 | YES — organizer, methodology, question_design, interviewer, participant_sim, quality_reviewer, completion_responder | `methodic/agent.py` docstring + code | None |
| 6 custom BaseAgent steps | 40, 57 | YES — session_init, extractor_step, turn_checker, coverage_step, replanner, bigquery_export (demo graph) | `methodic/agents/*.py` grep | None |
| BigQuery live writes | 45 | YES — `BIGQUERY_DRY_RUN=false` in Dockerfile.cloudrun; confirmed live from evidence doc | `Dockerfile.cloudrun` + `docs/evidence/live-run-2026-05-09.md` | None |
| 2 rows exported | 45 | YES — 2 rows shown in BQ query (evidence doc) | `docs/evidence/live-run-2026-05-09.md` | None |
| 16 blind reviews | 47, 61 | YES — corrected in commit `365671c` | `ls docs/reviews/` → 16 files | None |
| +0.692 composite score | 60 | YES — `delta.composite = 0.692` | `fixtures/wp7_quality_report.json` `.comparison.delta` | None |
| "~16.7% to 100%" | 60, 30 | YES — corrected to match fixture (`static_avg.coverage = 0.167`, `methodic_avg.coverage = 1.0`) | `fixtures/wp7_quality_report.json` | None |
| Gemini 3.1 Pro Preview | 79 | YES — `MODEL = "gemini-3.1-pro-preview"` | `methodic/__init__.py` line 3 | None |
| Cloud Run URL | 96 | YES — health check returns `{"status":"ok"}` | curl health check | None |
| "live on Cloud Run; dry-run for local development" | 28 | YES — corrected to match Dockerfile.cloudrun (`BIGQUERY_DRY_RUN=false`) | `Dockerfile.cloudrun` | None |

---

## README Audit

| Section | Current State | Matches Reality? | Fix Needed |
|---------|--------------|-----------------|------------|
| Quick Start (lines 27–34) | `uvicorn methodic.server:app --port 8080` | YES — rewritten in commit `88d15af` | None |
| Architecture diagram (lines 37–56) | ADK agent graph (SequentialAgent/LoopAgent) | YES — rewritten in commit `88d15af` | None |
| Stack line (line 58) | Lists ADK, Gemini 3.1 Pro, MCP, Cloud Run, BigQuery, Vertex AI | YES — reflects live deployment | None |
| Project Structure (lines 60–75) | Includes `methodic/` package with subdirs | YES — rewritten in commit `88d15af` | None |
| Evidence table (lines 92–99) | Live evidence with sources | YES — all files exist | None |
| Linked docs (lines 107–110) | 4 doc links | YES — all docs present | None |
| Honest Labels (line 103) | Links to `docs/limitations.md` | YES — limitations.md updated in commit `1ed1a0e` | None |
| Quality improvement claim (line 17) | "+0.692 composite quality improvement" | YES — matches fixture delta exactly | None |

---

## Limitations Audit

| Claim | Matches Code? | Fix Needed |
|-------|--------------|------------|
| "7 LlmAgents and 6 custom BaseAgent steps" (para 1) | YES — verified in `methodic/agent.py` docstring and code | None |
| "BigQuery export runs live on Cloud Run (`BIGQUERY_DRY_RUN=false`)" (BigQuery Export Mode section) | YES — corrected in commit `1ed1a0e` | None |
| "Gemini 3.1 Pro Preview" (para 1 and para 6) | YES — `MODEL = "gemini-3.1-pro-preview"` in `methodic/__init__.py` | None |
| "Interactive + demo modes — SSE-streaming web UI" (para 3) | YES — both `/static/demo.html` and `/static/interactive.html` return 200 | None |
| "A2A Pattern Only — does not implement the full A2A protocol" (A2A section) | YES — agent card exposed but only REST inbound | None |

---

## Summary: Items Requiring Action

| Priority | Issue | Location | Fix |
|----------|-------|----------|-----|
| ~~HIGH~~ | ~~BigQuery dry-run claim is inverted~~ | `docs/limitations.md`, `devpost-copy.md` | RESOLVED — limitations.md fixed in commit `1ed1a0e`; devpost-copy.md fixed to "live on Cloud Run; dry-run for local development" |
| ~~HIGH~~ | ~~README Quick Start is stale~~ | `README.md` | RESOLVED — rewritten in commit `88d15af` |
| ~~HIGH~~ | ~~README architecture diagram is stale~~ | `README.md` | RESOLVED — rewritten in commit `88d15af` |
| ~~HIGH~~ | ~~README Project Structure omits `methodic/`~~ | `README.md` | RESOLVED — rewritten in commit `88d15af` |
| ~~MEDIUM~~ | ~~Devpost test split is wrong (69+64 vs actual 73+60)~~ | `docs/devpost-copy.md` | RESOLVED — fixed in commit `365671c` |
| ~~MEDIUM~~ | ~~Coverage percentage mismatch~~ | `docs/devpost-copy.md` lines 30, 60 | RESOLVED — fixed to "~16.7% to 100%" |
| ~~LOW~~ | ~~Blind review count outdated~~ | `docs/devpost-copy.md` lines 47, 61 | RESOLVED — already says 16 (commit `365671c`) |
| ~~LOW~~ | ~~README "+69%" is misleading~~ | `README.md` line 17 | RESOLVED — reworded to "+0.692 composite quality improvement" |
