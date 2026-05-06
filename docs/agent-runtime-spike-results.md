# Agent Runtime Feasibility Spike — Results

**Date:** 2026-05-06
**Timebox:** 4 hours (started ~16:00, completed ~19:40)
**Project:** methodic-ai-challenge (GCP project 2030382823)
**Region:** us-central1

---

## Gate Results Summary

| # | Gate | Result | Evidence |
|---|------|--------|----------|
| 1 | `adk deploy agent_engine` succeeds | **FAIL** | Code 13 on 3 attempts (minimal + full agent) |
| 2 | Session creation via Agent Runtime API | SKIP | Blocked by Gate 1 |
| 3 | Streamed query returns agent output | SKIP | Blocked by Gate 1 |
| 4 | Custom BaseAgent step executes | SKIP | Blocked by Gate 1 |
| 5 | MCP tool invocation works | SKIP | Blocked by Gate 1 |
| 6 | Agent Runtime API returns intermediate events | SKIP | Blocked by Gate 1 |

**Verdict: Agent Runtime is NOT viable for this submission. Proceed with Cloud Run deployment.**

---

## Gate 1: Agent Engine Deployment — FAIL

### Attempts

**Attempt 1 — Full Methodic agent (`methodic/`)**
- Command: `adk deploy agent_engine --project=methodic-ai-challenge --region=us-central1 --display_name="Methodic Agent" methodic/`
- Build phase: SUCCESS (container image built and pushed, digest sha256:60b9cadd...)
- Deploy phase: FAIL
- Error: `{'code': 13, 'message': 'Please refer to our documentation...'}`

**Attempt 2 — Minimal LlmAgent (`minimal_agent/`)**
- Created a stripped-down agent with only: `LlmAgent(name="minimal_test", model="gemini-2.5-flash", instruction="...")`
- Same error: code 13
- This rules out our agent complexity (BaseAgent, LoopAgent, MCP) as the cause

**Attempt 3 — Minimal agent in us-east1**
- Same code 13 error — not region-specific

**Attempt 4 — Minimal agent after IAM fix**
- Granted `roles/storage.objectAdmin` and `roles/storage.objectViewer` to compute SA and AI Platform service agent
- Same code 13 error

### Root Cause Analysis

- Code 13 = `INTERNAL` in gRPC status codes — an opaque server-side error
- The build phase succeeds every time (container image is created), so the failure is in the Agent Engine runtime provisioning step
- Minimal agent with zero custom code still fails, confirming this is a platform-level issue
- Tested across two regions (us-central1, us-east1) with identical results
- Cloud Logging shows no application-level errors — only build audit logs
- After 4 attempts across 2+ hours, this is not transient

### IAM State at Time of Testing

```
roles/cloudbuild.builds.builder        -> 2030382823@cloudbuild.gserviceaccount.com
roles/cloudbuild.serviceAgent          -> service-2030382823@gcp-sa-cloudbuild.iam.gserviceaccount.com  
roles/storage.objectAdmin              -> 2030382823-compute@developer.gserviceaccount.com
roles/storage.objectAdmin              -> service-2030382823@gcp-sa-aiplatform.iam.gserviceaccount.com
roles/storage.objectViewer             -> 2030382823-compute@developer.gserviceaccount.com
roles/aiplatform.user                  -> wiktorgancarz@uszatki.co.uk
roles/artifactregistry.repoAdmin       -> wiktorgancarz@uszatki.co.uk
roles/bigquery.admin                   -> wiktorgancarz@uszatki.co.uk
```

---

## Cloud Run Fallback — Testing

### ADK CLI Cloud Run Deploy

- Command: `adk deploy cloud_run --project=methodic-ai-challenge --region=us-central1 minimal_agent/`
- Build phase: Container build started in Cloud Build regional pool
- Result: FAILURE (status code 9 = FAILED_PRECONDITION)
- Build logs empty (CLOUD_LOGGING_ONLY mode, logs not surfaced)
- Earlier attempt failed with storage IAM error (fixed), but post-fix attempt still fails in build

### Manual Docker Build + Deploy — SUCCESS

- Built container locally: `docker build --platform linux/amd64 -t us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/minimal-agent:v1`
- Pushed to Artifact Registry: `docker push us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/minimal-agent:v1`
- Deployed to Cloud Run: `gcloud run deploy methodic-minimal --image=... --port=8000 --max-instances=1 --memory=512Mi`
- Service URL: `https://methodic-minimal-2030382823.us-central1.run.app`
- **Verified working**: `/list-apps` returns `["minimal_agent"]`, session creation succeeds, SSE query returns Gemini 2.5 Flash response via Vertex AI
- Required IAM fix: granted `roles/aiplatform.user` to default compute SA for `aiplatform.endpoints.predict`
- Org policy blocks `allUsers` binding (no public access) — authenticated access via identity token works

---

## Decision

Given Gate 1 failure across all configurations:

1. **Agent Runtime is not viable** for the Methodic submission within the remaining timeline
2. **Cloud Run is the deployment target** — deploy via pre-built container image to avoid Cloud Build issues
3. **Vertex AI routing** via `GOOGLE_GENAI_USE_VERTEXAI=1` is set regardless of runtime
4. **ADK api_server** provides the REST API on Cloud Run (replaces custom FastAPI)
5. **MCP** runs in-process via McpToolset (no serialization issue on Cloud Run)

### What We Gain on Cloud Run

- Direct REST API access (no proxy needed)
- Full control over the demo UI
- McpToolset works natively (no serialization constraint)
- Custom BaseAgent subclasses work without restrictions
- ADK `api_server` command provides standard endpoints

### What We Lose vs Agent Runtime

- No managed sessions (use `InMemorySessionService`, acceptable for demo)
- No built-in observability (add Cloud Trace manually via OpenTelemetry)
- No Playground UI integration (custom demo UI is better for judging anyway)
- Slightly weaker "platform alignment" signal for Technical Implementation rubric

### Risk Mitigation

- Add Cloud Trace instrumentation for observability proof
- Include ADK Evaluation artifact in submission
- Document Agent Runtime spike results honestly — shows platform awareness
- The before/after demo UI (our key differentiator) works better on Cloud Run

---

## Proven Deployment Workflow

```bash
# 1. Build locally (cross-platform for Cloud Run)
docker build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1 .

# 2. Push to Artifact Registry
docker push us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1

# 3. Deploy to Cloud Run
gcloud run deploy methodic \
  --image=us-central1-docker.pkg.dev/methodic-ai-challenge/methodic-repo/methodic:v1 \
  --project=methodic-ai-challenge \
  --region=us-central1 \
  --port=8000 \
  --max-instances=1 \
  --memory=1Gi \
  --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=1,GOOGLE_CLOUD_PROJECT=methodic-ai-challenge,GOOGLE_CLOUD_LOCATION=us-central1

# 4. Test (authenticated)
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" https://<SERVICE_URL>/list-apps
```

### Required IAM Bindings

| Role | Principal | Purpose |
|------|-----------|---------|
| `roles/aiplatform.user` | Compute SA (`*-compute@developer.gserviceaccount.com`) | Gemini model access via Vertex AI |
| `roles/storage.objectAdmin` | Compute SA | Artifact Registry image pull |
| `roles/bigquery.dataEditor` | Compute SA | BigQuery export (for full Methodic agent) |

### API Endpoints (ADK api_server)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/list-apps` | GET | List available agents |
| `/apps/{app}/users/{user}/sessions` | POST | Create session |
| `/run_sse` | POST | Run agent query (SSE stream) |

## Recommendations

1. Deploy Methodic to Cloud Run using `adk api_server` via the proven workflow above
2. Build container locally, push to Artifact Registry, deploy from pre-built image
3. Add minimal OpenTelemetry/Cloud Trace instrumentation
4. Create one ADK Evaluation trajectory artifact
5. Reference this spike in submission to show platform exploration
