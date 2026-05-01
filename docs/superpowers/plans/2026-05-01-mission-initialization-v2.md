# Mission Initialization — Implementation Plan v2 (Path M)

> Supersedes `2026-05-01-mission-initialization.md`.
> Date: 2026-05-01. Status: Proposed.
> Pairs with: `docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md`.
> Mode: **Path M (MCP-native)** — extends the upstream MCP server to support multi-agent claims rather than working around its current schema.

> **For agentic workers:** REQUIRED SUB-SKILL — use `superpowers:executing-plans`. Steps use checkbox (`- [ ]`) syntax.

## Goal

Bootstrap the v2 hybrid harness by **(a)** extending the upstream `email-calendar-agent` MCP server with project-scoped multi-agent task tools, **(b)** deploying the changes without breaking the operator's existing dashboard, and **(c)** seeding the AIchallenge namespace so agents can begin coordinating. No scripts in this repo; no credentials in this repo; every write is an MCP tool call.

## Why this differs from v1 (and from the Path H draft)

- **v1** wrote directly to Postgres with hardcoded credentials and assumed an unverified atomic-claim primitive existed.
- **The earlier Path H draft** kept task coordination in files (`tasks/open|claimed|done/`) because the upstream MCP could not be modified. The operator owns the upstream and chose to expand it, so Path H is now obsolete.
- **Path M** moves coordination into the MCP itself with a proper schema, a real CAS claim, and an audit table. The cost is upstream Python + SQL work; the payoff is a single canonical store with no protocol gymnastics.

## Tech stack

- Postgres (existing brain DB, schema migration).
- Python (`brain/mission_db.py`, `brain/mission_server.py` in the upstream `email-calendar-agent` repo).
- MCP `FastMCP` (already in use upstream).
- No new dependencies, no new services, no scripts in this repo.

## Preconditions

- [ ] Verify MCP container is up: `docker ps --filter name=email-calendar-agent-mission-control-1 --format '{{.Status}}'` returns `Up …`.
- [ ] Confirm operator has write access to the `email-calendar-agent` repo and can rebuild + restart the container.
- [ ] Confirm a scratch Postgres instance is available for migration rehearsal (or be willing to test on the live DB after a verified backup).
- [ ] Confirm `.gemini/settings.json` already configures `mission-mcp` (it does, as of 2026-05-01).
- [ ] Confirm `.claude/settings.json` does **not** yet expose mission-mcp to Claude (it does not; addressed in Task 8).

---

## Task 1: Back up the brain DB

**Files:** none in this repo. Operator-side action.

- [ ] **Step 1.** From the host with DB access:
  ```bash
  pg_dump -h 192.168.0.225 -U <admin-user> -d brain \
    --format=custom --no-owner --no-acl \
    --file="brain-backup-$(date -u +%Y%m%dT%H%M%SZ).dump"
  ```
  Store the dump outside the running container's volume.
- [ ] **Step 2.** Verify the dump restores onto a scratch Postgres instance:
  ```bash
  pg_restore -h <scratch-host> -U <admin-user> -d brain_scratch \
    --no-owner --no-acl brain-backup-*.dump
  ```
  Confirm `SELECT count(*) FROM mission_tasks` matches the live DB.
- [ ] **Step 3.** Record the backup file path and timestamp in the operator's notes for rollback availability.

---

## Task 2: Branch the upstream `email-calendar-agent` repo

**Files:** in the upstream repo, not this one.

- [ ] **Step 1.** From the upstream repo, create a branch: `feat/mission-multi-agent-tasks`.
- [ ] **Step 2.** Tag the current upstream `main` with `pre-multi-agent` so rollback is one `git reset --hard pre-multi-agent` away.

---

## Task 3: Implement the schema migration upstream

**Files (upstream):**
- Create: `brain/migrations/2026-05-01-mission-multi-agent.sql`

- [ ] **Step 1.** Write the migration verbatim from the design v2 "Schema migration" section (`docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md` § Required upstream changes). The migration must:
  - Wrap in `BEGIN/COMMIT`.
  - Add columns with safe defaults so existing rows remain valid.
  - Backfill `status` from `is_done`.
  - Replace `is_done` with a generated column derived from `status`.
  - Add the `mission_task_events` audit table.
  - Add indexes on `(project, status)` and partial index on `requested_assignee` where `status='open'`.

- [ ] **Step 2.** Apply the migration to the scratch DB from Task 1 Step 2. Confirm:
  - `SELECT count(*) FROM mission_tasks WHERE project = 'operator'` equals the original row count.
  - `SELECT is_done FROM mission_tasks LIMIT 1` still works (generated column read).
  - Constraints reject invalid statuses: `INSERT … status='wat'` fails.

- [ ] **Step 3.** Do **not** apply to the live DB yet. Live deploy happens in Task 6 alongside the code changes.

---

## Task 4: Implement the new tool surface upstream

**Files (upstream):**
- Modify: `brain/mission_db.py`
- Modify: `brain/mission_server.py`

- [ ] **Step 1.** In `brain/mission_db.py`, rewrite `update_mission_task` to set `status` instead of `is_done` (the latter is now a generated column and cannot be written). Map `is_done=True → status='done'`, `is_done=False → status='open'` (clearing `claimed_by` and `claimed_at`).

- [ ] **Step 2.** In `brain/mission_db.py`, add helper functions for the new tools:
  - `add_mission_task(db_url, task_text, project, task_body, requested_assignee, parent_id, priority, blind)`
  - `list_mission_tasks(db_url, project, status, requested_assignee)`
  - `get_mission_task(db_url, task_id)` — returns row + last N events.
  - `claim_mission_task(db_url, task_id, claimer_id)` — implements the CAS shown in design v2 § Atomic claim primitive.
  - `complete_mission_task(db_url, task_id, completer_id, outcome)`
  - `refuse_mission_task(db_url, task_id, refuser_id, reason)`
  - `break_mission_claim(db_url, task_id, breaker_id, reason)` — only succeeds where `claimed_at < now() - interval '24 hours'`.
  - Each state-transition helper inserts a row into `mission_task_events` in the same transaction as the row update.

- [ ] **Step 3.** In `brain/mission_server.py`, add `@mcp.tool()` wrappers for each new helper, with the exact signatures specified in design v2 § New tool surface.

- [ ] **Step 4.** In `brain/mission_server.py`, update `fetch_summary_data` (operator dashboard read path) to filter `mission_tasks` queries with `WHERE project = 'operator'`. This isolates AIchallenge tasks from the operator's UI.

- [ ] **Step 5.** Keep `mission_add_task` backward-compatible: its existing single-arg signature (`task_text`) remains valid; new kwargs default to operator semantics. The operator dashboard's existing call sites need not change.

- [ ] **Step 6.** Add an authorization check on the state-transition tools: `mission_complete_task` and `mission_refuse_task` require `claimed_by == caller_id` (or an explicit `operator-override` actor). Reject otherwise.

- [ ] **Step 7.** Unit test the CAS: from two concurrent connections, both call `mission_claim_task` on the same `open` task. Confirm exactly one returns `claimed: true`.

---

## Task 5: Test on the scratch DB end-to-end

**Files (upstream):** test scripts under `brain/tests/` (or wherever the upstream keeps tests).

- [ ] **Step 1.** Wire the upstream code (with new tools) to the scratch DB.
- [ ] **Step 2.** Exercise:
  - Add an AIchallenge task: `mission_add_task("test", project='aichallenge', requested_assignee='claude')`.
  - Claim it: `mission_claim_task(<id>, 'claude-test-0001')` → returns `claimed: true`.
  - Attempt to claim again from the same id → `claimed: false`.
  - Complete it: `mission_complete_task(<id>, 'claude-test-0001', outcome='ok')`.
  - List operator tasks: confirm the AIchallenge task is **not** in the result.
  - Read `mission_task_events` for the test task: 3 rows (`created`, `claimed`, `completed`).
- [ ] **Step 3.** Exercise the operator path: add and toggle an operator task via `fetch_summary_data` and `update_mission_task`. Confirm `is_done` reflects the new status.

---

## Task 6: Deploy upstream changes to the live container

**Files:** none in this repo.

- [ ] **Step 1.** Confirm the backup from Task 1 is restorable. (Re-verify; do not skip.)
- [ ] **Step 2.** From the upstream repo, build and deploy:
  - Apply migration to live DB:
    ```bash
    psql -h 192.168.0.225 -U <admin-user> -d brain \
      -f brain/migrations/2026-05-01-mission-multi-agent.sql
    ```
  - Rebuild and restart the container so the new code is live:
    ```bash
    docker compose -f /path/to/email-calendar-agent/docker-compose.yml \
      up -d --build mission-control
    ```
- [ ] **Step 3.** Confirm container is healthy: `docker ps --filter name=email-calendar-agent-mission-control-1`.
- [ ] **Step 4.** Confirm the operator dashboard still loads tasks correctly (manual visual check of the dashboard URL). Add and complete a single operator task through the UI; confirm it persists.

**Rollback if any check fails:**

```bash
# 1. Restore container code
git -C /path/to/email-calendar-agent reset --hard pre-multi-agent
docker compose -f /path/to/email-calendar-agent/docker-compose.yml \
  up -d --build mission-control

# 2. Restore DB from backup (only if schema or data corruption observed)
pg_restore -h 192.168.0.225 -U <admin-user> -d brain --clean \
  brain-backup-*.dump
```

---

## Task 7: Mirror MCP config into Claude (this repo)

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1.** Add a `mcpServers.mission-mcp` entry that mirrors `.gemini/settings.json`:
  ```json
  {
    "mcpServers": {
      "mission-mcp": {
        "command": "docker",
        "args": ["exec", "-i", "email-calendar-agent-mission-control-1", "python", "brain/mission_server.py", "stdio"]
      }
    }
  }
  ```
  Preserve any existing keys.

- [ ] **Step 2.** In a fresh Claude session, list MCP tools and confirm the new ones are visible: `mission_claim_task`, `mission_complete_task`, `mission_refuse_task`, `mission_break_claim`, `mission_list_tasks`, `mission_get_task`, plus the existing `mission_add_task` (now with new optional kwargs) and `mission_get_strategy` / `mission_update_strategy`. If they are not visible, debug the MCP wiring before proceeding.

---

## Task 8: Seed the `aichallenge` strategy via MCP

- [ ] **Step 1.** Compose the seed payload from `docs/winning-strategy.md` and `docs/spec.md`. Proposed shape:
  ```json
  {
    "submission_track": "Track 1 — Build",
    "product_codename": "Methodic",
    "deadline_iso": "2026-06-05T17:00:00-07:00",
    "thesis": "No useful insights without good data; data capture is the weakest link.",
    "vertical_slice": "<one-paragraph slice description>",
    "stack_alignment": ["Gemini API", "ADK", "MCP", "Cloud Run"],
    "demo_must_show": [
      "agentic planning by organizer-facing AI",
      "methodology pushback on weak study designs",
      "interactive participant conversations",
      "measurable data quality improvement"
    ],
    "non_goals": [
      "marketing landing page before working experience",
      "over-claiming statistical rigor",
      "broad platform scope before vertical slice"
    ],
    "risks": [
      "harness coordination cost exceeds throughput gain",
      "Codex MCP transport unverified",
      "operator dashboard regression after migration"
    ]
  }
  ```

- [ ] **Step 2.** From an agent session with the MCP attached:
  ```
  mission_update_strategy(key="aichallenge", data={...payload from Step 1...})
  ```
  Capture the response.

- [ ] **Step 3.** Verify with `mission_get_strategy()` and confirm the returned dict contains the `aichallenge` key with the payload intact.

- [ ] **Step 4.** Do **not** check the JSON payload into git as a duplicate file. The MCP is the canonical store.

---

## Task 9: File the first round of tasks via MCP

- [ ] **Step 1.** File `001 — Adversarial review of design v2`:
  ```
  mission_add_task(
    task_text="Adversarial review of design v2",
    project="aichallenge",
    task_body="Read docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md. Review for unstated assumptions, race conditions, schema mismatches, contradictions between design and plan. Do not assume the author was correct. Required output: numbered list of issues with severity (Blocker|Major|Minor); ≥3 falsifiable assumptions; explicit verdict (ship-as-is | ship-with-changes | rewrite). Forbidden output: 'looks good' or any unscored validation.",
    requested_assignee="claude",
    priority="high",
    blind=True
  )
  ```

- [ ] **Step 2.** File `002 — Verify Codex MCP transport`:
  ```
  mission_add_task(
    task_text="Verify Codex MCP transport against mission-control",
    project="aichallenge",
    task_body="Confirm Codex (or whichever runtime fills that role) can connect to mission-mcp via docker exec stdio, list tools, and call mission_get_strategy() successfully. Document the exact configuration in .codex/ (or equivalent) or commit a non-participant note. Acceptance: configuration committed OR explicit non-participant decision recorded; round-trip evidence in completion outcome.",
    requested_assignee="codex",
    priority="high",
    blind=False
  )
  ```

- [ ] **Step 3.** File `003 — Draft Methodic vertical slice`:
  ```
  mission_add_task(
    task_text="Draft Methodic vertical slice — concrete demo path",
    project="aichallenge",
    task_body="Produce a vertical-slice demo plan at docs/methodic-vertical-slice.md. Constraints: Track 1 build, Gemini + ADK + MCP + Cloud Run, B2B framing, measurable data quality, no broad-platform scope, fits 5 weeks. Required: phased plan with daily-resolution milestones from 2026-05-02 to 2026-06-05; demo script (≤2 pages) showing the four demo_must_show items from mission_strategy['aichallenge']; explicit non-goals list referencing strategy non_goals.",
    requested_assignee="gemini",
    priority="high",
    blind=False
  )
  ```

- [ ] **Step 4.** Verify with `mission_list_tasks(project='aichallenge', status='open')` — three rows returned with the expected assignees.

---

## Task 10: End-to-end verification

- [ ] **Step 1.** From a Claude session, simulate the full loop on a throwaway task:
  - `mission_add_task("e2e-verification", project='aichallenge', requested_assignee='claude')`
  - `mission_claim_task(<id>, 'claude-2026-05-01T1100-e2e1')` → `claimed: true`
  - From a second session (or simulated second `claimer_id`), call `mission_claim_task(<id>, 'claude-2026-05-01T1100-e2e2')` → `claimed: false, reason='already_claimed'`
  - `mission_complete_task(<id>, 'claude-2026-05-01T1100-e2e1', outcome='e2e ok')`
  - `mission_get_task(<id>)` → status='done', completed_by populated, event log shows created/claimed/completed in order.
  - `mission_list_tasks(project='aichallenge', status='done')` → includes the e2e task.

- [ ] **Step 2.** Confirm operator isolation: from the operator dashboard, verify the e2e task does **not** appear and that no AIchallenge task is visible.

- [ ] **Step 3.** Confirm `mission_get_strategy()['aichallenge']` still returns the seeded payload from Task 8.

- [ ] **Step 4.** Optionally clean up: leave the e2e task in `done` (it's audit; harmless) or call a hypothetical cleanup. Recommendation: leave it as the first audit-trail entry.

---

## Task 11: Commit AIchallenge-side artifacts

**Files (this repo):**
- `.claude/settings.json` (from Task 7)
- `docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md`
- `docs/superpowers/plans/2026-05-01-mission-initialization-v2.md`

- [ ] **Step 1.** Stage explicitly (do not `git add .`):
  ```bash
  git add .claude/settings.json \
          docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md \
          docs/superpowers/plans/2026-05-01-mission-initialization-v2.md
  ```
- [ ] **Step 2.** Commit:
  ```
  chore: bootstrap v2 multi-agent harness (MCP-native, project-scoped tasks)
  ```
- [ ] **Step 3.** Verify `git log -1 --stat` matches expectations and that no credentials, no `192.168.0.x` connection strings, and no Postgres URLs appear in the diff.

---

## Risks and rollbacks

- **Operator dashboard regression after migration.** Highest-impact risk. Mitigations: scratch-DB rehearsal in Task 5; backup verified in Task 1; tagged rollback target in Task 2; explicit operator-side smoke test in Task 6 Step 4. Roll back via `git reset --hard pre-multi-agent` + `pg_restore`.
- **`mission_update_task` shim breaks legacy callers.** The dashboard calls `update_mission_task(db_url, id, is_done)`. After the migration, `is_done` is generated; the helper must write `status` instead. Caught by Task 5 Step 3 (operator-path test).
- **MCP not reachable from Claude after Task 7.** Symptom: tools not in tool list. Mitigation: revert `.claude/settings.json` change; harness still works for Gemini-only operation.
- **Codex MCP transport unverified.** Tracked as Task 9 Step 2. Until that completes, treat Codex as a non-participant and use `requested_assignee='any'` only when Claude or Gemini can pick up.
- **Operator's other projects accidentally see AIchallenge data.** Caught by Task 4 Step 4 (`fetch_summary_data` filter) and Task 6 Step 4 (visual check). If observed post-deploy, hotfix the filter; the data is harmless once filtered.
- **Harness fails the 2026-05-08 acceptance gate.** Recovery: ceasing AIchallenge tool calls leaves the operator's brain in a richer-but-compatible state. AIchallenge rows can be archived or `DELETE WHERE project='aichallenge'` if desired. Document the cause in `docs/superpowers/specs/2026-05-08-harness-postmortem.md`.

## Out of scope for this plan

- Building any part of Methodic (the actual Track 1 deliverable). Methodic build work is filed as tasks via this harness in Task 9 Step 3 and beyond.
- Adding an AIchallenge UI to the operator dashboard. The harness is agent-facing only for now; an operator-facing view of `project='aichallenge'` rows can be added later if useful.
- Multi-operator or remote agent participation. Single-operator local scope only.
