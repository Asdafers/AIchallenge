# CLAUDE.md

## Skills Policy (MANDATORY)

Before starting ANY task — including answering questions, exploring code, or planning — search available skills for relevance. If a skill has even a marginal chance of applying, invoke it via the Skill tool before proceeding.

Key skills to always consider:
- `superpowers:using-superpowers` — master skill discovery; invoke at session start
- `superpowers:code-reviewer` — after completing major implementation steps
- Brainstorming/planning skills — before entering plan mode or designing features
- Debugging skills — when investigating errors or unexpected behavior
- Domain-specific skills — match to task type (frontend, MCP, API, etc.)

**Do not rationalize skipping skills.** "This is just a quick fix" or "I already know what to do" are not valid reasons to skip the skill check.

## Design-Before-Code (MANDATORY)

For any non-trivial implementation (new scripts, multi-file changes, features with contracts or acceptance criteria):

1. **Plan first** — enter plan mode or produce a written design before writing any code. The plan must cover: inputs/outputs, data flow, key functions, contract boundaries, and what is explicitly out of scope.
2. **Get alignment** — present the plan to the user. Do not begin implementation until the user approves or redirects.
3. **Track progress** — use tasks to break the plan into steps and mark completion as you go.

"I already know what to build" is not a valid reason to skip planning. The plan catches design errors before they become code errors.

## Project Context

- B2B SaaS win-loss vertical slice (Methodic) for Google AI Agent Challenge
- Multi-agent coordination via Mission-MCP (see AGENTS-PROTOCOL.md for claim/complete protocol)
- Gemini ACP integration for cross-model dispatch (see docs/gemini-acp-control.md)
- Canonical schema: 8 structured_fields in docs/schema/participant-response.schema.json

## Validation

After any fixture or schema change, run both validators:
```bash
python3 scripts/validate_schemas.py docs/schema
python3 scripts/validate_fixtures.py
```

## Conventions

- Scripts go in `scripts/`, fixtures in `fixtures/`, schemas in `docs/schema/`
- Commits must not bundle unrelated artifacts (e.g., don't mix product code with harness infrastructure)
- Sandbox is disabled in settings.local.json for ACP network access — do not re-enable
- When completing mission tasks, cite `mission_strategy['aichallenge']` in completion outcomes
- Claimer ID format: `model-YYYY-MM-DDTHHMM-XXXX` (see AGENTS-PROTOCOL.md)
