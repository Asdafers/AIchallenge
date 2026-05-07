# Gemini Live Demo Deployment Review

Date: 2026-05-06
Task ID: e31ee070-b630-4c35-812b-a14e549fec44
Reviewer ID: gemini-2026-05-06T1300-DPLY
Verdict: REVISE_REQUIRED

## 1. Project Move and Strategy Assessment
Moving from planning to build-to-demo is the absolutely correct next move. Local tests are passing, and the vertical slice is functionally complete in the local environment. Using the $500 credits to prove this vertical slice in the cloud—rather than expanding scope—aligns perfectly with the strategy to produce a credible, hosted proof of the autonomous research operations agent.

## 2. Sequencing Assessment
The deployment phases (0 to 5) and the proof checklist are complete and correctly sequenced. Proceeding from local hygiene to infrastructure setup, deployment, smoke testing, and finally UI tuning and packaging is the most reliable path. 

## 3. Technical Plan Credibility & Risks
The choice of Cloud Run, Gemini API, and BigQuery is highly credible, cost-effective, and scalable. However, there are significant gaps in Cloud Run execution state and IAM/Security that must be addressed.

### Findings

#### 1. [BLOCKER] Cloud Run Ephemeral State and Scaling
*   **Issue:** The architecture uses endpoints like `/api/demo/run` followed by polling `/api/demo/{id}/status` and `/events`. Cloud Run scales instances dynamically based on traffic. If the demo's state (the `id` and its events) is held in-memory within the FastAPI app, a polling request might route to a different Cloud Run instance than the one executing the run, resulting in a 404 or lost state.
*   **Mitigation:** For a hackathon demo without a shared database (like Redis or Firestore), you must explicitly set `--max-instances=1` on the Cloud Run deployment. This guarantees all requests for a given demo session hit the same instance and memory space.

#### 2. [MAJOR] IAM Distinction: Deployment vs. Runtime Service Account
*   **Issue:** Phase 1 conflates deployment permissions with runtime permissions ("Create a deployment service account. Grant... Cloud Run runtime permissions... Artifact Registry pull... BigQuery job user"). 
*   **Mitigation:** Separate these identities. Create a specific **runtime service account** for the Cloud Run service. Give *this* account the BigQuery Job User and Data Editor roles. The deployment identity (the user deploying the app) needs roles to push to Artifact Registry and deploy to Cloud Run.

#### 3. [MAJOR] Secret Management for Gemini API Key
*   **Issue:** "Gemini API credential configuration" is mentioned in Phase 2, but plain text environment variables in Cloud Run are a security risk for API keys.
*   **Mitigation:** Store the Gemini API key in Google Cloud Secret Manager. Configure Cloud Run to expose this secret as an environment variable (e.g., `GEMINI_API_KEY`). Grant the new runtime service account the `Secret Manager Secret Accessor` role.

#### 4. [MAJOR] MCP Subprocess Dependencies in Docker
*   **Issue:** The risks section mentions the stdio MCP server cleanly spawning. Cloud Run can execute subprocesses, but the container must have all dependencies installed.
*   **Mitigation:** Ensure the `Dockerfile` explicitly installs any runtime environments (e.g., Node.js if using a TS MCP server, or Python dependencies) required by `scripts/wp6_mcp_server.py`, and ensure the script is executable.

#### 5. [MINOR] Demo UI Latency and Polling
*   **Issue:** LLM generation can take 10+ seconds. Simple polling might make the UI feel broken if state doesn't update frequently.
*   **Mitigation:** Ensure the UI shows continuous visual feedback (e.g., a "Thinking..." or "Executing Tool..." spinner) while polling `/status` and `/events`.

## 4. What Should Be Cut, Changed, or Added
*   **Add:** Setting `--max-instances=1` in Phase 2.
*   **Change:** Phase 1 IAM setup to distinguish runtime service account from deployment identity.
*   **Add:** Secret Manager integration for API keys in Phase 1 and 2.
*   **Cut:** No features should be cut. The vertical slice scope is perfectly sized.

## 5. Extension Proposals (Post-Checklist)
To maximize winning odds after the required proof checklist passes, consider these extensions:

1.  **Looker Studio Dashboard:** Connect a free Google Looker Studio dashboard directly to `methodic_demo.win_loss_responses`. Including a public link to a visualization of the extracted data powerfully proves the "decision-ready data" claim.
2.  **Dry-Run / Fallback Mock Mode:** Add a UI toggle or environment variable to run the demo with cached, static responses. If the live API is rate-limited during judging, this guarantees a working interactive demo.
3.  **Developer Trace Overlay:** Expose Cloud Logging trace links or raw JSON payloads in a collapsible UI section to solidify the "developer tool" and A2A narrative.

## Final Verdict
**REVISE_REQUIRED**

Please update the design document to address the Cloud Run state/scaling blocker (`--max-instances=1`) and the IAM/Secret Management major findings. Once those are incorporated, the plan is ready for immediate execution.