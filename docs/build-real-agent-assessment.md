# Assessment: What It Takes to Build the Real Methodic Agent

**Date:** 2026-05-04
**Deadline:** 2026-06-05 (32 days)
**Status:** Current codebase is a fixture-replay demo pipeline, not a working agent

## Current State (Honest)

| Layer | Status | What exists |
|-------|--------|-------------|
| Conversation engine | FIXTURE REPLAY | wp5 replays transcripts, no LLM generates questions |
| Extraction/NLP | FIXTURE GROUND TRUTH | structured_fields come from fixtures, not model inference |
| ADK orchestration | MISSING | Spec calls for SequentialAgent/ParallelAgent/LoopAgent — zero ADK code exists |
| Gemini integration | PARTIAL | wp4 can call Gemini for methodology review; conversations don't use Gemini |
| MCP boundary | REAL | wp6 has a working MCP server + client over stdio JSON-RPC 2.0 |
| A2A endpoint | MISSING | wp3 reads fixture JSON, no HTTP endpoint accepts agent requests |
| Cloud Run | NOT DEPLOYED | Dockerfile exists, never pushed to GCR |
| BigQuery | DRY-RUN ONLY | Schema validated, no actual writes |
| UI/Demo surface | MISSING | No frontend, no visual demo interface |
| Dependencies | MINIMAL | Only jsonschema + mcp; no ADK, no google-genai, no vertex SDK |

## What Must Be Built

### Tier 1: Non-Negotiable for a Real Submission (Weeks 1-2)

#### 1. ADK-Based Agent Orchestration
- Install `google-adk` (or `google-genai` + adk)
- Implement `SequentialAgent`: Organizer → Methodology → QuestionDesign → Conversation → Quality → Export
- Implement `ParallelAgent`: run multiple participant sessions concurrently
- Implement `LoopAgent` or bounded loop: coverage check → re-plan → additional session
- **Effort:** 3-5 days
- **Risk:** ADK API stability, documentation gaps

#### 2. Gemini-Powered Conversation Engine
- Replace wp5 fixture replay with real Gemini calls
- System prompt per agent role (interviewer, methodology critic, question designer)
- Conversation loop: Gemini generates question → participant responds → Gemini extracts structured data → coverage check → next question or stop
- Guardrail handling: detect vague answers, contradictions, disengagement
- **Effort:** 5-7 days
- **Risk:** Prompt engineering iteration, latency budget, quality of extraction

#### 3. Structured Field Extraction via Gemini
- After each participant turn, call Gemini to extract structured_fields
- Map to canonical schema (8 fields)
- Compute confidence scores from model output
- Evidence linking: quote + transcript_turn_id + context_used
- **Effort:** 2-3 days (coupled with #2)

#### 4. Cloud Run Deployment
- Push Docker image to Artifact Registry
- Deploy to Cloud Run with env vars
- Health check + /demo endpoint working live
- **Effort:** 1 day (if GCP project is set up)
- **Risk:** GCP project access, billing, IAM

#### 5. Real BigQuery Export
- Create dataset + tables from existing schema
- Write actual rows after pipeline completes
- Service account IAM at dataset scope
- **Effort:** 1 day
- **Risk:** Credentials, IAM setup

### Tier 2: Strongly Needed for Competitive Submission (Week 3)

#### 6. A2A-Pattern HTTP Endpoint
- FastAPI or Cloud Run endpoint that accepts agent-to-agent requests
- Clarification request/response flow over HTTP
- Honest labeling as "A2A-pattern" not full A2A compliance
- **Effort:** 2 days

#### 7. Demo UI / Visual Interface
- Minimal web UI showing:
  - Split-screen: static survey vs Methodic conversation
  - Live conversation with Gemini (or replay of a real conversation)
  - Coverage dashboard (variables, states, confidence)
  - Agent event timeline
- Options: Streamlit, Gradio, or plain HTML+JS
- **Effort:** 3-5 days
- **Risk:** Scope creep, polish time

#### 8. Demo Video Recording
- 3-4 minute video per spec
- Screen recording of live system
- Voiceover per demo-script.md
- **Effort:** 2 days (after everything works)

### Tier 3: Nice to Have (Week 4)

#### 9. Vertex AI Grounding
- Use Vertex AI Search for methodology grounding
- **Effort:** 2 days

#### 10. Multiple MCP Tools
- Add `trial_telemetry_lookup` alongside existing `lookup_deal_context`
- Add `dataset_export` MCP tool
- **Effort:** 1-2 days

## Critical Path

```
Week 1: ADK orchestration (#1) + Gemini conversation engine (#2, #3)
Week 2: Cloud Run (#4) + BigQuery (#5) + A2A endpoint (#6)
Week 3: Demo UI (#7) + integration testing + prompt tuning
Week 4: Demo video (#8) + submission polish + buffer
```

## Key Technical Decisions Needed

1. **ADK version**: Which version of google-adk? Is it stable enough? Fallback to LangChain/CrewAI?
2. **Gemini model**: gemini-2.0-flash for conversations, gemini-2.0-pro for methodology? Check current model names.
3. **Participant simulation**: For the demo, do we simulate participants (another Gemini call with persona prompts) or use the fixture personas with Gemini filling in the interviewer side?
4. **UI framework**: Streamlit (fast) vs custom (polished)?
5. **A2A compliance**: How close to real A2A protocol? Or just honest HTTP pattern?

## Biggest Risk

The conversation engine (#2) is the hardest piece. Getting Gemini to:
- Ask good follow-up questions bound to measurement variables
- Extract structured data reliably from free-text responses
- Know when to stop probing
- Handle guardrail cases (vague, contradictory, disengaged)

This requires significant prompt engineering and testing. It's the difference between "demo that works once on stage" and "system that works reliably."

## Recommendation

**Start with ADK + Gemini conversation engine.** Everything else is plumbing. If the conversation engine works well, the demo writes itself. If it doesn't, no amount of infrastructure will save the submission.

The fixture data we have is actually valuable as test cases — we can validate the real system against the expected outputs from our fixtures.
