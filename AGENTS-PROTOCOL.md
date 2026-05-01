# Agents — Operational Protocol

How Claude, Gemini, and Codex coordinate work in this project via the Mission Control MCP. If you are an AI agent landing in this repo to do AIchallenge work, **read this file before claiming a task**.

> Design rationale: `docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md`.
> Implementation plan + execution log: `docs/superpowers/plans/2026-05-01-mission-initialization-v2.md`.
> This file is the *operational quickstart*; the spec is the *why*.

---

## 1. Connect

The Mission Control MCP runs in a local Docker container `email-calendar-agent-mission-control-1`. All three CLIs reach it via `docker exec -i ... stdio`. The container must already be up — verify with `docker ps --filter name=email-calendar-agent-mission-control-1`.

### Claude Code
Already wired. See `.claude/settings.json` in this repo (committed). No further setup.

### Gemini CLI
Already wired. See `.gemini/settings.json` in this repo (committed). No further setup.

### Codex CLI
Add this block to `~/.codex/config.toml` on the host running Codex:

```toml
[mcp_servers.mission-mcp]
command = "docker"
args = [
    "exec",
    "-i",
    "email-calendar-agent-mission-control-1",
    "python",
    "brain/mission_server.py",
    "stdio",
]
```

(Reference: Codex CLI MCP server config docs. Tool-level approval modes can be added under `[mcp_servers.mission-mcp.tools.<name>]` if you want approval prompts on specific writes.)

### Verify the connection
From any of the three runtimes, call:

```
mission_get_strategy()
```

You should see a dict whose keys include `aichallenge`. If `aichallenge` is missing, the harness is not seeded and you should stop and tell the operator.

---

## 2. Identify yourself

Pick a `claimer_id` for this session and reuse it for every claim/complete/refuse call you make. Format:

```
<model>-<UTC-timestamp>-<4-char-suffix>
```

- `model`: `claude` | `gemini` | `codex`
- `UTC-timestamp`: `YYYY-MM-DDTHHMM` (no seconds; minute precision is enough for human-scale concurrency)
- `4-char-suffix`: lowercase hex you generate once, reuse all session

Examples: `claude-2026-05-01T1024-a3f7`, `gemini-2026-05-08T0915-9b2c`, `codex-2026-05-12T1730-44de`.

The suffix exists to disambiguate two sessions of the same model started in the same minute. You make it up; correctness depends on uniqueness within your session, not global registry.

---

## 3. The execution loop

Every work session follows this sequence. Step numbers map to the v2 design's "Execution loop" section.

### Step 1 — Sync & list

```
mission_list_tasks(project="aichallenge", status="open", requested_assignee="<your_model>")
```

Returns a list of dicts. Each has `id` (UUID), `task_text` (title), `task_body` (long-form), `priority`, `blind`, `parent_id`. Pick the highest-priority task. If no tasks match your assignee, also try `requested_assignee="any"`.

### Step 2 — Read the strategy (anti-drift gate)

```
mission_get_strategy()
```

The `aichallenge` key holds the canonical project strategy: track, codename, deadline, thesis, vertical_slice, demo_must_show, non_goals, risks. Read it now. You will need to cite at least one section in your completion outcome.

### Step 3 — Claim (atomic CAS)

```
mission_claim_task(task_id="<id-from-step-1>", claimer_id="<your-claimer-id>")
```

Returns `{"claimed": true|false, "task": {...}|null, "reason": "<string>|null"}`.

- `claimed: true` → you own this task. Proceed.
- `claimed: false` → another agent claimed it before you. Reasons: `not_found`, `already_claimed_by:<id>`, `status:<not-open>`. Do **not** retry the same task; go back to step 1 with a fresh `mission_list_tasks` call and pick another.

The CAS is server-side atomic. There is no race window large enough to claim the same task twice.

### Step 4 — Read full task

```
mission_get_task(task_id="<id>")
```

Returns `{"task": {...row}, "events": [{event_type, actor, details, occurred_at}, ...]}`. Read the `task_body` carefully. If `parent_id` is set, also `mission_get_task(parent_id)` — you are doing a child task (often a review of the parent's output).

### Step 5 — Strategy linkage (anti-drift)

In your working notes, write a 2–3 sentence rationale connecting this task to a strategy section (cite the section name, e.g. `demo_must_show[2]` or `risks[0]`). If you cannot honestly write one, **refuse the task** rather than rationalize:

```
mission_refuse_task(task_id="<id>", refuser_id="<your-claimer-id>",
                    reason="cannot link to mission_strategy['aichallenge']: <why>")
```

This is a feature, not a failure mode. Refusal is a first-class outcome; it forces drift to be visible in the audit trail.

### Step 6 — Execute

Do the work. File edits go in normal git commits (any message format), referencing the task UUID's first 8 chars for traceability if useful. Stay scoped to what the task asks.

### Step 7 — Peer review delegation (optional)

If your work needs a second pair of eyes, file a child task:

```
mission_add_task(
    task_text="Adversarial review of <thing>",
    project="aichallenge",
    task_body="<what to review, where it lives, what to look for>",
    requested_assignee="<other_model>",
    parent_id="<your-task-id>",
    priority="medium",
    blind=True
)
```

When you set `blind=True`, you must **not name yourself in the task body**. Use third-person framing ("the implementation at <path>"), not "the work I just did."

### Step 8 — Complete

```
mission_complete_task(
    task_id="<id>",
    completer_id="<your-claimer-id>",
    outcome="<structured outcome — see below>"
)
```

Returns `{"completed": true|false, "task": {...}, "reason": ...}`. Auth check: only the agent that claimed can complete (`completer_id` must equal `claimed_by`). The string `"operator-override"` is reserved for the human; do not use it as a claimer.

#### Outcome string convention

For non-review tasks: a short paragraph plus a bulleted list of artifacts (commit SHAs, file paths, URLs).

For **review tasks** (`parent_id is not None`), the outcome MUST contain:

1. A numbered list of issues, each labeled `Blocker | Major | Minor`.
2. At least 3 falsifiable assumptions whose violation would invalidate the work.
3. An explicit verdict: `ship-as-is` | `ship-with-changes` | `rewrite` (with rationale).

A review whose outcome lacks the numbered list, the falsification step, or an explicit verdict is, by protocol, **not a completed review**. Refuse with `mission_refuse_task` or revise before completing. Forbidden outcomes for reviews: "looks good", "well done", or any unscored validation.

### Step 9 — Loop

Back to step 1 until no matching tasks remain or the operator stops you.

---

## 4. Conventions

### Assignee strings
The `requested_assignee` column accepts exactly: `claude`, `gemini`, `codex`, `any`, or `NULL`. The CHECK constraint will reject anything else; do not invent variants.

### Priority
`low | medium | high`. Default `medium`. `high` is reserved for the small handful of tasks that block the 2026-06-05 deadline.

### Blind reviews
`blind=True` is a marker plus an authoring convention. The marker tells the reviewer to adopt adversarial posture; the convention tells the *task author* not to leak the executor's identity in the body. Both halves are needed.

### Strategy edits
Use `mission_update_strategy("aichallenge", {...})` — a full replacement of the `aichallenge` key. Read first, modify, write back; this is last-writer-wins. **Do not** edit any other key.

### Commit messages
Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`) — the upstream `email-calendar-agent` repo enforces this via commitizen. AIchallenge does not enforce, but follow the convention for consistency.

---

## 5. What not to do

- **Do not touch `project='operator'` rows.** Those belong to the operator's business board (Stripe MRR, lead pipeline, marketing milestones). The dashboard reads filter to operator-only; AIchallenge agents never write there.
- **Do not call `mission_update_task(task_id, is_done)`.** That is the legacy operator-dashboard tool, scoped to `project='operator'`. AIchallenge agents must use `mission_complete_task` / `mission_refuse_task` / `mission_break_claim`. The legacy tool is rejected against AIchallenge rows by design.
- **Do not bypass `mission_claim_task` by editing rows directly.** The CAS is the only correct way to take ownership. Direct UPDATE bypasses the audit event and the no-double-claim invariant.
- **Do not claim a task whose `parent_id` chain traces back to your own work.** Self-review defeats anti-sycophancy. Walk the parent chain via `mission_get_task` if uncertain.
- **Do not write to `mission_strategy` keys other than `aichallenge`.** All other keys belong to the operator's business state.
- **Do not push a feature branch before reviewing your own diff.** The repo's conventions assume reviewed work; surprise pushes erode the audit trail.

---

## 6. Self-check before you claim your first real task

Run this round-trip from your runtime to confirm everything is wired:

1. `mission_get_strategy()` → returns dict including `aichallenge` key. ✅ MCP reachable, namespace seeded.
2. `mission_list_tasks(project="aichallenge", status="open")` → returns ≥0 rows of dicts. ✅ Tool surface is the new schema.
3. Pick any returned `task["id"]`, then `mission_get_task(task_id=<id>)` → returns `{task, events}` with at least the `created` event. ✅ Audit trail is intact.

If any of these fails, stop and tell the operator. Do not "work around it."

---

## 7. Acceptance gate (2026-05-08)

The harness has an explicit go/no-go on 2026-05-08 (see v2 design § "Acceptance criteria for the harness itself"). Until then, every task you complete contributes to the gate's evidence:

- Completed tasks count toward the "≥5 tasks" criterion.
- Refused tasks with strategy-linkage rationale count too — refusals are first-class outcomes.
- Reviews with structured output count toward the "≥1 blind review" criterion.
- Any double-execution (same `task_id` claimed by two distinct actors) trips the gate.

If the gate fails, the harness is rolled back per design; the schema migration leaves the operator's brain in a richer-but-compatible state regardless. The deliverable is Methodic, not the harness — if the harness gets in the way, abandon it.
