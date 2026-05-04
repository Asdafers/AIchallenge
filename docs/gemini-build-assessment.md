# Gemini-Perspective Build Assessment

**Date:** 2026-05-04
**Source:** Web research on current ADK/Gemini/A2A ecosystem (Claude-authored, Gemini ACP failed)
**Purpose:** Independent technical assessment of what's needed to build the real Methodic agent

## Key Discovery: ADK Is Ready

The biggest finding from research: **Google ADK is production-ready and does most of the heavy lifting we assumed we'd build ourselves.**

| Capability | ADK Support | Our Current State |
|-----------|-------------|-------------------|
| `SequentialAgent` | Built-in | We manually chain scripts |
| `ParallelAgent` | Built-in | We don't parallelize |
| `LoopAgent` | Built-in | We fake coverage loops |
| `LlmAgent` | Built-in (Gemini native) | We don't use LLM for conversations |
| MCP integration | `McpToolset` wraps any MCP server | We have a working MCP server (wp6) ✓ |
| A2A protocol | Native ADK support, Python SDK | We read fixture JSON files |
| Cloud Run deploy | `adk deploy cloud_run` (one command) | We have a Dockerfile, never deployed |
| Web UI | `adk web` dev server built-in | We have nothing |

### What This Means

We don't need to build an orchestration framework. We don't need to build MCP client code. We don't need to figure out A2A. We don't need to write a web server. **ADK provides all of this out of the box.**

Our job reduces to: **write the agent prompts, define the tools, and wire up the flow.**

## Recommended Architecture

### Package: `google-adk`

```
pip install google-adk
```

### Agent Structure (ADK pattern)

```
methodic/
  __init__.py
  agent.py              # root_agent (SequentialAgent)
  agents/
    organizer.py        # LlmAgent — accepts request, asks clarification
    methodology.py      # LlmAgent — pushes back on bad methodology
    question_design.py  # LlmAgent — designs question pool
    interviewer.py      # LlmAgent — conducts participant conversations
    quality.py          # LlmAgent — scores data quality
    replanner.py        # LlmAgent — decides if more sessions needed
  tools/
    mcp_deal_context.py # McpToolset wrapping our existing wp6_mcp_server.py
    bigquery_export.py  # FunctionTool for BQ writes
```

### Root Agent (Simplified)

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, LlmAgent
from google.adk.tools import McpToolset

root_agent = SequentialAgent(
    name="methodic",
    sub_agents=[
        organizer_agent,        # Accept request, clarify
        methodology_agent,      # Push back on bad methodology
        question_design_agent,  # Design question pool
        conversation_loop,      # LoopAgent: interview → coverage check → replan
        quality_agent,          # Score data quality
        export_agent,           # BigQuery export
    ],
)
```

### Conversation Loop (the hard part)

```python
conversation_loop = LoopAgent(
    name="coverage_loop",
    max_iterations=5,
    sub_agents=[
        ParallelAgent(
            name="participant_sessions",
            sub_agents=[interviewer_agent],  # Can run multiple in parallel
        ),
        coverage_checker,  # LlmAgent that checks variable coverage
        replanner,         # LlmAgent that decides if more sessions needed
    ],
)
```

### MCP Integration (reuse our existing server)

```python
from google.adk.tools import McpToolset
from mcp.client.stdio import StdioServerParameters

deal_context_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="python3",
        args=["scripts/wp6_mcp_server.py"],
    ),
)

interviewer_agent = LlmAgent(
    name="interviewer",
    model="gemini-2.5-flash",
    tools=[deal_context_toolset],
    instruction="You are a B2B win-loss research interviewer...",
)
```

## Gemini Model Selection

| Agent Role | Model | Rationale |
|-----------|-------|-----------|
| Methodology pushback | `gemini-2.5-pro` | Deep reasoning needed for critique |
| Question design | `gemini-2.5-pro` | Structured output, variable mapping |
| Interviewer (conversation) | `gemini-2.5-flash` | Low latency, high throughput |
| Data quality scoring | `gemini-2.5-flash` | Structured extraction, fast |
| Re-plan decision | `gemini-2.5-pro` | Judgment call, needs reasoning |

Note: gemini-3-pro and gemini-3-flash exist but 2.5 versions are battle-tested. Use 2.5 for stability, upgrade later if needed.

## A2A Integration

ADK has native A2A support. This means we can:

1. Expose Methodic as an A2A agent with an Agent Card
2. Accept `request_study` as an A2A task
3. Send clarification as A2A message
4. Return completion as A2A task result

This is not a hack or "A2A-pattern" — it's real A2A protocol v0.3 via ADK.

## Cloud Run Deployment

```bash
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --service_name=methodic \
  --env_vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=methodic"
```

One command. No Dockerfile needed (ADK builds it). Our existing Dockerfile is unnecessary.

## Revised Build Plan (32 days)

### Week 1 (May 5-11): Foundation

- **Day 1-2:** Install google-adk, scaffold agent structure, get `adk web` running with a hello-world agent
- **Day 3-4:** Port organizer agent (wp3 → LlmAgent), port methodology agent (wp4 → LlmAgent with Gemini)
- **Day 5-7:** Build interviewer agent — THE critical piece. System prompt for B2B win-loss interviewing, structured field extraction, coverage tracking

### Week 2 (May 12-18): Core Loop

- **Day 8-10:** Wire MCP tools via McpToolset (reuse wp6_mcp_server.py), build conversation loop with LoopAgent
- **Day 11-12:** Build quality scoring agent, BigQuery export tool
- **Day 13-14:** Wire A2A endpoint, test end-to-end flow

### Week 3 (May 19-25): Integration & Polish

- **Day 15-17:** Prompt engineering iteration on interviewer agent (the make-or-break)
- **Day 18-19:** Deploy to Cloud Run, connect real BigQuery
- **Day 20-21:** Build demo UI enhancements (ADK web gives us a baseline)

### Week 4 (May 26-Jun 1): Demo & Submit

- **Day 22-24:** Record demo video per spec (3-4 min)
- **Day 25-26:** Write Devpost submission
- **Day 27-28:** Buffer for issues

### Final Week (Jun 2-5): Submit

- Polish, final testing, submit by June 5 5PM PT

## What to Keep vs Rewrite

| Asset | Keep? | Why |
|-------|-------|-----|
| `wp6_mcp_server.py` | YES | Real MCP server, use via McpToolset |
| Fixture data (16 files) | YES | Test cases for validating the real agent |
| Schema definitions | YES | Canonical contract for structured fields |
| Validators | YES | Quality gates |
| `wp3_organizer_flow.py` | REWRITE as LlmAgent | Current version is fixture replay |
| `wp4_methodology_review.py` | REWRITE as LlmAgent | Already has Gemini mode, upgrade to ADK |
| `wp5_conversation_engine.py` | REWRITE as LlmAgent | This is the biggest rewrite |
| `wp7_data_quality.py` | REWRITE as LlmAgent | Scoring logic can inform the prompt |
| `wp8_replan_trigger.py` | REWRITE as LoopAgent | ADK LoopAgent replaces manual logic |
| `wp9_demo_server.py` | DELETE | ADK web + Cloud Run replaces this |
| `wp9a_bigquery_export.py` | REWRITE as FunctionTool | Keep BQ schema, rewrite as ADK tool |
| Docs (spec, storyboard, etc.) | YES | Guide the prompts and demo |
| `Dockerfile` | DELETE | `adk deploy cloud_run` builds its own |

## Minimum Viable Demo (Scoring Optimized)

For **Technical Implementation (30%):**
- ADK multi-agent orchestration (Sequential + Parallel + Loop) ✓
- Real MCP boundary via McpToolset ✓
- Real A2A endpoint ✓
- Cloud Run deployed ✓
- BigQuery export ✓

For **Business Case (30%):**
- Win-loss research is a real $2B+ market
- Static survey vs Methodic comparison (keep existing quality metrics)
- Show the "price → unclear_roi" decomposition live

For **Innovation (20%):**
- Autonomous re-plan (LoopAgent checks coverage, adds sessions)
- Methodology pushback (agent corrects the user's bad plan)
- MCP triangulation (agent uses CRM context mid-conversation)

For **Demo (20%):**
- `adk web` gives us a conversation UI for free
- Split-screen: static form vs live Methodic conversation
- Coverage dashboard showing variables filling in real-time

## Biggest Risk (Unchanged)

The interviewer agent prompt engineering. Getting Gemini to:
- Ask probing follow-up questions tied to specific variables
- Extract structured data reliably from free-text
- Know when to stop (coverage threshold)
- Handle guardrail cases

This is 60% of the work and 80% of the value. Everything else is plumbing that ADK handles.

## Sources

- [ADK Python Quickstart](https://google.github.io/adk-docs/get-started/python/)
- [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- [ADK MCP Tools Integration](https://adk.dev/tools-custom/mcp-tools/)
- [ADK A2A Protocol](https://google.github.io/adk-docs/a2a/)
- [ADK Cloud Run Deployment](https://google.github.io/adk-docs/deploy/cloud-run/)
- [ADK + BigQuery MCP End-to-End](https://medium.com/google-cloud/end-to-end-ai-agent-on-gcp-adk-bigquery-mcp-agent-engine-and-cloud-run-4843fec27c13)
- [Google Cloud: Deploy ADK Agent to Cloud Run](https://docs.cloud.google.com/run/docs/ai/build-and-deploy-ai-agents/deploy-adk-agent)
- [MCP + ADK + A2A Codelab](https://codelabs.developers.google.com/codelabs/currency-agent)
- [Gemini Models](https://ai.google.dev/gemini-api/docs/models)
