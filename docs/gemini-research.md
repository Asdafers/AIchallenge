# Strategy Memo: Winning the Google for Startups AI Agent Challenge (Track 1)

**To:** Startup Team  
**From:** Gemini CLI Advisory  
**Subject:** Strategy for Track 1 Submission - "Methodic Agent"  
**Date:** May 1, 2026

---

## 1. Winning Positioning

### The Sharpest Version
Do not position this as a "survey tool." Surveying is a legacy term for static forms. Position this as **"Methodic: The Autonomous Research Operations (ResOps) Agent."** 

The core framing should be: **"There are no useful insights without good data. Methodic replaces brittle forms with a multi-agent system that plans research, designs instruments, and conducts interactive interviews to capture clean, decision-ready data at scale."**

### Product Name: **Methodic**
*   **Why:** It implies rigor, reliability, and methodology—key concerns for B2B buyers who find "chatbots" unscientific.

### The Strongest Business Case
**The "Garbage In, Garbage Out" Crisis.** Companies are spending millions on RAG and AI analytics, but the underlying data (from customers, employees, and markets) is shallow, biased, and inconsistent. Methodic fixes the "last mile" of data ingestion.

### What to Avoid
*   **"SurveyMonkey with AI":** Sounds like a feature, not a new agent.
*   **"Interactive Chatbot":** Sounds like a support bot.
*   **"Form Generator":** Sounds like a low-value utility.

---

## 2. Differentiation

| Feature | Legacy Tools (SurveyMonkey/Typeform) | Methodic (Agentic Data Capture) |
| :--- | :--- | :--- |
| **Logic** | Fixed branching logic (If A then B). | **Declarative intent.** Agent probes until a variable is "saturated." |
| **Context** | Zero. The form doesn't know your product. | **Deep Context.** Uses MCP to pull CRM/Product data to personalize probes. |
| **Engagement** | High drop-off due to length. | **Conversational.** Higher completion due to interactive feedback loops. |
| **Data Quality** | Shallow open-ends ("It was okay"). | **Active probing.** "You said it was okay; specifically, was it the UI or the speed?" |
| **Structure** | Unstructured text needs human coding. | **Real-time thematic coding.** Returns structured variables + evidence. |

---

## 3. Research and Methodology

To win, you must prove this is "Methodic," not just "Chatty."

### Key Concepts to Incorporate
*   **Variable Saturation:** The agent stops asking about a topic only when it has high confidence in the answer. Show a "Saturation Score" in the demo.
*   **Latent Theme Detection:** The QA agent should show how it grouped 50 interviews into 5 core themes using qualitative coding methodologies.
*   **Bias Mitigation:** The Methodology Agent should explicitly flag "Leading Question Risks" in the design phase.
*   **Triangulation:** Show how the agent uses MCP to check a user's claim ("The UI is slow") against real telemetry data ("Logs show 1200ms latency") in real-time.

### Metrics to Show in Demo
*   **Ambiguity Reduction %:** Number of vague answers clarified by follow-up probes.
*   **Variable Completion Rate:** % of decision-critical variables successfully captured vs. static baseline.
*   **Thematic Traceability:** Ability to click a data point and see the exact transcript snippet (evidence).

---

## 4. Agent Architecture

Use a **Collaborative Specialist** design managed by **ADK**.

### Agent Roles & Tool Boundaries
1.  **Organizer Agent (The PM):** Orchestrates the workflow. Tools: `project_config_tool`, `handoff_manager`.
2.  **Methodology Agent (The Scientist):** Grounds questions in research logic. Tools: `bias_detector`, `methodology_lookup_mcp`.
3.  **Question Design Agent (The Architect):** Creates the schema and branching. Tools: `schema_validator`, `wording_optimizer`.
4.  **Survey Agent Pool (The Researchers):** Conducts interviews. Memory: **Participant-specific state** (prevents repeating questions). Tools: `probing_engine`, `context_lookup_mcp`.
5.  **Data Quality Agent (The Analyst):** Validates and normalizes. Tools: `thematic_coder`, `bigquery_export`.

### The Google Stack
*   **Orchestration:** **ADK**. This is the challenge mandate. Use it to manage the complex handoffs between Organizer and Methodology agents.
*   **Intelligence:** **Gemini 1.5 Pro**. Use its large context window to keep the entire research brief and previous participant responses in memory during a session.
*   **External Access:** **MCP**. 
    *   *CRM MCP:* Pull user segments and historical data.
    *   *Knowledge MCP:* Access academic research methodology papers for grounding.
*   **Deployment:** **Cloud Run**. Ideal for the scaling survey pool. Use **BigQuery** for the final clean dataset storage.

---

## 5. Demo Strategy (3-5 Minutes)

### Scenario: SaaS Trial Conversion "Why didn't you buy?"
*   **0:00-1:00 (The Setup):** Organizer talks to the **Organizer Agent**. "I want to know why users from the Enterprise segment aren't converting." The agent asks about goals and decisions.
*   **1:00-1:45 (Agentic Planning):** The **Methodology Agent** interrupts: "To get a 95% confidence level, we need to probe specifically on 'Security Concerns' for this segment." The **Question Design Agent** builds a visual map of the interview flow.
*   **1:45-2:45 (The Interview):** Show a split screen. 
    *   Left: Static survey (User types "Price"). Ends. 
    *   Right: **Methodic Agent**. "Price can mean many things. Are we too high compared to [Competitor], or is it a budget cycle issue?" User: "Budget cycle." Agent: "Got it, I'll tag this for Q3 follow-up."
*   **2:45-3:30 (The Payload):** Show the **BigQuery dashboard**. Clean, structured data. "Methodic clarified 42% of vague 'Price' answers into 'Budget Cycle' or 'ROI proof' issues."

---

## 6. Judging Rubric Strategy

*   **Technical Implementation (30%):** Explicitly name-drop **ADK** and **MCP**. Show the "Agent-to-Agent" handoff log in a developer console view.
*   **Business Case (30%):** Quantify "Time to Insight." Static research takes 4 weeks. Methodic takes 48 hours from objective to clean data.
*   **Innovation (20%):** Highlight **declarative data capture** (agents pursuing variables, not just scripts). This is the "clearly agentic" part.
*   **Demo (20%):** Use a high-fidelity React dashboard for the "Research Brief" view. Make it look like a professional enterprise tool.

---

## 7. Risks and Pitfalls

*   **The "Chatbot" Trap:** If it feels like a standard chatbot, you lose on Innovation. Ensure the agent uses **Tools** (MCP) and **Planning** (ADK).
*   **Scope Creep:** Do not build the analysis dashboard. Focus 100% on **Data Capture**. Export to BigQuery/Looker and stop there.
*   **Hallucination:** Ensure the Survey Agent is strictly grounded in the approved "Question Pool."

---

## 8. Final Recommendations (Top 10)

1.  **Build the "Variable Saturation" logic first.** It's the strongest proof of agency.
2.  **Standardize the MCP tool for "Context Lookup."** Showing an agent pull a user's name and last product action is high-signal.
3.  **Create a "Developer View" for the demo.** Show the agents talking to each other behind the scenes.
4.  **Use simulated participants for the demo.** Don't rely on live humans.
5.  **Focus on "Thematic Traceability."** Judges love seeing a data point linked back to a transcript.
6.  **Deploy on Cloud Run early.** Proves production readiness.
7.  **Use Vertex AI Search** to ground the Methodology Agent in real research standards.
8.  **Define a "Confidence Score" for every captured variable.**
9.  **Build a "Visual Flow Map"** that updates as the Organizer Agent designs the study.
10. **Anchor on "Clean Data for AI Teams."** It’s a very 2026-relevant problem.

---
*End of Memo*
