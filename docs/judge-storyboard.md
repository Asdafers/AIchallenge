# Methodic: Judge Storyboard and Demo Narrative

## 1. The Core Memory (One Sentence)
**"Methodic is not an AI survey tool; it’s an autonomous research operations agent that turns a B2B business decision into governed, evidence-linked data."**

## 2. The Business Case: B2B Win-Loss Wedge
The win-loss wedge is highly effective. It translates a familiar revenue problem (deals slipping) into a data-quality problem (dashboards show "what," but static surveys give shallow "whys" like "price"). It gives Methodic a clear ROI story that judges will immediately understand.

## 3. Narrative Strategy

### Avoiding the "AI Survey Tool" Trap
To ensure Methodic is seen as an **agentic workflow**, the demo must emphasize its independence and methodological rigor:
- **Pushback:** It doesn't just do what it's told; it corrects the human organizer's biased sample (Methodology Pushback).
- **Measurement Intent:** It doesn't just chat; it uses MCP to look up CRM context to ask precise follow-ups.
- **Coverage & Re-plan:** It doesn't just collect transcripts; it tracks variable coverage and autonomously decides to field another interview when a variable is ambiguous.

### Showing the Google Stack (Without Distracting)
- **Gemini & ADK:** Narrated during the planning and conversation phases.
- **MCP:** Visually demonstrated during the participant conversation via a subtle "Developer Overlay" or "Trace Panel" showing the tool call (`lookup_deal_context`).
- **Cloud Run / BigQuery:** Proven at the end during the export phase, cementing the enterprise-readiness of the stack.

### What to Cut or Compress
If the 3-4 minute demo feels too busy:
- **Compress Question Generation:** Do not show the detailed mapping of every question. Focus on the Methodology Pushback instead.
- **Compress the Interviews:** Do not show all participant chats. Show a split-screen for *one* critical interaction (the ROI vs. Price clarification using MCP), then fast-forward to the aggregated results.
- **Guardrails:** Keep the guardrail recovery (e.g., handling contradiction) to a quick visual callout in the trace log rather than a full scene.

---

## 4. Recommended 3-4 Minute Scene Sequence

### Scene 1: The Hook & The Problem (0:00 - 0:30)
- **Visual:** A revenue dashboard showing slipping mid-market deals.
- **Voiceover:** "Dashboards tell you what happened. But to know *why*, B2B teams rely on static surveys that return vague answers like 'price'. Methodic fixes the upstream data-capture layer."
- **Action:** An external "Sales Insights Agent" sends a `request_study` payload to Methodic. Methodic asks one clarifying question ("Packaging or ROI?"), proving it's an agent, not an API.

### Scene 2: Agentic Planning & Pushback (0:30 - 1:10)
- **Visual:** Organizer workspace. The human suggests interviewing only "product champions."
- **Action:** Methodic's Methodology Agent pushes back on screen: *"Champions alone cannot answer pricing questions. Adding economic buyers to avoid sample bias."*
- **Voiceover:** "Methodic isn't a form generator. It's a governed research agent that pushes back on bad methodology."

### Scene 3: The Conversation & MCP Triangulation (1:10 - 2:00)
- **Visual:** Split-screen. Left: Static survey. Right: Methodic Participant Agent.
- **Action:** The participant says "Price was too high."
  - *Left (Static):* Accepts "Price" and moves on.
  - *Right (Methodic):* Opens a Developer Trace Overlay. It uses **MCP** to call `lookup_deal_context`, sees the trial account never reached the report builder, and asks: *"Was the cost an issue, or could your team not prove the ROI internally?"* 
- **Voiceover:** "Methodic uses the Model Context Protocol to securely pull CRM telemetry, turning vague answers into precise, evidence-linked data."

### Scene 4: Data Quality & Autonomous Re-Plan (2:00 - 2:50)
- **Visual:** Quality Dashboard showing variable coverage (missing, ambiguous, covered).
- **Action:** The variable `procurement_friction` is stuck at `ambiguous` after the planned sessions. Methodic autonomously triggers a re-plan, adding one targeted economic-buyer session to close the gap.
- **Voiceover:** "Methodic pursues measurement coverage. When a variable remains ambiguous, it autonomously re-plans and fields an additional session."

### Scene 5: Export & Google Stack Close (2:50 - 3:30)
- **Visual:** The structured JSON/CSV and the BigQuery export table.
- **Action:** Show the evidence quotes linked directly to the structured variables.
- **Voiceover:** "Powered by Gemini, built with the Agent Development Kit, and deployed on Cloud Run, Methodic exports clean, decision-ready data to BigQuery. Methodic: Decision in, governed data out."

---

## 5. Story Risks & Mitigations

| Risk | Severity | Mitigation |
| :--- | :--- | :--- |
| **Text-Heavy Split Screen** | Major | The split-screen comparison (Static vs Methodic) is crucial but hard to read quickly. Highlight or zoom in on the exact text of the Methodic follow-up question and the MCP trace. |
| **Re-plan Confusion** | Major | If the coverage metric isn't visually obvious, the re-plan looks random. Ensure the dashboard clearly displays `procurement_friction: AMBIGUOUS` turning red before the re-plan triggers. |
| **Stack Distraction** | Minor | Over-explaining ADK/Cloud Run could dilute the B2B SaaS product story. Keep the stack mentions brief and relegated to the developer overlay and export step. |