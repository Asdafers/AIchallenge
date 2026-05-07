# Agents — Operational Protocol

How Claude, Gemini, and Codex coordinate work in this project via the Mission Control MCP. If you are an AI agent landing in this repo to do AIchallenge work, **read this file before claiming a task**.

> Design rationale: `docs/superpowers/specs/2026-05-01-local-agent-collaboration-design-v2.md`.
> Implementation plan + execution log: `docs/superpowers/plans/2026-05-01-mission-initialization-v2.md`.
> One-time setup history (do not follow): `docs/archive/2026-05-01-agents-onboarding.md`.

**Failure rule.** All three runtimes are already wired to `mission-mcp`. Just call the tools. If any `mission_*` call returns an error or hangs, **stop and tell the operator** — do not investigate the container, logs, or config. The MCP error is the diagnostic.

---

## 1. Identify yourself

Pick a `claimer_id` for this session and reuse it for every claim/complete/refuse call. Format:

```
<model>-<UTC-timestamp>-<4-char-suffix>
```

- `model`: `claude` | `gemini` | `codex`
- `UTC-timestamp`: `YYYY-MM-DDTHHMM` (minute precision)
- `4-char-suffix`: lowercase hex you generate once, reuse all session

Examples: `claude-2026-05-01T1024-a3f7`, `gemini-2026-05-08T0915-9b2c`, `codex-2026-05-12T1730-44de`.

The suffix disambiguates two sessions of the same model started in the same minute; uniqueness is per-session, not global.

---

## 2. The execution loop

### Step 1 — List

```
mission_list_tasks(project="aichallenge", status="open", requested_assignee="<your_model>")
```

Returns dicts with `id`, `task_text`, `task_body`, `priority`, `blind`, `parent_id`. Pick the highest-priority task. If none match your assignee, also try `requested_assignee="any"`.

### Step 2 — Read the strategy (anti-drift gate)

```
mission_get_strategy()
```

The `aichallenge` key holds the canonical project strategy: track, codename, deadline, thesis, vertical_slice, demo_must_show, non_goals, risks. You must cite at least one section in your completion outcome.

### Step 3 — Claim (atomic CAS)

```
mission_claim_task(task_id="<id>", claimer_id="<your-claimer-id>")
```

Returns `{"claimed": true|false, "task": {...}|null, "reason": "<string>|null"}`.

- `claimed: true` → you own this task. Proceed.
- `claimed: false` → another agent claimed it first (`not_found`, `already_claimed_by:<id>`, `status:<not-open>`). Do **not** retry; go back to step 1 and pick another.

The CAS is server-side atomic. No double-claim is possible.

### Step 4 — Read full task

```
mission_get_task(task_id="<id>")
```

Returns `{"task": {...row}, "events": [...]}`. Read `task_body` carefully. If `parent_id` is set, also `mission_get_task(parent_id)` — you are doing a child task (often a review of the parent's output).

### Step 5 — Strategy linkage (anti-drift)

In your working notes, write a 2–3 sentence rationale connecting this task to a strategy section (cite the section name, e.g. `demo_must_show[2]`). If you cannot honestly write one, **refuse**:

```
mission_refuse_task(task_id="<id>", refuser_id="<your-claimer-id>",
                    reason="cannot link to mission_strategy['aichallenge']: <why>")
```

Refusal is a first-class outcome — it forces drift to be visible in the audit trail.

### Step 6 — Execute

Do the work. File edits go in normal git commits, referencing the task UUID's first 8 chars if useful. Stay scoped.

### Step 7 — Peer review delegation (optional)

If your work needs a second pair of eyes:

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

When `blind=True`, do **not name yourself in the task body**. Use third-person framing ("the implementation at <path>"), not "the work I just did."

### Step 8 — Complete

```
mission_complete_task(task_id="<id>", completer_id="<your-claimer-id>", outcome="<structured outcome>")
```

Auth check: only the agent that claimed can complete (`completer_id` must equal `claimed_by`). The string `"operator-override"` is reserved for the human.

#### Outcome string convention

For non-review tasks: a short paragraph plus a bulleted list of artifacts (commit SHAs, file paths, URLs).

For **review tasks** (`parent_id is not None`), the outcome MUST contain:

1. A numbered list of issues, each labeled `Blocker | Major | Minor`.
2. At least 3 falsifiable assumptions whose violation would invalidate the work.
3. An explicit verdict: `ship-as-is` | `ship-with-changes` | `rewrite` (with rationale).

A review missing any of these is, by protocol, **not a completed review**. Forbidden outcomes for reviews: "looks good", "well done", any unscored validation.

### Step 9 — Loop

Back to step 1 until no matching tasks remain or the operator stops you.

---

## 3. Conventions

- **Assignee strings.** Exactly: `claude`, `gemini`, `codex`, `any`, or `NULL`. The CHECK constraint rejects variants.
- **Priority.** `low | medium | high`. Default `medium`. `high` is reserved for tasks that block the 2026-06-05 deadline.
- **Blind reviews.** `blind=True` is a marker plus an authoring convention: marker tells the reviewer to adopt adversarial posture, convention tells the author not to leak the executor's identity in the body.
- **Strategy edits.** Use `mission_update_strategy("aichallenge", {...})` — full replacement of the `aichallenge` key. Read first, modify, write back; last-writer-wins. **Do not** edit any other key.
- **Commit messages.** Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

---

## 4. What not to do

- **Do not touch `project='operator'` rows.** Those belong to the operator's business board.
- **Do not call `mission_update_task(task_id, is_done)`.** That is the legacy operator-dashboard tool, scoped to `project='operator'`. Use `mission_complete_task` / `mission_refuse_task` / `mission_break_claim`.
- **Do not bypass `mission_claim_task` by editing rows directly.** The CAS is the only correct way to take ownership.
- **Do not claim a task whose `parent_id` chain traces back to your own work.** Self-review defeats anti-sycophancy. Walk the parent chain via `mission_get_task` if uncertain.
- **Do not write to `mission_strategy` keys other than `aichallenge`.**
- **Do not push a feature branch before reviewing your own diff.**
- **Do not investigate harness infrastructure.** If MCP calls fail, halt and tell the operator (see Failure rule at top).

---

## 5. Acceptance gate (2026-05-08)

Until 2026-05-08 the harness is on probation (see v2 design § "Acceptance criteria for the harness itself"). Every task you complete contributes evidence: completions count toward "≥5 tasks", refusals with strategy-linkage rationale count too, structured reviews count toward "≥1 blind review", and any double-execution trips the gate. The deliverable is Methodic, not the harness — if the harness gets in the way, abandon it and tell the operator.
