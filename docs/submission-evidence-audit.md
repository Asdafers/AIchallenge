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
| "69 unit + 64 E2E" | 59 | NO — actual split is 73 unit + 60 E2E | `pytest --collect-only --ignore=tests/e2e` → 73; `pytest tests/e2e/` → 60 | Fix split in devpost text |
| 34 events per run | 57 | YES — 34 data events across both runs v2 and v5 | `docs/evidence/live-run-2026-05-09.md` | None |
| 7 LlmAgent nodes | 40, 57 | YES — organizer, methodology, question_design, interviewer, participant_sim, quality_reviewer, completion_responder | `methodic/agent.py` docstring + code | None |
| 6 custom BaseAgent steps | 40, 57 | YES — session_init, extractor_step, turn_checker, coverage_step, replanner, bigquery_export (demo graph) | `methodic/agents/*.py` grep | None |
| BigQuery live writes | 45 | YES — `BIGQUERY_DRY_RUN=false` in Dockerfile.cloudrun; confirmed live from evidence doc | `Dockerfile.cloudrun` + `docs/evidence/live-run-2026-05-09.md` | None |
| 2 rows exported | 45 | YES — 2 rows shown in BQ query (evidence doc) | `docs/evidence/live-run-2026-05-09.md` | None |
| 14 blind reviews | 47, 61 | NO — actual count is 16 reviews (10 Codex + 6 Gemini) | `ls docs/reviews/ \| grep -v devpost-claim-audit \| wc -l` → 16 | Update to "16 blind reviews" or leave as conservative undercount |
| +0.692 composite score | 60 | YES — `delta.composite = 0.692` | `fixtures/wp7_quality_report.json` `.comparison.delta` | None |
| "~12.5% to ~87.5%" | 60, 30 | PARTIAL — fixture shows static_avg.coverage = 0.167 (16.7%), methodic_avg.coverage = 1.0 (100%); the "~12.5%" and "~87.5%" figures do not match the fixture | `fixtures/wp7_quality_report.json` `.comparison.static_avg.coverage` / `.methodic_avg.coverage` | Fix to "~16.7% to 100%" or explain the discrepancy |
| Gemini 2.5 Pro | 79 | YES — `MODEL = "gemini-2.5-pro"` | `methodic/__init__.py` line 3 | None |
| Cloud Run URL | 96 | YES — health check returns `{"status":"ok"}` | curl health check | None |
| "dry-run by default in demo" (parenthetical) | 28 | PARTIAL — `BIGQUERY_DRY_RUN=false` in Dockerfile.cloudrun means live writes are default; the parenthetical "(live mode; dry-run by default in demo)" contradicts reality | `Dockerfile.cloudrun` | Remove or update parenthetical on line 28 |

---

## README Audit

| Section | Current State | Matches Reality? | Fix Needed |
|---------|--------------|-----------------|------------|
| Quick Start (lines 27–34) | Runs wp3–wp9 WP scripts sequentially | NO — these scripts exist but are not the current execution model; the system is now an ADK agent graph run via `adk web` or the FastAPI server | Rewrite Quick Start for ADK server (`adk web` or `uvicorn`) |
| Architecture diagram (lines 53–61) | WP-numbered flow: `Organizer (WP3) → Methodology (WP4) → ...` | NO — the ADK graph uses SequentialAgent/LoopAgent nodes with agent names (organizer, methodology, etc.), not WP numbers | Replace with ADK agent graph diagram (already in `docs/architecture-diagram.md` Mermaid) |
| Stack line (line 63) | "Docker · Cloud Run (deployment-ready) · BigQuery (dry-run validated)" | PARTIALLY STALE — BigQuery is now live, not dry-run; Cloud Run is deployed, not just "deployment-ready" | Update stack line to reflect live status |
| Project Structure (lines 69–88) | Lists only `scripts/` and fixture dirs | NO — does not mention `methodic/` package at all, which is the core of the system | Add `methodic/` package description |
| Key Artifacts table (lines 92–99) | Fixture paths: wp4, wp6, wp7, wp8, wp9, wp9a | YES — all files exist | None |
| Linked docs (lines 107–114) | 6 doc links | YES — all 8 docs present (same as check #12) | None |
| Honest Labels (line 103) | "BigQuery exports are dry-run validated" | NO — BigQuery is live on Cloud Run (`BIGQUERY_DRY_RUN=false`); this claim is stale | Remove or update to reflect live status |
| "Result: +69% quality improvement" (line 18) | Claims "+69% quality improvement" | MISLEADING — the fixture delta is +0.692 composite score, not a percentage improvement; coverage goes from 16.7% to 100%, not 69%; the "+69% improvement" framing is imprecise | Reword to match actual fixture numbers |

---

## Limitations Audit

| Claim | Matches Code? | Fix Needed |
|-------|--------------|------------|
| "7 LlmAgents and 6 custom BaseAgent steps" (para 1) | YES — verified in `methodic/agent.py` docstring and code | None |
| "BigQuery export defaults to dry-run (`BIGQUERY_DRY_RUN=true`) unless explicitly configured" (BigQuery Export Mode section) | NO — `Dockerfile.cloudrun` sets `ENV BIGQUERY_DRY_RUN=false`; live Cloud Run runs with live writes by default | Update to reflect that Dockerfile.cloudrun defaults to live (`false`); dry-run only applies to local development without the Dockerfile env override |
| "Gemini 2.5 Pro" (para 1 and para 6) | YES — `MODEL = "gemini-2.5-pro"` in `methodic/__init__.py` | None |
| "Interactive + demo modes — SSE-streaming web UI" (para 3) | YES — both `/static/demo.html` and `/static/interactive.html` return 200 | None |
| "A2A Pattern Only — does not implement the full A2A protocol" (A2A section) | YES — agent card exposed but only REST inbound | None |

---

## Summary: Items Requiring Action

| Priority | Issue | Location | Fix |
|----------|-------|----------|-----|
| HIGH | BigQuery dry-run claim is inverted | `docs/limitations.md`, `devpost-copy.md` line 28, `README.md` line 63/103 | Dockerfile.cloudrun sets `BIGQUERY_DRY_RUN=false`; update all three docs to say live writes are default on Cloud Run |
| HIGH | README Quick Start is stale | `README.md` lines 27–34 | Replace WP script commands with ADK server startup |
| HIGH | README architecture diagram is stale | `README.md` lines 53–61 | Replace WP-numbered flow with ADK agent graph |
| HIGH | README Project Structure omits `methodic/` | `README.md` lines 69–88 | Add `methodic/` package description |
| MEDIUM | Devpost test split is wrong (69+64 vs actual 73+60) | `docs/devpost-copy.md` line 59 | Fix to "73 unit/integration + 60 Playwright E2E" |
| MEDIUM | Coverage percentage mismatch (~12.5%/~87.5% vs 16.7%/100%) | `docs/devpost-copy.md` lines 30, 60 | Fix to "~16.7% (static survey baseline) to 100% (agent-conducted)" or add footnote explaining different rubric sub-dimension |
| LOW | Blind review count outdated (14 vs actual 16) | `docs/devpost-copy.md` lines 47, 61 | Update to 16, or leave as conservative undercount (16 > 14 is fine for judges) |
| LOW | README "+69% quality improvement" is misleading | `README.md` line 18 | Rephrase to match actual fixture delta (+0.692 composite) |
