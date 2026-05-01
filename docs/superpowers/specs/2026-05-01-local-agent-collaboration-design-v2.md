# Local Agent Collaboration Workflow — Design v2 (Path M)

> Supersedes `2026-05-01-local-agent-collaboration-design.md`.
> Date: 2026-05-01. Status: Proposed.
> Mode: **Path M (MCP-native)** — task coordination lives in the mission-control MCP, with schema and tool surface extended to support multi-agent claims. The operator owns the upstream MCP and chose to expand it rather than work around its constraints.

## What changed from v1

A review of v1 surfaced four problems that this revision fixes:

1. **Race condition unsolved.** v1's "Concurrency Mitigation" was read-then-write — exactly the TOCTOU race it claimed to address. v2 replaces it with `mission_claim_task`, an atomic compare-and-swap implemented as a single SQL `UPDATE ... WHERE status='open' RETURNING ...`.
2. **Seed plan contradicted the design's premise.** v1's pair plan wrote directly to Postgres with hardcoded credentials, bypassing the MCP it called canonical. v2 has no scripts, no credentials, no DB-direct access — every write is an MCP tool call.
3. **Stringly-typed protocol.** v1 packed assignee + status + free text into one column because the schema offered no alternative. v2 promotes assignee, status, claim ownership, parent, priority, and blind-review flag to first-class columns.
4. **Schema mismatch with the actual upstream MCP.** v1 referenced tools and behaviors the upstream did not implement (`mission_tasks` is `(id, task_text, is_done)` with `task_text` truncated to 150 chars on compact reads). v2 specifies the exact additive migration that makes the rest of the design real, and includes the upstream changes in the implementation plan.

## Architectural choice: MCP-native, single canonical store

Single source of truth for tasks and strategy. The operator's existing dashboard remains the UI; AIchallenge agents extend the same store under a project namespace. Path H (file-based ledger) was rejected because the operator owns the MCP and prefers a single coherent backend over lifecycle separation.

Cost trade: ~1–2 days of upstream Python + SQL work, paid once. The harness then runs without coordination overhead in this repo.

## Project namespace

All AIchallenge rows carry `project = 'aichallenge'`. The operator's existing rows are migrated to `project = 'operator'`. Every read and write from AIchallenge agents passes `project='aichallenge'`. The operator's dashboard is updated to filter to `project='operator'` so the existing UX is unchanged.

This is the single most important isolation invariant. Violating it pollutes the operator's business board.

## Task lifecycle (state machine)

```
        mission_add_task                 mission_claim_task
   ──────────────────────►  open  ──────────────────────►  claimed
                             ▲                                │
                             │ mission_break_claim            │
                             │ (claimed_at > 24h)             │
                             └────────────────────────────────┤
                                                              │
                  ┌───────────────────────────────────────────┤
                  │                                           │
                  │ mission_refuse_task                       │ mission_complete_task
                  ▼                                           ▼
              refused                                       done
```

States:

- `open` — filed, unclaimed.
- `claimed` — atomically owned by exactly one agent identity.
- `done` — completed; immutable; carries `completed_by`, `completed_at`, and an outcome record.
- `refused` — the assignee determined the task should not be executed (e.g., cannot link to strategy). Carries `refused_reason`. Terminal; a different task can be filed if the work is still desired.
- `broken_claim` — a stale claim (>24h) was forcibly returned to `open` by another agent. Recorded as a transition event, not a sticky state; the row reverts to `open`.

`in_review` is **not** a state. Reviews are first-class child tasks with `parent_id` set; the parent stays `claimed` (by the executor) until the reviewer completes the child task and the executor decides what to do. This avoids parent/child status entanglement.

## Required upstream changes

These are additive, deployable to the running container without breaking the operator's dashboard. Implementation lives in the email-calendar-agent repo, not this one.

### Schema migration

```sql
BEGIN;

ALTER TABLE mission_tasks
  ADD COLUMN project              TEXT NOT NULL DEFAULT 'operator',
  ADD COLUMN task_body            TEXT,
  ADD COLUMN requested_assignee   TEXT,
  ADD COLUMN status               TEXT NOT NULL DEFAULT 'open',
  ADD COLUMN claimed_by           TEXT,
  ADD COLUMN claimed_at           TIMESTAMPTZ,
  ADD COLUMN completed_by         TEXT,
  ADD COLUMN completed_at         TIMESTAMPTZ,
  ADD COLUMN parent_id            TEXT,
  ADD COLUMN priority             TEXT NOT NULL DEFAULT 'medium',
  ADD COLUMN blind                BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN refused_reason       TEXT;

ALTER TABLE mission_tasks
  ADD CONSTRAINT mission_tasks_status_chk
    CHECK (status IN ('open','claimed','done','refused')),
  ADD CONSTRAINT mission_tasks_priority_chk
    CHECK (priority IN ('low','medium','high')),
  ADD CONSTRAINT mission_tasks_assignee_chk
    CHECK (requested_assignee IS NULL OR requested_assignee IN ('claude','gemini','codex','any'));

-- Backfill existing rows: any row with is_done=true becomes status='done'.
UPDATE mission_tasks SET status = 'done' WHERE is_done = TRUE;

-- Keep is_done backward-compatible with the operator's existing dashboard reads.
-- Drop the writable column and replace with a derived view of status.
ALTER TABLE mission_tasks DROP COLUMN is_done;
ALTER TABLE mission_tasks
  ADD COLUMN is_done BOOLEAN GENERATED ALWAYS AS (status = 'done') STORED;

CREATE INDEX idx_mission_tasks_project_status ON mission_tasks(project, status);
CREATE INDEX idx_mission_tasks_assignee_open
  ON mission_tasks(requested_assignee) WHERE status = 'open';

CREATE TABLE mission_task_events (
  id          BIGSERIAL PRIMARY KEY,
  task_id     TEXT NOT NULL REFERENCES mission_tasks(id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,         -- created|claimed|completed|refused|broken|edited
  actor       TEXT,
  details     JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mission_task_events_task ON mission_task_events(task_id, occurred_at);

COMMIT;
```

Notes on safety:

- All new columns are nullable or have defaults — no read paths break.
- `is_done` is regenerated as a generated column derived from `status`. Existing reads (`SELECT is_done FROM mission_tasks`) continue to work.
- `update_mission_task(db_url, task_id, is_done)` in `brain/mission_db.py` must be rewritten to update `status` instead, since `is_done` is no longer writable. This is a code change paired with the migration.
- Do not run this migration without first taking a database backup. The brain DB is shared with operator-critical workflows (Stripe MRR, lead pipeline, marketing).

### New tool surface

Added in `brain/mission_server.py`. Existing tools remain for backward compatibility; the operator dashboard's call sites need not change beyond the `update_mission_task` signature shim.

```python
@mcp.tool()
async def mission_add_task(
    task_text: str,
    project: str = "operator",
    task_body: str | None = None,
    requested_assignee: str | None = None,
    parent_id: str | None = None,
    priority: str = "medium",
    blind: bool = False,
) -> dict:
    """Add a task. AIchallenge agents pass project='aichallenge'."""

@mcp.tool()
async def mission_list_tasks(
    project: str = "aichallenge",
    status: str | None = None,
    requested_assignee: str | None = None,
) -> list[dict]:
    """Filtered list. Returns full rows including task_body."""

@mcp.tool()
async def mission_get_task(task_id: str) -> dict:
    """Read a single task by id, including task_body and event history (last N)."""

@mcp.tool()
async def mission_claim_task(task_id: str, claimer_id: str) -> dict:
    """Atomic CAS claim.
    SQL: UPDATE mission_tasks
            SET status='claimed', claimed_by=$1, claimed_at=now()
          WHERE id=$2 AND status='open'
          RETURNING *;
    Returns {claimed: bool, task: dict | None, reason: str | None}.
    Also inserts a row into mission_task_events with event_type='claimed'."""

@mcp.tool()
async def mission_complete_task(
    task_id: str, completer_id: str, outcome: str
) -> dict:
    """Atomic completion. Requires the caller to be the current claimer
    (claimed_by = completer_id) unless completer_id == 'operator-override'.
    Sets status='done', completed_by, completed_at; inserts task_events row."""

@mcp.tool()
async def mission_refuse_task(
    task_id: str, refuser_id: str, reason: str
) -> dict:
    """Refuse a claimed task. Sets status='refused', refused_reason.
    Caller must be current claimer."""

@mcp.tool()
async def mission_break_claim(
    task_id: str, breaker_id: str, reason: str
) -> dict:
    """Recover a stale claim. Requires claimed_at < now() - interval '24 hours'.
    Returns task to status='open', clears claimed_by/claimed_at,
    inserts task_events row with event_type='broken'."""
```

Backward-compatible shim:

```python
@mcp.tool()
async def mission_update_task(task_id: str, is_done: bool) -> str:
    """[Backward-compat] Toggles status between 'open' and 'done'.
    Operator dashboard continues to use this. AIchallenge agents MUST NOT —
    use mission_complete_task or mission_refuse_task instead."""
    # Map true → status='done' (via mission_complete_task with outcome='legacy')
    # Map false → status='open' (clearing claim fields and inserting an 'edited' event)
```

### Operator dashboard isolation

`fetch_summary_data()` is updated to `WHERE project = 'operator'` for all `mission_tasks` reads. Operator UI sees nothing AIchallenge-related. AIchallenge has no UI in the dashboard until/unless added intentionally.

## Atomic claim primitive — semantics

`mission_claim_task` is the load-bearing primitive. A correct implementation:

```sql
WITH claimed AS (
  UPDATE mission_tasks
     SET status='claimed', claimed_by=$1, claimed_at=now()
   WHERE id=$2 AND status='open'
  RETURNING *
)
INSERT INTO mission_task_events (task_id, event_type, actor, details)
SELECT id, 'claimed', $1, jsonb_build_object('claimed_at', claimed_at)
FROM claimed
RETURNING (SELECT * FROM claimed);
```

The `WHERE status='open'` predicate makes this atomic at the row level under Postgres' default `READ COMMITTED`. Two concurrent claim attempts on the same task: one sees `status='open'` and updates; the other's `WHERE` clause matches zero rows. Both calls return; only one carries `claimed: true`. No application-level locking required.

The `claimer_id` convention is `<model>-<YYYY-MM-DDTHHMM>-<4-char-suffix>` — e.g., `claude-2026-05-01T1024-a3f7`. Agents pick a session-scoped suffix once. Collisions across sessions are theoretically possible but operationally negligible at single-operator scale.

## Anti-sycophancy: structural enforcement

v1 relied on prompting the reviewer to "act as a strict critic." v2 makes critical posture **structurally enforced** at the protocol level:

- **Author-blinding via the `blind` column.** When a review task has `blind=true`, the executor's identity is not revealed in the task body, and the executor is operationally indistinguishable from a first-time reader. Enforced by convention in task body authoring.
- **Required output schema.** Reviews must produce a numbered list of issues with severity (`Blocker | Major | Minor`). A review whose completion outcome lacks a numbered list is, by protocol, not complete; the reviewer should call `mission_refuse_task` with reason "did not produce required schema."
- **Mandatory falsification step.** Every review lists at least 3 assumptions whose violation would break the work. If fewer than 3 are reachable, the review must say so explicitly and explain why.
- **No self-review.** An agent must not claim a task whose `parent_id` chain traces back to a task they completed. Enforced by convention; the `mission_get_task` parent traversal is cheap to walk.

## Anti-drift: forced linkage

Every task execution writes a `strategy_linkage` paragraph (delivered as part of the completion outcome string) citing a section of `mission_strategy['aichallenge']`. If the agent cannot honestly write one, the task is refused via `mission_refuse_task` — not silently rationalized. This converts drift from a soft tendency into an explicit decision visible in `mission_task_events`.

## Reliability semantics

| Failure mode                     | Behavior                                                                                                        |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| MCP container down               | Agents block. There is no local fallback in Path M; the MCP is the single store. Operator restarts container.   |
| Postgres / Brain DB down         | Same — agents block. Both the MCP and the operator dashboard are unavailable.                                   |
| Agent crash mid-task             | Claim becomes stale after 24h and may be broken by `mission_break_claim`.                                       |
| Two agents claim the same task   | Cannot happen — Postgres row update CAS serializes. Second claimer receives `claimed: false`.                   |
| Two agents file conflicting edits to the same workspace file | Standard git merge conflict in this repo. Lower-priority concern; both agents are local to one operator. |
| Strategy update conflict         | `mission_update_strategy` is last-writer-wins. Mitigation: keep AIchallenge strategy edits short and infrequent. |
| Operator dashboard regression after migration | See migration safety section; mitigated by test in plan Task 5 and by `is_done` generated column.   |

## Acceptance criteria for the harness itself

The harness is **working** if, by 2026-05-08:

- [ ] At least 5 AIchallenge tasks have moved through `open → claimed → done` (or `→ refused`).
- [ ] At least 1 review task with `blind=true` produced a numbered-issue-list outcome and resulted in a follow-up edit.
- [ ] Zero cases where two agents executed the same task. (Confirmable by querying `mission_task_events` for duplicate `claimed` events on the same task_id with different actors.)
- [ ] Zero cases where AIchallenge tasks appeared in the operator's dashboard. (Confirmable by visual check of the dashboard.)
- [ ] Operator dashboard regression: zero. (No change in operator's task counts, totals, or behavior compared to a snapshot taken before the migration.)
- [ ] At least 60% of work that should have gone through the harness actually did.

If any of these fail by 2026-05-08, the harness is rolled back: the schema migration is non-destructive (additive columns; the `is_done` generated column preserves dashboard semantics) so rollback is mostly a matter of ceasing AIchallenge tool calls and optionally truncating `WHERE project='aichallenge'`. Document the cause in `docs/superpowers/specs/2026-05-08-harness-postmortem.md`.

## Migration safety

The schema migration touches a production database serving the operator's business. Required safeguards in execution order:

1. **Take a logical backup** of the brain DB (`pg_dump`) before any schema change. Verify restore on a scratch DB.
2. **Apply the migration in a transaction.** The SQL above is wrapped in `BEGIN/COMMIT`; if any statement fails, the whole migration rolls back.
3. **Update `brain/mission_db.py` and `brain/mission_server.py` in lockstep with the migration.** Specifically: `update_mission_task` cannot write `is_done` after the column becomes generated — it must write `status` instead. The deploy must include both the SQL and the code; do not deploy SQL ahead of code or vice versa.
4. **Smoke-test the operator dashboard immediately after deploy.** Add/toggle a task via the operator's UI; confirm it persists and `is_done` updates as expected.
5. **Only after 1–4 pass**, exercise the AIchallenge tool path end-to-end (plan Task 7 below).

## When NOT to use this harness

If, after one full week of running v2, the multi-agent loop is producing more coordination overhead than throughput, fall back to **a single Claude session using the `Agent` subagent tool for parallelism**. The deliverable is the Methodic Track 1 submission by 2026-06-05, not the harness. This decision is preserved from the Path H draft because the strategic question is independent of the architecture choice.

Concrete fallback trigger: by 2026-05-08, evaluate against the acceptance criteria above. If <60% of "should have been agent-driven" tasks went through the harness, abandon it. The schema migration leaves the operator's brain in a richer-but-compatible state regardless.

## Open questions

- **Codex runtime.** Confirm Codex has MCP support compatible with `docker exec -i ... stdio` in this workspace. If not, treat Codex as a non-participant; the protocol works with any subset of {Claude, Gemini, Codex}.
- **Strategy seed content.** The initial `aichallenge` strategy JSON is decided in plan Task 6. Proposed shape mirrors `docs/winning-strategy.md` so linkage paragraphs cite stable section keys.
- **Task event retention.** `mission_task_events` will accumulate indefinitely. For sprint scope, no retention policy. Revisit if the table grows unwieldy.
- **Multi-instance same-model identity.** `claimer_id` carries a 4-char suffix to disambiguate concurrent same-model sessions. If concurrency increases beyond a few sessions, consider a registration tool that mints unique ids server-side.
