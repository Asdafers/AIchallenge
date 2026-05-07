# Methodic Live Demo Deployment Design

Date: 2026-05-06
Status: Superseded by `docs/deployment-architecture-decision.md`
Context: The hackathon has provided $500 in Google Cloud credits. The `feat/methodic-adk-agent` branch now has a real `methodic/` ADK runtime, custom `BaseAgent` workflow steps, a FastAPI/ADK server, A2A-shaped Agent Card, MCP wrapper, BigQuery export path, demo UI, and local tests passing.

## Decision

This document is now a proving-ground deployment plan, not the submission architecture.

The submission target should be aligned with the challenge-recommended tools and platforms first: ADK, Agent Runtime / Agent Platform, Agents CLI conventions, MCP, sessions/state, observability, evaluation, and BigQuery. Cloud Run remains useful as a fallback or thin frontend/proxy, but it is no longer the default core runtime unless the Agent Runtime feasibility spike records a hard blocker.

Move from planning/review into target-platform validation before build-to-demo.

This is not the moment to broaden Methodic into a product platform. The credits should be used to prove the existing vertical slice in a hosted, judge-visible environment:

1. Agent Runtime / Agent Platform hosts the Methodic ADK agent, or Cloud Run fallback is justified with blocker evidence.
2. Gemini powers at least one live adaptive participant conversation path.
3. MCP is invoked in the participant path for approved deal or telemetry context.
4. Gemini structured extraction produces a schema-valid `ParticipantResponse`.
5. Coverage and quality scoring update non-empty demo state.
6. BigQuery receives at least one real export row.
7. The demo UI shows the data-quality delta, tool events, coverage state, and export result.

The winning claim is: Methodic is an autonomous research operations agent that turns a business decision into governed, evidence-linked, analysis-ready data. The deployment must prove that claim visibly.

## Why Now

The remaining risk is no longer primarily architecture. Local verification on May 6 showed:

- `tests/`: 43 passing tests
- schema and fixture validators passing
- `methodic/` runtime present with custom `BaseAgent` deterministic steps
- `google-genai` dependency present
- FastAPI/ADK server exposes `/api/demo/*`, `/health`, and `/.well-known/agent-card.json`
- BigQuery export code includes table setup/error handling
- MCP wrapper and extended telemetry tool exist

The next unknowns are live-environment unknowns:

- Google Cloud project/API/IAM setup
- Cloud Run packaging/runtime behavior
- Gemini API credentials and model IDs
- BigQuery dataset/table write permissions
- live demo latency and reliability
- whether the UI tells the story clearly enough

Those risks cannot be resolved by more local planning. They require a deployed smoke path on the target platform first, with Cloud Run as fallback only if Agent Runtime cannot support the required graph/tooling in time.

## Target-Platform Gate

Before executing the Cloud Run phases below, complete the gate in `docs/deployment-architecture-decision.md`:

1. Attempt Agent Runtime deployment using the existing `methodic/agent.py` and `root_agent`.
2. Exercise session creation and streamed query.
3. Verify custom `BaseAgent` steps.
4. Verify MCP tool access or record the exact blocker.
5. Run Agents CLI in a scratch folder and harvest useful scaffold/IAM/evaluation/observability conventions.
6. Decide from evidence whether the final architecture is Agent Runtime core, Agent Runtime plus Cloud Run frontend/proxy, or Cloud Run fallback.

The rest of this document is retained as the Cloud Run fallback/proving-ground plan.

## Credit Use Policy

Treat the $500 as a demo-proving budget, not an invitation to add infrastructure.

Use credits for:

- Cloud Run service hosting
- Artifact Registry image storage
- BigQuery dataset/table and write tests
- Gemini API live smoke runs
- Cloud Logging for demo debugging
- a small number of repeated end-to-end demo runs

Do not use credits for:

- broad Vertex AI Search integration before the vertical slice works
- GKE
- multi-region deployment
- large-scale load tests
- long-running scheduled workloads
- production participant recruitment
- broad observability stack beyond Cloud Logging and simple traces

Budget guardrails:

- Keep all services in one Google Cloud project.
- Use one Cloud Run service for the demo.
- Set minimum instances to zero unless cold start becomes a demo problem.
- Set Cloud Run max instances to one while demo state is in process memory.
- Use one BigQuery dataset and one or two tables.
- Keep live Gemini smoke runs short and scripted.
- Shut down or pause anything not needed for the demo.

## Target Architecture

```text
Judge browser
  |
  | HTTPS
  v
Cloud Run: methodic-demo
  |
  | FastAPI / ADK app
  | - /static/demo.html
  | - /api/demo/run
  | - /api/demo/{id}/status
  | - /api/demo/{id}/events
  | - /api/demo/{id}/coverage
  | - /.well-known/agent-card.json
  |
  v
Methodic ADK root_agent
  |
  +-- Organizer LlmAgent
  +-- Methodology LlmAgent
  +-- Question Design LlmAgent
  +-- Fieldwork LoopAgent
  |     +-- SessionInitStep custom BaseAgent
  |     +-- Interview LoopAgent
  |     |     +-- Interviewer LlmAgent
  |     |     +-- ParticipantSim LlmAgent
  |     |     +-- ExtractorStep custom BaseAgent
  |     |     +-- TurnCheckerStep custom BaseAgent
  |     +-- CoverageStep custom BaseAgent
  |     +-- ReplannerStep custom BaseAgent
  +-- Quality LlmAgent
  +-- BigQueryExportStep custom BaseAgent
  +-- Completion responder LlmAgent
  |
  +-- MCP stdio server: scripts/wp6_mcp_server.py
  |
  +-- Gemini API
  |
  +-- BigQuery: methodic_demo.win_loss_responses
```

A2A scope remains deliberately narrow: the demo exposes an A2A 1.0-shaped Agent Card and an A2A-pattern request flow. Full `to_a2a()` compliance is not a precondition for this deployment unless it can be proven quickly with a real A2A client.

## Deployment Phases

### Phase 0: Repo And Branch Hygiene

Goal: preserve current working state before cloud changes.

Actions:

1. Review the dirty worktree and separate user/other-agent changes from deployment work.
2. Commit the current runtime, reviews, and strategy docs on `feat/methodic-adk-agent` if not already committed.
3. Push the branch to the private GitHub repo.
4. Record the commit SHA in the deployment notes.

Acceptance gate:

- `git status -sb` is understood and there are no untracked critical artifacts at risk of being lost.
- `python3 -m pytest tests/ -q --tb=short` passes.
- `python3 scripts/validate_schemas.py docs/schema/ && python3 scripts/validate_fixtures.py` passes.

### Phase 1: Google Cloud Project Setup

Goal: create the minimal cloud substrate.

Actions:

1. Select or create the dedicated GCP project that received the hackathon credits.
2. Confirm billing/credits are active.
3. Enable required APIs:
   - Cloud Run
   - Artifact Registry
   - Cloud Build
   - BigQuery
   - Secret Manager
   - Gemini API / Generative Language API path used by `google-genai`
4. Separate the deployment identity from the runtime identity.
   - Deployment identity: the human or CI identity that builds/pushes/deploys.
   - Runtime identity: a Cloud Run service account used by the deployed service.
5. Create runtime service account `methodic-demo-runner`.
6. Grant least-privilege runtime roles:
   - BigQuery job user on the project
   - BigQuery data editor scoped to the demo dataset
   - Secret Manager Secret Accessor for the Gemini API key secret
7. Ensure the deployment identity can:
   - push to Artifact Registry
   - deploy Cloud Run services
   - attach the runtime service account to the Cloud Run service
8. Create or reserve the BigQuery dataset `methodic_demo`.
9. Store the Gemini API key in Secret Manager, not as a plain Cloud Run environment variable.

Acceptance gate:

- Local `gcloud config get-value project` points at the correct project.
- Required APIs are enabled.
- Runtime service account is identifiable.
- Gemini API key secret exists and the runtime service account can access it.
- BigQuery dataset exists or can be created by deployment code.

### Dedicated Project Setup Commands

Use the console if the hackathon credit flow requires it, but the CLI shape should be:

```bash
export PROJECT_ID="methodic-demo-$(date +%y%m%d)"
export PROJECT_NAME="Methodic Demo"
export REGION="us-central1"
export BILLING_ACCOUNT_ID="<your-billing-account-id>"

gcloud projects create "$PROJECT_ID" \
  --name="$PROJECT_NAME" \
  --set-as-default

gcloud billing projects link "$PROJECT_ID" \
  --billing-account="$BILLING_ACCOUNT_ID"

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  bigquery.googleapis.com \
  secretmanager.googleapis.com \
  generativelanguage.googleapis.com \
  aiplatform.googleapis.com

gcloud artifacts repositories create methodic \
  --repository-format=docker \
  --location="$REGION" \
  --description="Methodic demo containers"

bq --location="$REGION" mk --dataset "$PROJECT_ID:methodic_demo"
```

Runtime service account and secret:

```bash
export RUNTIME_SA="methodic-demo-runner"
gcloud iam service-accounts create "$RUNTIME_SA" \
  --display-name="Methodic Cloud Run runtime"

export RUNTIME_SA_EMAIL="$RUNTIME_SA@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/bigquery.dataEditor"

printf "%s" "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
  --replication-policy=automatic \
  --data-file=-

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:$RUNTIME_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

Budget alert:

```bash
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT_ID" \
  --display-name="Methodic demo budget" \
  --budget-amount=400 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

The exact billing-account step may require Console access depending on how the hackathon credits were issued. Do not proceed until the dedicated project clearly shows the credit-backed billing account.

### Phase 2: Container Build And Cloud Run Deploy

Goal: get the demo service online.

Actions:

1. Build the Docker image.
2. Push to Artifact Registry.
3. Deploy to Cloud Run with:
   - `GOOGLE_CLOUD_PROJECT`
   - `BIGQUERY_DATASET=methodic_demo`
   - `BIGQUERY_DRY_RUN=false`
   - `METHODIC_MODEL=gemini-2.5-flash` unless a preview model has been verified
   - Gemini API key mounted from Secret Manager as `GEMINI_API_KEY`
   - `$PORT` respected by the container
   - runtime service account `methodic-demo-runner`
   - `--max-instances=1` while demo state remains in process memory
4. Keep min instances at zero initially.
5. Capture the Cloud Run URL.

Example deploy command:

```bash
export IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/methodic/methodic-demo:$(git rev-parse --short HEAD)"

docker build -t "$IMAGE" .
docker push "$IMAGE"

gcloud run deploy methodic-demo \
  --image="$IMAGE" \
  --region="$REGION" \
  --allow-unauthenticated \
  --service-account="$RUNTIME_SA_EMAIL" \
  --max-instances=1 \
  --min-instances=0 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=methodic_demo,BIGQUERY_DRY_RUN=false,METHODIC_MODEL=gemini-2.5-flash" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

Acceptance gate:

- `GET /health` returns success.
- `GET /.well-known/agent-card.json` returns valid JSON.
- `GET /static/demo.html` renders.
- Cloud Run logs do not show import/runtime errors.

### Phase 3: Live Smoke Test

Goal: prove the live path, not only local mocks.

Actions:

1. Trigger `POST /api/demo/run`.
2. Poll:
   - `/api/demo/{id}/status`
   - `/api/demo/{id}/events`
   - `/api/demo/{id}/coverage`
3. Confirm at least one Gemini-powered participant conversation path runs.
4. Confirm at least one MCP context lookup event is present.
5. Confirm at least one structured extraction result validates against the schema.
6. Confirm BigQuery export reports success.
7. Query BigQuery for the exported row.

Acceptance gate:

- Demo status reaches `complete`, not only `running`.
- Events list is non-empty and includes agent/tool/export events.
- Coverage state is non-empty and includes the ambiguous-to-resolved proof path or a clear re-plan event.
- BigQuery contains at least one row from the live deployed run.
- Any failure is surfaced in the event timeline, not hidden.
- A separate MCP subprocess smoke runs successfully in Cloud Run before the full demo is considered reliable.

### Phase 4: Judge-Facing Demo Pass

Goal: make the demo understandable in under five minutes.

Actions:

1. Open `/static/demo.html` from the Cloud Run URL.
2. Run the demo from a fresh browser session.
3. Verify the page shows:
   - static survey side
   - Methodic conversation side
   - MCP/tool event
   - structured fields
   - evidence quote
   - coverage state
   - BigQuery export status
4. Tune the UI text only where it clarifies the workflow.
5. Avoid landing-page copy or feature explanation screens.

Acceptance gate:

- A viewer can answer these questions after watching the demo:
  - What business decision was Methodic supporting?
  - What did Methodic do that a static survey could not?
  - Where did MCP tool use happen?
  - What data quality improved?
  - Where did the structured data go?

### Phase 5: Submission Packaging

Goal: turn the hosted proof into submission material.

Actions:

1. Update README with:
   - Cloud Run URL
   - setup/deploy commands
   - demo path
   - environment variables
   - known limitations
2. Add architecture diagram.
3. Add a short business-case section:
   - B2B SaaS win-loss research
   - faster capture cycle
   - higher-quality, evidence-linked data
   - not statistically representative without larger sample
4. Record a 3-5 minute demo video.
5. Add a final smoke-test transcript or deployment proof artifact.

Acceptance gate:

- Submission can be evaluated without reading internal planning docs.
- Claims match what the deployed demo actually does.
- Limitations are honest.

## Required Proof Checklist

The deployment is not ready for submission until these are true:

- [ ] Agent Runtime feasibility spike completed with evidence.
- [ ] Agents CLI scratch comparison completed.
- [ ] Final architecture decision updated from target-platform evidence.
- [ ] Session/state approach is explicit and challenge-aligned.
- [ ] Observability or trace evidence exists.
- [ ] Lightweight trajectory/evaluation artifact exists.
- [ ] Branch pushed and recoverable.
- [ ] Local tests pass.
- [ ] Local schema/fixture validators pass.
- [ ] Chosen deployed runtime is live.
- [ ] Health or connection check succeeds in the chosen runtime.
- [ ] Agent card or platform agent identity is visible and honestly labeled.
- [ ] Demo UI or Cloud Console path renders the before/after story.
- [ ] `/api/demo/run` starts a real run.
- [ ] Demo run reaches `complete`.
- [ ] Events include agent handoffs.
- [ ] Events include an MCP lookup.
- [ ] Events include structured extraction or extraction-step evidence.
- [ ] Coverage state is non-empty.
- [ ] BigQuery export reports success.
- [ ] BigQuery table contains at least one row from the deployed run.
- [ ] UI shows static-vs-Methodic comparison.
- [ ] UI shows evidence-linked structured output.
- [ ] Demo video recorded from the deployed URL.

## Known Risks

### Risk: Gemini model ID mismatch

Mitigation: verify configured model IDs before deployment. If preview models fail, use `gemini-2.5-flash` as the default for all demo agents and optimize later.

### Risk: Cloud Run cannot spawn the stdio MCP server cleanly

Mitigation: run an isolated Cloud Run smoke that hits the MCP wrapper path. Confirm the server can run from the packaged `/app/scripts/` path and that any temporary writes use `/tmp`. If subprocess behavior is problematic, keep the MCP server in-process for demo only while preserving an MCP-compatible boundary locally, and document the compromise honestly.

### Risk: BigQuery IAM blocks live export

Mitigation: test BigQuery write separately before full demo run. Surface export errors in the demo event timeline.

### Risk: live Gemini latency makes demo too slow

Mitigation: use `gemini-2.5-flash` for demo runtime, shorten participant turns, and keep a cached-live trace mode clearly labeled as fallback.

### Risk: A2A claims exceed implementation

Mitigation: call this an A2A-shaped or A2A-pattern prototype unless a real A2A client smoke test passes.

### Risk: UI is too sparse to persuade judges

Mitigation: prioritize the developer trace and data-quality scorecard over visual polish. Judges must see agent handoffs, MCP call, coverage transition, evidence quote, and export proof.

### Risk: Cloud Run in-memory demo state is lost across instances

Mitigation: deploy with `--max-instances=1` until demo state is moved to durable storage such as Firestore, Redis, or ADK session storage backed by an external database.

### Risk: Gemini API key leaks through environment configuration

Mitigation: store the key in Secret Manager and mount it as a Cloud Run secret environment variable. Grant Secret Manager access only to the runtime service account.

## Extension Candidates

Only consider these after the required proof checklist passes:

1. Real `to_a2a()` endpoint with A2A SDK client smoke test.
2. Vertex AI Search or grounded methodology references for the Methodology Agent.
3. Human participant mode in the demo UI.
4. Cloud Logging trace export shown in developer overlay.
5. Second study/persona path to prove repeatability.
6. Small business-case calculator showing estimated time saved.
7. Looker Studio dashboard connected to `methodic_demo.win_loss_responses`.

## Explicit Non-Goals

- Do not move to GKE.
- Do not build multi-tenant auth.
- Do not add broad analytics dashboards.
- Do not attempt real participant recruitment.
- Do not claim statistical representativeness.
- Do not broaden beyond B2B SaaS win-loss before the demo is deployed.

## Immediate Next Action

Start with the Agent Runtime and Agents CLI feasibility gate, then choose the deployment path from evidence. The $500 credits should buy proof on the target tools/platforms: hosted ADK runtime, live Gemini path, MCP call, trace/trajectory evidence, real BigQuery row, and a demo video. If a task does not contribute to that proof, it should wait.
